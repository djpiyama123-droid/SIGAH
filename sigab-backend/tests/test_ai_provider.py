"""
Tests unitarios para la capa de proveedor IA (WS-3).

Verifica la lógica de fallback edge → MiniMax sin requerir
que Ollama ni MiniMax estén corriendo (usando mocks).
"""
import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Asegura que el paquete raíz esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProbeEdge(unittest.IsolatedAsyncioTestCase):
    async def test_probe_edge_returns_true_on_200(self):
        """Cuando Ollama responde 200, el probe debe retornar True."""
        import services.gemma_service as svc

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("services.gemma_service.httpx.AsyncClient", return_value=mock_cm):
            result = await svc._probe_edge()

        self.assertTrue(result)

    async def test_probe_edge_returns_false_on_connection_error(self):
        """Cuando Ollama no está disponible, el probe debe retornar False (sin lanzar)."""
        import services.gemma_service as svc
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("services.gemma_service.httpx.AsyncClient", return_value=mock_cm):
            result = await svc._probe_edge()

        self.assertFalse(result)


class TestVerificarOllama(unittest.IsolatedAsyncioTestCase):
    async def test_verificar_cuando_edge_ok(self):
        """verificar_ollama debe reportar proveedor_activo=ollama_edge cuando edge responde."""
        import services.gemma_service as svc

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "gemma3:4b"}]}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("services.gemma_service.httpx.AsyncClient", return_value=mock_cm):
            result = await svc.verificar_ollama()

        self.assertTrue(result["ollama_activo"])
        self.assertEqual(result["proveedor_activo"], "ollama_edge")

    async def test_verificar_cuando_edge_caido_y_minimax_configurado(self):
        """Cuando edge cae y MINIMAX_API_KEY está, proveedor_activo debe ser minimax_nube."""
        import services.gemma_service as svc
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("services.gemma_service.httpx.AsyncClient", return_value=mock_cm):
            with patch("services.gemma_service.MINIMAX_API_KEY", "test-key-123"):
                result = await svc.verificar_ollama()

        self.assertFalse(result["ollama_activo"])
        self.assertEqual(result["proveedor_activo"], "minimax_nube")
        self.assertTrue(result["fallback_minimax_configurado"])

    async def test_verificar_cuando_todo_caido(self):
        """Sin edge ni MiniMax, ok debe ser False y proveedor_activo ninguno."""
        import services.gemma_service as svc
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("services.gemma_service.httpx.AsyncClient", return_value=mock_cm):
            with patch("services.gemma_service.MINIMAX_API_KEY", ""):
                result = await svc.verificar_ollama()

        self.assertFalse(result["ok"])
        self.assertEqual(result["proveedor_activo"], "ninguno")


class TestMiniMaxNoStream(unittest.IsolatedAsyncioTestCase):
    async def test_retorna_error_sin_api_key(self):
        """Sin MINIMAX_API_KEY, debe retornar mensaje de error, no lanzar excepción."""
        import services.gemma_service as svc

        with patch("services.gemma_service.MINIMAX_API_KEY", ""):
            result = await svc._minimax_no_stream([{"role": "user", "content": "hola"}])

        self.assertIn("SIGAB_MINIMAX_API_KEY", result)

    async def test_parsea_respuesta_openai_compatible(self):
        """_minimax_no_stream debe extraer content del formato OpenAI choices[0].message."""
        import services.gemma_service as svc

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Respuesta de prueba MiniMax"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("services.gemma_service.MINIMAX_API_KEY", "test-key"):
            with patch("services.gemma_service.httpx.AsyncClient", return_value=mock_cm):
                result = await svc._minimax_no_stream([{"role": "user", "content": "hola"}])

        self.assertEqual(result, "Respuesta de prueba MiniMax")


if __name__ == "__main__":
    unittest.main()
