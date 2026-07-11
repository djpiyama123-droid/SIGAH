"""
routes/scan3d.py — Registros de escaneo 3D (MIRACO Plus)

El escáner de metrología MIRACO Plus genera nube de puntos 3D de cada
equipo biomédico. Estos registros documentan las dimensiones físicas
reales como evidencia de trazabilidad de activos (Industria 4.0 / NOM-016).

Endpoints:
  POST /scan3d/              — Registrar nuevo escaneo 3D
  GET  /scan3d/equipo/{id}   — Listar escaneos por equipo
  GET  /scan3d/{id}          — Detalle de un escaneo
"""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from auth.dependencies import get_current_user
from database import get_async_session
from models.scan3d import Scan3DRegistro
from models.equipo import Equipo

router = APIRouter()

_RESULTADOS_VALIDOS = {"conforme", "no_conforme", "pendiente_revision"}


@router.post("/")
async def registrar_scan3d(
    data: dict,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Registra un nuevo escaneo 3D de metrología (MIRACO Plus).

    Body:
      {
        "equipo_id": 1,
        "archivo_ref": "/scans/2026-06-04/monitor_b650_scan01.ply",
        "formato_archivo": "PLY",           (STL | PLY | OBJ | E57 | XYZ)
        "mediciones_json": {                (dimensiones en mm)
          "largo_mm": 350,
          "ancho_mm": 280,
          "alto_mm": 120,
          "peso_kg": 4.5
        },
        "resultado": "conforme",            (conforme | no_conforme | pendiente_revision)
        "observaciones": "Texto libre...",
        "fecha_scan": "2026-06-04T10:30:00" (opcional, default=ahora)
      }
    """
    equipo_id = data.get("equipo_id")
    if not equipo_id:
        raise HTTPException(status_code=400, detail="equipo_id es requerido")

    equipo = await session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    resultado = data.get("resultado", "conforme")
    if resultado not in _RESULTADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"resultado debe ser uno de: {sorted(_RESULTADOS_VALIDOS)}",
        )

    mediciones = data.get("mediciones_json")
    mediciones_str: Optional[str] = None
    if mediciones is not None:
        if isinstance(mediciones, dict):
            mediciones_str = json.dumps(mediciones, ensure_ascii=False)
        elif isinstance(mediciones, str):
            # Validar que sea JSON válido
            try:
                json.loads(mediciones)
                mediciones_str = mediciones
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="mediciones_json debe ser JSON válido")

    fecha_scan_raw = data.get("fecha_scan")
    fecha_scan = (
        datetime.fromisoformat(fecha_scan_raw)
        if fecha_scan_raw
        else datetime.now(timezone.utc)
    )

    scan = Scan3DRegistro(
        equipo_id=equipo_id,
        archivo_ref=data.get("archivo_ref"),
        formato_archivo=(data.get("formato_archivo") or "").upper() or None,
        mediciones_json=mediciones_str,
        resultado=resultado,
        observaciones=data.get("observaciones"),
        tecnico_id=user["id"],
        fecha_scan=fecha_scan,
    )
    session.add(scan)

    try:
        await session.commit()
        await session.refresh(scan)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar escaneo: {exc}")

    return {
        "ok": True,
        "id": scan.id,
        "equipo_id": equipo_id,
        "equipo_nombre": equipo.nombre,
        "equipo_serie": equipo.serie,
        "resultado": scan.resultado,
        "fecha_scan": scan.fecha_scan.isoformat(),
        "mensaje": "Escaneo 3D registrado correctamente",
    }


@router.get("/equipo/{equipo_id}")
async def listar_scans_equipo(
    equipo_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Lista todos los escaneos 3D registrados para un equipo, más reciente primero."""
    query = (
        select(Scan3DRegistro)
        .where(Scan3DRegistro.equipo_id == equipo_id)
        .order_by(Scan3DRegistro.fecha_scan.desc())
    )
    result = await session.execute(query)
    scans = result.scalars().all()

    scans_out = []
    for s in scans:
        d = s.model_dump()
        d["fecha_scan"] = s.fecha_scan.isoformat() if s.fecha_scan else None
        d["created_at"] = s.created_at.isoformat() if s.created_at else None
        # Parsear mediciones JSON para respuesta legible
        if s.mediciones_json:
            try:
                d["mediciones"] = json.loads(s.mediciones_json)
            except json.JSONDecodeError:
                d["mediciones"] = None
        else:
            d["mediciones"] = None
        scans_out.append(d)

    return {"scans": scans_out, "total": len(scans_out)}


@router.get("/{scan_id}")
async def detalle_scan(
    scan_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Detalle completo de un registro de escaneo 3D."""
    scan = await session.get(Scan3DRegistro, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")

    d = scan.model_dump()
    d["fecha_scan"] = scan.fecha_scan.isoformat() if scan.fecha_scan else None
    d["created_at"] = scan.created_at.isoformat() if scan.created_at else None
    if scan.mediciones_json:
        try:
            d["mediciones"] = json.loads(scan.mediciones_json)
        except json.JSONDecodeError:
            d["mediciones"] = None
    else:
        d["mediciones"] = None

    return d
