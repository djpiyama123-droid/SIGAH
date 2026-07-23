# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

**Sistema Integral de Gestión de Activos Biomédicos (SIGAB) V2.0** — plataforma 100% On-Premise para el Hospital General Regional No. 1 IMSS Tijuana. Cumple NOM-016-SSA3-2012 (trazabilidad/auditoría), NOM-240-SSA1-2012 (tecnovigilancia) e ISO 13485. Nota: el repositorio se llama `SIGAH` pero el proyecto es SIGAB.

Todo el código, comentarios, UI y mensajes están en **español mexicano**.

## Comandos

### Backend (FastAPI + Python 3.12, puerto 8000)
```bash
cd sigab-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Tests (solo backend; no hay tests de frontend)
```bash
cd sigab-backend
pytest                              # toda la suite (tests/)
pytest tests/test_iso8601.py        # un archivo
pytest tests/test_permissions.py::test_nombre   # un test
```
Los tests corren **sin MySQL ni Ollama**: `tests/conftest.py` mockea `aiomysql` y `config` a nivel de sesión antes de importar los módulos bajo test. No hay linter configurado.

### Frontend (React + Vite + Tailwind 3, puerto 5173)
```bash
cd sigab-frontend
npm install
npm run dev        # dev server con proxy /api → localhost:8000
npm run build      # build de producción
```

### Base de datos (MySQL 8.0)
```bash
docker compose up -d mysql                               # opción Docker
mysql -u root -p < database/sigab_schema_fresh.sql       # esquema limpio
mysql -u root -p sigab_prod < database/seed_data.sql     # datos demo
```
Migraciones incrementales en `database/migrations/` (004-010), SQL plano aplicado a mano. Existe `alembic/` en el backend pero el flujo real es SQL directo.

### Variables de entorno clave (prefijo `SIGAB_`, ver `sigab-backend/config.py`)
- `SIGAB_DB_HOST/PORT/USER/PASS/NAME` — conexión MySQL
- `SIGAB_JWT_SECRET` — obligatorio en producción
- `SIGAB_DISABLE_COPILOT=1` — arranca sin el router de IA (útil si no hay Ollama)
- `SIGAB_SSL_DISABLED=true` — sin SSL a MySQL (default en desarrollo)
- `SIGAB_OLLAMA_HOST` (`:11434`), `SIGAB_GEMINI_API_KEY`, `SIGAB_MINIMAX_API_KEY`

## Arquitectura

### Backend — `sigab-backend/`
- `main.py` registra ~20 routers bajo `/api/<modulo>` (equipos, ordenes, trazabilidad, preventivos, dashboard, tecnovigilancia, auditoria, checklists, almacen, metrologia, capacitaciones, copilot, ocr, events, casillas, etc.). Health check en `/health`.
- **Dos patrones de acceso a datos coexisten**:
  1. Legacy: aiomysql crudo vía `config.get_db` (dependency que entrega la conexión) — la mayoría de las rutas.
  2. Moderno: SQLModel async (`mysql+asyncmy`) vía `database.get_async_session` — módulos nuevos (auditoría, checklists, almacén, metrología, capacitaciones).
  Al tocar una ruta, seguir el patrón que ya usa ese archivo.
- `services/` contiene la lógica de negocio: PDF/Excel (`pdf_service`, `reporte_*`), QR (`qr_service`, segno nivel H), SSE (`sse_service`, `event_broadcaster`), IA (`gemma_service` — Ollama primario con fallback automático a MiniMax cloud tras probe de 3 s), OCR (`ocr_service` — Gemini 2.5 Flash), auditoría (`audit_service`).
- **Auditoría NOM-016**: `AuditService.log_event()` escribe en un log con **hashing SHA-256 encadenado** (cada registro incluye el hash del anterior). Toda mutación relevante de negocio debe registrarse ahí.
- **Máquinas de estado**: transiciones válidas se declaran en un dict `TRANSICIONES` dentro de la ruta (ver `routes/tecnovigilancia.py`) y se validan antes de cambiar estado. Es el patrón establecido para cualquier flujo con estados.
- Tiempo real: Server-Sent Events por `routes/events.py` (`/api/v1/events`), consumidos por el hook `useSSE` del frontend (alimenta el TV Dashboard).
- Auth: JWT (access 60 min + refresh 7 días) en `auth/`; folios con formato ISO 8601 `SIGAB-HGR1-YYYYMMDD-HHMM-NNNN`.

### Frontend — `sigab-frontend/`
- **Todo el tráfico HTTP pasa por `src/api/sigab.js`**: cliente Axios único con baseURL `/api` (proxy de Vite), interceptores que inyectan el JWT desde `localStorage`, devuelven `response.data` directo (no usar `.data.data`) y ante 401 limpian sesión y redirigen a `/login`. Endpoints nuevos se agregan como métodos del objeto `api`, no con axios/fetch suelto.
- Páginas en `src/pages/` (una por módulo: Dashboard, Equipos, Ordenes, Preventivos, Trazabilidad, Tecnovigilancia, Copilot, Almacen, Metrologia, Capacitaciones, Auditoria, Checklists, QRBatch, QRScanner, TVDashboard, Analitica…), rutas en `App.jsx`, sesión en `context/AuthContext.jsx`, permisos con `hooks/usePermissions.js`.
- UI: Tailwind utility classes, Headless UI, Tremor/Recharts para gráficas, `react-hot-toast` para notificaciones.

### Otros componentes
- `sigab-bot/` — bot de WhatsApp en Node.js (whatsapp-web.js): `index.js`, `commands.js`, `scheduler.js`.
- `.claude/skills/ui-ux-pro-max` — invocar esta skill al trabajar en páginas/componentes del frontend (rediseños, accesibilidad, nuevos módulos con UI). Paleta: azul IMSS `#006CB7`, emerald biomédico, alertas amber/red; tipografía Inter + Source Sans Pro.
- CI: `.github/workflows/deploy.yml` despliega por SSH al VPS en cada push a `main`/`master` (rebuild de Docker Compose + frontend). Un push a main **despliega a producción**.

## Principios de IA Agéntica (Copilot, OCR y automatizaciones)

SIGAB corre IA en producción hospitalaria, no en demo. Al trabajar en `gemma_service`, `ocr_service`, `intake_graph`, `routes/copilot.py` o cualquier automatización nueva con agentes, aplicar estos conceptos anclados al código existente:

1. **Harness engineering** — el entorno del agente es el edge on-premise: Ollama en `:11434` dentro del ThinkCentre, sin salida de datos del hospital salvo los fallbacks cloud explícitos (MiniMax, Gemini). No agregar llamadas externas fuera de esa superficie.
2. **Loop engineering** — toda llamada a IA lleva condición de corte: probe al edge con `SIGAB_AI_PROBE_TIMEOUT` (3 s) antes de caer a MiniMax. Nada de reintentos indefinidos contra Ollama.
3. **Context engineering** — al Copilot se le pasa solo el contexto del equipo/orden en cuestión, no volcados completos de la base; mantener los prompts de `gemma_service` acotados.
4. **Tool design** — el sistema es tan seguro como el peor edge case de sus herramientas: el OCR valida con umbrales (`SIGAB_OCR_CONFIDENCE` 0.85, mínimo de palabras) antes de aceptar una extracción.
5. **Memory architecture** — la IA no persiste memoria propia: todo lo que deba recordarse se escribe en MySQL vía los flujos normales (órdenes, trazabilidad), auditado como cualquier mutación.
6. **Orchestration patterns** — patrón de agente único con fallback en cascada (Ollama → MiniMax); si se agregan subagentes o pipelines (p. ej. `intake_graph`), documentar sus modos de fallo propios.
7. **Guardrails & permissions** — la IA nunca muta estado clínico directamente: las transiciones pasan por los dicts `TRANSICIONES` y los permisos JWT igual que un usuario; `SIGAB_DISABLE_COPILOT=1` es el kill-switch del módulo completo.
8. **Evals** — la salida de IA no se prueba como función pura: los tests (`test_ai_provider.py`) validan la lógica de selección de proveedor y fallback con mocks; extracciones OCR se evalúan contra el umbral de confianza, no con asserts exactos.
9. **Human-in-the-loop** — las decisiones clínicas y de estado de equipo son siempre humanas: el Copilot sugiere diagnósticos y el OCR pre-llena formularios, pero un técnico confirma antes de guardar. No automatizar ese paso.
10. **Observability & tracing** — toda acción derivada de IA que mute datos queda en el audit trail SHA-256 (`AuditService`), con folio ISO 8601; ante un fallo se inspecciona esa cadena, no se adivina.

La madurez está en los puntos 7-10: cualquier cambio a los servicios de IA debe explicar su impacto en guardrails, validación, confirmación humana y auditoría.

## Convenciones

- Textos de UI y mensajes de error en español mexicano; notificaciones con `toast.success/error/loading`.
- Colores de estado de equipo: `emerald` = operativo, `amber` = mantenimiento, `red` = fuera_servicio, `slate` = baja (constantes en `src/utils/constants.js`).
- Estados de negocio: validar con dict `TRANSICIONES` en el backend antes de mutar.
- Mutaciones auditables: registrar vía `AuditService` (cadena SHA-256, NOM-016).
- Fechas/folios en formato ISO 8601.
