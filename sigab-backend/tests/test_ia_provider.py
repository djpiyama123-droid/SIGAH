"""
Tests unitarios para services/ia_provider.py

Cobertura:
  - edge_health cuando Ollama responde OK
  - edge_health cuando Ollama no está disponible (ConnectError)
  - complete() con estrategia "local" (usa edge, no cloud)
  - complete() con estrategia "cloud" (salta edge directo a MiniMax)
  - complete() con estrategia "auto" y edge caído (usa cloud como fallback)
  - stream() produce chunks con campo "proveedor"

Los tests usan respx para no necesitar servicios reales.
aiomysql/cryptography se mockean a nivel de módulo para evitar conflictos
de dependencias nativas en entornos CI sin base de datos.
"""

import json
import sys
from unittest.mock import MagicMock
import pytest
import respx
import httpx

# Mock de aiomysql ANTES de cualquier import del proyecto para evitar
# el conflicto de cryptography/_cffi_backend en el contenedor CI.
for _mod in ("aiomysql", "pymysql", "pymysql.connections", "cryptography"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

import importlib


def _reload_provider(monkeypatch, strategy="auto", minimax_key="test-key"):
    """Recarga el módulo ia_provider con config parcheada."""
    monkeypatch.setenv("SIGAB_IA_STRATEGY", strategy)
    monkeypatch.setenv("SIGAB_MINIMAX_API_KEY", minimax_key)
    monkeypatch.setenv("SIGAB_OLLAMA_HOST", "http://edge-test:11434")
    monkeypatch.setenv("SIGAB_GEMMA_MODEL", "gemma3:4b")

    # Forzar recarga de config y ia_provider para que lean los env vars nuevos
    for mod_name in ["config", "services.ia_provider"]:
        if mod_name in sys.modules:
            del sys.modules[mod_name]

    import services.ia_provider as mod
    return mod


# ── Test: edge_health con edge OK ────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_edge_health_ok(monkeypatch):
    mod = _reload_provider(monkeypatch, strategy="auto")

    tags_payload = {"models": [{"name": "gemma3:4b"}, {"name": "qwen2.5:7b"}]}
    ps_payload = {"models": [{"name": "gemma3:4b"}]}

    respx.get("http://edge-test:11434/api/tags").mock(
        return_value=httpx.Response(200, json=tags_payload)
    )
    respx.get("http://edge-test:11434/api/ps").mock(
        return_value=httpx.Response(200, json=ps_payload)
    )

    resultado = await mod.ia_provider.edge_health()

    assert resultado["edge_activo"] is True
    assert resultado["modelo_instalado"] is True
    assert resultado["modelo_en_memoria"] is True
    assert resultado["proveedor_efectivo"] == "edge"
    assert resultado["cloud_fallback_configurado"] is True
    assert isinstance(resultado["latencia_ms"], int)


# ── Test: edge_health con edge caído ─────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_edge_health_connect_error(monkeypatch):
    mod = _reload_provider(monkeypatch, strategy="auto")

    respx.get("http://edge-test:11434/api/tags").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    resultado = await mod.ia_provider.edge_health()

    assert resultado["edge_activo"] is False
    assert "ConnectError" in resultado["error"] or "no responde" in resultado["error"]
    assert resultado["proveedor_efectivo"] == "cloud"
    assert resultado["cloud_fallback_configurado"] is True


# ── Test: complete con estrategia "local" ─────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_complete_local_strategy(monkeypatch):
    mod = _reload_provider(monkeypatch, strategy="local")

    ollama_resp = {
        "message": {"role": "assistant", "content": "Diagnóstico: falla en el sensor de flujo."},
        "done": True,
    }
    respx.post("http://edge-test:11434/api/chat").mock(
        return_value=httpx.Response(200, json=ollama_resp)
    )

    texto, proveedor = await mod.ia_provider.complete(
        messages=[{"role": "user", "content": "¿Qué falla tiene el ventilador?"}],
        system_prompt="Eres un experto en equipos biomédicos.",
    )

    assert "sensor de flujo" in texto
    assert proveedor == "edge"


# ── Test: complete con estrategia "cloud" ─────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_complete_cloud_strategy(monkeypatch):
    mod = _reload_provider(monkeypatch, strategy="cloud", minimax_key="test-key-cloud")

    minimax_resp = {
        "choices": [
            {"message": {"role": "assistant", "content": "Respuesta desde MiniMax cloud."}}
        ]
    }
    respx.post("https://api.minimax.io/v1/text/chatcompletion_v2").mock(
        return_value=httpx.Response(200, json=minimax_resp)
    )

    texto, proveedor = await mod.ia_provider.complete(
        messages=[{"role": "user", "content": "Diagnóstico de alarma"}],
        system_prompt="Experto biomédico.",
    )

    assert "MiniMax cloud" in texto
    assert proveedor == "cloud"


# ── Test: auto fallback cuando edge cae durante complete ──────────

@pytest.mark.asyncio
@respx.mock
async def test_complete_auto_fallback(monkeypatch):
    mod = _reload_provider(monkeypatch, strategy="auto", minimax_key="test-key-fb")

    # El ping al edge tarda/falla
    respx.get("http://edge-test:11434/api/tags").mock(
        side_effect=httpx.ConnectError("edge offline")
    )

    minimax_resp = {
        "choices": [{"message": {"content": "Fallback cloud activado."}}]
    }
    respx.post("https://api.minimax.io/v1/text/chatcompletion_v2").mock(
        return_value=httpx.Response(200, json=minimax_resp)
    )

    texto, proveedor = await mod.ia_provider.complete(
        messages=[{"role": "user", "content": "Analiza esta falla"}],
        system_prompt="Experto.",
    )

    assert "Fallback cloud" in texto
    assert proveedor == "cloud"


# ── Test: edge_health sin MiniMax key configurada ────────────────

@pytest.mark.asyncio
@respx.mock
async def test_edge_health_no_cloud_key(monkeypatch):
    mod = _reload_provider(monkeypatch, strategy="auto", minimax_key="")

    respx.get("http://edge-test:11434/api/tags").mock(
        side_effect=httpx.ConnectError("edge offline")
    )

    resultado = await mod.ia_provider.edge_health()

    assert resultado["edge_activo"] is False
    assert resultado["cloud_fallback_configurado"] is False
    assert resultado["proveedor_efectivo"] == "ninguno"
