"""
Tests unitarios para ai_provider_service.

Verifica la lógica de enrutamiento edge→cloud sin necesitar
Ollama ni MiniMax reales (usa mocks de httpx y gemma_service).

El mock de aiomysql al inicio es necesario en entornos CI donde la
librería cryptography nativa no está disponible. No afecta el código
de producción.

Ejecutar:
    cd sigab-backend
    pip install pytest pytest-asyncio
    pytest tests/test_ai_provider.py -v
"""

import sys
from unittest.mock import MagicMock

# Bloquear imports con dependencias nativas rotas en entornos CI
for _mod in ("aiomysql", "pymysql", "cryptography"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

import pytest
from unittest.mock import AsyncMock, patch


# ── Helpers ───────────────────────────────────────────────────────

def _make_response(status: int, body: dict = None):
    m = MagicMock()
    m.status_code = status
    if body:
        m.json.return_value = body
    m.raise_for_status = MagicMock()
    return m


def _patch_httpx_client(get_resp=None, post_resp=None):
    """Context manager que sustituye httpx.AsyncClient con un mock."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    if get_resp is not None:
        mock_client.get = AsyncMock(return_value=get_resp)
    if post_resp is not None:
        mock_client.post = AsyncMock(return_value=post_resp)
    return patch("services.ai_provider_service.httpx.AsyncClient", return_value=mock_client), mock_client


# ── _is_edge_available ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_is_edge_available_true():
    """Edge disponible cuando Ollama devuelve HTTP 200."""
    ctx, _ = _patch_httpx_client(get_resp=_make_response(200))
    with ctx:
        import importlib
        import services.ai_provider_service as svc
        importlib.reload(svc)
        result = await svc._is_edge_available()
    assert result is True


@pytest.mark.asyncio
async def test_is_edge_available_false_on_connect_error():
    """Edge no disponible cuando Ollama lanza ConnectError."""
    import httpx as real_httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=real_httpx.ConnectError("refused"))

    with patch("services.ai_provider_service.httpx.AsyncClient", return_value=mock_client):
        import services.ai_provider_service as svc
        result = await svc._is_edge_available()
    assert result is False


@pytest.mark.asyncio
async def test_is_edge_available_false_on_non_200():
    """Edge no disponible cuando Ollama devuelve status != 200."""
    ctx, _ = _patch_httpx_client(get_resp=_make_response(503))
    with ctx:
        import services.ai_provider_service as svc
        result = await svc._is_edge_available()
    assert result is False


# ── verificar_proveedor ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_verificar_proveedor_edge_activo():
    """proveedor_activo='edge_local' cuando Ollama responde."""
    edge_mock = {
        "ok": True,
        "ollama_activo": True,
        "modelo": "gemma3:4b",
        "modelo_disponible": True,
        "modelos_instalados": ["gemma3:4b"],
    }
    import services.ai_provider_service as svc
    with patch.object(svc.gemma_service, "verificar_ollama", AsyncMock(return_value=edge_mock)):
        result = await svc.verificar_proveedor()

    assert result["proveedor_activo"] == "edge_local"
    assert result["ok"] is True
    assert result["edge"]["disponible"] is True
    assert result["cloud"]["proveedor"] == "MiniMax"


@pytest.mark.asyncio
async def test_verificar_proveedor_cloud_fallback():
    """proveedor_activo='cloud_minimax' cuando Ollama no responde pero API key existe."""
    edge_mock = {
        "ok": False,
        "ollama_activo": False,
        "modelo": "gemma3:4b",
        "modelo_disponible": False,
        "modelos_instalados": [],
    }
    import services.ai_provider_service as svc
    with (
        patch.object(svc.gemma_service, "verificar_ollama", AsyncMock(return_value=edge_mock)),
        patch.object(svc, "MINIMAX_API_KEY", "fake-test-key"),
    ):
        result = await svc.verificar_proveedor()

    assert result["proveedor_activo"] == "cloud_minimax"
    assert result["ok"] is True
    assert result["edge"]["disponible"] is False
    assert result["cloud"]["configurado"] is True


@pytest.mark.asyncio
async def test_verificar_proveedor_ninguno():
    """proveedor_activo='ninguno' cuando no hay edge ni API key."""
    edge_mock = {
        "ok": False,
        "ollama_activo": False,
        "modelo": "gemma3:4b",
        "modelo_disponible": False,
        "modelos_instalados": [],
    }
    import services.ai_provider_service as svc
    with (
        patch.object(svc.gemma_service, "verificar_ollama", AsyncMock(return_value=edge_mock)),
        patch.object(svc, "MINIMAX_API_KEY", ""),
    ):
        result = await svc.verificar_proveedor()

    assert result["proveedor_activo"] == "ninguno"
    assert result["ok"] is False


# ── analizar_no_stream ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analizar_no_stream_usa_edge_cuando_disponible():
    """analizar_no_stream delega a gemma_service cuando el edge está up."""
    import services.ai_provider_service as svc
    with (
        patch.object(svc, "_is_edge_available", AsyncMock(return_value=True)),
        patch.object(svc.gemma_service, "analizar_no_stream", AsyncMock(return_value="respuesta edge")),
    ):
        result = await svc.analizar_no_stream("¿estado del hospital?")

    assert result == "respuesta edge"


@pytest.mark.asyncio
async def test_analizar_no_stream_fallback_a_minimax():
    """analizar_no_stream usa MiniMax cuando el edge no responde."""
    minimax_body = {
        "choices": [{"message": {"content": "respuesta desde minimax"}}]
    }
    post_resp = _make_response(200, minimax_body)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=post_resp)

    import services.ai_provider_service as svc
    with (
        patch.object(svc, "_is_edge_available", AsyncMock(return_value=False)),
        patch.object(svc.gemma_service, "_build_system_prompt", MagicMock(return_value="sys")),
        patch.object(svc, "MINIMAX_API_KEY", "fake-key"),
        patch("services.ai_provider_service.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await svc.analizar_no_stream("¿estado?", {})

    assert result == "respuesta desde minimax"


@pytest.mark.asyncio
async def test_analizar_no_stream_sin_api_key_devuelve_error():
    """Sin API key de MiniMax y sin edge, retorna mensaje de error descriptivo."""
    import services.ai_provider_service as svc
    with (
        patch.object(svc, "_is_edge_available", AsyncMock(return_value=False)),
        patch.object(svc.gemma_service, "_build_system_prompt", MagicMock(return_value="sys")),
        patch.object(svc, "MINIMAX_API_KEY", ""),
    ):
        result = await svc.analizar_no_stream("¿estado?")

    assert "SIGAB_MINIMAX_API_KEY" in result
    assert "Error" in result
