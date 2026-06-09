from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from auth.dependencies import get_current_user
from sqlmodel import select, or_, func, update
from sqlmodel.ext.asyncio.session import AsyncSession
from database import get_async_session
from models.preventivo import PreventivoProgramado
from models.equipo import Equipo
from models.usuario import Usuario
from datetime import date, timedelta

router = APIRouter()


@router.get("/")
async def listar_preventivos(
    vencidos: Optional[bool] = None,
    equipo_id: Optional[int] = None,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(
        PreventivoProgramado, 
        Equipo.nombre.label("equipo_nombre"), 
        Equipo.serie.label("equipo_serie"),
        Equipo.marca.label("equipo_marca"), 
        Equipo.area.label("equipo_area"),
        Usuario.nombre.label("tecnico_nombre")
    ).join(Equipo, PreventivoProgramado.equipo_id == Equipo.id)\
     .outerjoin(Usuario, PreventivoProgramado.tecnico_asignado_id == Usuario.id)\
     .where(PreventivoProgramado.activo == True)
    
    if vencidos is True:
        query = query.where(PreventivoProgramado.proxima_ejecucion <= date.today())
    if equipo_id:
        query = query.where(PreventivoProgramado.equipo_id == equipo_id)

    query = query.order_by(PreventivoProgramado.proxima_ejecucion.asc())
    
    result = await session.execute(query)
    rows = result.all()
    
    preventivos_list = []
    for pp, eq_nom, eq_ser, eq_mar, eq_area, tech_nom in rows:
        d = pp.model_dump()
        d["equipo_nombre"] = eq_nom
        d["equipo_serie"] = eq_ser
        d["equipo_marca"] = eq_mar
        d["equipo_area"] = eq_area
        d["tecnico_nombre"] = tech_nom
        preventivos_list.append(d)

    return {"preventivos": preventivos_list, "total": len(preventivos_list)}


@router.post("/")
async def crear_preventivo(
    data: dict, 
    user: dict = Depends(get_current_user), 
    session: AsyncSession = Depends(get_async_session)
):
    nuevo_pp = PreventivoProgramado(**data)
    if not nuevo_pp.frecuencia_dias:
        nuevo_pp.frecuencia_dias = 90
        
    session.add(nuevo_pp)
    await session.commit()
    await session.refresh(nuevo_pp)
    
    return {"ok": True, "id": nuevo_pp.id}


@router.put("/{prev_id}/ejecutar")
async def marcar_ejecutado(
    prev_id: int, 
    user: dict = Depends(get_current_user), 
    session: AsyncSession = Depends(get_async_session)
):
    pp = await session.get(PreventivoProgramado, prev_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Preventivo no encontrado")

    nueva_fecha = date.today() + timedelta(days=pp.frecuencia_dias)
    
    # Actualizar preventivo
    pp.ultima_ejecucion = date.today()
    pp.proxima_ejecucion = nueva_fecha
    
    # Actualizar fecha en equipo
    equipo = await session.get(Equipo, pp.equipo_id)
    if equipo:
        equipo.fecha_ultimo_mantenimiento = date.today()
        equipo.fecha_proximo_mantenimiento = nueva_fecha

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al ejecutar preventivo: {str(e)}")

    return {"ok": True, "proxima_ejecucion": str(nueva_fecha)}
