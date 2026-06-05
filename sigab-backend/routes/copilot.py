"""
SIGAB Copilot Router — IA Local Biomédica con Gemma/Ollama

Endpoints:
  GET  /estado          → verifica Ollama + modelo disponible
  POST /chat            → chat streaming SSE
  POST /diagnostico     → análisis de falla estructurado (no streaming)
  POST /causa-raiz      → sugerencia causa raíz para Tecnovigilancia
  GET  /resumen-ia      → resumen ejecutivo narrativo del día
  POST /vision          → análisis de imagen multimodal (Gemma 4)
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import aiomysql
import base64
import json
from datetime import date

from config import get_db, GEMMA_MODEL
from auth.dependencies import get_current_user
from services import gemma_service
from services.reliability_service import obtener_metricas_fiabilidad

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────

async def _get_resumen_db(conn) -> dict:
    """Obtiene resumen rápido del dashboard para inyección de contexto."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT estado, COUNT(*) as total FROM equipos GROUP BY estado")
        estados = await cur.fetchall()

        await cur.execute(
            "SELECT COUNT(*) as total FROM ordenes_servicio WHERE estado IN ('abierta','en_progreso')"
        )
        tickets = (await cur.fetchone())["total"]

        await cur.execute("SELECT COUNT(*) as total FROM alertas WHERE leida = FALSE")
        alertas = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT COUNT(*) as total FROM preventivos_programados WHERE proxima_ejecucion <= CURDATE() AND activo = TRUE"
        )
        vencidos = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT COUNT(*) as total FROM tecnovigilancia_eventos WHERE estado NOT IN ('cerrado','cancelado')"
        )
        try:
            tv_activos = (await cur.fetchone())["total"]
        except Exception:
            tv_activos = 0

    return {
        "equipos_por_estado": [{"estado": e["estado"], "total": int(e["total"])} for e in estados],
        "tickets_abiertos": tickets,
        "alertas_pendientes": alertas,
        "preventivos_vencidos": vencidos,
        "eventos_adversos_activos": tv_activos,
        "fecha_hoy": date.today().isoformat(),
    }


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/estado")
async def estado_ollama(user: dict = Depends(get_current_user)):
    """
    Verifica estado del nodo edge IA (Ollama) y del fallback MiniMax.
    Campos clave:
      - ollama_activo:     bool (compatibilidad con frontend existente)
      - proveedor_activo:  "edge_local" | "cloud_minimax" | "no_disponible"
      - edge.online:       bool — Ollama responde en el ThinkCentre
      - fallback.configurado: bool — SIGAB_MINIMAX_API_KEY presente
    """
    resultado = await gemma_service.verificar_ollama()
    return resultado


@router.post("/chat")
async def copilot_chat(
    data: dict,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """
    Chat en streaming con Gemma. Retorna SSE.
    Body: {
      messages: [{role: "user"|"assistant", content: "..."}],
      contexto_tipo: "general"|"equipo"|"tecnovigilancia"  (opcional),
      equipo_id: int  (opcional, para inyectar contexto de equipo),
    }
    """
    messages = data.get("messages", [])
    contexto_tipo = data.get("contexto_tipo", "general")
    equipo_id = data.get("equipo_id")

    if not messages:
        raise HTTPException(status_code=400, detail="messages es requerido")

    # Construir contexto
    contexto = {}

    # Siempre incluir resumen general
    resumen = await _get_resumen_db(conn)
    contexto["resumen"] = resumen

    # Contexto específico de equipo
    if equipo_id:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM equipos WHERE id = %s", (equipo_id,))
            equipo = await cur.fetchone()
            if equipo:
                for k, v in equipo.items():
                    if hasattr(v, "isoformat"):
                        equipo[k] = v.isoformat()
                contexto["equipo"] = equipo

                await cur.execute(
                    """SELECT numero_orden, tipo_mantenimiento, estado, fecha,
                              falla_reportada, closed_at
                       FROM ordenes_servicio WHERE equipo_id = %s
                       ORDER BY fecha DESC LIMIT 8""",
                    (equipo_id,),
                )
                ordenes = await cur.fetchall()
                for o in ordenes:
                    for k, v in o.items():
                        if hasattr(v, "isoformat"):
                            o[k] = v.isoformat()
                contexto["historial_ordenes"] = ordenes

    # Métricas MTBF si se pide análisis de fiabilidad
    if contexto_tipo == "fiabilidad":
        try:
            fiabilidad = await obtener_metricas_fiabilidad(conn)
            contexto["fiabilidad"] = fiabilidad[:10]
        except Exception:
            pass

    return StreamingResponse(
        gemma_service.chat_stream(messages, contexto),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/diagnostico")
async def diagnostico_falla(
    data: dict,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """
    Diagnóstico estructurado de falla en equipo médico (sin streaming).
    Body: {
      falla: "descripción de la falla",
      equipo_id: int (opcional),
      equipo_tipo: "monitor" (opcional si no hay equipo_id),
      marca: "GE",
      modelo: "CARESCAPE B650"
    }
    """
    falla = data.get("falla", "").strip()
    if not falla:
        raise HTTPException(status_code=400, detail="falla es requerido")

    equipo_id = data.get("equipo_id")
    contexto = {}

    marca = data.get("marca", "desconocida")
    modelo = data.get("modelo", "desconocido")
    equipo_tipo = data.get("equipo_tipo", "equipo médico")

    if equipo_id:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM equipos WHERE id = %s", (equipo_id,))
            eq = await cur.fetchone()
            if eq:
                for k, v in eq.items():
                    if hasattr(v, "isoformat"):
                        eq[k] = v.isoformat()
                contexto["equipo"] = eq
                marca = eq.get("marca", marca)
                modelo = eq.get("modelo", modelo)
                equipo_tipo = eq.get("nombre", equipo_tipo)

                await cur.execute(
                    """SELECT tipo_mantenimiento, falla_reportada, estado, fecha
                       FROM ordenes_servicio WHERE equipo_id = %s
                       ORDER BY fecha DESC LIMIT 5""",
                    (equipo_id,),
                )
                ordenes = await cur.fetchall()
                for o in ordenes:
                    for k, v in o.items():
                        if hasattr(v, "isoformat"):
                            o[k] = v.isoformat()
                contexto["historial_ordenes"] = ordenes

    prompt = gemma_service.prompt_diagnostico(falla, equipo_tipo, marca, modelo)
    analisis = await gemma_service.analizar_no_stream(prompt, contexto)

    return {
        "ok": True,
        "modelo": GEMMA_MODEL,
        "falla": falla,
        "diagnostico": analisis,
        "equipo": {
            "tipo": equipo_tipo,
            "marca": marca,
            "modelo": modelo,
        },
    }


@router.post("/causa-raiz")
async def sugerir_causa_raiz(
    data: dict,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """
    Sugiere causa raíz para un evento adverso (Tecnovigilancia NOM-240).
    Body: {
      evento_id: int (opcional, carga datos automáticamente),
      dispositivo: "nombre del dispositivo" (si no hay evento_id),
      tipo_evento: "falla_funcional",
      severidad: "grave",
      descripcion: "descripción del evento"
    }
    """
    evento_id = data.get("evento_id")
    contexto = {}

    dispositivo = data.get("dispositivo", "dispositivo médico")
    tipo_evento = data.get("tipo_evento", "")
    severidad = data.get("severidad", "")
    descripcion = data.get("descripcion", "").strip()

    if evento_id:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM tecnovigilancia_eventos WHERE id = %s", (evento_id,)
            )
            ev = await cur.fetchone()
            if ev:
                for k, v in ev.items():
                    if hasattr(v, "isoformat"):
                        ev[k] = v.isoformat()
                contexto["evento_adverso"] = ev
                dispositivo = ev.get("dispositivo_nombre", dispositivo)
                tipo_evento = ev.get("tipo_evento", tipo_evento)
                severidad = ev.get("severidad", severidad)
                descripcion = ev.get("descripcion_evento", descripcion)

    if not descripcion:
        raise HTTPException(status_code=400, detail="descripcion es requerida")

    prompt = gemma_service.prompt_causa_raiz(
        dispositivo, tipo_evento, severidad, descripcion
    )
    analisis = await gemma_service.analizar_no_stream(prompt, contexto)

    return {
        "ok": True,
        "modelo": GEMMA_MODEL,
        "dispositivo": dispositivo,
        "tipo_evento": tipo_evento,
        "severidad": severidad,
        "analisis_causa_raiz": analisis,
    }


@router.get("/resumen-ia")
async def resumen_ejecutivo_ia(
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """
    Genera un resumen ejecutivo narrativo del estado actual del SIGAB.
    Útil para el reporte matutino del Jefe de Conservación.
    """
    datos = await _get_resumen_db(conn)
    prompt = gemma_service.prompt_resumen_diario(datos)
    resumen = await gemma_service.analizar_no_stream(prompt)

    return {
        "ok": True,
        "modelo": GEMMA_MODEL,
        "fecha": datos["fecha_hoy"],
        "datos_base": datos,
        "resumen_narrativo": resumen,
    }


@router.post("/vision")
async def analizar_imagen_vision(
    data: dict,
    user: dict = Depends(get_current_user),
):
    """
    Análisis de imagen con Gemma 4 multimodal (vision).
    Body: {
      imagen_b64: "base64...",
      tipo_doc: "etiqueta_equipo" | "reporte_servicio" | "general",
      pregunta_custom: "..." (opcional — sobreescribe el prompt predefinido)
    }
    """
    imagen_b64 = data.get("imagen_b64", "").strip()
    if not imagen_b64:
        raise HTTPException(status_code=400, detail="imagen_b64 es requerida")

    tipo_doc = data.get("tipo_doc", "general")
    pregunta = data.get("pregunta_custom") or gemma_service.prompt_vision_etiqueta(tipo_doc)

    # Validar que sea base64 válido
    try:
        base64.b64decode(imagen_b64[:100])
    except Exception:
        raise HTTPException(status_code=400, detail="imagen_b64 no es base64 válido")

    resultado = await gemma_service.analizar_imagen(imagen_b64, pregunta)

    # Intentar parsear JSON si el resultado lo es (para etiqueta_equipo)
    datos_extraidos = None
    if tipo_doc in ("etiqueta_equipo", "reporte_servicio"):
        try:
            inicio = resultado.find("{")
            fin = resultado.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                datos_extraidos = json.loads(resultado[inicio:fin])
        except Exception:
            pass

    return {
        "ok": True,
        "modelo": GEMMA_MODEL,
        "tipo_doc": tipo_doc,
        "analisis": resultado,
        "datos_extraidos": datos_extraidos,
    }


@router.get("/prompts-rapidos")
async def prompts_rapidos(user: dict = Depends(get_current_user)):
    """
    Retorna los prompts rápidos sugeridos para el chat.
    El frontend los muestra como botones de acceso rápido.
    """
    return {
        "prompts": [
            {
                "id": "mtbf_criticos",
                "label": "Equipos en riesgo",
                "icon": "warning",
                "texto": "¿Qué equipos tienen mayor riesgo de falla según el MTBF? Dame las acciones prioritarias.",
                "contexto_tipo": "fiabilidad",
            },
            {
                "id": "prev_vencidos",
                "label": "Preventivos vencidos",
                "icon": "calendar",
                "texto": "¿Cuántos preventivos están vencidos y cuál es la estrategia recomendada para ponerse al día?",
                "contexto_tipo": "general",
            },
            {
                "id": "nom240",
                "label": "Guía NOM-240",
                "icon": "shield",
                "texto": "¿Cuándo debo escalar un evento adverso a COFEPRIS según la NOM-240? Dame los criterios.",
                "contexto_tipo": "general",
            },
            {
                "id": "vida_util",
                "label": "Vida útil y baja",
                "icon": "clock",
                "texto": "¿Qué criterios técnicos y legales aplican para dar de baja un equipo médico en el IMSS?",
                "contexto_tipo": "general",
            },
            {
                "id": "calibracion",
                "label": "Calibración",
                "icon": "tool",
                "texto": "¿Qué equipos médicos requieren calibración periódica obligatoria según NOM-016? ¿Con qué frecuencia?",
                "contexto_tipo": "general",
            },
        ]
    }
