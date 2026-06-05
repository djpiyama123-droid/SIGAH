"""
ai_provider.py — Capa de abstracción de proveedor IA para SIGAB Copilot.

Estrategia Edge-Local-First con fallback a nube:
  1. Proveedor PRIMARIO: Ollama en el Lenovo ThinkCentre (edge node del hospital).
     - Privacidad total: los datos clínicos no salen del hospital.
     - Costo variable = $0 (modelo local Gemma 4B/12B).
  2. Proveedor FALLBACK: MiniMax API (nube) cuando Ollama no disponible.
     - Se activa sólo si SIGAB_MINIMAX_API_KEY está configurado.
     - Compatible con formato OpenAI (chat/completions).

Interfaz pública:
  verificar_disponibilidad()       → dict con estado de cada proveedor
  chat_no_stream(messages, system) → (respuesta_str, Proveedor)
  chat_stream(messages, system)    → AsyncGenerator[str] en formato SSE SIGAB

Formato SSE interno de SIGAB:
  data: {"token": "...", "done": false, "proveedor": "edge_local"}
  data: {"token": "",   "done": true,  "proveedor": "edge_local"}
"""

import httpx
import json
from enum import Enum
from typing import AsyncGenerator

from config import (
    OLLAMA_HOST, GEMMA_MODEL,
    MINIMAX_API_KEY, MINIMAX_MODEL, MINIMAX_HOST,
)


class Proveedor(str, Enum):
    EDGE_LOCAL = "edge_local"
    CLOUD_MINIMAX = "cloud_minimax"
    NO_DISPONIBLE = "no_disponible"


# ── Verificación de disponibilidad ───────────────────────────────

async def verificar_disponibilidad() -> dict:
    """
    Verifica el estado de ambos proveedores.
    Devuelve un dict con estado detallado de edge, fallback y cuál está activo.
    """
    edge_ok = False
    edge_modelos: list[str] = []
    edge_error = None

    try:
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                edge_modelos = [m["name"] for m in resp.json().get("models", [])]
                edge_ok = any(GEMMA_MODEL.split(":")[0] in m for m in edge_modelos)
    except Exception as exc:
        edge_error = str(exc)

    minimax_configurado = bool(MINIMAX_API_KEY)

    if edge_ok:
        proveedor_activo = Proveedor.EDGE_LOCAL
    elif minimax_configurado:
        proveedor_activo = Proveedor.CLOUD_MINIMAX
    else:
        proveedor_activo = Proveedor.NO_DISPONIBLE

    return {
        "proveedor_activo": proveedor_activo,
        "edge": {
            "online": edge_ok,
            "host": OLLAMA_HOST,
            "modelo": GEMMA_MODEL,
            "modelos_instalados": edge_modelos,
            "error": edge_error,
        },
        "fallback": {
            "configurado": minimax_configurado,
            "proveedor": "MiniMax",
            "modelo": MINIMAX_MODEL if minimax_configurado else None,
            "base_url": MINIMAX_HOST if minimax_configurado else None,
        },
    }


async def _edge_ok_quick() -> bool:
    """Ping rápido (2 s) a Ollama para decidir si usarlo en streaming."""
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/ps")
            return resp.status_code == 200
    except Exception:
        return False


# ── Implementación Ollama (edge) ──────────────────────────────────

async def _ollama_no_stream(messages: list, system_prompt: str) -> str | None:
    payload = {
        "model": GEMMA_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 1024},
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")
    except Exception:
        return None


async def _ollama_stream(
    messages: list, system_prompt: str
) -> AsyncGenerator[str, None]:
    payload = {
        "model": GEMMA_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": True,
        "options": {"temperature": 0.7, "num_predict": 2048, "top_p": 0.9},
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload) as response:
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Ollama error {response.status_code}', 'done': True, 'proveedor': Proveedor.EDGE_LOCAL})}\n\n"
                    return
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        done = data.get("done", False)
                        yield f"data: {json.dumps({'token': token, 'done': done, 'proveedor': Proveedor.EDGE_LOCAL})}\n\n"
                        if done:
                            break
                    except json.JSONDecodeError:
                        continue
    except httpx.ConnectError:
        return  # Señal para intentar fallback


# ── Implementación MiniMax (fallback nube) ────────────────────────

async def _minimax_no_stream(messages: list, system_prompt: str) -> str | None:
    if not MINIMAX_API_KEY:
        return None
    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": False,
        "temperature": 0.5,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{MINIMAX_HOST}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None


async def _minimax_stream(
    messages: list, system_prompt: str
) -> AsyncGenerator[str, None]:
    """
    Llama a MiniMax con stream=True (OpenAI SSE) y re-emite en formato SSE SIGAB.
    """
    if not MINIMAX_API_KEY:
        yield f"data: {json.dumps({'error': 'MiniMax no configurado (SIGAB_MINIMAX_API_KEY vacío).', 'done': True, 'proveedor': Proveedor.NO_DISPONIBLE})}\n\n"
        return

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{MINIMAX_HOST}/chat/completions", json=payload, headers=headers
            ) as response:
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'MiniMax error {response.status_code}', 'done': True, 'proveedor': Proveedor.CLOUD_MINIMAX})}\n\n"
                    return
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        yield f"data: {json.dumps({'token': '', 'done': True, 'proveedor': Proveedor.CLOUD_MINIMAX})}\n\n"
                        break
                    try:
                        data = json.loads(raw)
                        delta = data["choices"][0].get("delta", {})
                        token = delta.get("content", "")
                        done = data["choices"][0].get("finish_reason") is not None
                        yield f"data: {json.dumps({'token': token, 'done': done, 'proveedor': Proveedor.CLOUD_MINIMAX})}\n\n"
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except Exception as exc:
        yield f"data: {json.dumps({'error': f'MiniMax no disponible: {exc}', 'done': True, 'proveedor': Proveedor.CLOUD_MINIMAX})}\n\n"


# ── Interfaz pública ──────────────────────────────────────────────

async def chat_no_stream(
    messages: list,
    system_prompt: str,
) -> tuple[str, Proveedor]:
    """
    Llama al proveedor activo sin streaming.
    Intenta edge local primero; si falla y MiniMax está configurado, usa fallback.
    Retorna (texto_respuesta, proveedor_usado).
    """
    resultado = await _ollama_no_stream(messages, system_prompt)
    if resultado is not None:
        return resultado, Proveedor.EDGE_LOCAL

    if MINIMAX_API_KEY:
        resultado = await _minimax_no_stream(messages, system_prompt)
        if resultado is not None:
            return resultado, Proveedor.CLOUD_MINIMAX

    return (
        "Error: ningún proveedor de IA disponible. "
        "Verifica que Ollama esté corriendo en el servidor edge o configura SIGAB_MINIMAX_API_KEY.",
        Proveedor.NO_DISPONIBLE,
    )


async def chat_stream(
    messages: list,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """
    Streaming con fallback automático.
    - Si Ollama responde: usa edge local.
    - Si Ollama falla en conexión: intenta MiniMax.
    - Si ninguno disponible: emite error SSE.
    """
    edge_disponible = await _edge_ok_quick()

    if edge_disponible:
        buffer_vacio = True
        async for chunk in _ollama_stream(messages, system_prompt):
            buffer_vacio = False
            yield chunk
        if not buffer_vacio:
            return

    # Edge no disponible o buffer vacío — intenta fallback
    if MINIMAX_API_KEY:
        async for chunk in _minimax_stream(messages, system_prompt):
            yield chunk
        return

    yield f"data: {json.dumps({'error': 'Ollama no disponible y SIGAB_MINIMAX_API_KEY no configurado.', 'done': True, 'proveedor': Proveedor.NO_DISPONIBLE})}\n\n"
