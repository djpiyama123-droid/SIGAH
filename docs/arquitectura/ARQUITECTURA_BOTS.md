# Arquitectura de Bots SIGAH — SIGAB (WhatsApp) + Hermes (Telegram)

> **Estado:** PLAN / DISEÑO. Documento de referencia previo a implementación.
> **Bloqueador activo:** la implementación de código espera los specs definitivos
> de la PC on-premise (ex-topógrafo) y la confirmación del setup en la nube Minimax.
> **Hospital General Regional No.1 IMSS Tijuana — NOM-016 / NOM-240 / ISO-13485**

---

## 0. TL;DR

Dos bots, dos propósitos, dos canales:

| Bot | Canal | Usuarios | Propósito | Modelo IA |
|-----|-------|----------|-----------|-----------|
| **SIGAB Bot** | WhatsApp (Baileys) | Personal hospitalario (médicos, técnicos, encargados de área, jefes de conservación) | Alta/baja de reportes, consulta de equipos por QR, asistencia agéntica (manuales, historial, búsqueda web) | Frontera (Minimax) en nube + OSS local para datos sensibles |
| **Hermes Bot** | Telegram | Solo superadmins: **Gustavo** y **Carlos** | Ing. de IT IA: reparar backend/frontend ante bugs/caídas, deploy y operación de SIGAH | Frontera (Minimax) en nube |

Infraestructura **híbrida**:
- **Nube (Minimax, plan agéntico):** aloja dominio + repo SIGAH + ecosistema; OpenClaw conectado a modelo frontera Minimax. Hermes corre aquí.
- **Local (ex-topógrafo, on-premise en hospital):** corre modelos **open-source** sobre los datos sensibles/clínicos que no deben salir del hospital (cumplimiento NOM/ISO + protección de datos del paciente y del activo).

---

## 1. Estado actual del repo (línea base)

### 1.1 sigab-bot/ (Node.js, ya existe)

```
WhatsApp (grupo "Residentes de biomedica 2025")
        │
        ▼
┌─────────────────────────┐    HTTP     ┌──────────────────────────┐
│  sigab-bot (Node.js)    │ ◄────────► │  FastAPI backend :8000   │
│  Baileys + Express :3000│            │  /api/openclaw/*         │
│  - index.js  (socket WA)│            │  /api/v1/events/whatsapp │
│  - commands.js (router) │            │  /api/copilot/*          │
│  - scheduler.js (cron)  │            └──────────────────────────┘
└─────────────────────────┘                        │
        ▲                                           ▼
        │ POST /send                         ┌───────────────┐
        └────────────────────────────────────│ Gemma/Ollama  │
                                              │ :11434 (local)│
                                              └───────────────┘
```

- **`index.js`** — socket Baileys. Reenvía todo mensaje (texto + audio en base64) al
  webhook `/api/v1/events/whatsapp/webhook`. Expone `POST /send` para que el backend
  mande mensajes/documentos, y `GET /health`.
- **`commands.js`** — router de comandos: `/equipo`, `/ticket`, `/estado`, `/traslado`,
  `/alertas`, `/reporte`, `/pdf`, `/email`, `/proveedor`, `/casillas` (OCR de formato
  físico desde foto). Texto libre ≥3 palabras → `cmdAI` → Gemma.
- **`scheduler.js`** — cron (timezone America/Tijuana): reporte matutino 07:00,
  preventivos 13:00, cierre 18:00, alertas críticas cada 15 min, metrología los lunes.

### 1.2 Backend relevante

- **`routes/openclaw.py`** — endpoints sin JWT pensados para el bot: `/ticket`,
  `/buscar-equipo`, `/estado-equipo/{serie}`, `/traslado`, `/alertas-pendientes`,
  `/reporte-diario`, `/cambiar-estado`, `/equipo-pdf/{serie}`, `/enviar-reporte`,
  `/chat`, `/check-calibraciones`.
- **`routes/events.py`** — webhook WhatsApp; `process_whatsapp_ai` invoca `intake_graph`.
- **`services/intake_graph.py`** — **STUB** (LangGraph deshabilitado). El intake real
  por NLP aún no está activo.
- **`services/gemma_service.py`** — interfaz Ollama/Gemma: `chat_stream`, `analizar_no_stream`,
  `analizar_imagen` (visión), prompts especializados (diagnóstico, causa raíz NOM-240,
  resumen diario, visión de etiquetas, predicción de insumos).
- **`services/reporte_excel_service.py`** — generación XLSX con `openpyxl` (reutilizable).
- **`models/usuario.py`** — tabla `usuarios`: `nombre, matricula, rol, telefono, whatsapp,
  email, ...`. Roles: `biomedico, supervisor, jefe_servicio, jefe_conservacion,
  jefe_biomedica, almacen, admin`.

### 1.3 Brechas detectadas (lo que NO existe hoy)

1. **Hermes no existe.** Cero referencias a Telegram en el repo. Se crea desde cero.
2. **El bot no identifica al remitente.** Solo guarda `pushName` + JID. No hay mapeo
   número → persona real → de ahí el directorio de contactos.
3. **No hay doctores en el modelo de datos.** `usuarios` cubre personal biomédico, no
   médicos tratantes. Falta una fuente de contactos de doctores.
4. **El bot no es agéntico.** No busca en internet, no lee manuales, no edita archivos.
   Solo comandos fijos + chat Gemma con contexto de BD.
5. **`intake_graph` es un stub** — el parsing inteligente de reportes de lenguaje natural
   no está operativo.

---

## 2. Arquitectura objetivo (híbrida nube + local)

```
                          ┌────────────────────────────────────────────┐
                          │                NUBE (Minimax)               │
                          │  - Dominio SIGAH + repo + ecosistema        │
                          │  - OpenClaw  ──►  Modelo frontera Minimax   │
                          │  - Hermes Bot (Telegram, dev/IT)            │
                          └───────────────┬────────────────────────────┘
                                          │ (datos NO sensibles, orquestación,
                                          │  razonamiento pesado, deploy)
                                          ▼
   WhatsApp ─► SIGAB Bot ─► Backend FastAPI (router de IA) ──┐
   (personal     (Baileys)        :8000                       │
    hospital)                                                 ▼
                                          ┌────────────────────────────────────┐
                                          │      LOCAL on-premise (ex-topógrafo)│
                                          │  - Modelos OSS (Ollama/vLLM)        │
                                          │  - Datos sensibles/clínicos         │
                                          │  - MySQL SIGAB, uploads, manuales   │
                                          └────────────────────────────────────┘
```

**Criterio de ruteo de IA (a definir con specs finales):**
- **Local OSS** → todo lo que toque datos del paciente, números de serie, contratos,
  historial clínico-técnico del equipo, OCR de formatos internos.
- **Nube Minimax** → razonamiento pesado, búsqueda web de manuales públicos,
  orquestación agéntica, tareas de Hermes (dev/deploy).
- El backend FastAPI actúa de **router**: decide local vs. nube según el tipo de dato
  y la sensibilidad. Punto único de control para auditoría NOM-016 (`log_actividad`).

> ⏳ **Pendiente de specs:** confirmar VRAM/GPU del ex-topógrafo para elegir el modelo OSS
> (p. ej. Llama 3.x / Qwen / Gemma de mayor tamaño vía vLLM) y dimensionar el cache.

---

## 3. Entregable 1 — Directorio de contactos (XLSX, plantilla + import)

**Decisión confirmada:** esquema + plantilla XLSX vacía + endpoint de importación.
Los datos reales se cargan por Excel; no se hardcodean.

### 3.1 Modelo de datos (nueva tabla `directorio_contactos`)

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | INT PK | autoincrement |
| `nombre` | VARCHAR | obligatorio |
| `rol` | ENUM | `tecnico`, `doctor`, `encargado_area`, `jefe_conservacion` |
| `telefono` | VARCHAR | normalizado E.164 (+52...) |
| `whatsapp` | VARCHAR | JID o número; clave de cruce con el bot |
| `area` | VARCHAR | servicio/área hospitalaria |
| `especialidad` | VARCHAR | opcional (doctores) |
| `activo` | BOOL | default TRUE |

### 3.2 Componentes a construir

- `models/contacto.py` — modelo SQLModel.
- `migrations/0XX_directorio_contactos.sql` — DDL (sigue numeración existente).
- `services/directorio_excel_service.py` — genera:
  - **Plantilla vacía** descargable (hojas "Técnicos" y "Doctores" con encabezados +
    validaciones de columna).
  - **Export** del directorio actual a XLSX (lo que "se sirve a SIGAB/SIGAP" como contexto).
- `routes/directorio.py`:
  - `GET /api/directorio/plantilla.xlsx` — descarga plantilla.
  - `POST /api/directorio/importar` — sube XLSX lleno → upsert por teléfono.
  - `GET /api/directorio.xlsx` — export del directorio vigente.
  - `GET /api/directorio/lookup?numero=...` — **cruce número → persona** (lo usa el bot).

### 3.3 Integración con el bot

Al recibir un mensaje, el bot normaliza el número y llama a `lookup`. Con eso:
- Sabe **quién** reporta y **desde qué número** → se inyecta en `tecnico_nombre` del ticket
  y en el contexto de Gemma/Minimax ("Reporte del Dr. X, área Y").
- Si el número no está en el directorio → flujo de registro / aviso al jefe de conservación.

---

## 4. Entregable 2 — Bot SIGAB agéntico (WhatsApp)

**Audiencia:** personal hospitalario (médicos, técnicos, encargados de área, jefes de
conservación). **Canal único:** WhatsApp.

### 4.1 Capacidades agénticas (tools)

1. **Buscar equipos en BD** (ya existe parcialmente: `/buscar-equipo`, `/estado-equipo`).
2. **Leer historial del equipo** y proponerlo como sugerencia de reparación/mitigación.
3. **Buscar manuales / info del equipo en internet** (nube Minimax con búsqueda web).
4. **Leer/generar/editar archivos** (manuales, reportes, evidencias).
5. **Generar reportes** (PDF/Excel — infra ya existe).
6. **Comunicar por WhatsApp** alta/baja de reportes vía texto, audio (STT/Whisper) e imagen.

### 4.2 Flujo QR → consulta

```
Médico escanea QR del equipo ─► abre chat WhatsApp con serie pre-cargada
   ─► pregunta ("¿qué significa esta alarma?", "¿cómo reinicio el monitor?")
   ─► bot trae: contexto del equipo + historial + manual + sugerencia IA
   ─► responde con mitigación / pasos / cuándo escalar a biomédico
```

### 4.3 Reescritura de `intake_graph`

Reactivar el grafo de intake (hoy stub) para parsear reportes en lenguaje natural:
extraer serie/NII, falla y prioridad; crear OS; confirmar al usuario. Ruteo de modelo
según sensibilidad (sección 2).

---

## 5. Entregable 3 — Hermes Bot (Telegram, dev/IT) — nuevo

**Audiencia:** solo superadmins **Gustavo** y **Carlos** (allowlist de Telegram user IDs).
**Canal:** Telegram. **Ubicación de ejecución:** nube Minimax.

### 5.1 Estructura propuesta

```
hermes-bot/
  index.js (o main.py)   # bot Telegram (grammY / python-telegram-bot)
  auth.js                # allowlist superadmins (IDs de Gustavo y Carlos)
  tools/                 # acciones de IT/dev (read logs, restart, deploy, diff)
  config.*               # tokens, endpoints, modelo Minimax
  README.md
```

### 5.2 Rol y capacidades

- Diagnóstico y **reparación de backend/frontend** ante bug o caída.
- **Deploy** de SIGAH (reusa `deploy_to_vps.sh`, `vps_setup.sh`, `docker-compose.yml`).
- Operación: estado de servicios, logs, reinicio de contenedores, health checks.
- Conectado al modelo frontera Minimax para razonamiento de ingeniería.

### 5.3 Seguridad (crítico)

- Allowlist estricta por Telegram user ID. Cualquier otro ID → ignorado y logueado.
- Acciones destructivas (deploy, restart, migraciones) → confirmación explícita.
- Auditoría completa en `log_actividad`.

---

## 6. Plan de implementación por fases

| Fase | Entregable | Depende de |
|------|-----------|------------|
| **0** | Este documento (plan) | — ✅ |
| **1** | Specs de hardware on-premise + decisión modelo OSS local | **Datos del usuario (pendiente)** |
| **2** | Setup nube Minimax (dominio, repo, OpenClaw → frontera) | Fase 1 |
| **3** | Directorio de contactos (tabla + plantilla XLSX + import + lookup) | Fase 2 |
| **4** | Cruce número→persona en SIGAB Bot | Fase 3 |
| **5** | Capacidades agénticas SIGAB Bot (tools, QR, intake real) | Fases 2–4 |
| **6** | Hermes Bot Telegram (esqueleto → IT/deploy) | Fase 2 |

---

## 7. Análisis del hardware on-premise candidato (ex-tomógrafo GE)

**Identificación (por fotos):** computadora de **consola/reconstrucción de un tomógrafo
GE de 16 cortes**. El panel trasero lo confirma: puertos `GSCB / TGP / HSP / HUB`,
`GSCB X-ray Abort`, `Scan Monitor (DP)`, `Option Fibre RX`, y USB asignados a
`Trackball / BarCodeReader / Service key`. Chasis Xeon con fuentes redundantes y ruedas.
Dos slots rotulados `GPU` = tarjetas de **reconstrucción de imagen**, no de cómputo IA.

### 7.1 Advertencias (verificar antes de comprometer arquitectura)

| Punto | Riesgo / realidad |
|-------|-------------------|
| "500 TB" | Improbable en consola de TC 16 cortes (típico 0.5–4 TB). Verificar con `lsblk`. Almacenamiento ≠ cómputo IA. |
| GPUs originales | Probables NVIDIA recon ~2012-2015 (VRAM 5-6 GB, sin bf16, sin soporte CUDA moderno) → **inservibles para LLMs**. |
| BIOS/firmware | Posible BIOS custom GE / secure boot / disco con SO propietario → puede no arrancar Linux estándar. |
| Factor decisivo IA | **VRAM y arquitectura de GPU**, no el Xeon. |

### 7.2 Rol recomendado

- ✅ **Servidor on-premise de SIGAH** (MySQL + FastAPI + bot WhatsApp + app). El Xeon y
  las fuentes redundantes sirven. Datos sensibles no salen del hospital (NOM-016/240).
- ⚠️ **IA local OSS:** solo rinde con **GPU moderna añadida** (≥16-24 GB VRAM, p. ej.
  RTX 3090/4090) si chasis/PCIe/PSU lo permiten. Sin ella → solo modelos chicos
  (Gemma/Qwen 7-8B cuantizados) en CPU, lento pero usable para tareas livianas.
- ☁️ **Razonamiento pesado + Hermes → Minimax nube** (sin cambios al plan).

### 7.3 Verificación pendiente

Correr `scripts/diagnostico_hardware.sh` en la máquina (tras arrancar Linux) para obtener
specs reales: CPU/flags AVX, RAM, discos, **GPU (modelo + VRAM + compute_cap)**, BIOS.
La decisión final (servidor de app vs. servidor de IA local) se toma con esa salida.

---

## 8. Bloqueadores / pendientes antes de codificar

1. ⏳ **Specs de la PC on-premise (ex-topógrafo):** CPU/Xeon, RAM, GPU/VRAM,
   almacenamiento (~500 TB), aceleración IA. Define el modelo OSS local.
2. ⏳ **Confirmación setup Minimax:** plan agéntico, límites de request, endpoint/SDK,
   modelo frontera a usar, cómo se conecta OpenClaw.
3. ⏳ **Política de datos:** qué datos NO pueden salir a la nube (definir matriz de
   sensibilidad para el ruteo local vs. nube).
4. ⏳ **Telegram:** token del bot Hermes + user IDs de Gustavo y Carlos.
5. ⏳ **Datos del directorio:** se cargarán por la plantilla XLSX una vez construida.

---

_Documento vivo. Se actualiza al recibir specs de hardware y confirmar el setup en la nube._
