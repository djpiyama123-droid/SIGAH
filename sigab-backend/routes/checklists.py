from fastapi import APIRouter, Depends, HTTPException
import aiomysql
from config import get_db
from auth.dependencies import get_current_user
from services.audit_service import AuditService

router = APIRouter()

@router.get("/templates")
async def get_checklist_templates(user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Obtiene plantillas de checklists NOM-016."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM nom016_checklists")
        return await cur.fetchall()

@router.post("/ejecutar")
async def save_checklist_result(
    data: dict,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Guarda el resultado de un checklist NOM-016 y lo registra en auditoría."""
    checklist_id = data.get("checklist_id")
    resultados = data.get("resultados") # JSON
    area_id = data.get("area_id")
    observaciones = data.get("observaciones")

    if not checklist_id or resultados is None:
        raise HTTPException(status_code=400, detail="Checklist ID y resultados son obligatorios")

    async with conn.cursor() as cur:
        await cur.execute(
            """INSERT INTO nom016_resultados (checklist_id, usuario_id, area_id, resultados, observaciones)
               VALUES (%s, %s, %s, %s, %s)""",
            (checklist_id, user["id"], area_id, resultados, observaciones)
        )
        res_id = cur.lastrowid
        
        # Registrar en Auditoría NOM-016 inalterable
        await AuditService.log_event(
            usuario_id=user["id"],
            accion="CHECKLIST_COMPLETED",
            entidad="nom016_resultados",
            entidad_id=res_id,
            datos={"checklist_id": checklist_id, "resultados": resultados}
        )

    return {"ok": True, "id": res_id, "mensaje": "Checklist guardado y auditado"}

@router.get("/resultados")
async def get_results(
    limit: int = 50,
    area_id: int = None,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Lista resultados de auditorías NOM-016 previas."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        query = """SELECT r.*, c.nombre as checklist_nombre, u.nombre as usuario_nombre, l.nombre as area_nombre
                   FROM nom016_resultados r
                   JOIN nom016_checklists c ON r.checklist_id = c.id
                   JOIN usuarios u ON r.usuario_id = u.id
                   LEFT JOIN ubicaciones l ON r.area_id = l.id
                   WHERE 1=1"""
        params = []
        if area_id:
            query += " AND r.area_id = %s"
            params.append(area_id)
            
        query += " ORDER BY r.fecha_ejecucion DESC LIMIT %s"
        params.append(limit)
        
        await cur.execute(query, params)
        res = await cur.fetchall()
        
    for r in res:
        if hasattr(r["fecha_ejecucion"], "isoformat"):
            r["fecha_ejecucion"] = r["fecha_ejecucion"].isoformat()
            
    return res
