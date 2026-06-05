"""
ai_provider.py — Capa de abstracción de proveedor de IA para SIGAB Copilot.

Prioridad de proveedor:
  1. Ollama LOCAL  — nodo edge Lenovo ThinkCentre M720q on-premise (sin internet requerido)
  2. MiniMax CLOUD — fallback automático cuando el edge no responde

El fallback a nube se activa si:
  - Ollama no responde en < 3 s (SIGAB_OLLAMA_HEALTH_TIMEOUT)
  - SIGAB_AI_FALLBACK_ENABLED = true  (default)
  - SIGAB_MINIMAX_API_KEY está configurada

Todos los chunks SSE incluyen el campo 'provider' para que el frontend
muestre al usuario si está usando IA local o nube.
"""

import time
import json
import httpx
from enum import Enum
from typing import AsyncGenerator

from config import (
    OLLAMA_HOST,
    GEMMA_MODEL,
    MINIMAX_API_KEY,
    MINIMAX_API_URL,
    MINIMAX_GROUP_ID,
    MINIMAX_MODEL,
    AI_FALLBACK_ENABLED,
)

OLLAMA_HEALTH_TIMEOUT = float(3.0)


class Provider(str, Enum):
    LOCAL = "ollama_local"
    CLOUD = "minimax_cloud"
    UNAVAILABLE = "unavailable"


# ── Healthchecks ──────────────────────────────────────────────────

async def check_ollama() -> tuple[bool, float]:
    """Ping rápido a Ollama. Retorna (modelo_disponible, latencia_ms)."""
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_HEALTH_TIMEOUT) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            latency_ms = (time.monotonic() - t0) * 1000
            if r.status_code != 200:
                return False, latency_ms
            modelos = [m["name"] for m in r.json().get("models", [])]
            modelo_ok = any(GEMMA_MODEL.split(":")[0] in m for m in modelos)
            return modelo_ok, latency_ms
    except Exception:
        return False, (time.monotonic() - t0) * 1000


def check_minimax() -> bool:
    """True si el fallback MiniMax está habilitado y tiene API key."""
    return bool(AI_FALLBACK_ENABLED and MINIMAX_API_KEY)


async def get_active_provider() -> Provider:
    """Determina el proveedor activo en este momento."""
    ollama_ok, _ = await check_ollama()
    if ollama_ok:
        return Provider.LOCAL
    if check_minimax():
        return Provider.CLOUD
    return Provider.UNAVAILABLE


async def edge_status() -> dict:
    """Healthcheck completo: nodo edge + fallback nube."""
    t0 = time.monotonic()
    ollama_ok, ollama_ms = await check_ollama()
    minimax_ok = check_minimax()

    proveedor = (
        Provider.LOCAL if ollama_ok
        else Provider.CLOUD if minimax_ok
        else Provider.UNAVAILABLE
    )

    return {
        "proveedor_activo": proveedor,
        "fallback_habilitado": AI_FALLBACK_ENABLED,
        "nodo_edge": {
            "activo": ollama_ok,
            "url": OLLAMA_HOST,
            "modelo": GEMMA_MODEL,
            "latencia_ms": round(ollama_ms, 1),
            "hardware": "Lenovo ThinkCentre M720q — on-premise HGR No. 1 IMSS Tijuana",
        },
        "fallback_nube": {
            "configurado": minimax_ok,
            "proveedor": "MiniMax API",
            "modelo": MINIMAX_MODEL if MINIMAX_API_KEY else None,
            "url_base": MINIMAX_API_URL if MINIMAX_API_KEY else None,
        },
        "diagnostico_ms": round((time.monotonic() - t0) * 1000, 1),
    }


# ── MiniMax (cloud fallback) ──────────────────────────────────────

def _minimax_headers() -> dict:
    return {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }


def _minimax_payload(messages: list, system: str, stream: bool = False) -> dict:
    payload: dict = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": 0.7 if stream else 0.5,
        "max_tokens": 2048 if stream else 1024,
    }
    if stream:
        payload["stream"] = True
    if MINIMAX_GROUP_ID:
        payload["group_id"] = MINIMAX_GROUP_ID
    return payload


async def _minimax_no_stream(messages: list, system: str) -> str:
    url = MINIMAX_API_URL.rstrip("/") + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=_minimax_payload(messages, system), headers=_minimax_headers())
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Fallback MiniMax no disponible: {e}]"


async def _minimax_stream(messages: list, system: str) -> AsyncGenerator[str, None]:
    url = MINIMAX_API_URL.rstrip("/") + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", url,
                json=_minimax_payload(messages, system, stream=True),
                headers=_minimax_headers(),
            ) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': f'MiniMax {resp.status_code}', 'done': True, 'provider': Provider.CLOUD})}\n\n"
                    return
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        yield f"data: {json.dumps({'token': '', 'done': True, 'provider': Provider.CLOUD})}\n\n"
                        return
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            token = chunk["choices"][0].get("delta", {}).get("content", "")
                            done = chunk["choices"][0].get("finish_reason") is not None
                            yield f"data: {json.dumps({'token': token, 'done': done, 'provider': Provider.CLOUD})}\n\n"
                        except Exception:
                            continue
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True, 'provider': Provider.CLOUD})}\n\n"


# ── API pública del módulo ────────────────────────────────────────

async def chat_stream(messages: list, contexto: dict = None) -> AsyncGenerator[str, None]:
    """
    Streaming unificado con fallback automático.
    Cada chunk SSE incluye 'provider': 'ollama_local' | 'minimax_cloud'.
    """
    from services import gemma_service

    ollama_ok, _ = await check_ollama()

    if ollama_ok:
        async for chunk in gemma_service.chat_stream(messages, contexto):
            try:
                data = json.loads(chunk.removeprefix("data: ").strip())
                data["provider"] = Provider.LOCAL
                yield f"data: {json.dumps(data)}\n\n"
            except Exception:
                yield chunk
        return

    if check_minimax():
        system = gemma_service._build_system_prompt(contexto or {})
        # Aviso inicial al cliente de que se usa IA en la nube
        yield f"data: {json.dumps({'token': '', 'done': False, 'provider': Provider.CLOUD, 'notice': 'Nodo edge no disponible — usando IA en la nube (MiniMax)'})}\n\n"
        async for chunk in _minimax_stream(messages, system):
            yield chunk
        return

    yield f"data: {json.dumps({'error': 'Ningún proveedor de IA disponible. Verifica Ollama en el nodo edge o configura SIGAB_MINIMAX_API_KEY.', 'done': True, 'provider': Provider.UNAVAILABLE})}\n\n"


async def analizar_no_stream(prompt_user: str, contexto: dict = None) -> str:
    """
    Análisis sin streaming con fallback automático.
    """
    from services import gemma_service

    ollama_ok, _ = await check_ollama()

    if ollama_ok:
        return await gemma_service.analizar_no_stream(prompt_user, contexto)

    if check_minimax():
        system = gemma_service._build_system_prompt(contexto or {})
        return await _minimax_no_stream([{"role": "user", "content": prompt_user}], system)

    return "Error: Ningún proveedor de IA disponible. Verifica Ollama en el nodo edge o configura SIGAB_MINIMAX_API_KEY."
