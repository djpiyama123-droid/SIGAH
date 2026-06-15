#!/bin/bash
# ================================================================
# SIGAB — Script de arranque rápido (sin Docker)
# Hospital General Regional No. 1 — IMSS Tijuana
# Entorno: WSL2 Ubuntu 24.04 / Lenovo ThinkCentre M720q
# Uso: bash start_sigab.sh [--reset-db] [--no-bot]
# ================================================================

set -e

RESET_DB=false
NO_BOT=false
[[ "$1" == "--reset-db" ]] && RESET_DB=true
[[ "$1" == "--no-bot" || "$2" == "--no-bot" ]] && NO_BOT=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
BACKEND_DIR="$PROJECT_DIR/sigab-backend"
FRONTEND_DIR="$PROJECT_DIR/sigab-frontend"
BOT_DIR="$PROJECT_DIR/sigab-bot"

DB_USER="${DB_USER:-sigab_user}"
DB_PASS="${DB_PASS:?Define DB_PASS antes de ejecutar (export DB_PASS=...)}"
DB_NAME="${DB_NAME:-sigab}"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "═══════════════════════════════════════════════"
echo "  SIGAB — Sistema de Gestión de Activos Biomédicos"
echo "  HGR No.1 IMSS Tijuana — On-Premise"
echo "  Lenovo ThinkCentre M720q (i5 / 8GB / 256GB)"
echo "═══════════════════════════════════════════════${NC}"

mkdir -p "$LOG_DIR"

# ── 1. Verificar MySQL ─────────────────────────────────────────
echo -e "\n${YELLOW}[1/5] Verificando MySQL...${NC}"
if ! command -v mysql &>/dev/null; then
    echo -e "${RED}MySQL no encontrado. Instala con: sudo apt install mysql-server${NC}"
    exit 1
fi

if ! systemctl is-active --quiet mysql 2>/dev/null; then
    echo "    Iniciando MySQL..."
    sudo service mysql start || sudo systemctl start mysql
fi

sleep 1
mysql -u "$DB_USER" -p"$DB_PASS" -e "SELECT 1;" "$DB_NAME" &>/dev/null || {
    echo -e "${RED}No se puede conectar a MySQL con $DB_USER@$DB_NAME${NC}"
    echo "Verifica credenciales o ejecuta el setup de BD primero."
    exit 1
}
echo -e "    ${GREEN}MySQL: OK${NC}"

# ── 2. Aplicar schema y seed ───────────────────────────────────
echo -e "\n${YELLOW}[2/5] Aplicando esquema de base de datos...${NC}"
if [[ "$RESET_DB" == "true" ]]; then
    echo "    Modo --reset-db: recreando tablas..."
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$PROJECT_DIR/database/sigab_schema.sql" 2>/dev/null || true
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$PROJECT_DIR/database/seed_data.sql" 2>/dev/null || true
    echo -e "    ${GREEN}Schema + Seed: OK${NC}"
else
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$PROJECT_DIR/database/sigab_schema.sql" 2>/dev/null || true
    echo -e "    ${GREEN}Schema: OK (sin cambios si ya existía)${NC}"
fi

# ── 3. Iniciar Backend FastAPI ─────────────────────────────────
echo -e "\n${YELLOW}[3/5] Iniciando backend FastAPI...${NC}"
pkill -f "uvicorn main:app" 2>/dev/null && sleep 1 || true

cd "$BACKEND_DIR"

if [[ ! -d "venv" ]]; then
    echo "    Creando virtualenv..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q --no-cache-dir

mkdir -p static/uploads

export SIGAB_DB_HOST="${DB_HOST:-127.0.0.1}"
export SIGAB_DB_PORT="${DB_PORT:-3306}"
export SIGAB_DB_USER="$DB_USER"
export SIGAB_DB_PASS="$DB_PASS"
export SIGAB_DB_NAME="$DB_NAME"

nohup uvicorn main:app --host 0.0.0.0 --port 8000 \
    > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"

echo -n "    Esperando backend"
for i in {1..20}; do
    sleep 1
    if curl -sf http://localhost:8000/health &>/dev/null; then
        echo -e " ${GREEN}OK${NC}"
        break
    fi
    echo -n "."
done

cd "$PROJECT_DIR"

# ── 4. Iniciar Frontend React ──────────────────────────────────
echo -e "\n${YELLOW}[4/5] Iniciando frontend React...${NC}"
pkill -f "vite" 2>/dev/null && sleep 1 || true

cd "$FRONTEND_DIR"

if [[ ! -d "node_modules" ]]; then
    echo "    Instalando dependencias npm..."
    npm install --silent
fi

nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "    Frontend PID: $FRONTEND_PID"

sleep 3
cd "$PROJECT_DIR"

# ── 5. Iniciar Bot WhatsApp (Baileys) ─────────────────────────
BOT_PID=""
if [[ "$NO_BOT" == "false" && -d "$BOT_DIR" ]]; then
    echo -e "\n${YELLOW}[5/5] Iniciando SIGAB Bot (WhatsApp)...${NC}"
    pkill -f "sigab-bot" 2>/dev/null && sleep 1 || true

    cd "$BOT_DIR"

    if [[ ! -d "node_modules" ]]; then
        echo "    Instalando dependencias del bot..."
        npm install --silent
    fi

    nohup node index.js > "$LOG_DIR/bot.log" 2>&1 &
    BOT_PID=$!
    echo "    Bot PID: $BOT_PID"
    echo -e "    ${GREEN}Bot WhatsApp: Iniciado${NC}"
    echo "    📱 Si es la primera vez, escanea el QR en: tail -f $LOG_DIR/bot.log"

    cd "$PROJECT_DIR"
else
    echo -e "\n${YELLOW}[5/5] Bot WhatsApp: omitido (--no-bot o carpeta no existe)${NC}"
fi

# ── Resumen ────────────────────────────────────────────────────
echo -e "\n${GREEN}"
echo "═══════════════════════════════════════════════"
echo "  SIGAB activo — Lenovo ThinkCentre M720q"
echo ""
echo "  Dashboard:    http://localhost:5173"
echo "  Modo TV:      http://localhost:5173/tv"
echo "  API Docs:     http://localhost:8000/docs"
echo "  SSE Stream:   http://localhost:8000/api/dashboard/stream"
echo "  Bot Logs:     tail -f $LOG_DIR/bot.log"
echo "  Logs:         $LOG_DIR/"
echo ""
echo "  Para detener: bash scripts/stop_sigab.sh"
echo "═══════════════════════════════════════════════${NC}"

# Guardar PIDs para stop script
echo "$BACKEND_PID"  > "$LOG_DIR/backend.pid"
echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"
[[ -n "$BOT_PID" ]] && echo "$BOT_PID" > "$LOG_DIR/bot.pid"
