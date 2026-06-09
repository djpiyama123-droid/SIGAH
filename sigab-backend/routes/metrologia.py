from fastapi import APIRouter, Depends, HTTPException, Form
import aiomysql
from datetime import datetime, timedelta
from config import get_db
from auth.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def listar_calibraciones(equipo_id: int = None, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    async with conn.cursor(aiomysql.DictCursor) as cur:
        query = """
            SELECT m.*, e.nombre as equipo_nombre, e.serie as equipo_serie 
            FROM metrologia_calibracion m 
            JOIN equipos e ON m.equipo_id = e.id 
        """
        params = []
        if equipo_id:
            query += " WHERE m.equipo_id = %s"
            params.append(equipo_id)
        
        query += " ORDER BY m.proxima_calibracion ASC"
        await cur.execute(query, params)
        return await cur.fetchall()

from models.schemas import CalibracionSchema

@router.post("/")
async def registrar_calibracion(
    data: CalibracionSchema,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    fecha_dt = datetime.combine(data.fecha_calibracion, datetime.min.time())
    proxima_dt = fecha_dt + timedelta(days=30 * data.vigencia_meses)
    
    async with conn.cursor() as cur:
        await cur.execute(
            """INSERT INTO metrologia_calibracion 
               (equipo_id, tipo_medicion, fecha_calibracion, proxima_calibracion, certificado_numero, entidad_calibradora) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (data.equipo_id, data.tipo_medicion, data.fecha_calibracion, proxima_dt.date(), data.certificado_numero, data.entidad_calibradora)
        )
        return {"ok": True, "id": cur.lastrowid}

@router.get("/vencidas")
async def calibraciones_vencidas(user: dict = Depends(get_current_user), conn=Depends(get_db)):
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("""
            SELECT m.*, e.nombre, e.serie 
            FROM metrologia_calibracion m 
            JOIN equipos e ON m.equipo_id = e.id 
            WHERE m.proxima_calibracion <= CURDATE()
        """)
        return await cur.fetchall()
