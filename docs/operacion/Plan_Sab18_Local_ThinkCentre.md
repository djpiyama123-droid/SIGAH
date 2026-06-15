# 🖥️ SIGAB — Plan Pragmático Sáb 18 → Lun 20 · abril 2026
## Levantamiento LOCAL en Lenovo ThinkCentre (antes del Ambigu martes 21)

> **Cambio de alcance:** El sábado NO se instala en la oficina IMSS. Solo se prepara la ThinkCentre EN CASA como ambiente de pruebas local. Objetivo: tener SIGAB corriendo 100% en la ThinkCentre para visualizar, probar y afinar sábado, domingo y lunes. Instalación en sitio → pospuesta.

---

## 0. Decisión técnica: ¿Linux o Windows?

### Recomendación: **Ubuntu 24.04 LTS** ✅

| Criterio | Ubuntu 24.04 LTS | Windows 11 |
|---|---|---|
| Docker nativo | ✅ Rendimiento completo | ⚠️ Docker Desktop via WSL2 — overhead ~15% |
| Ollama + Gemma | ✅ Soporte nativo CPU/GPU | ⚠️ Más lento, más RAM |
| MySQL 8 | ✅ Óptimo | ⚠️ Funciona pero más pesado |
| systemd auto-arranque | ✅ Nativo | ❌ Requiere configuración manual |
| RAM idle | ~1.2 GB | ~4 GB |
| Costo licencia | $0 | Si no tienes licencia, $$$ |
| Coherencia con producción | ✅ Misma plataforma que servidor IMSS | ❌ Divergencia |
| Tiempo de instalación | 25–30 min | 45–60 min |

> La ThinkCentre M720q probablemente tiene 8–16 GB RAM. Ubuntu te deja 5–7 GB libres para Docker + Ollama. Windows te deja 2–4 GB — apretado para Gemma.

**Veredicto:** Ubuntu 24.04 LTS Desktop (no Server — necesitas GUI para ver el navegador corriendo SIGAB).

---

## 1. Sábado 18 · hoy — Setup base ThinkCentre (estimado 4–6 h)

### 1.1 Respaldo de archivos personales (45 min)
Antes de formatear, rescata lo que importa.

```bash
# Conectar USB externo (≥ 32 GB)
# Desde el SO actual de la ThinkCentre (Windows o Linux viejo):

# Carpetas típicas a respaldar:
#   C:\Users\<usuario>\Desktop
#   C:\Users\<usuario>\Documents
#   C:\Users\<usuario>\Pictures
#   C:\Users\<usuario>\Downloads (revisar qué vale la pena)

# Si es Windows, usa Explorador → arrastra a USB
# Si es Linux, rsync:
rsync -av --progress /home/tu_usuario/ /media/usb/backup_20260418/
```

**Checklist respaldo:**
- [ ] Fotos y videos personales
- [ ] Documentos (PDFs, Word, tesis, tareas)
- [ ] Configs de apps que uses (claves SSH, .bashrc, bookmarks navegador)
- [ ] Proyectos de código si los tienes ahí
- [ ] Listado `ls -la ~` comparado con el USB para confirmar

**Verificación integridad:**
```bash
# Verifica que el USB tenga todos los archivos
du -sh /media/usb/backup_20260418/
# Compáralo con: du -sh ~/ del sistema viejo
```

### 1.2 Crear USB booteable Ubuntu 24.04 LTS (30 min)

**Descargar ISO** (en la Asus TUF, mientras respaldas):
```
https://releases.ubuntu.com/24.04/
→ ubuntu-24.04.x-desktop-amd64.iso  (~5.5 GB)
```

**Crear USB booteable:**
- En Windows: [Rufus](https://rufus.ie) → seleccionar ISO → escribir USB (8 GB+)
- En Linux: `sudo dd if=ubuntu-24.04.iso of=/dev/sdX bs=4M status=progress && sync`
- En Mac: usar Balena Etcher o `dd`

### 1.3 Instalación Ubuntu 24.04 LTS (40 min)

1. Insertar USB en ThinkCentre, power on, **F12** = boot menu (Lenovo).
2. Seleccionar USB.
3. "Try or Install Ubuntu" → **Install Ubuntu**.
4. Idioma: Español (México). Teclado: Spanish (Latin American).
5. Conexión a Wi-Fi/Ethernet de CASA (no IMSS aún).
6. Tipo de instalación: **Erase disk and install Ubuntu** (ya respaldaste).
7. Zona horaria: Tijuana.
8. Usuario:
   - Tu nombre: Gustavo Aguilar
   - Nombre del equipo: `sigab-server`
   - Usuario: `sigab`
   - Password: <password-fuerte-que-recuerdes>
   - [x] Require password to log in
9. Instalar → 15–20 min → Reiniciar → quitar USB.

### 1.4 Post-instalación — actualizar y herramientas esenciales (20 min)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Herramientas básicas
sudo apt install -y \
    curl wget git htop tree unzip \
    build-essential ca-certificates \
    software-properties-common \
    net-tools openssh-server \
    vim nano

# Habilitar SSH por si quieres conectarte desde la Asus
sudo systemctl enable --now ssh

# Ver la IP que te dio el router de casa
ip a | grep inet
# Ejemplo: 192.168.1.55 — anótala para conectarte desde la Asus si quieres
```

### 1.5 Instalar Docker + Docker Compose (20 min)

```bash
# Añadir repositorio oficial Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Permitir a tu usuario usar docker sin sudo
sudo usermod -aG docker $USER
# IMPORTANTE: cerrar sesión y volver a entrar para que aplique

# Verificar (después del re-login):
docker run hello-world
docker compose version
```

### 1.6 Instalar Node.js 20 + Python 3.12 (15 min)

```bash
# Node.js 20 LTS (para frontend dev si necesitas correr sin Docker)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # debe mostrar v20.x
npm --version

# Python 3.12 (ya viene con Ubuntu 24.04)
python3 --version   # debe mostrar 3.12.x
sudo apt install -y python3-pip python3-venv
```

### 1.7 Clonar repo SIGAB (10 min)

```bash
# Desde donde tengas el repo — opciones:

# Opción A: Si el repo está en GitHub/GitLab privado
cd ~
git clone https://github.com/<tu-usuario>/sigab.git
cd sigab
git checkout prototipo    # o la rama que tengas como "funcional"

# Opción B: Si tienes el repo en la Asus TUF
# Desde la Asus:
#   cd ~/sigab
#   tar czf /tmp/sigab-prototipo.tar.gz .
#   scp /tmp/sigab-prototipo.tar.gz sigab@192.168.1.55:~/
# En la ThinkCentre:
cd ~
tar xzf sigab-prototipo.tar.gz -C ~/sigab
cd ~/sigab

# Opción C: USB
# Copia la carpeta del repo al USB y de ahí a la ThinkCentre:
cp -r /media/usb/sigab ~/
cd ~/sigab
```

**Verifica estructura:**
```bash
ls -la
# Debes ver:
#   sigab-backend/
#   sigab-frontend/
#   sigab-bot/        (si ya existe)
#   migrations/
#   docker-compose.yml
#   README.md
```

### 1.8 Configurar variables de entorno (5 min)

```bash
cd ~/sigab

# Si existe .env.example, copiar a .env
cp .env.example .env
nano .env   # editar si hace falta

# Valores mínimos típicos:
# MYSQL_ROOT_PASSWORD=${DB_ROOT_PASS}
# MYSQL_DATABASE=sigab
# MYSQL_USER=sigab_admin
# MYSQL_PASSWORD=${ADMIN_PASSWORD}
# JWT_SECRET_KEY=<genera-uno-seguro>
# OLLAMA_MODEL=gemma3:4b
```

### 1.9 Descargar imágenes Docker (15–30 min, depende de tu internet)

```bash
cd ~/sigab

# Descargar todas las imágenes necesarias de antemano
docker compose pull

# Esto bajará:
#  - mysql:8.0      (~600 MB)
#  - python:3.12    (~1 GB)
#  - node:20        (~1 GB)
#  - ollama/ollama  (~300 MB)
```

### 1.10 Primer arranque del stack (20 min)

```bash
cd ~/sigab
docker compose up -d

# Seguir logs en vivo
docker compose logs -f
# Ctrl+C cuando veas "Application startup complete" del backend
# y "ready in X ms" del frontend

# Verificar
docker compose ps

# Healthchecks
curl -s localhost:8000/health | python3 -m json.tool
curl -s -o /dev/null -w "HTTP %{http_code}\n" localhost:5173

# Abrir el navegador en la ThinkCentre
firefox http://localhost:5173 &
# O Chrome si lo instalas:
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# sudo apt install ./google-chrome-stable_current_amd64.deb
```

### 1.11 Descargar modelo Gemma para Ollama (15–20 min)

```bash
# Gemma 3 4B cuantizado (~3 GB)
docker exec -it ollama-gemma ollama pull gemma3:4b

# Verifica
docker exec ollama-gemma ollama list

# Si la ThinkCentre es de 8 GB RAM, usa el modelo 1B para margen:
# docker exec -it ollama-gemma ollama pull gemma3:1b
```

### 1.12 Seed de datos demo (5 min)

```bash
# Ejecutar el script de siembra
docker exec sigab-backend python -m scripts.seed_demo
# Crea: 25 equipos, 6 zonas, 10 órdenes, 5 preventivos, 3 alertas

# Login en el navegador:
#   Usuario: ADMIN001
#   Password: ${ADMIN_PASSWORD}
```

### 1.13 Validación final del sábado (10 min)

Recorre estas 7 pantallas y marca que cargan sin error:

- [ ] Dashboard — KPIs visibles, mapa presente
- [ ] Equipos — tabla con 25+ equipos, filtros funcionan
- [ ] Órdenes — lista de órdenes, click a detalle
- [ ] Preventivos — calendario renderiza
- [ ] Alertas — panel de alertas
- [ ] Tecnovigilancia — formulario NOM-240 carga
- [ ] Copilot — chat funciona (prueba: "¿cuántos equipos hay?")

Si algo falla → anota el error exacto, no lo arregles hoy. Mañana (domingo) revisamos todo.

### 1.14 Último paso del sábado: auto-arranque (5 min)

```bash
# Crear servicio systemd para que SIGAB arranque solo al prender la PC
sudo tee /etc/systemd/system/sigab.service > /dev/null <<EOF
[Unit]
Description=SIGAB Stack (Docker Compose)
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/sigab/sigab
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sigab.service
sudo systemctl status sigab.service
```

**Prueba el auto-arranque:** reinicia la ThinkCentre (`sudo reboot`). Al regresar, espera 60 s y abre `http://localhost:5173`. Debe cargar sin que tú hagas `docker compose up`.

---

## 2. Domingo 19 · abril — Día de pruebas visuales (todo el día)

> **Mantra del domingo:** Hoy NO instalas nada nuevo. Solo USAS SIGAB y documentas qué se ve mal.

### 2.1 Lista de flujos a probar exhaustivamente

Por cada flujo, abre una nota en `~/sigab/_notas_domingo.md` y anota bugs:

1. **Login** — probar bien, mal, olvidar password, cerrar sesión.
2. **Dashboard** — ¿carga el mapa? ¿los KPIs tienen sentido? ¿SSE actualiza?
3. **Equipos** — crear nuevo, editar, filtrar por zona/estado/tipo, eliminar, QR.
4. **Órdenes** — crear manual, transicionar estados, cerrar, generar PDF.
5. **Preventivos** — ver calendario, crear preventivo, marcar completado.
6. **Alertas** — ver alertas activas, marcar como leídas.
7. **Tecnovigilancia** — llenar formato evento adverso.
8. **Trazabilidad** — verificar cadena hash.
9. **Copilot** — 5 preguntas en lenguaje natural.
10. **Reportes** — generar PDF mensual, Excel de equipos.

### 2.2 Si algo no funciona

```bash
# Ver logs del contenedor específico
docker compose logs -f sigab-backend   # o sigab-frontend
docker compose logs --tail=200 sigab-backend | grep ERROR

# Reiniciar un contenedor puntual
docker compose restart sigab-backend

# Reset completo (sin borrar BD)
docker compose down && docker compose up -d

# Reset TOTAL (borra BD, re-seed)
docker compose down -v && docker compose up -d
docker exec sigab-backend python -m scripts.seed_demo
```

### 2.3 (Opcional, si hay tiempo) Configurar OpenClaw bot WhatsApp

Si terminas las pruebas temprano y quieres adelantar:

```bash
cd ~/sigab/sigab-bot
npm install
# Seguir instrucciones específicas del README del bot
# Requiere: teléfono IMSS + ADB + Chromium
```

**Decisión:** si OpenClaw no arranca en 1–2 h, diferir. No es crítico para la presentación del Ambigu — se puede mostrar por video previo.

---

## 3. Lunes 20 · abril — Pulido + ensayo (media mañana)

### 3.1 AM: corregir los bugs anotados el domingo
- Revisar lista `_notas_domingo.md`
- Arreglar los críticos (los que impiden demostrar)
- Diferir los cosméticos

### 3.2 PM: ensayo de la demo
- Cronometra tu demo completa (meta: 12–15 min)
- Graba con OBS Studio la pantalla para revisar
- Práctica las preguntas típicas (ver Guion de Demo)

---

## 4. Checklist de dependencias — qué DEBE estar instalado al final del sábado

```
SISTEMA OPERATIVO
☐ Ubuntu 24.04 LTS Desktop
☐ Usuario "sigab" con sudo
☐ SSH habilitado

HERRAMIENTAS DE SISTEMA
☐ git
☐ curl, wget
☐ build-essential
☐ openssh-server

RUNTIMES
☐ Docker CE + docker compose plugin
☐ Node.js 20 LTS + npm
☐ Python 3.12 + pip + venv

IMÁGENES DOCKER DESCARGADAS
☐ mysql:8.0
☐ python:3.12 (base del backend)
☐ node:20 (base del frontend)
☐ ollama/ollama
☐ Cualquier otra imagen de docker-compose.yml

MODELOS IA
☐ gemma3:4b (o 1b si la RAM es justa) via Ollama

REPO CLONADO Y CORRIENDO
☐ ~/sigab con el código del prototipo
☐ .env configurado
☐ docker compose up -d sin errores
☐ Los 4 contenedores en healthy
☐ http://localhost:5173 responde 200
☐ http://localhost:8000/health responde {"status":"ok"}

AUTO-ARRANQUE
☐ systemd unit sigab.service habilitado
☐ Prueba: reboot y sigue arriba

DATOS DEMO
☐ seed_demo ejecutado (25+ equipos)
☐ Login ADMIN001 funciona
```

---

## 5. Matriz de tiempos — sábado

| Actividad | Duración | Acumulado |
|---|---|---|
| Respaldo archivos personales | 45 min | 0:45 |
| Crear USB booteable | 30 min | 1:15 |
| Instalar Ubuntu 24.04 | 40 min | 1:55 |
| Post-instalación + apt upgrade | 20 min | 2:15 |
| Docker + Docker Compose | 20 min | 2:35 |
| Node + Python | 15 min | 2:50 |
| Clonar repo | 10 min | 3:00 |
| Configurar .env | 5 min | 3:05 |
| Descargar imágenes Docker | 30 min | 3:35 |
| Primer arranque stack | 20 min | 3:55 |
| Descargar Gemma | 20 min | 4:15 |
| Seed demo | 5 min | 4:20 |
| Validación 7 pantallas | 10 min | 4:30 |
| Auto-arranque systemd | 5 min | 4:35 |

**Total estimado: 4 h 35 min** — si arrancas a las 10:00 AM, terminas a las 14:35. Descontando 30 min de almuerzo y algún imprevisto → **terminas alrededor de las 16:00**.

---

## 6. Problemas comunes y solución rápida

| Síntoma | Solución |
|---|---|
| USB no bootea | En BIOS (F1 al encender), desactiva Secure Boot y Fast Boot. Prioridad 1: USB. |
| Ubuntu no ve el disco | Probablemente RAID/Intel RST. En BIOS cambiar SATA mode a AHCI. |
| `docker run hello-world` pide permisos | No cerraste sesión tras `usermod -aG docker`. Logout + login. |
| `docker compose up` dice "port already in use" | Algo usa 5173/8000. `sudo lsof -i :5173` y mata el proceso. |
| Ollama responde "model not found" | `docker exec ollama-gemma ollama pull gemma3:4b` |
| Frontend carga pero queda en loading | Backend no responde. `docker compose logs sigab-backend` |
| MySQL "connection refused" al backend | BD tarda ~20 s en arrancar. Espera. Si persiste: `docker compose restart sigab-backend` |
| La ThinkCentre se queda sin RAM con Gemma 4B | Bájalo a 1B: `docker exec ollama-gemma ollama pull gemma3:1b` y cambia `.env` |

---

## 7. Cuando termines el sábado

1. Toma captura de pantalla del Dashboard cargado (prueba de éxito).
2. Reinicia la ThinkCentre y verifica que SIGAB vuelve solo.
3. Déjala prendida durante el fin de semana (modo ahorro de energía OFF).
4. Desde la Asus, prueba acceder: `http://<ip-thinkcentre-lan-casa>:5173`.
5. Descansa. Mañana es día de PROBAR, no de configurar.

---

## 8. Lo que NO estás haciendo hoy (deliberadamente)

- ❌ Instalar en la oficina de Conservación → se difiere
- ❌ Configurar IP estática de red IMSS → se difiere
- ❌ Conectar a BD existente del IMSS → se difiere
- ❌ Refactor del Dashboard v2 → se hace después del Ambigu si Carlos lo pide
- ❌ Eliminar módulos → se hace después del Ambigu
- ❌ OpenClaw bot → opcional, domingo si hay tiempo

**La meta es simple:** tener SIGAB corriendo en la ThinkCentre para poder DEMOSTRARLO visualmente el martes.

---

🤖 *Plan pragmático — revisado a la realidad del día.*
