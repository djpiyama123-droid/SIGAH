"""
SIGAB Edge Health — Estado del nodo edge de IA local

GET /api/edge/health
  Retorna el estado del servidor Ollama (nodo edge Lenovo ThinkCentre) y
  si el fallback a nube MiniMax está configurado.

Usado por el monitor del frontend (badge en Copilot) y por sistemas
de alerta de operación para saber en qué modo está corriendo la IA.
"""

from fastapi import APIRouter, Depends
import httpx
import platform
from datetime import datetime, timezone

from config import OLLAMA_HOST, GEMMA_MODEL, MINIMAX_API_KEY, MINIMAX_MODEL
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/health")
async def edge_health(user: dict = Depends(get_current_user)):
    """
    Devuelve el estado del nodo edge (Ollama) y del fallback de nube.

    Campos:
      - timestamp:          ISO 8601 del momento de la consulta
      - edge_disponible:    true si Ollama responde en OLLAMA_HOST
      - edge_modelo:        modelo activo en Ollama
      - edge_modelos:       lista de modelos instalados
      - fallback_nube:      true si MINIMAX_API_KEY está configurado
      - fallback_modelo:    modelo de nube configurado
      - modo_activo:        "edge" | "nube" | "sin_ia"
      - ollama_host:        host configurado (sin credenciales)
    """
    ollama_status = await _check_ollama()

    fallback_nube = bool(MINIMAX_API_KEY)

    if ollama_status["disponible"]:
        modo = "edge"
    elif fallback_nube:
        modo = "nube"
    else:
        modo = "sin_ia"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "edge_disponible": ollama_status["disponible"],
        "edge_modelo": GEMMA_MODEL,
        "edge_modelos": ollama_status.get("modelos", []),
        "edge_modelo_cargado": ollama_status.get("modelo_cargado", False),
        "edge_error": ollama_status.get("error"),
        "fallback_nube": fallback_nube,
        "fallback_modelo": MINIMAX_MODEL if fallback_nube else None,
        "modo_activo": modo,
        "ollama_host": OLLAMA_HOST,
    }


async def _check_ollama() -> dict:
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                modelos = [m["name"] for m in data.get("models", [])]
                modelo_cargado = any(GEMMA_MODEL.split(":")[0] in m for m in modelos)
                return {
                    "disponible": True,
                    "modelos": modelos,
                    "modelo_cargado": modelo_cargado,
                }
            return {"disponible": False, "error": f"HTTP {resp.status_code}"}
    except httpx.ConnectError:
        return {"disponible": False, "error": "Ollama no responde (ConnectError)"}
    except httpx.ConnectTimeout:
        return {"disponible": False, "error": "Ollama timeout (>4s)"}
    except Exception as e:
        return {"disponible": False, "error": str(e)}
