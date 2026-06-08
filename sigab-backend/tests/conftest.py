"""
conftest.py — Mocks de nivel de sesión para tests unitarios del backend SIGAB.

Intercepta aiomysql y config antes de que se importen los módulos bajo test,
evitando el crash de cryptography en el entorno de CI/remoto.
"""
import sys
from unittest.mock import MagicMock, AsyncMock

# ── Mock aiomysql (evita cadena pymysql→cryptography en entorno CI) ──
aiomysql_mock = MagicMock()
aiomysql_mock.connect = AsyncMock()
aiomysql_mock.DictCursor = MagicMock()
sys.modules.setdefault("aiomysql", aiomysql_mock)

# ── Mock config con las variables que usa gemma_service ──────────────
config_mock = MagicMock()
config_mock.OLLAMA_HOST = "http://localhost:11434"
config_mock.GEMMA_MODEL = "gemma3:4b"
config_mock.QWEN_MODEL = "qwen2.5:7b"
config_mock.MINIMAX_API_KEY = ""
config_mock.MINIMAX_BASE_URL = "https://api.minimax.io/v1"
config_mock.MINIMAX_MODEL = "MiniMax-Text-01"
config_mock.AI_EDGE_PROBE_TIMEOUT = 3
config_mock.get_db = AsyncMock()
sys.modules.setdefault("config", config_mock)
