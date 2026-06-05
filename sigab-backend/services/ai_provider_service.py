"""
SIGAB AI Provider Service — Enrutamiento IA local + nube

Arquitectura de prioridad (Industria 4.0 — nodo edge hospitalario):
  1. Edge local: Ollama/Gemma corriendo en el Lenovo ThinkCentre del hospital.
     Latencia cero, datos 100% on-premise, sin costos variables por token.
  2. Cloud fallback: MiniMax API (compatible OpenAI).
     Solo se activa si el edge no responde en EDGE_HEALTH_TIMEOUT segundos.
     Requiere configurar SIGAB_MINIMAX_API_KEY en el entorno.

Este módulo es el punto de entrada para copilot.py; no reemplaza gemma_service.py
(que sigue siendo el adaptador puro de Ollama).

Uso típico:
    from services import ai_provider_service
    estado = await ai_provider_service.verificar_proveedor()
    texto  = await ai_provider_service.analizar_no_stream(prompt, contexto)
    # streaming:
    async for chunk in ai_provider_service.chat_stream(messages, contexto):
        yield chunk
"""

import httpx
import json
from typing import AsyncGenerator, Optional

from config import (
    OLLAMA_HOST,
    GEMMA_MODEL,
    MINIMAX_API_KEY,
    MINIMAX_BASE_URL,
    MINIMAX_MODEL,
    MINIMAX_TIMEOUT,
    EDGE_HEALTH_TIMEOUT,
)
from services import gemma_service


# ── Health check del edge ─────────────────────────────────────────

async def _is_edge_available() -> bool:
    """Ping rápido a Ollama. True si responde dentro del timeout configurado."""
    try:
        async with httpx.AsyncClient(timeout=EDGE_HEALTH_TIMEOUT) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


# ── Adaptador MiniMax ─────────────────────────────────────────────

def _build_minimax_messages(messages: list, system_prompt: str) -> list:
    return [{"role": "system", "content": system_prompt}, *messages]


async def _minimax_no_stream(messages: list, system_prompt: str) -> str:
    """Llamada síncrona a MiniMax (formato OpenAI-compatible). Retorna texto completo."""
    if not MINIMAX_API_KEY:
        return "Error: cloud IA no configurada. Define SIGAB_MINIMAX_API_KEY para activar el fallback."

    payload = {
        "model": MINIMAX_MODEL,
        "messages": _build_minimax_messages(messages, system_prompt),
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
            resp = await client.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        return f"Error MiniMax API ({e.response.status_code}): {e.response.text[:300]}"
    except Exception as e:
        return f"Error nube IA: {str(e)}"


async def _minimax_stream(
    messages: list, system_prompt: str
) -> AsyncGenerator[str, None]:
    """Streaming desde MiniMax. Emite SSE en formato SIGAB idéntico al de Ollama."""
    if not MINIMAX_API_KEY:
        yield f'data: {{"error": "Cloud IA no configurada (SIGAB_MINIMAX_API_KEY vacía)", "done": true}}\n\n'
        return

    # Avisa al frontend que el edge no está disponible
    yield (
        'data: {"token": "[⚡ Edge no disponible — usando IA nube MiniMax]\\n\\n",'
        ' "done": false, "proveedor": "cloud_minimax"}\n\n'
    )

    payload = {
        "model": MINIMAX_MODEL,
        "messages": _build_minimax_messages(messages, system_prompt),
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{MINIMAX_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                if response.status_code != 200:
                    yield (
                        f'data: {{"error": "MiniMax error HTTP {response.status_code}",'
                        f' "done": true}}\n\n'
                    )
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        yield 'data: {"token": "", "done": true}\n\n'
                        break
                    try:
                        data = json.loads(raw)
                        choice = data["choices"][0]
                        token = choice.get("delta", {}).get("content", "")
                        done = choice.get("finish_reason") is not None
                        yield f"data: {json.dumps({'token': token, 'done': done})}\n\n"
                        if done:
                            break
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    except httpx.ConnectError:
        yield 'data: {"error": "No se pudo conectar a MiniMax API", "done": true}\n\n'
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"


# ── Interfaz pública ──────────────────────────────────────────────

async def verificar_proveedor() -> dict:
    """
    Verifica estado del edge local y del cloud fallback.
    Retorna qué proveedor está activo ahora mismo.
    """
    edge_result = await gemma_service.verificar_ollama()
    edge_ok = edge_result.get("ollama_activo", False)
    cloud_configurado = bool(MINIMAX_API_KEY)

    if edge_ok:
        proveedor_activo = "edge_local"
    elif cloud_configurado:
        proveedor_activo = "cloud_minimax"
    else:
        proveedor_activo = "ninguno"

    return {
        "ok": edge_ok or cloud_configurado,
        "proveedor_activo": proveedor_activo,
        "edge": {
            "disponible": edge_ok,
            "host": OLLAMA_HOST,
            "modelo": GEMMA_MODEL,
            "modelo_cargado": edge_result.get("modelo_disponible", False),
            "modelos_instalados": edge_result.get("modelos_instalados", []),
        },
        "cloud": {
            "configurado": cloud_configurado,
            "proveedor": "MiniMax",
            "modelo": MINIMAX_MODEL,
            "base_url": MINIMAX_BASE_URL,
        },
    }


async def chat_stream(
    messages: list,
    contexto: Optional[dict] = None,
) -> AsyncGenerator[str, None]:
    """
    Chat en streaming. Usa el edge local si está disponible;
    cae a MiniMax en caso contrario.
    """
    if await _is_edge_available():
        async for chunk in gemma_service.chat_stream(messages, contexto):
            yield chunk
    else:
        system_prompt = gemma_service._build_system_prompt(contexto or {})
        async for chunk in _minimax_stream(messages, system_prompt):
            yield chunk


async def analizar_no_stream(
    prompt_user: str,
    contexto: Optional[dict] = None,
) -> str:
    """
    Análisis sin streaming. Usa el edge local si está disponible;
    cae a MiniMax en caso contrario.
    """
    if await _is_edge_available():
        return await gemma_service.analizar_no_stream(prompt_user, contexto)

    system_prompt = gemma_service._build_system_prompt(contexto or {})
    return await _minimax_no_stream(
        [{"role": "user", "content": prompt_user}],
        system_prompt,
    )
