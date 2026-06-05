"""
main.py — Punto de entrada del backend SIGAB.

Configura la aplicación FastAPI con:
- Middleware CORS para comunicación con el frontend (puertos 5173/5174/3000)
- Montaje de archivos estáticos (uploads, imágenes de equipos)
- Registro de 20 routers organizados por módulo funcional
- Endpoint de health check para monitoreo

Ejecutar con: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Autor: Equipo SIGAB — Bioingeniería Xochicalco
Versión: 2.0.0
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import uvicorn

from config import UPLOAD_DIR, CORS_EXTRA
from routes import (
    equipos, ordenes, trazabilidad, reservas,
    alertas, preventivos, dashboard, openclaw, reportes,
    tecnovigilancia, auditoria, checklists,
    almacen, metrologia, capacitaciones,
    auth as auth_routes,
    ocr, events, casillas, edge_health
)
_COPILOT_ON = os.getenv("SIGAB_DISABLE_COPILOT", "0") != "1"
if _COPILOT_ON:
    from routes import copilot


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs("static/uploads", exist_ok=True)
    print("SIGAB Backend iniciado — 100% Local")
    yield
    print("SIGAB Backend detenido")


app = FastAPI(
    title="SIGAB API",
    description="Sistema Integral de Gestión de Activos Biomédicos — HGR No.1 IMSS",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", *CORS_EXTRA]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_routes.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR Inteligente (Local + Cloud)"])
app.include_router(equipos.router, prefix="/api/equipos", tags=["Equipos"])
app.include_router(ordenes.router, prefix="/api/ordenes", tags=["Órdenes de Servicio"])
app.include_router(trazabilidad.router, prefix="/api/trazabilidad", tags=["Trazabilidad"])
app.include_router(reservas.router, prefix="/api/reservas", tags=["Reservas"])
app.include_router(alertas.router, prefix="/api/alertas", tags=["Alertas"])
app.include_router(preventivos.router, prefix="/api/preventivos", tags=["Preventivos"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(openclaw.router, prefix="/api/openclaw", tags=["OpenClaw"])
app.include_router(reportes.router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(auditoria.router, prefix="/api/auditoria", tags=["Auditoría NOM-016"])
app.include_router(checklists.router, prefix="/api/checklists", tags=["Checklists NOM-016"])
app.include_router(tecnovigilancia.router, prefix="/api/tecnovigilancia", tags=["Tecnovigilancia NOM-240"])
if _COPILOT_ON:
    app.include_router(copilot.router, prefix="/api/copilot", tags=["SIGAB Copilot (IA Local)"])
app.include_router(almacen.router, prefix="/api/almacen", tags=["Gestión de Almacén"])
app.include_router(metrologia.router, prefix="/api/metrologia", tags=["Metrología y Calibración"])
app.include_router(capacitaciones.router, prefix="/api/capacitaciones", tags=["Capacitación de Personal"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Eventos"])
app.include_router(casillas.router, tags=["Casillas CENEVAL (Conservación)"])
app.include_router(edge_health.router, prefix="/api/edge", tags=["Edge Node IA (Ollama + Fallback)"])


@app.get("/health")
def health():
    return {"status": "ok", "sistema": "SIGAB", "modo": "on-premise"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
