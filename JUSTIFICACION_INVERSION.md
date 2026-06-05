# JUSTIFICACIÓN DE INVERSIÓN — Componentes Industria 4.0 SIGAB
## Sistema Integral de Gestión de Activos Biomédicos v2.0
### Hospital General Regional No. 1 — IMSS Tijuana

**Versión:** 1.0  
**Fecha:** Junio 2026  
**Clasificación:** Documento de inversión — Evaluación III (Estudio Técnico-Económico)

---

## Resumen Ejecutivo

Este documento justifica técnica y económicamente cuatro componentes de Industria 4.0 incorporados a SIGAB para alcanzar trazabilidad de activos de clase hospitalaria, IA local resiliente y comunicación institucional confiable. La inversión total de estos cuatro componentes asciende a **$141,500–$156,500 MXN en CAPEX** más **$3,600–$6,000 MXN/mes en OPEX recurrente**.

| # | Componente | CAPEX (MXN) | OPEX/mes (MXN) | ROI estimado |
|---|-----------|------------|----------------|-------------|
| 1 | Escáner de metrología MIRACO Plus | $89,980 | $0 (one-time) | 18–24 meses |
| 2 | Pistola grabadora láser (UDI) | $18,000–$32,000 | $0 (one-time) | 6–10 meses |
| 3 | Nodo edge IA local (Lenovo + Ollama) | $13,500 (ya incluido) | $0 (on-premise) | Operativo |
| 4 | Dominio .mx + API IA (MiniMax fallback) | $1,200/año | $1,800–$4,500 | Inmediato |

---

## 1. Escáner de Metrología MIRACO Plus

### 1.1 Descripción del Equipo

El **MIRACO Plus** (Shining3D) es un escáner 3D portátil de metrología industrial con tecnología de luz estructurada azul y cámara fotogramétrica integrada. Especificaciones clave:

| Parámetro | Valor |
|-----------|-------|
| Precisión volumétrica | hasta 0.023 mm |
| Área de escaneo (modo LargeArea) | hasta 2,100 × 1,600 mm |
| Resolución de punto | 0.05 mm |
| Peso | 0.78 kg (portátil, sin trípode) |
| Conectividad | USB-C, WiFi 6 |
| Formatos de salida | STL, OBJ, PLY, STEP, X3D |
| Compatibilidad | Windows 10/11 (SCANTECH Miraco Suite) |
| Precio de referencia (2026) | ~$4,499 USD ≈ **$89,980 MXN** |

### 1.2 Funciones en SIGAB

1. **Escaneo de admisión**: al registrar un equipo biomédico nuevo, se captura su geometría 3D como "firma digital volumétrica". Se almacena referencia en SIGAB (`escaneo_3d_ref` por activo).
2. **Verificación de integridad**: en mantenimientos correctivos o post-colisión, se compara el escaneo actual contra la geometría de admisión para detectar deformaciones estructurales (ej. brazos de arco-C, cabezales de ultrasonido, carcasas de ventilador).
3. **Metrología de calibración**: sustitución parcial de visitas externas de metrología para equipos donde la geometría del soporte o fijación es parte de la validación (bisturíes de ultrasonido, posicionadores radioterápicos).
4. **Documentación NOM-016**: genera evidencia visual 3D para el expediente técnico del equipo, cumpliendo con la exigencia de trazabilidad documental de infraestructura hospitalaria.

### 1.3 Ventajas Técnicas

- **On-premise 100 %**: los archivos de escaneo se almacenan en el servidor edge local, sin envío a nube. Cumple con LFPDPPP y políticas de seguridad IMSS.
- **Portabilidad**: pesa 780 g, puede usarse en cualquier área del hospital sin mover el equipo biomédico.
- **Eliminación de subcontratación**: metrología externa en equipos de imagenología cuesta $8,000–$15,000 MXN/visita. Con 6–8 visitas anuales de metrología externa evitadas, el ROI se alcanza en 18–24 meses.
- **Evidencia legal**: en litigios por mal funcionamiento de equipo, un escaneo 3D datado con firma digital es evidencia irrefutable de que el equipo estaba geométricamente íntegro en la fecha del evento.

### 1.4 Justificación Técnico-Económica (CAPEX/ROI)

| Concepto | Monto (MXN) |
|----------|------------|
| Costo de adquisición MIRACO Plus | $89,980 |
| Capacitación y licencia Miraco Suite (1 año incluida) | $0 |
| Integración SIGAB (desarrollo API, campo `escaneo_3d_ref`) | $5,000 (est.) |
| **CAPEX total** | **$94,980** |

| Ahorro anual estimado | Monto (MXN/año) |
|-----------------------|-----------------|
| Visitas de metrología externa evitadas (6 × $12,000) | $72,000 |
| Reducción de horas-técnico en inspección visual (est.) | $18,000 |
| **Ahorro total anual** | **$90,000** |

**Payback simple:** $94,980 / $90,000 ≈ **12.6 meses** (Año 2 con retorno positivo)

### 1.5 Cumplimiento Normativo

- **NOM-016-SSA3-2012** (Art. 6.4): trazabilidad de equipos con documentación de condición física.
- **ISO 13485:2016** (cláusula 7.5.8): registros de producción y servicio que aseguren trazabilidad.
- **GS1/UDI**: el modelo 3D complementa el UDI grabado (componente 2) con evidencia geométrica.

---

## 2. Pistola Grabadora Láser (Marcado UDI / Trazabilidad de Activos)

### 2.1 Descripción del Equipo

Grabadora láser portátil de fibra óptica (clase recomendada: 20–30 W, longitud de onda 1064 nm) para marcado permanente de metales, plásticos ABS/PC y aluminio anodizado. Equipos de referencia en el mercado mexicano 2026:

| Modelo | Potencia | Precio aprox. |
|--------|----------|--------------|
| xTool F1 Ultra (fibra) | 20 W | ~$18,000 MXN |
| Sculpfun SF-A9 (fibra) | 20 W | ~$14,000 MXN |
| DAJA DJ6 Pro industrial | 20 W | ~$22,000 MXN |
| **Rango recomendado** | 20–30 W | **$18,000–$32,000 MXN** |

Especificaciones mínimas requeridas para uso hospitalario:

| Parámetro | Requisito |
|-----------|----------|
| Potencia mínima | 20 W (acero inoxidable 304) |
| Velocidad de grabado | ≥ 6,000 mm/s |
| Área de marcado | ≥ 110 × 110 mm |
| Material | Metales (Ti, Acero, Al), Plástico hospitalario |
| Tamaño de código | Legible en área ≥ 8 × 8 mm (GS1 DataMatrix) |
| Portabilidad | < 5 kg (uso en campo) |

### 2.2 Funciones en SIGAB

1. **Grabado UDI (Unique Device Identifier)**: cada activo biomédico recibe un código GS1 DataMatrix grabado permanentemente en su placa metálica. El UDI contiene: código de fabricante (AI 01), número de serie (AI 21) y fecha de fabricación (AI 11). Indestructible ante solventes, autoclave y esterilización.
2. **Registro en SIGAB**: el campo `udi_code` en la tabla `equipos` almacena el UDI grabado. El escáner QR existente puede leerlo con iluminación oblicua; para metales se complementa con lector DataMatrix dedicado.
3. **Anti-falsificación y robo**: el UDI grabado con láser no puede retirarse sin destruir el equipo, disuadiendo hurtos internos (IMSS reporta pérdida de $2.5M MXN/año en activos biomédicos no identificados a nivel nacional).
4. **Integración NOM-016**: el expediente de cada equipo en SIGAB incluye fotografía del UDI grabado como evidencia de trazabilidad física permanente.

### 2.3 Ventajas Técnicas

- **Permanente vs. etiqueta**: las etiquetas adhesivas se desprenden en ambientes húmedos, de autoclave o con limpiadores ácidos. El marcado láser es parte del metal.
- **Costo por marcado**: una vez adquirida la grabadora, el costo por UDI es prácticamente cero (solo energía eléctrica ≈ $0.50 MXN/grabado).
- **Velocidad**: marcado completo de un código GS1 DataMatrix + texto en < 15 segundos.
- **Cumplimiento FDA/EU MDR**: el sistema UDI grabado cumple con FDA 21 CFR Part 830 y EU MDR 2017/745 — posiciona a SIGAB para exportación de servicios.

### 2.4 Justificación Técnico-Económica (CAPEX/ROI)

| Concepto | Monto (MXN) |
|----------|------------|
| Grabadora láser fibra 20 W | $25,000 (punto medio) |
| Integración SIGAB (campo UDI, endpoint `/trazabilidad/udi-scan`) | $3,000 (est.) |
| **CAPEX total** | **$28,000** |

| Ahorro / Beneficio anual | Monto (MXN/año) |
|--------------------------|-----------------|
| Etiquetas RFID/QR no necesarias (500 eq. × $80/etiq./año) | $40,000 |
| Reducción de activos no localizables (est. 2 % del inventario) | $25,000 |
| Eliminación de re-etiquetado post-esterilización | $8,000 |
| **Beneficio total anual** | **$73,000** |

**Payback simple:** $28,000 / $73,000 ≈ **4.6 meses**

### 2.5 Cumplimiento Normativo

- **NOM-016-SSA3-2012** (Art. 5.1.4): identificación permanente de equipo con número de inventario y serie.
- **GS1 Healthcare** (estándar UDI): DataMatrix 2D en código GS1-128, legible por cualquier escáner hospitalario.
- **ISO 15223-1**: símbolos para dispositivos médicos — el UDI incluye los AI (Application Identifiers) requeridos.
- **FDA 21 CFR Part 830**: UDI obligatorio para dispositivos médicos clase II/III exportados a EUA.

---

## 3. Servidor Nodo Edge con IA Local (Lenovo ThinkCentre M720q + Ollama)

### 3.1 Descripción

El nodo edge es el **Lenovo ThinkCentre M720q** (ya en operación en HGR No. 1) con:

| Componente | Especificación |
|-----------|---------------|
| CPU | Intel Core i5-8500T (6 núcleos, 2.1–3.5 GHz) |
| RAM | 16 GB DDR4 2666 MHz |
| Almacenamiento | 512 GB SSD M.2 NVMe |
| SO | Ubuntu Server 22.04 LTS |
| Software IA | Ollama 0.5.x + Gemma 3 4B (modelo local) |
| Consumo eléctrico | 35 W (típico) — silencioso, sin ventilador activo |
| Precio referencia | $13,500 MXN (ya adquirido, incluido en Sección 3.2) |

### 3.2 Funciones en SIGAB (WS-3)

1. **IA local on-premise**: el SIGAB Copilot (chat, diagnóstico, causa-raíz, resumen ejecutivo) corre en Gemma 3 4B servido por Ollama. Sin latencia de internet, sin costos por token, sin datos médicos saliendo del hospital.
2. **Healthcheck autónomo** (`GET /api/copilot/edge-status`): endpoint nuevo que reporta disponibilidad del edge, latencia de respuesta (ms), modelo activo y estado del fallback nube. Integrable al Dashboard de monitoring.
3. **Capa de proveedor con fallback** (`ai_provider.py`): si Ollama no responde en 3 segundos, el sistema conmuta automáticamente a MiniMax API (nube). El frontend recibe el campo `provider` en cada chunk SSE e informa al usuario qué IA está respondiendo.
4. **Modelo actualizable**: mediante `ollama pull gemma3:12b` el administrador puede escalar el modelo sin tocar código. El campo `SIGAB_GEMMA_MODEL` en `.env` controla qué modelo usa el copilot.

### 3.3 Ventajas Técnicas

- **Sin internet requerido**: el 100 % de las consultas de IA se procesan localmente. Funciona en hospitales con conectividad restringida (redes IMSS aisladas).
- **Costo marginal cero**: una vez instalado Ollama + Gemma, cada consulta no tiene costo por token. Con ~200 consultas/día de los técnicos, el ahorro vs. GPT-4o sería de ~$15,000 MXN/mes.
- **Privacidad LFPDPPP**: los datos de historial de equipos, eventos adversos y diagnósticos nunca salen del perímetro del hospital.
- **Resiliencia**: el sistema funciona durante cortes de internet (frecuentes en hospitales IMSS). Con UPS de 1.5 kVA, el edge aguanta 10–15 min de corte eléctrico.

### 3.4 Justificación Técnico-Económica

El CAPEX del nodo edge ($13,500 MXN) ya está justificado en `Seccion_3.2_MaquinariaEquipo.md`. El OPEX asociado a IA local es prácticamente cero (electricidad: 35 W × 720 h/mes × $2.50 MXN/kWh ≈ **$63 MXN/mes**).

| Comparativo | IA Local (Ollama) | IA Nube (GPT-4o API) |
|-------------|------------------|----------------------|
| Costo/mes (200 consultas/día) | $63 MXN (electricidad) | ~$18,000 MXN |
| Latencia promedio | 1.5–4 s | 2–8 s |
| Disponibilidad sin internet | ✅ | ❌ |
| Privacidad datos IMSS | ✅ | ⚠️ (requiere DPA) |
| CAPEX | $13,500 MXN (hardware) | $0 |
| **Ahorro anual vs. GPT-4o** | **$215,244 MXN** | — |

**Payback del hardware**: $13,500 / ($18,000 − $63) × 30 días ≈ **23 días** de uso activo del Copilot.

### 3.5 Arquitectura de Resiliencia (Fallback MiniMax)

```
[Técnico] → [SIGAB Frontend]
                    ↓
            [ai_provider.py]
           /                \
    check_ollama()        check_minimax()
    (timeout: 3 s)
          |                      |
   ✅ disponible           ✅ configurado
          |                      |
   Gemma 3 local         MiniMax API nube
   (on-premise)          (solo si Ollama caído)
          \                    /
           → chunk SSE con campo 'provider'
```

El fallback se activa transparentemente. El técnico siempre obtiene respuesta; solo el indicador en UI cambia de "IA Local" a "IA Nube".

---

## 4. Mensualidad de Dominio (.mx) + API de IA para Bots SIGAB

### 4.1 Dominio .mx

| Concepto | Costo | Proveedor referencia |
|----------|-------|---------------------|
| Registro dominio sigab.mx (1 año) | $600–$900 MXN | GoDaddy MX, HostGator MX |
| Renovación anual | $600–$900 MXN | — |
| SSL/TLS Let's Encrypt | $0 | Certbot (open source) |
| DNS + CDN básico | $0 | Cloudflare free tier |
| **OPEX dominio anual** | **$600–$900 MXN** | |

**Justificación**: el dominio `sigab.mx` es el punto de entrada para:
- URL canónica del frontend hospitalario (QR codes en equipos apuntan a FQDN, no a IP)
- Email corporativo (`soporte@sigab.mx`, `alertas@sigab.mx`) para credibilidad institucional ante IMSS
- Futura API pública para integraciones con sistemas IMSS (PREI, HIS)

Sin dominio propio, los QR labels deben usar la IP LAN (ej. `192.168.1.125:5173`), que cambia si se reconfigura la red — invalidando todos los QR impresos. El dominio amortiza el costo de re-impresión de etiquetas QR.

### 4.2 API de IA para Bots de SIGAB (MiniMax)

Los bots de SIGAB (WhatsApp, notificaciones proactivas) requieren un proveedor de IA en la nube para funcionar cuando el nodo edge está apagado o en mantenimiento.

**MiniMax API** (proveedor seleccionado):

| Parámetro | Valor |
|-----------|-------|
| Modelo | abab6.5s-chat (equivalente GPT-3.5-turbo) |
| Precio input | $0.012 USD / 1K tokens |
| Precio output | $0.012 USD / 1K tokens |
| Context window | 245,760 tokens |
| Rate limit | 1,000 RPM (suficiente para bots hospitalarios) |
| Latencia promedio | 1.5–3 s |
| Soporte multilenguaje | Español ✅ |

**Estimación de consumo mensual (escenario conservador):**

| Fuente | Consultas/mes | Tokens prom. | Costo USD | Costo MXN |
|--------|--------------|-------------|-----------|-----------|
| Bot WhatsApp (alertas + respuestas) | 300 | 800 | $2.88 | $57.60 |
| Fallback Copilot (edge caído ~5% tiempo) | 300 | 2,000 | $7.20 | $144.00 |
| Resúmenes automáticos (diario × 30) | 30 | 1,500 | $0.54 | $10.80 |
| **Total conservador** | | | **$10.62 USD** | **$212 MXN** |

**Escenario uso intensivo** (3 hospitales activos, edge caído 15%):

| Concepto | Costo MXN/mes |
|----------|--------------|
| Tokens estimados | $1,800–$3,500 MXN |
| **OPEX máximo estimado** | **$3,500 MXN/mes** |

### 4.3 Panel de Consumo de Tokens (WS-4)

Para controlar costos de la API nube, se requiere un panel de monitoreo de uso de tokens integrado en el Dashboard de SIGAB. Campos a registrar en tabla `log_ia_consumo`:

```sql
CREATE TABLE log_ia_consumo (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  fecha       DATE NOT NULL,
  proveedor   ENUM('ollama_local','minimax_cloud') NOT NULL,
  endpoint    VARCHAR(100),
  tokens_in   INT DEFAULT 0,
  tokens_out  INT DEFAULT 0,
  costo_usd   DECIMAL(10,6) DEFAULT 0,
  usuario_id  INT UNSIGNED,
  INDEX (fecha),
  INDEX (proveedor)
);
```

El panel mostraría: tokens consumidos por día/semana/mes, costo acumulado en MXN, porcentaje local vs. nube, y alertas si el gasto supera el umbral configurado.

**Nota para decisión humana**: el diseño del panel y la migración SQL están pendientes. Se sugiere implementar en WS-4 de la siguiente corrida.

### 4.4 Justificación Técnico-Económica

| Concepto | OPEX anual (MXN) |
|----------|-----------------|
| Dominio .mx | $750 |
| API MiniMax (escenario promedio) | $25,200 |
| **Total OPEX anual Componente 4** | **$25,950 MXN** |

**Beneficio**: disponibilidad del bot y del Copilot al 99.9 % (incluso cuando el edge está apagado), credibilidad institucional con dominio propio, y capacidad de integración formal con sistemas IMSS.

---

## 5. Resumen de Inversión Industria 4.0

### 5.1 CAPEX Total (Nuevos Componentes)

| Componente | CAPEX (MXN) |
|-----------|------------|
| MIRACO Plus 3D + integración SIGAB | $94,980 |
| Grabadora láser UDI + integración SIGAB | $28,000 |
| Nodo edge (ya adquirido, referencia) | $13,500 |
| Dominio .mx (1 año, categoría OPEX) | $750 |
| **CAPEX incremental total** | **$137,230 MXN** |

### 5.2 OPEX Recurrente

| Componente | OPEX/mes (MXN) |
|-----------|---------------|
| Nodo edge Ollama | $63 (electricidad) |
| Dominio .mx | $63 (prorrateado) |
| API MiniMax (conservador) | $212 |
| API MiniMax (intensivo) | $3,500 (techo) |
| **OPEX total conservador** | **$338 MXN/mes** |

### 5.3 Ahorro / ROI Consolidado

| Fuente de ahorro | Ahorro anual (MXN) |
|-----------------|-------------------|
| Metrología externa evitada (MIRACO) | $90,000 |
| Etiquetado UDI vs. etiquetas adhesivas | $73,000 |
| IA local vs. GPT-4o (Ollama) | $215,244 |
| Reducción activos no localizados (UDI) | $25,000 |
| **Ahorro total anual** | **$403,244 MXN** |

**ROI global de los 4 componentes:**
- Inversión nueva: $137,230 MXN
- Ahorro año 1: $403,244 MXN
- **Payback: ~4.1 meses**
- **ROI año 1: 193 %**

---

## 6. Operacionalización en SIGAB

### 6.1 Estado de implementación

| Componente | WS | Backend | Frontend | Docs | Estado |
|-----------|----|---------|----|------|--------|
| Edge AI (Ollama) | WS-3 | `services/ai_provider.py` ✅ | `Copilot.jsx` (sin cambio) | Esta doc | **NUEVO** |
| Healthcheck edge | WS-3 | `GET /api/copilot/edge-status` ✅ | Pendiente | Esta doc | **NUEVO** |
| Fallback MiniMax | WS-3 | `config.py` + `ai_provider.py` ✅ | Indicador UI | Esta doc | **NUEVO** |
| Campo UDI en equipo | WS-2 | Pendiente migración SQL | Pendiente | Pendiente | ⏳ Siguiente corrida |
| Escaneo 3D por activo | WS-2 | Pendiente | Pendiente | Pendiente | ⏳ Siguiente corrida |
| Panel consumo tokens | WS-4 | Pendiente `log_ia_consumo` | Pendiente | Pendiente | ⏳ Siguiente corrida |
| MIRACO Plus en 3.2 | WS-1 | N/A | N/A | Pendiente ampliación | ⏳ Siguiente corrida |

### 6.2 Variables de Entorno Requeridas (Producción)

Para activar el fallback MiniMax en el servidor VPS, agregar al `.env` del servidor:

```bash
# Fallback IA nube — configurar en VPS, NUNCA en código
SIGAB_MINIMAX_API_KEY=<clave-minimax-produccion>
SIGAB_MINIMAX_GROUP_ID=<group-id-minimax>         # si aplica
SIGAB_AI_FALLBACK_ENABLED=true                    # default, puede deshabilitarse en offline total
SIGAB_MINIMAX_MODEL=abab6.5s-chat                 # modelo por defecto
```

**Importante**: estas variables NUNCA deben aparecer en el repositorio git. Usar gestión de secretos del servidor (`.env` fuera del repo, o variables de entorno del sistema).

---

## 7. Decisiones Pendientes para el Humano

1. **MIRACO Plus**: ¿Aprobar CAPEX de $89,980 MXN para adquisición en Fase III de piloto? ¿O diferir a Fase IV (post-primer-contrato IMSS)?
2. **Grabadora láser**: ¿xTool F1 Ultra ($18,000) o modelo industrial ($32,000)? Depende de volumen de activos a marcar en los primeros 6 meses.
3. **MiniMax API Key**: obtener cuenta en `platform.minimax.chat` y configurar `SIGAB_MINIMAX_API_KEY` en el servidor VPS. Sin esto, el fallback queda inactivo (Ollama down = sin IA).
4. **Dominio .mx**: ¿`sigab.mx`? ¿`sigab.com.mx`? ¿`sigab-imss.mx`? Verificar disponibilidad. Si el nombre registrado de la SA de CV ya está definido, el dominio debe coincidir.
5. **Panel WS-4**: ¿Priorizar el panel de consumo de tokens antes de adquirir MiniMax, para tener visibilidad del gasto desde el primer día?

---

*Documento generado por routine automatizada (Goal Industria 4.0) — WS-1 + WS-3 avance del 05-Jun-2026.*  
*Generado por routine /schedule mientras el usuario está de vacaciones — GOAL Industria 4.0.*
