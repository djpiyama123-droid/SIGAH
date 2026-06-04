# Justificación de Inversión — Industria 4.0 SIGAB
## 4 Componentes Tecnológicos Avanzados | HGR No. 1 IMSS Tijuana

**Versión:** 1.0  
**Fecha:** Junio 2026  
**Propósito:** Argumentar la adquisición de 4 activos Industria 4.0 con ROI, CAPEX/OPEX y beneficio técnico-normativo medibles.

---

## Resumen Ejecutivo

| # | Componente | CAPEX (MXN) | OPEX Anual (MXN) | Beneficio principal | ROI estimado |
|---|-----------|:-----------:|:----------------:|---------------------|:------------:|
| 1 | Escáner metrología MIRACO Plus | $45,000 | $0 | Calibración 3D sin papel; auditoría NOM-016 | 18 meses |
| 2 | Pistola grabadora láser (UDI) | $12,000 | $1,200 | Marcado permanente UDI/GS1; elimina etiquetas caducas | 6 meses |
| 3 | Servidor nodo edge IA (Ollama) | $13,500 | $3,600 | IA local sin latencia cloud; datos 100% on-premise | 12 meses |
| 4 | Dominio .mx + API IA bots SIGAH | $4,800/año | $4,800 | Presencia web SIGAB + bots operativos 24/7 | 8 meses |
| | **TOTAL** | **$75,300** | **$9,600** | | |

---

## 1. Escáner de Metrología MIRACO Plus (SHINING3D)

### Descripción técnica
Escáner 3D de mano con precisión volumétrica de hasta **0.05 mm**, resolución de punto de **0.05 mm**, y rango de operación sin marcadores. Captura geometría completa de equipos biomédicos en tiempo real.

### Funciones en SIGAB
| Función | Módulo SIGAB | Impacto |
|---------|-------------|---------|
| Escaneo dimensional de equipos en calibración | `Metrología` | Registro 3D como evidencia de certificación |
| Verificación de integridad física (daños, deformaciones) | `Órdenes de Servicio` | Diagnóstico objetivo previo a correctivo |
| Trazabilidad de condición física por año | `Trazabilidad NOM-016` | Historial auditable de estado dimensional |
| Foto-registro en expediente digital del activo | `Equipos` | Reemplaza inspección visual subjetiva |

### Justificación técnico-económica
- **Problema actual:** Los informes de calibración son manuales (papel), sin evidencia fotométrica objetiva. Una auditoría NOM-016 exige trazabilidad de condición física del equipo.
- **Con MIRACO Plus:** Cada calibración genera un archivo 3D `.stl` firmado y almacenado en el expediente del activo en SIGAB, con hash SHA-256 para no repudio.
- **CAPEX:** ~$45,000 MXN (cotización SHINING3D México, Q2-2026).
- **Ahorro operativo:** Elimina contratación de empresa externa de metrología dimensional (~$8,000/evento × 4 eventos/año = $32,000/año). ROI = 45,000/32,000 ≈ **17 meses**.
- **Compliance:** Cubre evidencia de condición física requerida por NOM-016-SSA3 Art. 34 y bases de licitación IMSS para certificación de equipos de diagnóstico.

### Operacionalización en SIGAB (pendiente de implementar)
```
Módulo: Metrología
  - Campo nuevo: scan_3d_url  (ruta al archivo .stl en /static/uploads/3d/)
  - Campo nuevo: scan_fecha   (fecha de captura)
  - Campo nuevo: scan_tecnico (usuario que capturó)
Módulo: Equipos
  - Badge "Escaneado 3D" en ficha del equipo
  - Botón "Ver modelo 3D" (viewer Three.js)
```
> **WS-2 siguiente paso:** Migración SQL + endpoint `POST /metrologia/{id}/scan3d` + badge en Equipos.jsx.

---

## 2. Pistola Grabadora Láser (Marcado UDI / Trazabilidad de Activos)

### Descripción técnica
Grabadora láser portátil de fibra (20W), capaz de grabar acero, aluminio y policarbonato con código Data Matrix (UDI estándar GS1) a velocidad de 300 mm/s. Resistente a esterilización en autoclave.

### Funciones en SIGAB
| Función | Módulo SIGAB | Impacto |
|---------|-------------|---------|
| Grabado permanente UDI/GS1 en carcasa | `QR Batch` | Etiqueta indestructible, auditoría COFEPRIS |
| Re-marcado de equipos sin etiqueta original | `Equipos` | Recupera activos "grises" sin identificación |
| Marcado de refacciones críticas (bombas, módulos) | `Almacén` | Trazabilidad de componente individual |

### Justificación técnico-económica
- **Problema actual:** Las etiquetas QR impresas en papel/vinilo se dañan con desinfectantes hospitalarios. Frecuencia de re-etiquetado: ~200 equipos/año a $25/etiqueta + mano de obra = ~$8,000/año. Además, NOM-240 exige identificación permanente del dispositivo para reporte de eventos adversos.
- **Con pistola láser:** Marcado único, permanente, certificable. Costo por grabado = $0.20 energía eléctrica. Elimina el 100% del costo de re-etiquetado.
- **CAPEX:** ~$12,000 MXN (grabadora láser fibra 20W, disponible en Alibaba/Amazon MX).
- **Ahorro operativo:** $8,000/año en etiquetado. ROI = 12,000/8,000 ≈ **18 meses**. Considerando eliminación de mano de obra: **6 meses**.
- **Compliance:** UDI (Unique Device Identifier) es requisito emergente de COFEPRIS alineado con FDA 21 CFR Part 830 para dispositivos médicos importados y fabricados en México.

### Operacionalización en SIGAB (pendiente de implementar)
```
Módulo: Equipos
  - Campo nuevo: udi_grabado      (boolean)
  - Campo nuevo: udi_codigo       (string Data Matrix GS1)
  - Campo nuevo: udi_fecha_grabado
  - Endpoint: POST /equipos/{id}/udi  { codigo, fecha }
  - Badge "UDI Grabado" en ficha + QR del UDI
Módulo: QR Batch
  - Opción "Imprimir para grabado" → genera plantilla Data Matrix para laser
```
> **WS-2 siguiente paso:** Schema SQL + endpoint UDI + badge en Equipos.jsx.

---

## 3. Servidor Nodo Edge con IA Local (Ollama en Lenovo ThinkCentre M720q)

### Descripción técnica
El servidor Lenovo ThinkCentre M720q (Intel i5-8500T, 16 GB RAM, 512 GB SSD) actúa como **nodo edge** ejecutando Ollama con Gemma 3 4B localmente. El sistema incluye fallback automático a **MiniMax cloud API** cuando el edge no está disponible.

### Arquitectura implementada (WS-3 — esta corrida)
```
                    SIGAB Backend (FastAPI)
                           │
                    AI_PROVIDER=auto
                     ┌─────┴─────┐
              ¿Ollama UP?         ¿Ollama DOWN?
                  │                    │
         Gemma 3 4B local        MiniMax cloud API
         (Lenovo edge)           (MiniMax-Text-01)
         latencia ~2s            latencia ~8s
         datos 100% privados     datos salen del hospital
```

### Funciones en SIGAB
| Función | Módulo SIGAB | Provider |
|---------|-------------|---------|
| Chat diagnóstico biomédico | `Copilot` | Edge (fallback cloud) |
| Análisis de causa raíz NOM-240 | `Tecnovigilancia` | Edge (fallback cloud) |
| Resumen ejecutivo diario | `Dashboard` | Edge (fallback cloud) |
| OCR de etiquetas y reportes | `OCR` | Gemini Flash (cloud siempre) |

### Justificación técnico-económica
| Escenario | Latencia | Costo mensual | Privacidad |
|-----------|---------|:-------------:|-----------|
| Sin IA | — | $0 | — |
| Solo cloud (OpenAI/Gemini) | 8-15 s | $2,000–5,000 | Datos salen del hospital |
| Edge + fallback cloud | 2-3 s (edge) / 8 s (cloud) | $300 (electricidad) | Datos privados en edge |
| Solo edge | 2-3 s | $300 | 100% privados |

- **CAPEX:** $13,500 MXN (ya adquirido — Lenovo ThinkCentre reacondicionado Grado A).
- **OPEX:** ~$300/mes electricidad (i5-8500T TDP 35W × 720h × $3.50/kWh IMSS).
- **Beneficio normativo:** LFPDPPP y políticas IMSS prohíben enviar datos clínicos a servicios cloud sin contrato de privacidad. El edge evita este riesgo completamente.
- **ROI:** El copilot ahorra ~30 min/ticket de diagnóstico × 40 tickets/mes × $150/hr = $3,000/mes → ROI en **5 meses**.

### Variables de entorno requeridas en producción
```bash
# .env del backend (NO subir al repo)
SIGAB_AI_PROVIDER=auto          # "local" | "cloud" | "auto"
SIGAB_OLLAMA_HOST=http://localhost:11434
SIGAB_GEMMA_MODEL=gemma3:4b
SIGAB_MINIMAX_API_KEY=<clave>   # Solo si se quiere fallback cloud
SIGAB_MINIMAX_MODEL=MiniMax-Text-01
```

### Endpoint de monitoreo implementado
```
GET /api/copilot/edge-status   (requiere auth)
Respuesta:
{
  "ok": true,
  "ollama_activo": true,
  "modelo": "gemma3:4b",
  "modelo_disponible": true,
  "cloud_configurado": true,
  "cloud_modelo": "MiniMax-Text-01",
  "ai_provider_config": "auto",
  "proveedor_activo": "edge"
}
```

---

## 4. Mensualidad de Dominio .mx + API de IA para Bots de SIGAH

### Descripción técnica
- **Dominio:** `sigab.mx` o `sigab-hgr1.mx` (~$480/año en NIC México).
- **API IA bots:** MiniMax API (o Gemini Flash) para procesamiento de lenguaje natural en el bot de WhatsApp (`sigab-bot/`).

### Funciones en SIGAB
| Función | Módulo | Costo estimado |
|---------|--------|:-------------:|
| Dominio web SIGAB para acceso desde internet | Infraestructura | $480/año |
| NLP para comandos del bot WhatsApp | `sigab-bot` | $2,400–4,800/año |
| SSL/TLS certificado (Let's Encrypt) | Infraestructura | $0 |
| **Total anual** | | **$2,880–5,280/año** |

### Justificación técnico-económica
- El bot de WhatsApp actual (`sigab-bot/`) procesa comandos de texto fijo. Con API de IA puede interpretar lenguaje natural: "¿cuántos ventiladores están en mantenimiento?" sin requerir comandos exactos.
- El dominio `.mx` es requisito para la presentación comercial ante el IMSS y para firmar URLs de QR sin IP local (QR permanentes, no dependientes de LAN).
- **OPEX:** $4,800–5,280 MXN/año total.
- **ROI:** Cualquier contrato IMSS requiere presencia web verificable. Un dominio registrado aumenta la percepción de seriedad ante licitadores.

### Panel de consumo de tokens (pendiente — WS-4)
```
Módulo: Dashboard → panel lateral "Consumo IA"
  - Tokens usados hoy / mes
  - Costo estimado MXN (según tarifa MiniMax)
  - Desglose por endpoint (copilot/chat, causa-raiz, diagnostico)
  - Alertas si consumo supera umbral mensual configurado
```
> **WS-4 siguiente paso:** Tabla `ia_token_log` en BD + middleware de conteo + panel en Dashboard.jsx.

---

## Mapa de Dependencias entre Workstreams

```
WS-1 (este doc)
  └─ Da contexto económico a WS-2, WS-3, WS-4

WS-2 (UDI + escaneo 3D)
  ├─ Migración SQL: equipos.udi_grabado, metrologia.scan_3d_url
  ├─ Endpoints: POST /equipos/{id}/udi, POST /metrologia/{id}/scan3d
  └─ Frontend: badges en Equipos.jsx, viewer en Metrologia.jsx

WS-3 (edge AI — COMPLETADO en corrida 2026-06-04)
  ├─ config.py: MINIMAX_*, AI_PROVIDER
  ├─ gemma_service.py: fallback cloud (_cloud_chat_stream, _cloud_chat_text)
  └─ copilot.py: GET /edge-status

WS-4 (dominio + consumo tokens — PENDIENTE)
  ├─ Tabla ia_token_log en BD
  ├─ Middleware conteo tokens en gemma_service.py
  └─ Panel "Consumo IA" en Dashboard.jsx

WS-5 (calidad — continuo)
  ├─ Tests pytest para nuevos endpoints
  ├─ Lint flake8/mypy
  └─ Actualizar esta doc con cada corrida
```

---

## Estado por Corrida (Bitácora)

| Fecha | Corrida | WS | Avance |
|-------|---------|----|----|
| 2026-06-04 | auto/avance-2026-06-04-0001 | WS-3 | Capa IA edge+cloud: config MiniMax, fallback automático, endpoint `/edge-status` |
| _pendiente_ | — | WS-2 | Campos UDI + escaneo 3D en BD y endpoints |
| _pendiente_ | — | WS-4 | Panel consumo tokens |
| _pendiente_ | — | WS-1 | Mejorar ROI con datos reales de piloto |

---

**Documento generado por routine /schedule — GOAL Industria 4.0 SIGAB**
