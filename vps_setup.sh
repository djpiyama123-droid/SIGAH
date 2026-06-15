#!/bin/bash
# ================================================================
# SIGAB — Setup completo en VPS Ubuntu
# Se ejecuta REMOTAMENTE desde deploy_to_vps.sh
# ================================================================
set -e

REMOTE_DIR="/opt/sigab"
cd "${REMOTE_DIR}"

log() { echo ""; echo "━━━ $1"; }

# ── FASE 1: Sistema base ─────────────────────────────────────
log "FASE 1: Actualizando sistema e instalando dependencias base"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl wget git nginx ufw python3 python3-pip \
  ca-certificates gnupg lsb-release build-essential

# ── Docker CE ────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Instalando Docker CE"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
fi

# ── Node.js 22 ───────────────────────────────────────────────
if ! node --version 2>/dev/null | grep -q "^v22"; then
  log "Instalando Node.js 22 LTS"
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y -qq nodejs
fi
echo "Node: $(node --version) | npm: $(npm --version)"

# ── FASE 2: Ollama ───────────────────────────────────────────
log "FASE 2: Instalando Ollama"
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.ai/install.sh | sh
fi
systemctl enable ollama
systemctl start ollama || true
sleep 3

# Descargar modelo cuantizado (gemma3:4b — ~2.5GB, razonable para VPS)
echo "Descargando gemma3:4b (puede tardar varios minutos según conexión)..."
ollama pull gemma3:4b || echo "[WARN] No se pudo descargar gemma3:4b — Copilot IA estará inactivo"

# ── FASE 3: Build del frontend React ────────────────────────
log "FASE 3: Compilando frontend React"
cd "${REMOTE_DIR}/sigab-frontend"
npm ci --silent
npm run build
echo "Frontend compilado en: ${REMOTE_DIR}/sigab-frontend/dist/"
cd "${REMOTE_DIR}"

# ── FASE 4: Docker Compose (MySQL + Backend) ─────────────────
log "FASE 4: Levantando servicios con Docker Compose"
docker compose --env-file .env pull --quiet 2>/dev/null || true
docker compose --env-file .env up -d --build

echo "Esperando que MySQL y el backend arranquen..."
sleep 15

# Verificar health del backend
for i in $(seq 1 12); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend OK"
    break
  fi
  echo "Esperando backend... intento $i/12"
  sleep 5
done

# ── FASE 5: Nginx ────────────────────────────────────────────
log "FASE 5: Configurando Nginx"
cat > /etc/nginx/sites-available/sigab << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    root /opt/sigab/sigab-frontend/dist;
    index index.html;

    # React SPA — todas las rutas sirven index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API → FastAPI
    location /api/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   Connection '';
        # SSE — sin buffering
        proxy_buffering    off;
        proxy_cache        off;
        proxy_read_timeout 3600s;
        chunked_transfer_encoding on;
    }

    # Archivos estáticos (imágenes de equipos)
    location /static/ {
        proxy_pass http://127.0.0.1:8000;
    }

    client_max_body_size 20M;
}
NGINXEOF

ln -sf /etc/nginx/sites-available/sigab /etc/nginx/sites-enabled/sigab
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
systemctl enable nginx

# ── FASE 6: Firewall ─────────────────────────────────────────
log "FASE 6: Configurando firewall"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ── Resultado final ──────────────────────────────────────────
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║          SIGAB DESPLEGADO EXITOSAMENTE               ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Frontend: http://${VPS_IP}/                    "
echo "║  API:      http://${VPS_IP}/api/docs            "
echo "║  Health:   http://${VPS_IP}/api/health          "
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Admin:    ADMIN001 / (ver SIGAB_ADMIN_PASSWORD)     ║"
echo "╚══════════════════════════════════════════════════════╝"
