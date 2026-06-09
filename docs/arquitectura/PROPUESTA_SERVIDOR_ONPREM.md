# Propuesta — Servidor on-premise SIGAH sobre PC GE (ex-tomógrafo) + IA híbrida con Minimax

> **Tipo:** Propuesta técnica / justificación para aprovechamiento de activo.
> **Fecha:** Junio 2026 · **Estado:** PROPUESTA (pendiente diagnóstico de hardware real, ver §9).
> **HGR No.1 IMSS Tijuana — NOM-016 / NOM-240 / ISO-13485.**

---

## 1. Resumen ejecutivo

Se propone **reutilizar la computadora Intel Xeon de General Electric** (consola/recon del
tomógrafo de 16 cortes dado de baja por incompatibilidad de firmware con el equipo nuevo de
~300 cortes) como **servidor on-premise del ecosistema SIGAH**: base de datos, backend,
frontend, bot de WhatsApp y un motor de IA local para datos sensibles.

El razonamiento pesado, la búsqueda web y los flujos agénticos (incluido el bot **Hermes**)
se delegan a **Minimax en la nube**. Resultado: una **arquitectura híbrida** que aprovecha un
activo ya pagado (CapEx ≈ $0 en cómputo base), mantiene los datos clínicos dentro del hospital
(cumplimiento normativo) y escala la inteligencia sin depender de hardware viejo.

**Inversión incremental sugerida:** una **GPU/acelerador** (≈ $300–900 USD según opción) para
correr LLMs pequeños localmente + el plan de **Minimax Agent ($19/mes)** para la IA frontera.

---

## 2. Justificación: ¿por qué tomar esta máquina?

| Criterio | Argumento |
|----------|-----------|
| **CapEx ≈ 0** | El equipo ya es propiedad del hospital y quedó fuera de uso. Recuperar el activo evita comprar un servidor nuevo ($1,500–4,000 USD). |
| **Grado servidor** | Chasis Xeon con **fuentes redundantes** (visibles en fotos), pensado para operación 24/7 — justo lo que pide el bot/scheduler de SIGAH. |
| **RAM ECC probable** | Las plataformas Xeon usan memoria con corrección de errores → mayor confiabilidad para BD médica. |
| **Soberanía de datos** | On-premise = datos de pacientes, series, contratos y clínicos **no salen del hospital**. Refuerza NOM-016/240 e ISO-13485. |
| **Sostenibilidad** | Da segunda vida a un activo que iría a baja; alineado con buenas prácticas de gestión IMSS. |
| **Control total** | Sin rentas mensuales de servidor; mantenimiento y respaldos bajo control del área de biomédica/IT. |

> ⚠️ **Condición:** la justificación se sostiene **si el BIOS no está bloqueado por GE** y la
> máquina arranca un SO estándar. Esto se valida con `scripts/diagnostico_hardware.sh` (§9).

---

## 3. Plan de servidor + alojamiento de datos

### 3.1 Sistema operativo y plataforma

- **SO:** Ubuntu Server LTS 24.04 (o Debian 12) — estable, soporte largo, drivers NVIDIA.
- **Contenedores:** Docker + Docker Compose. El repo **ya trae `docker-compose.yml`**, por lo
  que el stack se levanta casi sin cambios.

### 3.2 Stack desplegado (todo on-premise)

```
┌──────────────────────── PC GE Xeon (Ubuntu Server) ─────────────────────────┐
│  Docker Compose                                                              │
│   ├─ mysql:8        → BD SIGAB (equipos, órdenes, usuarios, directorio…)     │
│   ├─ sigab-backend  → FastAPI :8000 (router de IA local/nube + auditoría)    │
│   ├─ sigab-frontend → React/Vite tras Nginx :80/:443                         │
│   ├─ sigab-bot      → WhatsApp/Baileys :3000                                 │
│   ├─ ollama         → modelos OSS locales :11434 (datos sensibles)           │
│   └─ caddy/nginx    → reverse proxy + TLS interno                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Alojamiento de datos y respaldos

- **Layout de discos** (confirmar con `lsblk`): disco SO + volumen de datos (MySQL + `static/uploads`
  de evidencias/QRs) + volumen de respaldos.
- **Respaldos automáticos:** `mysqldump` diario + sincronía de `uploads/` a NAS o nube cifrada.
  Retención 30 días. (Hoy existe `auto_push.sh`; se extiende a respaldo de datos.)
- **Dominio interno:** `sigab.hgr1.local` resuelto en la LAN del hospital; sin exposición directa
  a internet (acceso externo solo vía VPN/túnel hacia la nube si se requiere).

### 3.4 Seguridad y operación

- Firewall (ufw), `fail2ban`, usuarios sin root, SSH con llave.
- Auditoría NOM-016 ya implementada (`log_actividad`) — se mantiene como fuente única.
- Monitoreo de salud: `GET /health` del bot + healthchecks de Compose; Hermes vigila caídas.

---

## 4. Ruta de upgrade: GPU / acelerador para LLMs pequeños

**Premisa:** el Xeon corre la app y la BD perfecto, pero para IA local **el cuello de botella es
la GPU (VRAM + arquitectura)**. Las tarjetas originales de reconstrucción del tomógrafo **no
sirven** para LLMs modernos. Se propone **añadir una GPU dedicada**.

### 4.1 Verificaciones físicas previas (antes de comprar)

1. **Slot PCIe x16** libre y con espacio físico (¿caben 2–2.5 slots de alto?).
2. **Watts y conectores de la PSU** (¿tiene PCIe 6/8-pin? ¿capacidad sobrante?).
3. **Enfriamiento/flujo de aire** del chasis.
4. **Largo máximo** de tarjeta que admite el gabinete.

### 4.2 Opciones de GPU (escalonadas)

| Nivel | Tarjeta | VRAM | Consumo | Modelos que corre bien (cuantizados Q4) | Precio aprox. |
|-------|---------|------|---------|------------------------------------------|---------------|
| Entrada | RTX 3060 (usada) | 12 GB | 170 W | Gemma 2 9B, Qwen2.5 7B, Llama 3.1 8B | $250–350 |
| **Recomendado** | RTX 4060 Ti 16 GB | 16 GB | 165 W | Lo anterior + contexto largo / 14B ligeros | $450–550 |
| Pro low-profile | NVIDIA RTX A4000 | 16 GB | 140 W | Igual, **1 slot**, ideal si el chasis es apretado | $600–800 |
| Máximo VRAM | RTX 3090 (usada) | 24 GB | 350 W | Modelos 14B–32B cuantizados | $700–900 |

> Si la PSU/espacio no permiten GPU: **fallback a CPU** (Ollama corre Gemma/Qwen 7-8B en CPU,
> ~3–8 tok/s — usable para tareas livianas mientras se consigue la tarjeta).

### 4.3 Qué corre localmente (datos sensibles)

- Clasificación rápida de reportes WhatsApp, extracción de serie/falla (reactivar `intake_graph`).
- OCR/visión de etiquetas y formatos internos.
- Consultas sobre historial de equipos y datos del paciente que **no deben salir**.

Motor: **Ollama** (ya integrado en `gemma_service.py`) con modelo OSS, p. ej. `gemma2:9b`,
`qwen2.5:7b` o `llama3.1:8b` en cuantización Q4_K_M.

---

## 5. Minimax en la nube (IA frontera + agente)

Para razonamiento pesado, búsqueda web de manuales y orquestación agéntica se usa **Minimax**,
conectado vía OpenClaw y como cerebro de **Hermes**.

### 5.1 Modelos y costos (verificado, jun-2026)

- **Familia M2 (MoE):** la última **M2.7** es un MoE de 230B parámetros con ~10B activos en
  inferencia; contexto ~204K tokens. Pricing API ≈ **$0.279 / 1M tokens entrada** y
  **$1.20 / 1M salida**. La **M2.5** es la más barata (~$0.15 / 1M entrada).
- **Plan de API (pago por uso):** ideal para tráfico variable; se paga por token.
- **Plan Agent (cuota mensual):** **$19/mes** (≈ 10,000 créditos / ~30 tareas) — el que
  mencionaste — o **$69/mes** (~40,000 créditos / ~120 tareas) para uso intensivo. Hay un
  *lightning plan* gratuito para pruebas.

### 5.2 Rol de Minimax en SIGAH

- **SIGAB Bot (WhatsApp):** búsqueda de manuales en internet, razonamiento de diagnóstico
  complejo, redacción de sugerencias de mitigación.
- **Hermes Bot (Telegram):** agente dev/IT — diagnosticar y reparar backend/frontend, deploy.
- **OpenClaw:** punto de conexión del backend al modelo frontera Minimax.

> 📌 **A confirmar al contratar:** endpoint/SDK exacto, formato de API key, y si conviene el
> plan Agent ($19) vs. pago por token según el volumen real de uso.

---

## 6. Arquitectura híbrida y ruteo de datos

El **backend FastAPI actúa de router de IA**: decide local (Ollama) vs. nube (Minimax) según la
**sensibilidad del dato**. Punto único de control para auditoría.

| Tipo de petición | Motor | Por qué |
|------------------|-------|---------|
| Datos de paciente, series, contratos, historial clínico-técnico | **Local OSS (Ollama)** | No deben salir del hospital (NOM/ISO). |
| OCR/visión de formatos internos | **Local OSS** | Documentos internos. |
| Búsqueda web de manuales públicos | **Minimax nube** | Información pública + razonamiento. |
| Diagnóstico complejo / resúmenes ejecutivos largos | **Minimax nube** | Calidad de modelo frontera. |
| Tareas de Hermes (dev/deploy) | **Minimax nube** | Código + razonamiento de ingeniería. |

---

## 7. Presupuesto estimado (incremental)

| Concepto | Costo aprox. |
|----------|--------------|
| Cómputo base (PC GE) | **$0** (activo existente) |
| GPU recomendada (RTX 4060 Ti 16 GB) | $450–550 USD (una vez) |
| Cable/adaptador PSU si hace falta | $0–40 USD |
| Minimax Agent | **$19 USD/mes** (o pago por token) |
| Dominio (si externo) | opcional |
| **Total arranque** | **≈ $470–610 USD + $19/mes** |

Comparado con comprar servidor + GPU nuevos ($2,000–5,000 USD), el ahorro es sustancial.

---

## 8. Plan de migración (paso a paso)

1. **Diagnóstico** (mañana): arrancar la PC, correr `scripts/diagnostico_hardware.sh`,
   capturar specs reales (CPU, RAM, discos, GPU, **estado del BIOS**).
2. **Decisión GPU:** según slots/PSU/espacio, elegir tarjeta de §4.2 (o fallback CPU).
3. **Instalar SO + Docker**, clonar repo, levantar `docker-compose.yml`.
4. **Migrar datos** (BD + uploads) y validar la app on-premise.
5. **Instalar Ollama + modelo OSS**; reconectar `gemma_service.py`.
6. **Contratar Minimax** y conectar OpenClaw + Hermes.
7. **Implementar ruteo de IA** local/nube en el backend (§6).
8. **Respaldo automático** + monitoreo + endurecimiento de seguridad.

---

## 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| BIOS/firmware GE bloqueado, no arranca SO | Media | Diagnóstico §1; si bloqueado, evaluar reemplazo de disco/CMOS o usar como solo-BD. |
| GPU no entra (espacio/PSU) | Media | Tarjeta single-slot low-power (A4000) o fallback CPU. |
| "500 TB" no es real | Alta | Verificar con `lsblk`; storage no es el factor crítico. |
| Dependencia de internet para Minimax | Baja | Lo crítico (app/BD/bot) es local; Minimax solo para razonamiento extra. |
| Datos sensibles a la nube por error | Media | Router de §6 + auditoría `log_actividad`. |

---

## Fuentes (Minimax, jun-2026)

- [MiniMax API Docs — Product Pricing](https://platform.minimax.io/docs/pricing/overview)
- [MiniMax M2 & Agent — anuncio oficial](https://www.minimax.io/news/minimax-m2)
- [MiniMax M2.7 — pricing & benchmarks (OpenRouter)](https://openrouter.ai/minimax/minimax-m2.7)
- [MiniMax M2 API Pricing 2026 (pricepertoken)](https://pricepertoken.com/pricing-page/model/minimax-minimax-m2)

_Documento vivo. Se actualiza con los specs reales tras el diagnóstico de hardware._
