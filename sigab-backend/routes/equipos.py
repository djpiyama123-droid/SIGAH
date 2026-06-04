"""
routes/equipos.py — Endpoints CRUD para gestión de equipos biomédicos.

Operaciones:
  GET    /equipos/              — Listado paginado con filtros (estado, área, piso, búsqueda)
  GET    /equipos/{id}          — Detalle con últimas órdenes y traslados
  POST   /equipos/              — Alta con token QR opaco generado automáticamente
  PUT    /equipos/{id}          — Actualización con campos filtrados por rol
  DELETE /equipos/{id}          — Baja (cascade a órdenes y trazabilidad)
  GET    /equipos/public/{qr}   — Consulta pública vía escaneo QR (sin auth)
  GET    /equipos/{id}/qr       — Generar QR PNG (Segno, nivel H, 30% recuperación)
  GET    /equipos/{id}/qr/label — Etiqueta A6 imprimible (PDF)
  POST   /equipos/validar       — Triple Validación Poka-Yoke (QR + Inventario + Serie)
  PATCH  /equipos/{id}/posicion — Drag & drop en mapa interactivo

Normativas: NOM-016-SSA3-2012 (audit trail), ISO 13485 (trazabilidad)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from typing import Optional
import aiomysql
import os
import secrets
import uuid
from datetime import datetime
from config import get_db, UPLOAD_DIR, MAX_UPLOAD_MB, PUBLIC_BASE_URL
from auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    require_action,
)
from auth.permissions import (
    can,
    filter_equipo_publico,
    allowed_update_fields,
    CAMPOS_EDITABLES_TODOS,
)
from services.qr_service import generate_qr_png, generate_qr_label_a6_pdf
from services.audit_service import AuditService

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import sqlalchemy as sa
from database import get_async_session
from models.equipo import Equipo
from models.orden_servicio import OrdenServicio
from models.preventivo import PreventivoProgramado

router = APIRouter()

# ... rutas ...

@router.get("/public/{qr_token}")
async def equipo_por_qr(qr_token: str, session: AsyncSession = Depends(get_async_session)):
    """Endpoint PÚBLICO (sin auth) para escaneo QR.
    Devuelve datos básicos del equipo identificado por su qr_token opaco."""
    
    # Buscar equipo por token
    statement = select(Equipo).where(Equipo.qr_token == qr_token)
    result = await session.execute(statement)
    equipo = result.scalar_one_or_none()

    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado o QR inválido")

    # Historial resumido (últimas 5 órdenes, público)
    stmt_ordenes = select(OrdenServicio).where(OrdenServicio.equipo_id == equipo.id).order_by(OrdenServicio.fecha.desc()).limit(5)
    res_ordenes = await session.execute(stmt_ordenes)
    ordenes = res_ordenes.scalars().all()

    stmt_prev = select(PreventivoProgramado).where(
        PreventivoProgramado.equipo_id == equipo.id, 
        PreventivoProgramado.activo == True
    ).order_by(PreventivoProgramado.proxima_ejecucion.asc()).limit(3)
    res_prev = await session.execute(stmt_prev)
    preventivos = res_prev.scalars().all()

    return {
        "equipo": equipo,
        "ordenes_recientes": ordenes,
        "preventivos": preventivos,
    }


from models.mapa import ZonasMapa
from sqlmodel import func

@router.get("/areas/catalogo")
async def catalogo_areas(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
):
    stmt_areas = select(Equipo.area).where(Equipo.area != None).distinct().order_by(Equipo.area)
    res_areas = await session.execute(stmt_areas)
    areas = res_areas.scalars().all()

    stmt_pisos = select(Equipo.piso).where(Equipo.piso != None).distinct().order_by(Equipo.piso)
    res_pisos = await session.execute(stmt_pisos)
    pisos = res_pisos.scalars().all()
    
    return {"areas": areas, "pisos": pisos}


@router.get("/zonas/catalogo")
async def catalogo_zonas(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
):
    """Lista las zonas del mapa para el formulario de alta/edición de equipos."""
    stmt = select(ZonasMapa).where(ZonasMapa.activa == True).order_by(ZonasMapa.orden, ZonasMapa.nombre)
    res = await session.execute(stmt)
    zonas = res.scalars().all()
    return {"zonas": zonas}


@router.post("/")
async def crear_equipo(
    data: dict,
    user: dict = Depends(require_action("create_equipo")),
    session: AsyncSession = Depends(get_async_session),
):
    """Crea un nuevo equipo biomédico en el inventario."""
    if not data.get("nombre") or not data.get("serie"):
        raise HTTPException(status_code=400, detail="Nombre y serie son obligatorios")

    # Crear instancia del modelo
    nuevo_equipo = Equipo(**data)
    
    # Valores por defecto y token
    if not nuevo_equipo.estado:
        nuevo_equipo.estado = "operativo"
    if not nuevo_equipo.criticidad:
        nuevo_equipo.criticidad = "media"
    if nuevo_equipo.pos_x is None:
        nuevo_equipo.pos_x = 50.0
    if nuevo_equipo.pos_y is None:
        nuevo_equipo.pos_y = 50.0
    
    nuevo_equipo.qr_token = secrets.token_urlsafe(12)[:16]

    try:
        session.add(nuevo_equipo)
        await session.commit()
        await session.refresh(nuevo_equipo)
        
        # Auditoría NOM-016
        await AuditService.log_event(
            usuario_id=user["id"],
            accion="CREATE_EQUIPO",
            entidad="equipos",
            entidad_id=nuevo_equipo.id,
            datos=data
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail=f"Error al crear: {str(e)}")

    return {"ok": True, "id": nuevo_equipo.id, "qr_token": nuevo_equipo.qr_token, "mensaje": f"Equipo '{nuevo_equipo.nombre}' creado"}


from models.trazabilidad import Trazabilidad

@router.delete("/{equipo_id}")
async def eliminar_equipo(
    equipo_id: int,
    user: dict = Depends(require_action("delete_equipo")),
    session: AsyncSession = Depends(get_async_session),
):
    """Elimina un equipo del inventario (cascade a trazabilidad)."""
    # Buscar equipo
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    nombre_equipo = equipo.nombre
    imagen_url = equipo.imagen_url

    try:
        # Liberar referencias en órdenes para no romper FK (si no es ON DELETE CASCADE)
        # Nota: En SQLAlchemy/SQLModel podemos configurar la relación, 
        # pero aquí hacemos el update manual para replicar la lógica original.
        stmt_cleanup = sa.update(OrdenServicio).where(OrdenServicio.equipo_id == equipo_id).values(equipo_id=None)
        await session.execute(stmt_cleanup)
        
        await session.delete(equipo)
        await session.commit()

        # Auditoría NOM-016
        await AuditService.log_event(
            usuario_id=user["id"],
            accion="DELETE_EQUIPO",
            entidad="equipos",
            entidad_id=equipo_id,
            datos={"nombre": nombre_equipo}
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

    # Borrar imagen física si existía
    if imagen_url:
        try:
            ruta = imagen_url.lstrip("/")
            if os.path.isfile(ruta):
                os.remove(ruta)
        except Exception:
            pass

    return {"ok": True, "mensaje": f"Equipo '{nombre_equipo}' eliminado"}


@router.post("/{equipo_id}/imagen")
async def subir_imagen_equipo(
    equipo_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(require_action("edit_equipo")),
    session: AsyncSession = Depends(get_async_session),
):
    """Sube una imagen PNG/JPG y la asocia al equipo."""
    extensiones_validas = {".png", ".jpg", ".jpeg", ".webp"}
    nombre_original = file.filename or "imagen.png"
    ext = os.path.splitext(nombre_original)[1].lower()

    if ext not in extensiones_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Usa: {', '.join(extensiones_validas)}",
        )

    contenido = await file.read()
    if len(contenido) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Archivo excede {MAX_UPLOAD_MB} MB")

    # Guardar bajo static/uploads/equipos/
    carpeta = os.path.join("static", "uploads", "equipos")
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = f"eq_{equipo_id}_{uuid.uuid4().hex[:8]}{ext}"
    ruta_disco = os.path.join(carpeta, nombre_archivo)

    with open(ruta_disco, "wb") as f:
        f.write(contenido)

    # URL servida vía /static
    url_publica = f"/static/uploads/equipos/{nombre_archivo}"

    # Buscar equipo
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        os.remove(ruta_disco)
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    # Borrar imagen anterior si existe
    if equipo.imagen_url:
        try:
            anterior = equipo.imagen_url.lstrip("/")
            if os.path.isfile(anterior):
                os.remove(anterior)
        except Exception:
            pass

    equipo.imagen_url = url_publica
    await session.commit()

    return {"ok": True, "imagen_url": url_publica}


@router.get("/{equipo_id}/historial")
async def historial_equipo(equipo_id: int, session: AsyncSession = Depends(get_async_session)):
    """Devuelve historial completo de órdenes y traslados para el panel de Ficha Técnica."""
    from models.orden_servicio import EVIDENCIA_OS
    
    stmt_ordenes = select(OrdenServicio).where(OrdenServicio.equipo_id == equipo_id).order_by(OrdenServicio.fecha.desc(), OrdenServicio.id.desc()).limit(50)
    res_ordenes = await session.execute(stmt_ordenes)
    ordenes = res_ordenes.scalars().all()

    orden_ids = [o.id for o in ordenes]
    evidencias_map = {}
    if orden_ids:
        stmt_ev = select(EVIDENCIA_OS).where(EVIDENCIA_OS.orden_id.in_(orden_ids), EVIDENCIA_OS.tipo == 'documento')
        res_ev = await session.execute(stmt_ev)
        for ev in res_ev.scalars().all():
            evidencias_map[ev.orden_id] = ev.ruta_archivo

    ordenes_list = []
    for o in ordenes:
        od = o.model_dump()
        od["pdf_url"] = evidencias_map.get(o.id)
        ordenes_list.append(od)

    stmt_traslados = select(Trazabilidad).where(Trazabilidad.equipo_id == equipo_id).order_by(Trazabilidad.fecha_movimiento.desc()).limit(50)
    res_traslados = await session.execute(stmt_traslados)
    traslados = res_traslados.scalars().all()

    stmt_preventivos = select(PreventivoProgramado).where(
        PreventivoProgramado.equipo_id == equipo_id, 
        PreventivoProgramado.activo == True
    ).order_by(PreventivoProgramado.proxima_ejecucion.asc())
    res_preventivos = await session.execute(stmt_preventivos)
    preventivos = res_preventivos.scalars().all()

    return {
        "equipo_id": equipo_id,
        "ordenes": ordenes_list,
        "traslados": [t.model_dump() for t in traslados],
        "preventivos": [p.model_dump() for p in preventivos],
    }


@router.get("/")
async def listar_equipos(
    estado: Optional[str] = None,
    area: Optional[str] = None,
    piso: Optional[str] = None,
    buscar: Optional[str] = None,
    criticidad: Optional[str] = None,
    tipo_equipo: Optional[str] = None,
    marca: Optional[str] = None,
    zona_id: Optional[int] = None,
    clase_cofepris: Optional[str] = None,
    orden: Optional[str] = "nombre",
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Equipo)
    count_query = select(func.count()).select_from(Equipo)
    
    # Filtros dinámicos
    conditions = []
    if estado:
        conditions.append(Equipo.estado == estado)
    if area:
        conditions.append(Equipo.area.contains(area))
    if piso:
        conditions.append(Equipo.piso == piso)
    if criticidad:
        conditions.append(Equipo.criticidad == criticidad)
    if tipo_equipo:
        conditions.append(Equipo.tipo_equipo == tipo_equipo)
    if marca:
        conditions.append(Equipo.marca.contains(marca))
    if zona_id:
        conditions.append(Equipo.zona_id == zona_id)
    if clase_cofepris:
        conditions.append(Equipo.clase_cofepris == clase_cofepris)
    if buscar:
        conditions.append(
            sa.or_(
                Equipo.nombre.contains(buscar),
                Equipo.serie.contains(buscar),
                Equipo.marca.contains(buscar),
                Equipo.modelo.contains(buscar),
                Equipo.inventario.contains(buscar),
                Equipo.ubicacion.contains(buscar),
            )
        )
    
    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    # Ordenamiento
    order_map = {
        "nombre": Equipo.nombre.asc(),
        "nombre_desc": Equipo.nombre.desc(),
        "marca": Equipo.marca.asc(),
        "estado": sa.case(
            (Equipo.estado == 'fuera_servicio', 1),
            (Equipo.estado == 'en_mantenimiento', 2),
            (Equipo.estado == 'en_traslado', 3),
            (Equipo.estado == 'operativo', 4),
            else_=5
        ),
        "criticidad": sa.case(
            (Equipo.criticidad == 'alta', 1),
            (Equipo.criticidad == 'media', 2),
            (Equipo.criticidad == 'baja', 3),
            else_=4
        ),
        "serie": Equipo.serie.asc(),
        "area": Equipo.area.asc(),
        "reciente": Equipo.created_at.desc(),
    }
    query = query.order_by(order_map.get(orden, Equipo.nombre.asc()))
    query = query.limit(limit).offset(offset)
    
    res = await session.execute(query)
    equipos = res.scalars().all()

    # Total count con los mismos filtros
    total = (await session.execute(count_query)).scalar()

    # Catálogos únicos para filtros del frontend
    stmt_marcas = select(Equipo.marca).distinct().order_by(Equipo.marca)
    marcas_disponibles = (await session.execute(stmt_marcas)).scalars().all()
    
    stmt_tipos = select(Equipo.tipo_equipo).distinct().order_by(Equipo.tipo_equipo)
    tipos_disponibles = (await session.execute(stmt_tipos)).scalars().all()

    # Convert to dict and filter confidential
    equipos_list = [e.model_dump() for e in equipos]
    if not can(user, "view_confidential"):
        equipos_list = [filter_equipo_publico(e) for e in equipos_list]

    # Inyectar conteo de tickets abiertos (órdenes abiertas/en_progreso) por equipo
    if equipos_list:
        equipo_ids = [e["id"] for e in equipos_list]
        stmt_tickets = (
            select(OrdenServicio.equipo_id, func.count(OrdenServicio.id).label("cnt"))
            .where(
                OrdenServicio.equipo_id.in_(equipo_ids),
                OrdenServicio.estado.in_(["abierta", "en_progreso"]),
            )
            .group_by(OrdenServicio.equipo_id)
        )
        res_tickets = await session.execute(stmt_tickets)
        tickets_map = {r[0]: r[1] for r in res_tickets.all()}
        for eq in equipos_list:
            eq["tickets_abiertos"] = tickets_map.get(eq["id"], 0)

    return {
        "equipos": equipos_list,
        "total": total,
        "limit": limit,
        "offset": offset,
        "catalogos": {
            "marcas": marcas_disponibles,
            "tipos": tipos_disponibles,
        }
    }


@router.get("/{equipo_id}")
async def obtener_equipo(
    equipo_id: int,
    user: Optional[dict] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
):
    # Nota: v_dashboard_equipos es una vista, SQLModel puede mapearla si definimos el modelo,
    # pero por ahora usamos Equipo directamente o hacemos un join.
    # Dado que es AG-01, priorizamos el uso de modelos.
    equipo = await session.get(Equipo, equipo_id)

    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    stmt_ordenes = select(OrdenServicio).where(OrdenServicio.equipo_id == equipo_id).order_by(OrdenServicio.fecha.desc()).limit(10)
    res_ordenes = await session.execute(stmt_ordenes)
    ordenes = res_ordenes.scalars().all()

    stmt_traslados = select(Trazabilidad).where(Trazabilidad.equipo_id == equipo_id).order_by(Trazabilidad.fecha_movimiento.desc()).limit(5)
    res_traslados = await session.execute(stmt_traslados)
    traslados = res_traslados.scalars().all()

    equipo_dict = equipo.model_dump()
    if not can(user, "view_confidential"):
        equipo_dict = filter_equipo_publico(equipo_dict)
        ordenes = []
        traslados = []

    return {
        "equipo": equipo_dict, 
        "ordenes": [o.model_dump() for o in ordenes], 
        "traslados": [t.model_dump() for t in traslados]
    }


@router.patch("/{equipo_id}/posicion")
async def actualizar_posicion(
    equipo_id: int,
    body: dict,
    user: dict = Depends(require_action("edit_equipo")),
    session: AsyncSession = Depends(get_async_session),
):
    """Guarda nueva posición X/Y después de drag & drop en el mapa."""
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    equipo.pos_x = float(body.get("pos_x", 50))
    equipo.pos_y = float(body.get("pos_y", 50))
    equipo.zona_id = body.get("zona_id")

    await session.commit()
    return {"ok": True}

from models.modulos_extra import PokaYokeLog

@router.put("/{equipo_id}")
async def actualizar_equipo(
    equipo_id: int,
    data: dict,
    user: dict = Depends(require_action("edit_equipo")),
    session: AsyncSession = Depends(get_async_session),
):
    """Actualiza campos del equipo. Los campos permitidos dependen del rol."""
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    campos_permitidos = allowed_update_fields(user)
    updates = {k: v for k, v in data.items() if k in campos_permitidos}

    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos válidos para actualizar con tu rol")

    for k, v in updates.items():
        setattr(equipo, k, v)

    try:
        await session.commit()
        
        # Auditoría NOM-016
        await AuditService.log_event(
            usuario_id=user["id"],
            accion="UPDATE_EQUIPO",
            entidad="equipos",
            entidad_id=equipo_id,
            datos=updates
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

    return {"ok": True, "mensaje": f"Equipo {equipo_id} actualizado"}


@router.get("/{equipo_id}/qr/info")
async def obtener_info_qr(
    equipo_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Devuelve el token y la URL canónica embebida en el QR del equipo.
    Usado por el frontend para mostrar exactamente la misma URL que se codifica
    en el PNG, sin divergencias basadas en window.location.origin."""
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    # Lazy-create token si el equipo antiguo no lo tiene
    token = equipo.qr_token
    if not token:
        token = secrets.token_urlsafe(12)[:16]
        equipo.qr_token = token
        await session.commit()

    url = f"{PUBLIC_BASE_URL}/equipo/{token}"
    return {
        "equipo_id": equipo.id,
        "qr_token": token,
        "url": url,
        "public_base_url": PUBLIC_BASE_URL,
    }


@router.get("/{equipo_id}/qr")
async def generar_qr(
    equipo_id: int,
    user: dict = Depends(require_action("regenerar_qr")),
    session: AsyncSession = Depends(get_async_session),
):
    """Genera un QR PNG para el equipo con token opaco."""
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    token = equipo.qr_token
    if not token:
        token = secrets.token_urlsafe(12)[:16]
        equipo.qr_token = token
        await session.commit()

    url = f"{PUBLIC_BASE_URL}/equipo/{token}"
    png_bytes = generate_qr_png(url)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=qr_equipo_{equipo_id}.png"},
    )


@router.get("/{equipo_id}/qr/label")
async def generar_etiqueta_qr(
    equipo_id: int,
    user: dict = Depends(require_action("regenerar_qr")),
    session: AsyncSession = Depends(get_async_session),
):
    """Genera una etiqueta A6 imprimible (PDF) con QR + datos del equipo."""
    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    token = equipo.qr_token
    if not token:
        token = secrets.token_urlsafe(12)[:16]
        equipo.qr_token = token
        await session.commit()

    url = f"{PUBLIC_BASE_URL}/equipo/{token}"
    pdf_bytes = generate_qr_label_a6_pdf(equipo.model_dump(), url)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=etiqueta_equipo_{equipo_id}.pdf"},
    )


@router.post("/validar")
async def validar_poka_yoke(
    data: dict,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Implementa Triple Validación (Poka-Yoke): QR + Inventario + Serie."""
    qr_token = data.get("qr_token")
    inventario = (data.get("inventario") or "").strip()
    serie = (data.get("serie") or "").strip()

    if not qr_token or not inventario or not serie:
        raise HTTPException(status_code=400, detail="Faltan datos para la triple validación")

    # Buscar equipo por QR
    stmt = select(Equipo).where(Equipo.qr_token == qr_token)
    res = await session.execute(stmt)
    equipo = res.scalar_one_or_none()

    es_valido = False
    match_inventario = False
    match_serie = False
    error_msg = ""

    if equipo:
        match_inventario = (equipo.inventario == inventario)
        match_serie = (equipo.serie == serie)
        es_valido = match_inventario and match_serie
        
        if not es_valido:
            error_msg = f"Inconsistencia: Inventario={match_inventario}, Serie={match_serie}"
    else:
        error_msg = "Token QR no reconocido"

    # Registrar el intento (Log Poka-Yoke)
    log = PokaYokeLog(
        equipo_id=equipo.id if equipo else None,
        tecnico_id=user["id"],
        qr_escaneado=qr_token,
        inventario_leido=inventario,
        serie_leida=serie,
        es_valido=es_valido,
        error_detalle=error_msg
    )
    session.add(log)
    await session.commit()

    return {
        "ok": es_valido,
        "equipo": equipo.model_dump() if (es_valido and equipo) else None,
        "detail": error_msg if not es_valido else "Validación triple exitosa",
        "matches": {
            "inventario": match_inventario,
            "serie": match_serie
        }
    }


# ── UDI (Unique Device Identifier) — Industria 4.0 ────────────────

@router.patch("/{equipo_id}/udi")
async def registrar_udi(
    equipo_id: int,
    data: dict,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Registra o actualiza el código UDI grabado en un equipo biomédico.

    El código UDI (Unique Device Identifier) es el identificador grabado
    físicamente con la pistola láser, conforme a GS1-128 / GS1 DataMatrix.

    Body:
      {
        "udi_code": "01084700010046001724103110GTIN...",
        "laser_grabado_at": "2026-06-04T10:30:00"  (opcional, default=ahora)
      }

    Requiere permiso `edit_equipo`. Genera registro en log_actividad (NOM-016).
    """
    if not can(user, "edit_equipo"):
        raise HTTPException(status_code=403, detail="Sin permiso para editar equipos")

    udi_code = (data.get("udi_code") or "").strip()
    if not udi_code:
        raise HTTPException(status_code=400, detail="udi_code es requerido")

    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    udi_anterior = equipo.udi_code
    equipo.udi_code = udi_code
    equipo.laser_grabado_at = (
        datetime.fromisoformat(data["laser_grabado_at"])
        if data.get("laser_grabado_at")
        else datetime.utcnow()
    )
    equipo.updated_at = datetime.utcnow()

    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar UDI: {exc}")

    # Audit trail NOM-016
    await AuditService.log_event(
        usuario_id=user["id"],
        accion="udi_grabado",
        entidad="equipos",
        entidad_id=equipo_id,
        datos={"udi_code": udi_code, "udi_anterior": udi_anterior},
        session=session,
    )

    return {
        "ok": True,
        "equipo_id": equipo_id,
        "udi_code": udi_code,
        "laser_grabado_at": equipo.laser_grabado_at.isoformat(),
        "mensaje": "Código UDI registrado correctamente",
    }
