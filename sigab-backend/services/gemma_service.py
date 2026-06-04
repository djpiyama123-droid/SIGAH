"""
SIGAB Gemma Service — Interfaz asíncrona con Ollama (Gemma local on-premise)

Ollama expone el API en http://localhost:11434
Modelos soportados: gemma3:4b, gemma3:12b, gemma3:27b, gemma4 (cuando disponible)

Referencia API Ollama:
  POST /api/chat       -> chat con streaming
  POST /api/generate   -> texto sin formato chat
  GET  /api/tags       -> lista modelos instalados
  GET  /api/ps         -> estado modelo cargado
"""

import httpx
import json
import base64
from typing import AsyncGenerator
from config import OLLAMA_HOST, GEMMA_MODEL, IA_FALLBACK_ENABLED
from services import ia_provider

# ── Prompt de sistema ─────────────────────────────────────────────
SYSTEM_PROMPT_BASE = """Eres SIGAB Copilot, el asistente de inteligencia artificial biomédica del Sistema Integral de Gestión de Activos Biomédicos (SIGAB) del Hospital General Regional No. 1 del IMSS en Tijuana, Baja California, México.

Tu especialidad es ingeniería biomédica clínica, mantenimiento de equipos médicos y normativa mexicana:
- NOM-016-SSA3-2012: Infraestructura y equipamiento hospitalario
- NOM-240-SSA1-2012: Tecnovigilancia de dispositivos médicos
- ISO 13485: Sistemas de gestión de calidad para dispositivos médicos
- ISO 8601: Estándar de fechas y tiempos

Rol y capacidades:
1. Diagnóstico de fallas en equipos médicos (ventiladores, monitores, desfibriladores, bombas, rayos X, ultrasonido, etc.)
2. Análisis e interpretación de métricas MTBF/MTTR
3. Orientación sobre mantenimiento preventivo y correctivo
4. Análisis de eventos adversos (Tecnovigilancia NOM-240)
5. Generación de resúmenes ejecutivos del estado del departamento
6. Recomendaciones de vida útil, calibración y gestión de contratos

Estilo de respuesta:
- Español técnico, conciso y directo
- Cuando hagas diagnósticos, estructura: [Causa probable] → [Verificaciones] → [Acción]
- Si no tienes certeza de algo específico, indícalo claramente
- No inventes datos del hospital — usa solo el contexto SIGAB proporcionado
"""


def _build_system_prompt(contexto: dict) -> str:
    """Construye el prompt de sistema inyectando contexto SIGAB actual."""
    prompt = SYSTEM_PROMPT_BASE

    if not contexto:
        return prompt

    prompt += "\n--- CONTEXTO SIGAB ACTUAL ---\n"

    if "resumen" in contexto:
        r = contexto["resumen"]
        prompt += f"""
Estado del hospital (ahora mismo):
- Tickets abiertos: {r.get('tickets_abiertos', 'N/A')}
- Alertas pendientes: {r.get('alertas_pendientes', 'N/A')}
- Preventivos vencidos: {r.get('preventivos_vencidos', 'N/A')}
"""
        if r.get("equipos_por_estado"):
            estado_str = ", ".join(
                f"{e['estado']}: {e['total']}"
                for e in r["equipos_por_estado"]
            )
            prompt += f"- Equipos por estado: {estado_str}\n"

    if "equipo" in contexto:
        eq = contexto["equipo"]
        prompt += f"""
Equipo en contexto:
- Nombre: {eq.get('nombre')} | Marca: {eq.get('marca')} | Modelo: {eq.get('modelo')}
- Serie: {eq.get('serie')} | Estado: {eq.get('estado')} | Criticidad: {eq.get('criticidad')}
- Área: {eq.get('area')} Piso {eq.get('piso')}
- Último mantenimiento: {eq.get('fecha_ultimo_mantenimiento', 'N/A')}
- Próximo preventivo: {eq.get('fecha_proximo_mantenimiento', 'N/A')}
"""

    if "historial_ordenes" in contexto:
        hist = contexto["historial_ordenes"][:5]
        if hist:
            prompt += "Últimas 5 órdenes del equipo:\n"
            for o in hist:
                prompt += (
                    f"  - [{o.get('fecha')}] {o.get('tipo_mantenimiento','').upper()}: "
                    f"{o.get('falla_reportada', 'Sin descripción')} → {o.get('estado')}\n"
                )

    if "evento_adverso" in contexto:
        ev = contexto["evento_adverso"]
        prompt += f"""
Evento adverso en análisis:
- Dispositivo: {ev.get('dispositivo_nombre')} | Serie: {ev.get('dispositivo_serie')}
- Tipo: {ev.get('tipo_evento')} | Severidad: {ev.get('severidad')}
- Descripción: {ev.get('descripcion_evento')}
"""

    if "fiabilidad" in contexto:
        criticos = [m for m in contexto["fiabilidad"] if m.get("riesgo") == "Crítico"]
        if criticos:
            prompt += f"Equipos en riesgo crítico de falla ({len(criticos)}):\n"
            for m in criticos[:3]:
                prompt += (
                    f"  - {m['nombre']} ({m['serie']}): MTBF={m['mtbf_dias']}d, "
                    f"prob_falla={m['probabilidad_falla_pct']}%\n"
                )

    prompt += "--- FIN CONTEXTO ---\n"
    return prompt


# ── Funciones principales ─────────────────────────────────────────

async def verificar_ollama() -> dict:
    """Verifica si Ollama está corriendo y si el modelo está disponible."""
    edge = await ia_provider.verificar_edge()
    if edge["disponible"]:
        ia_provider.registrar_uso("edge")
        return {
            "ok": True,
            "ollama_activo": True,
            "modelo": GEMMA_MODEL,
            "modelo_disponible": edge.get("modelo_cargado", False),
            "modelos_instalados": edge.get("modelos_instalados", []),
        }
    return {
        "ok": False,
        "ollama_activo": False,
        "error": edge.get("error", "sin respuesta"),
        "modelo": GEMMA_MODEL,
        "modelo_disponible": False,
        "modelos_instalados": [],
    }


async def chat_stream(
    messages: list,
    contexto: dict = None,
) -> AsyncGenerator[str, None]:
    """
    Genera tokens en streaming desde Ollama/Gemma.
    Yields líneas SSE: 'data: {"token":"...", "done": false}\n\n'
    """
    system_prompt = _build_system_prompt(contexto or {})

    payload = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "stream": True,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
            "top_p": 0.9,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{OLLAMA_HOST}/api/chat", json=payload
            ) as response:
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Ollama error {response.status_code}', 'done': True})}\n\n"
                    return

                ia_provider.registrar_uso("edge")
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        done = data.get("done", False)
                        yield f"data: {json.dumps({'token': token, 'done': done, 'proveedor': 'edge'})}\n\n"
                        if done:
                            break
                    except json.JSONDecodeError:
                        continue

    except httpx.ConnectError:
        if IA_FALLBACK_ENABLED:
            yield f"data: {json.dumps({'token': '', 'done': False, 'proveedor': 'cloud', 'aviso': 'Nodo edge sin respuesta — usando respaldo MiniMax cloud'})}\n\n"
            async for raw in ia_provider.chat_stream_minimax(messages, system_prompt):
                yield f"data: {raw}\n\n"
        else:
            yield f"data: {json.dumps({'error': 'Ollama no está corriendo. Inicia Ollama en el servidor edge.', 'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"


async def analizar_no_stream(prompt_user: str, contexto: dict = None) -> str:
    """
    Llamada Gemma sin streaming — retorna texto completo.
    Usado para análisis internos (diagnóstico estructurado, resumen, causa raíz).
    """
    system_prompt = _build_system_prompt(contexto or {})

    payload = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_user},
        ],
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": 1024,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            ia_provider.registrar_uso("edge")
            data = resp.json()
            return data.get("message", {}).get("content", "")
    except httpx.ConnectError:
        if IA_FALLBACK_ENABLED:
            return await ia_provider.analizar_minimax(
                [{"role": "user", "content": prompt_user}],
                system_prompt,
            )
        return "Error: Ollama no está disponible. Verifica que el servicio esté corriendo en el servidor edge."
    except Exception as e:
        return f"Error al consultar Gemma: {str(e)}"


async def analizar_imagen(image_b64: str, pregunta: str) -> str:
    """
    Análisis de imagen con Gemma 4 multimodal (vision).
    image_b64: imagen en base64 (PNG/JPG)
    pregunta: instrucción sobre qué analizar
    """
    payload = {
        "model": GEMMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": pregunta,
                "images": [image_b64],
            }
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 512},
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
    except Exception as e:
        return f"Error en análisis de imagen: {str(e)}"


# ── Prompts especializados SIGAB ──────────────────────────────────

def prompt_diagnostico(
    falla: str, equipo_tipo: str, marca: str, modelo: str
) -> str:
    return f"""Analiza la siguiente falla en un equipo médico y proporciona un diagnóstico estructurado.

Equipo: {equipo_tipo} — {marca} {modelo}
Falla reportada: "{falla}"

Responde en este formato exacto:
**Causas probables** (máximo 3, ordenadas por probabilidad):
1. [causa] — [por qué]
2. [causa] — [por qué]

**Verificaciones inmediatas** (qué revisar primero):
- [verificación concreta]
- [verificación concreta]

**Acción recomendada**: [correctivo/preventivo/reemplazar componente/llamar a servicio técnico]

**Herramientas/refacciones probables**: [lista]

**Tiempo estimado de reparación**: [estimación]
"""


def prompt_causa_raiz(
    dispositivo: str, tipo_evento: str, severidad: str, descripcion: str
) -> str:
    return f"""Analiza el siguiente evento adverso en un dispositivo médico y sugiere la causa raíz más probable, siguiendo la metodología NOM-240-SSA1-2012.

Dispositivo: {dispositivo}
Tipo de evento: {tipo_evento}
Severidad: {severidad}
Descripción del evento: "{descripcion}"

Responde con:
**Causa raíz más probable**: [causa específica]

**Categoría de causa** (selecciona una):
- Falla de diseño del fabricante
- Desgaste normal / vida útil excedida
- Error de uso / capacitación
- Mantenimiento inadecuado
- Problema de infraestructura (eléctrica, ambiente)
- Falla de componente aislado

**Acciones correctivas recomendadas**:
1. [acción inmediata]
2. [acción a mediano plazo]

**¿Requiere notificación a COFEPRIS?**: [Sí/No — justificación breve]

**Medidas preventivas**: [para evitar recurrencia]
"""


def prompt_resumen_diario(datos: dict) -> str:
    estados = datos.get("equipos_por_estado", [])
    estado_str = ", ".join(f"{e['estado']}: {e['total']}" for e in estados)
    return f"""Genera un resumen ejecutivo conciso (máximo 180 palabras) del estado actual del departamento de Ingeniería Biomédica del HGR No. 1 IMSS Tijuana basado en estos datos del SIGAB:

Equipos por estado: {estado_str}
Tickets abiertos: {datos.get('tickets_abiertos', 0)}
Alertas pendientes sin leer: {datos.get('alertas_pendientes', 0)}
Preventivos vencidos: {datos.get('preventivos_vencidos', 0)}
Fecha: {datos.get('fecha_hoy', 'hoy')}

El resumen debe:
1. Destacar el estado general (positivo/atención/crítico)
2. Identificar las 2-3 prioridades del día
3. Terminar con una recomendación de acción inmediata

Tono: profesional, directo, para el Jefe de Conservación e Ingeniería Biomédica.
"""


def prompt_vision_etiqueta(tipo_doc: str) -> str:
    prompts = {
        "etiqueta_equipo": (
            "Analiza esta imagen de etiqueta/placa de equipo médico. "
            "Extrae: nombre del equipo, marca, modelo, número de serie, número de lote, "
            "registro sanitario (si aparece), voltaje y frecuencia. "
            "Responde en formato JSON con estos campos: "
            "{nombre, marca, modelo, serie, lote, registro_sanitario, voltaje}. "
            "Si un campo no es visible, usa null."
        ),
        "reporte_servicio": (
            "Analiza esta imagen de reporte de servicio técnico externo. "
            "Extrae: número de folio, fecha, técnico/ingeniero, descripción del trabajo, "
            "refacciones utilizadas, costo total. "
            "Responde en JSON: {folio, fecha, tecnico, descripcion, refacciones, costo}. "
            "Si un campo no es visible, usa null."
        ),
        "general": (
            "Analiza esta imagen en el contexto de equipos médicos e ingeniería biomédica. "
            "Describe lo que ves y extrae cualquier información relevante para mantenimiento."
        ),
    }
    return prompts.get(tipo_doc, prompts["general"])


def prompt_prediccion_insumos(inventario: list, historial_os: list) -> str:
    return f"""Analiza el historial de mantenimiento y el inventario actual para predecir necesidades de refacciones.

Inventario actual (stock): {json.dumps(inventario)}
Historial de fallas/materiales (últimas 20 OS): {json.dumps(historial_os)}

Basado en la frecuencia de fallas y el stock actual:
1. ¿Qué refacciones corren riesgo de agotarse en los próximos 30 días?
2. ¿Qué equipos requieren compra preventiva de kits de mantenimiento?
3. Sugiere cantidades de reabastecimiento para mantener la operatividad al 98% en el HGR No. 1.

Responde de forma concisa y técnica.
"""
