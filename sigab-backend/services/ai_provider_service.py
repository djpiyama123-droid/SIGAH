"""
SIGAB AI Provider Service — Capa de abstracción de proveedores IA

Proveedor primario : Ollama (nodo edge Lenovo on-premise, puerto 11434)
Proveedor fallback : MiniMax API (nube), activo sólo cuando edge no responde
                     y SIGAB_MINIMAX_API_KEY está configurado.

Flujo de selección:
  1. Verificar Ollama (healthcheck rápido, timeout 3 s)
  2. Si Ollama OK → usar OllamaProvider
  3. Si Ollama falla Y fallback habilitado Y API key presente → MiniMaxProvider
  4. Si ambos fallan → retornar error claro al caller

Interfaces públicas:
  get_providers_status()         → dict con salud de ambos proveedores
  chat_no_stream(messages, sys)  → str
  chat_stream(messages, sys)     → AsyncGenerator[str SSE, None]
"""

import httpx
import json
import time
from typing import AsyncGenerator

from config import (
    OLLAMA_HOST,
    GEMMA_MODEL,
    MINIMAX_API_KEY,
    MINIMAX_BASE_URL,
    MINIMAX_MODEL,
    AI_PROVIDER,
    AI_FALLBACK_ENABLED,
)


# ─────────────────────────────────────────────────────────────────
# Healthchecks
# ─────────────────────────────────────────────────────────────────

async def _check_ollama() -> dict:
    """Verifica disponibilidad del nodo edge Ollama. Timeout agresivo (3 s)."""
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            latencia_ms = int((time.monotonic() - t0) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                modelos = [m["name"] for m in data.get("models", [])]
                modelo_ok = any(GEMMA_MODEL.split(":")[0] in m for m in modelos)
                return {
                    "status": "online",
                    "latencia_ms": latencia_ms,
                    "modelo_ok": modelo_ok,
                    "modelos": modelos,
                }
            return {"status": "offline", "latencia_ms": latencia_ms, "modelo_ok": False, "modelos": []}
    except Exception as exc:
        return {"status": "offline", "latencia_ms": None, "modelo_ok": False, "error": str(exc)}


async def _check_minimax() -> dict:
    """Verifica disponibilidad de la API MiniMax (solo si hay API key)."""
    if not MINIMAX_API_KEY:
        return {"status": "no_key", "habilitado": False}
    if not AI_FALLBACK_ENABLED:
        return {"status": "deshabilitado", "habilitado": False}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Llamada mínima (1 token) para verificar autenticación y conectividad
            resp = await client.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
                json={
                    "model": MINIMAX_MODEL,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
            )
            if resp.status_code in (200, 400):
                # 400 puede ser error de cuota pero indica que la API responde
                return {"status": "online", "habilitado": True}
            return {"status": "error_http", "habilitado": True, "codigo": resp.status_code}
    except Exception as exc:
        return {"status": "offline", "habilitado": True, "error": str(exc)}


async def get_providers_status() -> dict:
    """
    Retorna el estado de ambos proveedores y el modo activo.
    Útil para el endpoint /copilot/estado-edge del healthcheck.
    """
    import asyncio
    edge, cloud = await asyncio.gather(_check_ollama(), _check_minimax())

    if edge["status"] == "online" and edge.get("modelo_ok"):
        modo = "edge"
    elif edge["status"] == "online":
        modo = "edge_sin_modelo"
    elif cloud.get("habilitado") and cloud["status"] == "online":
        modo = "cloud"
    else:
        modo = "sin_ia"

    return {
        "edge": {
            "proveedor": "Ollama",
            "host": OLLAMA_HOST,
            "modelo": GEMMA_MODEL,
            **edge,
        },
        "cloud": {
            "proveedor": "MiniMax",
            "modelo": MINIMAX_MODEL,
            "fallback_habilitado": AI_FALLBACK_ENABLED and bool(MINIMAX_API_KEY),
            **cloud,
        },
        "modo_activo": modo,
    }


# ─────────────────────────────────────────────────────────────────
# Selección de proveedor activo
# ─────────────────────────────────────────────────────────────────

async def _use_edge() -> bool:
    """True si debemos usar el proveedor edge (Ollama)."""
    if AI_PROVIDER == "cloud":
        return False
    if AI_PROVIDER == "local":
        return True  # forzado; si falla, el caller verá el error
    # "auto": usar edge si está disponible
    result = await _check_ollama()
    return result["status"] == "online"


# ─────────────────────────────────────────────────────────────────
# MiniMax chat (sin streaming)
# ─────────────────────────────────────────────────────────────────

async def _minimax_chat_no_stream(messages: list, system_prompt: str) -> str:
    """Llama a MiniMax API (sin streaming). Retorna texto completo."""
    all_messages = []
    if system_prompt:
        all_messages.append({"role": "system", "content": system_prompt})
    all_messages.extend(messages)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
                json={
                    "model": MINIMAX_MODEL,
                    "messages": all_messages,
                    "temperature": 0.5,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.ConnectError:
        return "Error: API MiniMax no accesible. Verifica conectividad a internet."
    except Exception as exc:
        return f"Error MiniMax: {exc}"


# ─────────────────────────────────────────────────────────────────
# MiniMax chat (streaming) — formato SSE compatible con el frontend
# ─────────────────────────────────────────────────────────────────

async def _minimax_chat_stream(
    messages: list,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """Llama a MiniMax API en modo streaming. Yields líneas SSE SIGAB."""
    all_messages = []
    if system_prompt:
        all_messages.append({"role": "system", "content": system_prompt})
    all_messages.extend(messages)

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
                json={
                    "model": MINIMAX_MODEL,
                    "messages": all_messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            ) as response:
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'MiniMax HTTP {response.status_code}', 'done': True})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
                        return
                    try:
                        chunk = json.loads(raw)
                        token = chunk["choices"][0]["delta"].get("content", "")
                        done = chunk["choices"][0].get("finish_reason") is not None
                        yield f"data: {json.dumps({'token': token, 'done': done, 'proveedor': 'minimax'})}\n\n"
                        if done:
                            return
                    except (json.JSONDecodeError, KeyError):
                        continue

    except httpx.ConnectError:
        yield f"data: {json.dumps({'error': 'MiniMax no accesible. Sin conexión a internet.', 'done': True})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"


# ─────────────────────────────────────────────────────────────────
# API pública — con fallback automático
# ─────────────────────────────────────────────────────────────────

async def _ollama_chat_stream(
    messages: list,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """Llama a Ollama directamente usando system_prompt ya construido."""
    payload = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "stream": True,
        "options": {"temperature": 0.7, "num_predict": 2048, "top_p": 0.9},
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Ollama HTTP {resp.status_code}', 'done': True})}\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        done = data.get("done", False)
                        yield f"data: {json.dumps({'token': token, 'done': done, 'proveedor': 'ollama'})}\n\n"
                        if done:
                            return
                    except json.JSONDecodeError:
                        continue
    except httpx.ConnectError:
        yield f"data: {json.dumps({'error': 'Ollama no disponible.', 'done': True})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"


async def _ollama_chat_no_stream(messages: list, system_prompt: str) -> str:
    """Llama a Ollama sin streaming usando system_prompt ya construido."""
    payload = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 1024},
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")
    except httpx.ConnectError:
        return "Error: Ollama no disponible."
    except Exception as exc:
        return f"Error Ollama: {exc}"


# ─────────────────────────────────────────────────────────────────
# API pública — con fallback automático
# ─────────────────────────────────────────────────────────────────

async def chat_no_stream(messages: list, system_prompt: str = "") -> tuple[str, str]:
    """
    Chat sin streaming con fallback automático.
    Retorna (texto_respuesta, proveedor_usado).
    """
    if await _use_edge():
        return await _ollama_chat_no_stream(messages, system_prompt), "ollama"

    if AI_FALLBACK_ENABLED and MINIMAX_API_KEY:
        return await _minimax_chat_no_stream(messages, system_prompt), "minimax"

    return "Sin IA disponible: Ollama offline y fallback MiniMax no configurado.", "ninguno"


async def chat_stream(
    messages: list,
    system_prompt: str = "",
) -> AsyncGenerator[str, None]:
    """
    Chat en streaming con fallback automático.
    Yields líneas SSE. Incluye campo 'proveedor' en cada chunk.
    """
    if await _use_edge():
        async for chunk in _ollama_chat_stream(messages, system_prompt):
            yield chunk
        return

    if AI_FALLBACK_ENABLED and MINIMAX_API_KEY:
        async for chunk in _minimax_chat_stream(messages, system_prompt):
            yield chunk
        return

    yield f"data: {json.dumps({'error': 'Sin IA: Ollama offline y MiniMax no configurado.', 'done': True})}\n\n"
