#!/bin/bash
# ================================================================
# SIGAB — Deploy a VPS Bluehost
# Uso: bash deploy_to_vps.sh [VPS_PASS]
# ================================================================
set -e

VPS_IP="129.121.100.147"
VPS_USER="root"
REMOTE_DIR="/opt/sigab"
VPS_PASS="${1:-}"

# ── Verificar sshpass ────────────────────────────────────────
if ! command -v sshpass &>/dev/null; then
  echo "[ERROR] sshpass no está instalado. Instala con:"
  echo "  sudo apt install sshpass"
  echo ""
  echo "Alternativa sin sshpass (requiere llave SSH ya copiada):"
  echo "  Comenta las líneas SSHCMD/SCPCMD y usa ssh/scp directamente."
  exit 1
fi

if [ -z "$VPS_PASS" ]; then
  echo -n "Contraseña root del VPS: "
  read -s VPS_PASS
  echo ""
fi

SSH="sshpass -p ${VPS_PASS} ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP}"
SCP="sshpass -p ${VPS_PASS} scp -o StrictHostKeyChecking=no"

# ── Generar secretos de producción ──────────────────────────
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

echo "╔══════════════════════════════════════════════════════╗"
echo "║         SIGAB — Despliegue VPS ${VPS_IP}       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Crear .env para VPS ──────────────────────────────────────
cat > /tmp/sigab_vps.env << EOF
DB_USER=sigab_user
DB_PASS=${DB_PASS}
DB_NAME=sigab
DB_ROOT_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
SIGAB_JWT_SECRET=${JWT_SECRET}
SIGAB_PUBLIC_BASE_URL=http://${VPS_IP}
SIGAB_CORS_EXTRA=http://${VPS_IP},http://${VPS_IP}:80
SIGAB_OLLAMA_HOST=http://host-gateway:11434
SIGAB_GEMMA_MODEL=gemma3:4b
SIGAB_DISABLE_COPILOT=0
EOF

echo "[1/4] Transfiriendo proyecto al VPS..."
$SSH "mkdir -p ${REMOTE_DIR}"
sshpass -p "${VPS_PASS}" rsync -az --progress \
  --exclude='sigab-backend/venv' \
  --exclude='sigab-frontend/node_modules' \
  --exclude='sigab-frontend/dist' \
  --exclude='sigab-frontend/.vite' \
  --exclude='*.log' \
  --exclude='.git' \
  --exclude='logs/' \
  -e "ssh -o StrictHostKeyChecking=no" \
  "$(dirname "$0")/" \
  "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/"

echo "[2/4] Copiando variables de entorno..."
$SCP /tmp/sigab_vps.env "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/.env"
rm /tmp/sigab_vps.env

echo "[3/4] Ejecutando setup en el VPS (puede tomar 5-10 minutos)..."
$SSH "bash ${REMOTE_DIR}/vps_setup.sh 2>&1"

echo ""
echo "[4/4] ¡Despliegue completado!"
echo ""
echo "  Frontend: http://${VPS_IP}/"
echo "  API Docs: http://${VPS_IP}/api/docs"
echo "  Health:   http://${VPS_IP}/api/health"
echo ""
echo "  Credenciales admin:"
echo "    Matrícula: ADMIN001"
echo "    Password:  (el definido en SIGAB_ADMIN_PASSWORD)"
