"""
config.py — Variables de configuración centralizadas del backend SIGAB.

Todas las configuraciones se leen de variables de entorno con prefijo SIGAB_*.
Se proporcionan valores por defecto para desarrollo local.

Secciones:
  - DB_CONFIG:         Conexión MySQL (host, port, user, pass, db)
  - JWT:               Secreto, algoritmo, TTL de acceso y refresh
  - PUBLIC_BASE_URL:   URL embebida en QRs (IP LAN en producción)
  - CORS_EXTRA:        Orígenes adicionales para celulares en LAN
  - OLLAMA/GEMMA:      IA local vía Ollama (Gemma 4B / Qwen 7B) — nodo edge Lenovo
  - MINIMAX:           Fallback cloud API (MiniMax) cuando Ollama no responde
  - OCR:               Umbral de confianza y API key de Gemini
"""
import aiomysql
import os

DB_CONFIG = {
    "host": os.getenv("SIGAB_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("SIGAB_DB_PORT", 3306)),
    "user": os.getenv("SIGAB_DB_USER", "sigab_user"),
    "password": os.getenv("SIGAB_DB_PASS", "sigab_pass_2026"),
    "db": os.getenv("SIGAB_DB_NAME", "sigab"),
    "autocommit": True,
}

UPLOAD_DIR = os.getenv("SIGAB_UPLOAD_DIR", "./static/uploads")
MAX_UPLOAD_MB = 10

# ── Autenticación JWT ─────────────────────────────────────────────
# SIGAB_JWT_SECRET es OBLIGATORIO en producción. En dev cae a un valor
# fijo (no aleatorio) para no invalidar sesiones al reiniciar.
JWT_SECRET = os.getenv(
    "SIGAB_JWT_SECRET",
    "dev-secret-CAMBIAR-EN-PRODUCCION-usa-secrets.token_urlsafe-48",
)
JWT_ALG = os.getenv("SIGAB_JWT_ALG", "HS256")
ACCESS_TTL_MIN = int(os.getenv("SIGAB_ACCESS_TTL_MIN", "60"))
REFRESH_TTL_DAYS = int(os.getenv("SIGAB_REFRESH_TTL_DAYS", "7"))

# URL base pública para embeber en QR. Puede ser IP LAN, hostname o dominio.
PUBLIC_BASE_URL = os.getenv("SIGAB_PUBLIC_BASE_URL", "http://localhost:5173")

# CORS extra (separados por coma) para permitir escaneo desde celulares LAN
_cors_env = os.getenv("SIGAB_CORS_EXTRA", "")
_cors_lan = ["http://192.168.1.125:5173", "http://192.168.1.125:5174"]
CORS_EXTRA = [*_cors_lan, *[o.strip() for o in _cors_env.split(",") if o.strip()]]

# ── IA Local (Qwen / Gemma via Ollama) ────────────────────────────
# Ollama se instala en el mismo servidor (Lenovo ThinkCentre) y expone :11434
OLLAMA_HOST = os.getenv("SIGAB_OLLAMA_HOST", "http://localhost:11434")
GEMMA_MODEL = os.getenv("SIGAB_GEMMA_MODEL", "gemma3:4b")
QWEN_MODEL = os.getenv("SIGAB_QWEN_MODEL", "qwen2.5:7b")

# ── Fallback IA Nube (MiniMax) ────────────────────────────────────
# Activo solo cuando SIGAB_MINIMAX_API_KEY está definido en .env.
# Proporciona continuidad del Copilot cuando el nodo edge Lenovo no está disponible.
# API compatible con OpenAI Chat Completions v1.
MINIMAX_API_KEY = os.getenv("SIGAB_MINIMAX_API_KEY", "")
MINIMAX_HOST = os.getenv("SIGAB_MINIMAX_HOST", "https://api.minimax.io/v1")
MINIMAX_MODEL = os.getenv("SIGAB_MINIMAX_MODEL", "abab6.5s-chat")

# ── OCR Pipeline Config ──────────────────────────────────────────
OCR_CONFIDENCE_THRESHOLD = float(os.getenv("SIGAB_OCR_CONFIDENCE", "0.85"))
OCR_MIN_WORDS_THRESHOLD = int(os.getenv("SIGAB_OCR_MIN_WORDS", "5"))
GEMINI_API_KEY = os.getenv("SIGAB_GEMINI_API_KEY", "")


async def get_db():
    conn = await aiomysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()
