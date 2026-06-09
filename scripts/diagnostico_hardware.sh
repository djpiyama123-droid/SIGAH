#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════
# SIGAH — Diagnóstico de hardware on-premise
# Correr en la PC candidata (ex-tomógrafo GE) una vez que arranque Linux.
#
# Objetivo: capturar specs REALES para decidir si sirve como servidor
# on-premise y/o para correr modelos OSS de IA localmente.
#
# Uso:
#   chmod +x diagnostico_hardware.sh
#   ./diagnostico_hardware.sh | tee diagnostico_$(hostname)_$(date +%Y%m%d).txt
#
# Mandame el archivo de salida y con eso aterrizamos la arquitectura.
# ════════════════════════════════════════════════════════════════════
set -uo pipefail

sec() { printf '\n══════ %s ══════\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

sec "IDENTIDAD / SO"
date
hostname
uname -a
( . /etc/os-release 2>/dev/null && echo "OS: ${PRETTY_NAME:-desconocido}" ) || echo "OS: desconocido"

sec "CPU (lo importante: modelo, núcleos, AVX2/AVX-512)"
if have lscpu; then
  lscpu | grep -Ei 'model name|socket|core|thread|cpu\(s\)|mhz' || true
  echo "--- flags relevantes para IA ---"
  lscpu | grep -Eio 'avx2|avx512[a-z]*|fma|f16c|amx[a-z_]*' | sort -u | tr '\n' ' '; echo
else
  grep -Ei 'model name|flags' /proc/cpuinfo | head -2
fi

sec "MEMORIA RAM (clave para cuán grande un modelo cabe en CPU)"
free -h 2>/dev/null || cat /proc/meminfo | head -3

sec "GPU — EL FACTOR DECISIVO PARA IA LOCAL"
if have nvidia-smi; then
  echo ">>> NVIDIA detectada:"
  nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv 2>/dev/null \
    || nvidia-smi
  echo "NOTA: para LLMs útiles se quiere compute_cap >= 7.0 y VRAM >= 16 GB."
else
  echo ">>> Sin driver NVIDIA. GPUs físicas presentes en el bus PCIe:"
fi
if have lspci; then
  lspci | grep -Ei 'vga|3d|display|nvidia|amd/ati' || echo "  (ninguna GPU listada por lspci)"
else
  echo "  lspci no disponible — instalar pciutils"
fi

sec "ALMACENAMIENTO (verificar el famoso '500 TB')"
lsblk -o NAME,SIZE,TYPE,MODEL,MOUNTPOINT 2>/dev/null || true
echo "--- uso de filesystems ---"
df -hT 2>/dev/null | grep -Ev 'tmpfs|loop' || true

sec "RED (interfaces; ojo con las propietarias del tomógrafo)"
ip -br addr 2>/dev/null || ifconfig -a 2>/dev/null | grep -E 'flags|inet ' || true

sec "VIRTUALIZACIÓN / CONTENEDORES (para Docker)"
if have lscpu; then lscpu | grep -i virtual || true; fi
have docker && docker --version || echo "Docker: no instalado"

sec "BIOS / PLACA (riesgo de firmware bloqueado GE)"
if have dmidecode; then
  sudo dmidecode -t bios -t baseboard -t system 2>/dev/null \
    | grep -Ei 'manufacturer|product|version|vendor|release date' | head -20 \
    || echo "  (requiere sudo / dmidecode)"
else
  echo "  dmidecode no disponible — instalar para ver fabricante/BIOS"
fi

sec "VEREDICTO RÁPIDO (heurística)"
ram_gb=$(free -g 2>/dev/null | awk '/Mem:/{print $2}')
echo "RAM total: ${ram_gb:-?} GB"
if have nvidia-smi; then
  echo "→ Hay GPU NVIDIA: revisar VRAM y compute_cap arriba para dimensionar el modelo OSS."
else
  echo "→ Sin GPU NVIDIA usable: viable solo para modelos chicos (7-8B cuantizados) en CPU,"
  echo "  o como servidor de app/BD/bot. Para IA seria, agregar GPU moderna (≥16-24 GB VRAM)."
fi
echo ""
echo "Listo. Enviá el .txt generado para definir la arquitectura final."
