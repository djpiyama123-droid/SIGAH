# SIGAB — Guía de Instalación en Ubuntu (desde cero)

## Requisitos del sistema
- **Ubuntu 22.04/24.04** (LTS recomendado)
- **4 GB RAM** mínimo (8 GB recomendado)
- **10 GB** de disco libre
- Conexión a internet (solo para instalación inicial)

---

## Opción A: Instalación automática (recomendada)

```bash
# 1. Copiar la carpeta SIGAB al servidor
# (USB, SCP, o git clone)

# 2. Entrar a la carpeta y ejecutar el script
cd ~/SIGAB
chmod +x setup.sh
./setup.sh
```

El script instala todo automáticamente: Node.js 18, Python 3.11+, MySQL 8, dependencias, BD, y arranca el sistema.

---

## Opción B: Instalación manual paso a paso

### 1. Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar MySQL 8.0

```bash
sudo apt install -y mysql-server mysql-client
sudo systemctl start mysql
sudo systemctl enable mysql

# Configurar contraseña de root
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';"

# Crear usuario y base de datos
sudo mysql -u root -p${DB_ROOT_PASS} -e "
CREATE DATABASE IF NOT EXISTS sigab CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS dummyequipomedicoimss CHARACTER SET utf8mb3;
CREATE USER IF NOT EXISTS 'sigab_user'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON sigab.* TO 'sigab_user'@'localhost';
GRANT ALL PRIVILEGES ON dummyequipomedicoimss.* TO 'sigab_user'@'localhost';
FLUSH PRIVILEGES;
"
```

### 3. Importar esquemas y datos

```bash
cd ~/SIGAB

# Esquema SIGAB (crea tablas del sistema)
mysql -u sigab_user -p${DB_PASS} sigab < database/sigab_schema_fresh.sql

# Migraciones adicionales (mapa, QR, etc.)
mysql -u sigab_user -p${DB_PASS} sigab < database/migrations/004_mapa_interactivo.sql
mysql -u sigab_user -p${DB_PASS} sigab < database/migrations/004_seed_hgr1.sql

# BD real del hospital (datos de equipos)
mysql -u sigab_user -p${DB_PASS} dummyequipomedicoimss < BaseDeDatosV2_190326.sql

# Migrar datos reales a SIGAB
pip3 install pymysql
python3 database/migrate_real_data.py
```

### 4. Instalar Node.js 18

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node -v   # Debe mostrar v18.x
npm -v
```

### 5. Instalar dependencias del frontend

```bash
cd ~/SIGAB/sigab-frontend
npm install
```

### 6. Instalar Python y dependencias del backend

```bash
sudo apt install -y python3 python3-pip python3-venv

cd ~/SIGAB/sigab-backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Instalar dependencias core (sin IA/OCR para la demo)
pip install fastapi==0.115.0 uvicorn[standard]==0.30.0 aiomysql==0.2.0 \
    python-multipart==0.0.9 aiofiles==24.1.0 qrcode[pil]==8.0 \
    Pillow==10.4.0 reportlab==4.2.5 python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 bcrypt==4.0.1 openpyxl==3.1.5 \
    httpx==0.27.0 sse-starlette>=1.8.0 sqlmodel asyncmy pymysql
```

> **Nota:** Las dependencias de IA (PaddleOCR, LangChain, etc.) son opcionales
> y pesadas. Para la demo no son necesarias.

### 7. Configurar variables de entorno

Crear archivo `.env` en `~/SIGAB/sigab-backend/`:

```bash
cat > ~/SIGAB/sigab-backend/.env << 'EOF'
SIGAB_DB_HOST=127.0.0.1
SIGAB_DB_PORT=3306
SIGAB_DB_USER=sigab_user
SIGAB_DB_PASS=${DB_PASS}
SIGAB_DB_NAME=sigab
SIGAB_SSL_DISABLED=true
SIGAB_JWT_SECRET=demo-hgr1-2026-secreto-cambiar-en-produccion
SIGAB_PUBLIC_BASE_URL=http://localhost:5173
EOF
```

### 8. Arrancar el sistema

**Terminal 1 — Backend:**
```bash
cd ~/SIGAB/sigab-backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd ~/SIGAB/sigab-frontend
npm run dev
```

### 9. Verificar

Abrir en el navegador:
- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

---

## Opción C: Docker Compose (si Docker está instalado)

```bash
cd ~/SIGAB

# Instalar Docker (si no está)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Arrancar todo
docker compose up -d

# Ver logs
docker compose logs -f
```

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `Error de conexión con el backend` | Verificar que uvicorn corra en puerto 8000 |
| `Access denied for user` | Verificar credenciales en `.env` |
| `Module not found` (Python) | Activar venv: `source venv/bin/activate` |
| `ENOSPC: no space left` | Liberar espacio en disco |
| El mapa no muestra equipos | Ejecutar `python3 database/migrate_real_data.py` |

---

## Acceso desde la red local

Para que otros dispositivos en la red del hospital accedan:

```bash
# Obtener la IP del servidor
ip addr show | grep "inet " | grep -v 127.0.0.1

# El frontend ya escucha en 0.0.0.0:5173
# Acceder desde otro equipo: http://<IP_DEL_SERVIDOR>:5173
```

---

**SIGAB v1.0.0** — Sistema Integral de Gestión de Activos Biomédicos
HGR No.1 IMSS Tijuana — Bioingeniería Xochicalco
