"""
Tests unitarios para WS-3: capa proveedor IA edge + fallback MiniMax.

Valida:
  - Circuit-breaker: abre cuando Ollama falla, cierra cuando regresa
  - proveedor_activo() devuelve 'edge' | 'nube' | 'sin_ia' correctamente
  - analizar_no_stream() usa edge cuando está sano
  - analizar_no_stream() usa nube cuando edge está caído y hay API key
  - analizar_no_stream() devuelve mensaje de error cuando no hay ningún proveedor
  - _minimax_no_stream() formatea el request OpenAI-compatible correctamente
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ── Fixtures helpers ──────────────────────────────────────────────

def _reset_circuit():
    """Reinicia el estado del circuit-breaker entre tests."""
    import services.gemma_service as svc
    svc._edge_healthy = True
    svc._edge_next_check_at = 0.0
    svc._edge_circuit_open_until = 0.0


# ── Tests circuit-breaker ─────────────────────────────────────────

def test_circuito_abierto_cuando_cooldown_activo():
    import services.gemma_service as svc
    _reset_circuit()
    svc._edge_circuit_open_until = time.monotonic() + 30
    assert svc._circuito_edge_abierto() is True


def test_circuito_cerrado_cuando_cooldown_expirado():
    import services.gemma_service as svc
    _reset_circuit()
    svc._edge_circuit_open_until = time.monotonic() - 1  # expirado
    assert svc._circuito_edge_abierto() is False


def test_abrir_circuito_establece_cooldown():
    import services.gemma_service as svc
    _reset_circuit()
    antes = time.monotonic()
    svc._abrir_circuito_edge()
    assert svc._edge_circuit_open_until > antes
    assert svc._edge_healthy is False


def test_cerrar_circuito_limpia_estado():
    import services.gemma_service as svc
    _reset_circuit()
    svc._abrir_circuito_edge()
    svc._cerrar_circuito_edge()
    assert svc._edge_circuit_open_until == 0.0
    assert svc._edge_healthy is True


# ── Tests _ping_ollama ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ping_ollama_exitoso_cierra_circuito():
    import services.gemma_service as svc
    _reset_circuit()
    svc._abrir_circuito_edge()  # simula que estaba caído

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": []}

    with patch("services.gemma_service.httpx.AsyncClient") as mock_client_cls:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_ctx

        result = await svc._ping_ollama()

    assert result is True
    assert svc._edge_circuit_open_until == 0.0


@pytest.mark.asyncio
async def test_ping_ollama_fallo_abre_circuito():
    import services.gemma_service as svc
    _reset_circuit()

    with patch("services.gemma_service.httpx.AsyncClient") as mock_client_cls:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client_cls.return_value = mock_ctx

        result = await svc._ping_ollama()

    assert result is False
    assert svc._edge_circuit_open_until > time.monotonic()


# ── Tests proveedor_activo ────────────────────────────────────────

@pytest.mark.asyncio
async def test_proveedor_activo_edge_cuando_ollama_sano():
    import services.gemma_service as svc
    _reset_circuit()

    with patch("services.gemma_service._edge_disponible", return_value=True):
        resultado = await svc.proveedor_activo()

    assert resultado == svc.PROVEEDOR_EDGE


@pytest.mark.asyncio
async def test_proveedor_activo_nube_cuando_edge_caido_y_hay_apikey():
    import services.gemma_service as svc
    _reset_circuit()

    with patch("services.gemma_service._edge_disponible", return_value=False), \
         patch("services.gemma_service.MINIMAX_API_KEY", "test-key-123"):
        resultado = await svc.proveedor_activo()

    assert resultado == svc.PROVEEDOR_NUBE


@pytest.mark.asyncio
async def test_proveedor_activo_sin_ia_cuando_todo_falla():
    import services.gemma_service as svc
    _reset_circuit()

    with patch("services.gemma_service._edge_disponible", return_value=False), \
         patch("services.gemma_service.MINIMAX_API_KEY", ""):
        resultado = await svc.proveedor_activo()

    assert resultado == svc.PROVEEDOR_SIN_IA


# ── Tests analizar_no_stream ──────────────────────────────────────

@pytest.mark.asyncio
async def test_analizar_usa_edge_cuando_disponible():
    """Cuando Ollama está sano, la respuesta viene del edge."""
    import services.gemma_service as svc
    _reset_circuit()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"content": "Respuesta del edge"}
    }
    mock_response.raise_for_status = MagicMock()

    with patch("services.gemma_service._edge_disponible", return_value=True), \
         patch("services.gemma_service.httpx.AsyncClient") as mock_client_cls:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_ctx

        resultado = await svc.analizar_no_stream("¿Prueba?")

    assert resultado == "Respuesta del edge"


@pytest.mark.asyncio
async def test_analizar_fallback_a_minimax_cuando_edge_caido():
    """Cuando Ollama está caído y hay API key, usa MiniMax."""
    import services.gemma_service as svc
    _reset_circuit()

    minimax_response = MagicMock()
    minimax_response.status_code = 200
    minimax_response.json.return_value = {
        "choices": [{"message": {"content": "Respuesta de MiniMax"}}]
    }
    minimax_response.raise_for_status = MagicMock()

    with patch("services.gemma_service._edge_disponible", return_value=False), \
         patch("services.gemma_service.MINIMAX_API_KEY", "clave-prueba"), \
         patch("services.gemma_service.httpx.AsyncClient") as mock_client_cls:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.post = AsyncMock(return_value=minimax_response)
        mock_client_cls.return_value = mock_ctx

        resultado = await svc.analizar_no_stream("¿Prueba?")

    assert resultado == "Respuesta de MiniMax"


@pytest.mark.asyncio
async def test_analizar_retorna_error_cuando_sin_proveedores():
    """Sin Ollama ni API key, retorna mensaje de error claro."""
    import services.gemma_service as svc
    _reset_circuit()

    with patch("services.gemma_service._edge_disponible", return_value=False), \
         patch("services.gemma_service.MINIMAX_API_KEY", ""):
        resultado = await svc.analizar_no_stream("¿Prueba?")

    assert "Ollama" in resultado or "MINIMAX" in resultado or "Error" in resultado


# ── Tests _minimax_no_stream ──────────────────────────────────────

@pytest.mark.asyncio
async def test_minimax_no_stream_formatea_request_openai_compatible():
    """Verifica que la llamada a MiniMax usa formato OpenAI con Bearer token."""
    import services.gemma_service as svc

    llamadas_post = []

    async def fake_post(url, **kwargs):
        llamadas_post.append({"url": url, "kwargs": kwargs})
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.json.return_value = {
            "choices": [{"message": {"content": "OK"}}]
        }
        mock_r.raise_for_status = MagicMock()
        return mock_r

    with patch("services.gemma_service.MINIMAX_API_KEY", "mi-clave"), \
         patch("services.gemma_service.MINIMAX_BASE_URL", "https://api.minimax.chat/v1"), \
         patch("services.gemma_service.httpx.AsyncClient") as mock_cls:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.post = AsyncMock(side_effect=fake_post)
        mock_cls.return_value = mock_ctx

        await svc._minimax_no_stream("Prompt test", "System test")

    assert len(llamadas_post) == 1
    url = llamadas_post[0]["url"]
    headers = llamadas_post[0]["kwargs"].get("headers", {})
    body = llamadas_post[0]["kwargs"].get("json", {})

    assert "chat/completions" in url
    assert headers.get("Authorization", "").startswith("Bearer ")
    assert body.get("stream") is False
    assert any(m["role"] == "system" for m in body.get("messages", []))
    assert any(m["role"] == "user" for m in body.get("messages", []))
