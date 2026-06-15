# 🚀 SIGAB — Arranque Rápido Asus TUF · Café Quijarro

**Ejecuta estos comandos EN ORDEN en la Asus TUF. Copia-pega, uno por uno.**

---

## 1. Abrir terminal y posicionarse en el proyecto

```bash
cd ~/sigab
# (o la ruta donde tengas el repo — usa `ls` para verificar)
ls
# Debes ver: sigab-backend/ sigab-frontend/ sigab-bot/ migrations/ docker-compose.yml
```

---

## 2. Validar Docker corriendo

```bash
docker --version
docker compose version
```

Si Docker NO está arrancado (Linux):
```bash
sudo systemctl start docker
```

En Windows (WSL2): abrir **Docker Desktop** desde el menú inicio y esperar 30 s.

---

## 3. Levantar la stack completa (1 solo comando)

```bash
docker compose up -d
```

Esto arranca los 4 contenedores:
- `mysql-sigab` (puerto 3306)
- `sigab-backend` (FastAPI · puerto 8000)
- `sigab-frontend` (React + Vite · puerto 5173)
- `ollama-gemma` (IA local · puerto 11434)

Espera **60-90 segundos** a que todo levante.

---

## 4. Verificación rápida de salud (3 comandos, DEBEN responder)

```bash
curl -s localhost:8000/health
# Respuesta esperada: {"status":"ok"}

curl -s -o /dev/null -w "%{http_code}\n" localhost:5173
# Respuesta esperada: 200

curl -s localhost:11434/api/tags | head -c 200
# Respuesta esperada: JSON con modelo gemma
```

Si alguno falla → ir a la sección 9 (Troubleshooting).

---

## 5. Abrir el navegador

```bash
# Linux:
xdg-open http://localhost:5173 &

# Windows (WSL2):
cmd.exe /c start http://localhost:5173
```

O simplemente: abre **Chrome** y ve a `http://localhost:5173`

---

## 6. Login de demo

```
Matrícula: ADMIN001
Password : ${ADMIN_PASSWORD}
```

Pulsa **Enter** → debes aterrizar en el Dashboard con KPIs.

---

## 7. Pre-demo: cerrar distractores

```bash
# Cerrar Slack, Teams, notificaciones
# Maximizar Chrome (F11 para pantalla completa si quieres impresionar)
# Zoom de Chrome: Ctrl + (hasta 110-125 %) — Carlos debe leer desde enfrente
```

---

## 8. Carga de datos demo (si la BD está vacía)

```bash
docker exec sigab-backend python -m scripts.seed_demo
# Debe cargar: ~25 equipos, 10 órdenes, 5 preventivos, 3 alertas
```

Recarga el Dashboard (Ctrl+Shift+R) y confirma que ves equipos.

---

## 9. Troubleshooting relámpago

| Síntoma | Solución en 10 seg |
|---|---|
| `docker: command not found` | Abrir Docker Desktop |
| Puerto 5173 ocupado | `docker compose down && docker compose up -d` |
| Frontend no carga (blanco) | Esperar 30 s más, refrescar con Ctrl+Shift+R |
| Backend `{"status":"error"}` | `docker compose restart sigab-backend` |
| Ollama lento (>10 s) | Normal en primer query; después responde en 2-3 s |
| MySQL error de login | `docker compose restart mysql-sigab` y esperar 20 s |
| Todo rompe | `docker compose down && docker compose up -d` (reset limpio, 90 s) |

---

## 10. Pantallas clave a mostrar en orden durante la demo

1. **Login** (branding IMSS) — 15 s
2. **Dashboard** (KPIs + mapa + gráficos) — 2 min
3. **Equipos** (lista + QR) — 2 min
4. **Órdenes** (crear + flujo estados + PDF) — 3 min ⭐
5. **Preventivos** (calendario) — 1.5 min
6. **Tecnovigilancia** (NOM-240) — 1.5 min
7. **Copilot IA** (pregunta natural) — 1.5 min ⭐
8. **Trazabilidad** (hash encadenado) — 2 min
9. **Reportes** (generar PDF mensual) — 1 min

**Total demo:** ~15 min. Deja 10 min para el Resumen Ejecutivo impreso + 5-10 min de Q&A.

---

## 11. Comandos de respaldo durante la demo (si falla algo)

```bash
# Ver logs en vivo
docker compose logs -f --tail=50

# Solo backend
docker logs sigab-backend --tail 30

# Reset suave (sin perder datos)
docker compose restart

# Si todo se rompe en medio de la demo
docker compose down && docker compose up -d
# Espera 90 s y recarga el Dashboard
```

---

## 12. Al salir de Quijarro (12:45 h)

```bash
# DEJA la stack corriendo en la Asus (la vas a usar en el trayecto para validar)
# NO apagues Docker
# Carga la Asus al 100 % antes de salir

# Pon el ThinkCentre en la mochila:
# ☐ ThinkCentre M720q
# ☐ Cable corriente
# ☐ Cable HDMI
# ☐ Cable Ethernet
# ☐ Teclado + mouse USB
# ☐ USB booteable Ubuntu (backup)
```

---

**Al momento de abrir el Dashboard:** toma una captura con Snipping Tool (Win+Shift+S). Esa captura la agregamos al Reporte de Auditoría del lunes como evidencia del inicio del piloto.
