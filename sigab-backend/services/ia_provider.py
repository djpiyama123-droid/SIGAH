"""
ia_provider.py — Capa de proveedores IA para SIGAB.

Prioridad de uso:
  1. Nodo edge: Ollama (Lenovo ThinkCentre M720q, LAN on-premise) — sin costo, latencia <50 ms
  2. Nube fallback: MiniMax API — cuando el edge no está disponible

Variables de entorno relevantes:
  SIGAB_OLLAMA_HOST       URL Ollama edge       (default: http://localhost:11434)
  SIGAB_GEMMA_MODEL       Modelo edge           (default: gemma3:4b)
  SIGAB_MINIMAX_API_KEY   API key MiniMax cloud
  SIGAB_MINIMAX_MODEL     Modelo MiniMax        (default: abab6.5s-chat)
  SIGAB_MINIMAX_BASE_URL  URL base MiniMax      (default: https://api.minimaxi.chat/v1)
  SIGAB_IA_FALLBACK       "1" activa fallback   (default: "1")
"""

import httpx
import json
from datetime import datetime
from config import (
    OLLAMA_HOST,
    GEMMA_MODEL,
    MINIMAX_API_KEY,
    MINIMAX_MODEL,
    MINIMAX_BASE_URL,
    IA_FALLBACK_ENABLED,
)

# ── Telemetría en memoria (reseteada en cada reinicio del proceso) ──
_telemetria: dict = {
    "edge_requests": 0,
    "cloud_requests": 0,
    "cloud_tokens_estimados": 0,
    "ultimo_proveedor": None,
    "ultimo_fallback_ts": None,
}


def registrar_uso(proveedor: str, tokens_estimados: int = 0) -> None:
    _telemetria["ultimo_proveedor"] = proveedor
    if proveedor == "edge":
        _telemetria["edge_requests"] += 1
    else:
        _telemetria["cloud_requests"] += 1
        _telemetria["cloud_tokens_estimados"] += tokens_estimados
        _telemetria["ultimo_fallback_ts"] = datetime.now().isoformat()


def get_telemetria() -> dict:
    return {**_telemetria}


# ── Health checks ─────────────────────────────────────────────────

async def verificar_edge() -> dict:
    """Verifica disponibilidad del nodo edge Ollama (ThinkCentre LAN)."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                modelos = [m["name"] for m in data.get("models", [])]
                modelo_ok = any(GEMMA_MODEL.split(":")[0] in m for m in modelos)
                return {
                    "disponible": True,
                    "modelo_cargado": modelo_ok,
                    "modelo": GEMMA_MODEL,
                    "url": OLLAMA_HOST,
                    "modelos_instalados": modelos,
                }
    except Exception as exc:
        return {
            "disponible": False,
            "modelo_cargado": False,
            "modelo": GEMMA_MODEL,
            "url": OLLAMA_HOST,
            "error": str(exc),
        }
    return {"disponible": False, "error": "respuesta inesperada del edge"}


async def verificar_cloud() -> dict:
    """Verifica configuración del proveedor cloud MiniMax."""
    key_ok = bool(MINIMAX_API_KEY)
    return {
        "disponible": key_ok,
        "proveedor": "MiniMax",
        "modelo": MINIMAX_MODEL,
        "base_url": MINIMAX_BASE_URL,
        "api_key_configurada": key_ok,
        "fallback_habilitado": IA_FALLBACK_ENABLED,
    }


async def estado_proveedores() -> dict:
    """Estado completo de edge + cloud + telemetría de sesión."""
    edge = await verificar_edge()
    cloud = await verificar_cloud()

    if edge["disponible"]:
        proveedor_activo = "edge"
    elif cloud["disponible"] and IA_FALLBACK_ENABLED:
        proveedor_activo = "cloud"
    else:
        proveedor_activo = "ninguno"

    return {
        "edge": edge,
        "cloud": cloud,
        "proveedor_activo": proveedor_activo,
        "fallback_habilitado": IA_FALLBACK_ENABLED,
        "telemetria_sesion": get_telemetria(),
    }


# ── Streaming MiniMax ─────────────────────────────────────────────

async def chat_stream_minimax(messages: list, system_prompt: str):
    """
    Streaming SSE vía MiniMax cloud (API compatible con OpenAI).
    Cada elemento yielded es un str JSON (sin el prefijo 'data: ').
    """
    if not MINIMAX_API_KEY:
        yield json.dumps({
            "error": "SIGAB_MINIMAX_API_KEY no configurada. Agrega la variable de entorno.",
            "done": True,
            "proveedor": "cloud",
        })
        return

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": True,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    registrar_uso("cloud")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield json.dumps({
                        "error": f"MiniMax HTTP {response.status_code}: {body[:200].decode()}",
                        "done": True,
                        "proveedor": "cloud",
                    })
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        yield json.dumps({"token": "", "done": True, "proveedor": "cloud"})
                        return
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            choices = data.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            token = delta.get("content", "")
                            finish = choices[0].get("finish_reason")
                            done = bool(finish)
                            _telemetria["cloud_tokens_estimados"] += len(token.split())
                            yield json.dumps({"token": token, "done": done, "proveedor": "cloud"})
                            if done:
                                return
                        except (json.JSONDecodeError, IndexError, KeyError):
                            continue

    except Exception as exc:
        yield json.dumps({
            "error": f"Error MiniMax cloud: {exc}",
            "done": True,
            "proveedor": "cloud",
        })


# ── Non-streaming MiniMax ─────────────────────────────────────────

async def analizar_minimax(messages: list, system_prompt: str) -> str:
    """Llamada MiniMax sin streaming. Retorna texto completo."""
    if not MINIMAX_API_KEY:
        return "Error: SIGAB_MINIMAX_API_KEY no configurada. Configura el respaldo cloud."

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": False,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    registrar_uso("cloud", tokens_estimados=512)

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return "MiniMax no retornó respuesta."
    except Exception as exc:
        return f"Error al consultar MiniMax cloud: {exc}"
