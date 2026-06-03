"""
ia_provider.py — Capa de abstracción de proveedor IA para SIGAB Copilot.

Industria 4.0 — Nodo Edge Hospitalario
---------------------------------------
Arquitectura de dos niveles:
  1. EDGE LOCAL  : Ollama corriendo en el Lenovo ThinkCentre M720q del hospital
                   (gemma3:4b / qwen2.5:7b, 100% on-premise, sin datos a la nube)
  2. CLOUD FALLBACK : MiniMax API (internet) — se activa automáticamente si el
                   edge no responde en IA_EDGE_TIMEOUT_S segundos.

Estrategia seleccionada con SIGAB_IA_STRATEGY:
  auto  → edge primero, fallback cloud (producción recomendada)
  local → solo edge, sin fallback (privacidad máxima)
  cloud → solo MiniMax cloud (mantenimiento edge / pruebas)

Uso desde otros módulos:
    from services.ia_provider import ia_provider
    texto = await ia_provider.complete("¿Cuál es la causa probable de esta falla?")
    async for chunk in ia_provider.stream(messages): yield chunk
    estado = await ia_provider.edge_health()
"""

import httpx
import json
import time
import logging
from typing import AsyncGenerator
from config import (
    OLLAMA_HOST, GEMMA_MODEL,
    MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL,
    IA_STRATEGY,
)

logger = logging.getLogger(__name__)

# Timeout al verificar si el edge responde antes de decidir fallback
IA_EDGE_TIMEOUT_S = 4.0
# Timeout total para llamadas al edge (respuestas pueden ser lentas en 4B)
IA_EDGE_COMPLETE_TIMEOUT_S = 90.0
IA_EDGE_STREAM_TIMEOUT_S = 120.0


# ── Helpers edge (Ollama) ─────────────────────────────────────────

async def _edge_is_reachable() -> bool:
    """Ping rápido al nodo edge. Retorna True si Ollama responde en <IA_EDGE_TIMEOUT_S s."""
    try:
        async with httpx.AsyncClient(timeout=IA_EDGE_TIMEOUT_S) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def _edge_complete(messages: list, system_prompt: str, temperature: float = 0.5) -> str:
    payload = {
        "model": GEMMA_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 1024},
    }
    async with httpx.AsyncClient(timeout=IA_EDGE_COMPLETE_TIMEOUT_S) as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")


async def _edge_stream(messages: list, system_prompt: str) -> AsyncGenerator[str, None]:
    payload = {
        "model": GEMMA_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": True,
        "options": {"temperature": 0.7, "num_predict": 2048, "top_p": 0.9},
    }
    async with httpx.AsyncClient(timeout=IA_EDGE_STREAM_TIMEOUT_S) as client:
        async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    done = data.get("done", False)
                    yield json.dumps({"token": token, "done": done, "proveedor": "edge"})
                    if done:
                        break
                except json.JSONDecodeError:
                    continue


# ── Helpers cloud (MiniMax) ───────────────────────────────────────

def _minimax_headers() -> dict:
    return {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }


async def _cloud_complete(messages: list, system_prompt: str, temperature: float = 0.5) -> str:
    if not MINIMAX_API_KEY:
        raise RuntimeError("SIGAB_MINIMAX_API_KEY no configurada — fallback cloud no disponible")
    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": False,
        "temperature": temperature,
        "max_tokens": 1024,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{MINIMAX_BASE_URL}/text/chatcompletion_v2",
            headers=_minimax_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def _cloud_stream(messages: list, system_prompt: str) -> AsyncGenerator[str, None]:
    if not MINIMAX_API_KEY:
        yield json.dumps({"error": "SIGAB_MINIMAX_API_KEY no configurada", "done": True, "proveedor": "cloud"})
        return
    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        async with client.stream(
            "POST",
            f"{MINIMAX_BASE_URL}/text/chatcompletion_v2",
            headers=_minimax_headers(),
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    yield json.dumps({"token": "", "done": True, "proveedor": "cloud"})
                    break
                try:
                    data = json.loads(raw)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")
                    yield json.dumps({"token": token, "done": False, "proveedor": "cloud"})
                except json.JSONDecodeError:
                    continue


# ── IAProvider — API pública ──────────────────────────────────────

class IAProvider:
    """
    Punto de entrada único para toda la inferencia IA en SIGAB.
    Encapsula la lógica edge-first / cloud-fallback según IA_STRATEGY.
    """

    async def _should_use_edge(self) -> bool:
        if IA_STRATEGY == "cloud":
            return False
        if IA_STRATEGY == "local":
            return True
        # auto: probar si el edge responde
        return await _edge_is_reachable()

    async def complete(
        self,
        messages: list,
        system_prompt: str = "",
        temperature: float = 0.5,
    ) -> tuple[str, str]:
        """
        Llamada síncrona (sin streaming). Retorna (texto, proveedor_usado).
        proveedor_usado: "edge" | "cloud"
        """
        use_edge = await self._should_use_edge()
        if use_edge:
            try:
                texto = await _edge_complete(messages, system_prompt, temperature)
                return texto, "edge"
            except Exception as e:
                logger.warning("Edge IA falló (%s), usando fallback cloud", e)
                if IA_STRATEGY == "local":
                    raise
        texto = await _cloud_complete(messages, system_prompt, temperature)
        return texto, "cloud"

    async def stream(
        self,
        messages: list,
        system_prompt: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Streaming de tokens. Cada yield es una línea JSON:
          {"token": "...", "done": false, "proveedor": "edge"|"cloud"}
        Si el edge falla durante el stream, emite un token de aviso y continúa
        con cloud desde el inicio (no hay forma de retomar stream a la mitad).
        """
        use_edge = await self._should_use_edge()
        if use_edge:
            try:
                async for chunk in _edge_stream(messages, system_prompt):
                    yield chunk
                return
            except Exception as e:
                logger.warning("Edge stream falló (%s), cambiando a cloud fallback", e)
                if IA_STRATEGY == "local":
                    yield json.dumps({"error": f"Edge no disponible: {e}", "done": True, "proveedor": "edge"})
                    return
                yield json.dumps({
                    "token": "\n[⚠ Nodo edge no disponible — continuando con IA cloud]\n",
                    "done": False,
                    "proveedor": "cloud",
                })
        async for chunk in _cloud_stream(messages, system_prompt):
            yield chunk

    async def edge_health(self) -> dict:
        """
        Devuelve el estado detallado del nodo edge para el monitor del dashboard.
        Llamado por GET /api/copilot/edge-health.
        """
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=IA_EDGE_TIMEOUT_S) as client:
                tags_resp = await client.get(f"{OLLAMA_HOST}/api/tags")
                latencia_ms = round((time.monotonic() - t0) * 1000)

                if tags_resp.status_code != 200:
                    return {
                        "edge_activo": False,
                        "latencia_ms": latencia_ms,
                        "error": f"Ollama retornó HTTP {tags_resp.status_code}",
                        "estrategia_activa": IA_STRATEGY,
                        "proveedor_efectivo": "cloud" if MINIMAX_API_KEY else "ninguno",
                    }

                data = tags_resp.json()
                modelos = [m["name"] for m in data.get("models", [])]
                modelo_cargado = any(GEMMA_MODEL.split(":")[0] in m for m in modelos)

                # Verificar si el modelo está activamente en memoria (ps)
                modelo_en_memoria = False
                try:
                    ps_resp = await client.get(f"{OLLAMA_HOST}/api/ps")
                    if ps_resp.status_code == 200:
                        ps_data = ps_resp.json()
                        activos = [m.get("name", "") for m in ps_data.get("models", [])]
                        modelo_en_memoria = any(GEMMA_MODEL.split(":")[0] in m for m in activos)
                except Exception:
                    pass

                return {
                    "edge_activo": True,
                    "ollama_host": OLLAMA_HOST,
                    "modelo_configurado": GEMMA_MODEL,
                    "modelo_instalado": modelo_cargado,
                    "modelo_en_memoria": modelo_en_memoria,
                    "modelos_disponibles": modelos,
                    "latencia_ms": latencia_ms,
                    "estrategia_activa": IA_STRATEGY,
                    "proveedor_efectivo": "edge",
                    "cloud_fallback_configurado": bool(MINIMAX_API_KEY),
                    "cloud_modelo": MINIMAX_MODEL if MINIMAX_API_KEY else None,
                }

        except httpx.ConnectError:
            latencia_ms = round((time.monotonic() - t0) * 1000)
            return {
                "edge_activo": False,
                "ollama_host": OLLAMA_HOST,
                "latencia_ms": latencia_ms,
                "error": "Ollama no responde (ConnectError) — nodo edge posiblemente apagado",
                "estrategia_activa": IA_STRATEGY,
                "proveedor_efectivo": "cloud" if MINIMAX_API_KEY else "ninguno",
                "cloud_fallback_configurado": bool(MINIMAX_API_KEY),
                "cloud_modelo": MINIMAX_MODEL if MINIMAX_API_KEY else None,
            }
        except Exception as e:
            latencia_ms = round((time.monotonic() - t0) * 1000)
            return {
                "edge_activo": False,
                "latencia_ms": latencia_ms,
                "error": str(e),
                "estrategia_activa": IA_STRATEGY,
                "proveedor_efectivo": "cloud" if MINIMAX_API_KEY else "ninguno",
                "cloud_fallback_configurado": bool(MINIMAX_API_KEY),
            }


# Singleton exportado — importar este objeto en todos los módulos que usen IA
ia_provider = IAProvider()
