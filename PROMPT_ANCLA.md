# PROMPT ANCLA — Estado del GOAL Industria 4.0 SIGAB

> Archivo de continuidad. Cada corrida automatizada lo actualiza con el avance realizado.

---

## GOAL
Profundizar ficha técnica + justificación de 4 componentes I4.0 y operacionalizarlos en SIGAB:

| # | Componente | Justificación | Operacionalizado en código |
|---|-----------|:-------------:|:--------------------------:|
| 1 | Escáner MIRACO Plus | ✅ WS-1 doc | ⬜ WS-2 pendiente |
| 2 | Pistola grabadora láser (UDI) | ✅ WS-1 doc | ⬜ WS-2 pendiente |
| 3 | Nodo edge IA (Ollama + fallback) | ✅ WS-1 doc | ✅ WS-3 corrida 1 |
| 4 | Dominio .mx + API IA bots | ✅ WS-1 doc | ⬜ WS-4 pendiente |

---

## Bitácora de Sesiones

### Sesión 1 — 2026-06-04
- **Rama:** `auto/avance-2026-06-04-0001`
- **WS avanzado:** WS-3 (integración nodo edge IA)
- **Archivos modificados:**
  - `sigab-backend/config.py` — vars `MINIMAX_API_KEY`, `MINIMAX_API_HOST`, `MINIMAX_MODEL`, `AI_PROVIDER`
  - `sigab-backend/services/gemma_service.py` — funciones `verificar_edge()`, `_cloud_chat_text()`, `_cloud_chat_stream()`, fallback automático en `chat_stream()` y `analizar_no_stream()`
  - `sigab-backend/routes/copilot.py` — endpoint `GET /edge-status`
- **Archivos creados:**
  - `JUSTIFICACION_INVERSION.md` — ROI/CAPEX-OPEX de 4 componentes I4.0
  - `START_HERE_NUEVA_SESION.md` — guía de orientación para sesiones futuras
  - `PROMPT_ANCLA.md` — este archivo
- **Tests:** Sintaxis Python OK (ast.parse). No hay pytest suite todavía.
- **Decisiones pendientes para el humano:**
  - ¿Qué API key de MiniMax usar? Configurar `SIGAB_MINIMAX_API_KEY` en `.env` del VPS.
  - ¿Activar `AI_PROVIDER=auto` o `local` en producción? Default es `auto`.
  - Validar que `GET /api/copilot/edge-status` responde correctamente en VPS.

---

## Próximos Pasos Priorizados

### WS-2 — Trazabilidad activos UDI + escaneo 3D (desbloqueado)
1. Migración SQL:
   ```sql
   ALTER TABLE equipos ADD COLUMN udi_grabado BOOLEAN DEFAULT FALSE;
   ALTER TABLE equipos ADD COLUMN udi_codigo VARCHAR(100);
   ALTER TABLE equipos ADD COLUMN udi_fecha_grabado DATE;
   ALTER TABLE metrologia_calibracion ADD COLUMN scan_3d_url VARCHAR(255);
   ALTER TABLE metrologia_calibracion ADD COLUMN scan_fecha DATETIME;
   ```
2. Endpoint `POST /equipos/{id}/udi` — registrar marcado UDI
3. Endpoint `POST /metrologia/{id}/scan3d` — registrar escaneo 3D
4. Frontend: badge "UDI Grabado" en `Equipos.jsx`
5. Frontend: campo "Escaneo 3D" en `Metrologia.jsx`

### WS-4 — Panel consumo tokens IA (después de WS-2)
1. Tabla `ia_token_log (id, fecha, endpoint, tokens_in, tokens_out, provider, costo_usd)`
2. Middleware en `gemma_service.py` que registra tokens por llamada
3. Widget en `Dashboard.jsx`: tokens/día, costo estimado MXN, alerta de umbral

### WS-5 — Calidad (continuo)
1. Pytest para `/edge-status`: verificar estructura de respuesta
2. Pytest para fallback: mock Ollama down → verificar que responde con `proveedor_activo: cloud`
3. Flake8 sobre archivos modificados

---

## Contexto Técnico Crítico

- **Servidor edge:** Lenovo ThinkCentre M720q, i5-8500T, 16GB, 512GB SSD, WSL2 Ubuntu 24.04
- **Ollama:** `http://localhost:11434` (proceso en edge)
- **Modelo edge:** `gemma3:4b` (default; configurable vía `SIGAB_GEMMA_MODEL`)
- **Cloud fallback:** MiniMax `MiniMax-Text-01` (requiere `SIGAB_MINIMAX_API_KEY`)
- **VPS:** `sigab-vps` / `129.121.100.147` — solo el humano despliega ahí
- **DB:** MySQL 8.0, `sigab_prod`, puerto 3306
- **Frontend:** React 19 + Vite, puerto 5173
- **Backend:** FastAPI + uvicorn, puerto 8000
