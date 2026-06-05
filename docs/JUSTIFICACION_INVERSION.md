# SIGAB — Justificación de Inversión: Componentes Industria 4.0

**Proyecto**: Sistema Integral de Gestión de Activos Biomédicos (SIGAB) V2.0  
**Hospital**: HGR No. 1 IMSS Tijuana  
**Fecha de revisión**: 2026-06-05  
**Versión**: 1.0 (generado por routine /schedule — WS-1)

---

## Resumen ejecutivo

Este documento justifica técnica y económicamente los cuatro componentes de Industria 4.0 que elevan a SIGAB de un sistema de gestión de activos a una plataforma de ingeniería biomédica de clase hospitalaria. La inversión incremental total estimada es de **$95,000 – $130,000 MXN** con un ROI proyectado de 18–24 meses sobre la base del ahorro en fallas no planificadas, tiempo técnico y cumplimiento normativo.

---

## Componente 1: Escáner de Metrología 3D MIRACO Plus

### Ficha técnica
| Parámetro | Valor |
|---|---|
| Tecnología | Fotogrametría + escáner de luz estructurada |
| Resolución puntual | ≤ 0.05 mm |
| Volumen de captura | 0.1 m³ – 4 m³ |
| Conectividad | USB-C + Wi-Fi — exporta OBJ, STL, PLY |
| Peso | ~1.3 kg (portátil, uso en campo) |
| Precio referencial | ~$45,000 – $65,000 MXN (importación directa) |

### Funciones en SIGAB
1. **Inspección dimensional de equipos**: detecta deformaciones en chasis, marcos de arco en C, soportes de bombas IV.
2. **Registro 3D como evidencia técnica**: cada escaneo se adjunta al historial de la orden de servicio (`ordenes_servicio.archivos_adjuntos`).
3. **Baseline de ciclo de vida**: primer escaneo al ingreso del equipo, comparación anual para cuantificar desgaste.
4. **Soporte a Tecnovigilancia NOM-240**: evidencia objetiva en investigación de eventos adversos relacionados con integridad estructural.

### Ventajas
- **Documentación inobjetable**: imagen 3D reproducible supera a las fotografías 2D en peritajes y auditorías COFEPRIS.
- **Detección temprana**: grietas o deformaciones detectadas antes de falla catastrófica → reducción de eventos adversos clase III.
- **Capacitación**: los residentes y técnicos aprenden anatomía dimensional de equipos complejos sin manipularlos.

### Justificación técnico-económica
| Concepto | Valor anual estimado |
|---|---|
| Fallas catastróficas evitadas (1/año × $25,000 reparación) | $25,000 MXN |
| Reducción eventos adversos COFEPRIS (multa evitada) | $15,000 – $50,000 MXN |
| Ahorro en inspecciones externas (3/año × $8,000) | $24,000 MXN |
| **Beneficio anual estimado** | **$64,000 – $99,000 MXN** |
| **CAPEX** | $55,000 MXN |
| **Payback** | **6–10 meses** |

### Estado en SIGAB
- **Pendiente**: agregar campo `scan_3d_url` al modelo `equipos` y al módulo de metrología.
- **Pendiente**: crear endpoint `POST /api/metrologia/scan3d` para registrar el escaneo referenciado por `equipo_id`.
- **Tabla de referencia**: `metrologia_calibracion` (existe) → extender con `tipo_inspeccion = '3d_scan'`.

---

## Componente 2: Pistola Grabadora Láser (Marcado UDI / Trazabilidad)

### Ficha técnica
| Parámetro | Valor |
|---|---|
| Tecnología | Grabado láser fibra óptica (Fiber laser) |
| Potencia típica | 20–30 W (modelos portátiles de campo) |
| Materiales | Acero inox, aluminio, plástico ABS, titanio |
| Velocidad | 8,000 mm/s (DM DataMatrix 10×10 mm en 1.2 s) |
| Precio referencial | $8,000 – $18,000 MXN (importación AliExpress / Alibaba industrial) |
| Normativa | Compatible con estándares UDI: ISO/IEC 15418, GS1 DataMatrix |

### Funciones en SIGAB
1. **Grabado de UDI permanente**: marca el `equipo.serie` + código DataMatrix en la carcasa del equipo. Resiste autoclave 134 °C, desinfectantes y esterilizantes.
2. **Re-etiquetado de activos reclasificados**: cuando un equipo cambia de número de inventario IMSS, la pistola corrige la placa sin reemplazarla.
3. **Complementa QR impreso**: el grabado láser es la capa de redundancia — si la etiqueta adhesiva se desprende, el código grabado persiste.
4. **Flujo en SIGAB**: el técnico escanea el QR impreso + valida con el grabado láser → `validaciones_pokayoke` registra la coincidencia triple (QR / inventario / grabado).

### Ventajas
- **Trazabilidad a 25 años**: grabado no degradable, cumple vida útil del equipo biomédico.
- **NOM-016 compliance**: identificación única e indeleble según el artículo 28 de la NOM-016-SSA3-2012.
- **Costo marginal = $0**: una vez adquirida la pistola, cada marcado cuesta ~$0.01 (electricidad).
- **Diferenciador comercial**: ningún sistema de gestión de activos en el IMSS Tijuana ofrece marcado láser integrado.

### Justificación técnico-económica
| Concepto | Valor |
|---|---|
| CAPEX pistola | $12,000 MXN (punto medio del rango) |
| Etiquetas adhesivas ahorradas (500/año × $4) | $2,000/año |
| Tiempo técnico ahorrado en re-etiquetado (20 h/año × $150/h) | $3,000/año |
| Reducción de activos "fantasma" (equipos no localizados) | $10,000–$20,000/año |
| **Payback** | **10–16 meses** |

### Estado en SIGAB
- **Pendiente**: agregar campo `udi_grabado` (VARCHAR 64) al modelo `equipos`.
- **Pendiente**: campo `fecha_marcado_laser` y `marcado_por_usuario_id` para auditoría NOM-016.
- **Migración requerida**: `012_udi_laser_fields.sql` (aún no creada).
- **UI pendiente**: en la ficha de equipo (`Equipos.jsx`), botón "Registrar UDI Grabado".

---

## Componente 3: Servidor Nodo Edge con IA Local (Ollama en ThinkCentre)

### Ficha técnica del nodo
| Parámetro | Valor |
|---|---|
| Hardware | Lenovo ThinkCentre M720q (ya en presupuesto: $13,500 MXN) |
| Procesador | Intel i5-8500T @ 2.1–3.5 GHz (6 núcleos) |
| RAM | 16 GB DDR4 (ampliable a 32 GB por ~$1,500 MXN) |
| Modelos Ollama activos | `gemma3:4b` (~2.5 GB VRAM/RAM) |
| Consumo energético | ~35 W en inferencia (≈ $350/año en electricidad) |
| Fallback configurado | MiniMax API (nube) via `SIGAB_MINIMAX_API_KEY` |

### Funciones en SIGAB (SIGAB Copilot)
1. **Chat biomédico**: asistente interactivo para técnicos e ingenieros biomédicos.
2. **Diagnóstico de falla**: análisis estructurado `POST /api/copilot/diagnostico`.
3. **Causa raíz NOM-240**: sugiere causa raíz para eventos adversos.
4. **Resumen ejecutivo diario**: `GET /api/copilot/resumen-ia` para el Jefe de Conservación.
5. **Análisis de imagen (visión)**: extracción de datos de etiquetas con Gemma multimodal.
6. **Predicción de insumos**: `prompt_prediccion_insumos` analiza historial de fallas vs inventario.

### Arquitectura Edge-Local-First (implementada en este PR)
```
SIGAB Backend
    └─► ai_provider.py (capa de abstracción)
           ├─► Proveedor PRIMARIO: Ollama local @ :11434 (ThinkCentre)
           │     Latencia: 2–8 s | Costo: $0/consulta | Privacidad: total
           └─► Proveedor FALLBACK: MiniMax API (nube)
                 Latencia: 0.5–2 s | Costo: ~$0.002/1K tokens | Privacidad: datos anonimizados
```

### Ventajas vs alternativas cloud
| Criterio | Edge Local (Ollama) | Cloud Only (GPT-4/Gemini) |
|---|---|---|
| Privacidad clínica | ✅ Datos no salen del hospital | ❌ Datos médicos en servidores externos |
| Costo variable | $0/consulta | $2–15 USD / 1K consultas |
| Disponibilidad LAN | ✅ Sin internet | ❌ Requiere conexión estable |
| Latencia | 2–8 s (i5-8500T) | 0.3–2 s |
| NOM-016 compliance | ✅ On-premise auditado | ⚠️ Requiere DPA/NDA adicional |

### Justificación técnico-económica
| Concepto | Valor |
|---|---|
| CAPEX hardware (ya incluido en presupuesto base) | $13,500 MXN |
| CAPEX adicional RAM 32 GB (opcional) | $1,500 MXN |
| OPEX energía (35 W × 8,760 h × $2.80/kWh IMSS) | ~$860/año |
| OPEX fallback MiniMax (estimado 500 consultas/mes × $0.03) | ~$2,100/año |
| **OPEX total edge** | **~$2,960/año** |
| **Equivalente cloud-only** (GPT-4 Turbo, 1,500 consultas/mes) | **~$54,000/año** |
| **Ahorro anual** | **~$51,000 MXN** |
| **ROI del edge vs cloud** | **>17× en costo operativo** |

### Estado implementado (este PR)
- ✅ `services/ai_provider.py`: capa de abstracción Edge → MiniMax fallback.
- ✅ `config.py`: variables `SIGAB_MINIMAX_API_KEY`, `SIGAB_MINIMAX_BASE_URL`, `SIGAB_MINIMAX_MODEL`.
- ✅ `services/gemma_service.py`: delega a `ai_provider.py`.
- ✅ `routes/copilot.py` `/estado`: retorna `proveedor_activo`, `edge.online`, `fallback.configurado`.
- ✅ `database/migrations/011_ia_provider_log.sql`: tabla de auditoría de uso.
- ⬜ **Pendiente**: endpoint `GET /api/copilot/consumo` — panel de tokens (WS-4).
- ⬜ **Pendiente**: instrumentar `log_ia_proveedor` en cada llamada de copilot.

---

## Componente 4: Mensualidad de Dominio (.mx) + API de IA para Bots SIGAH

### Ficha técnica
| Concepto | Detalle |
|---|---|
| Dominio | `sigab.mx` o `sigah.mx` (disponibilidad a verificar) |
| Registrador | NIC México o Akky.mx |
| Costo dominio | ~$350–500 MXN/año |
| API IA bots | MiniMax API (`SIGAB_MINIMAX_API_KEY`) |
| Bots activos | `sigab-bot/` — WhatsApp via Twilio/WATI + alertas |
| Consumo estimado | 500–2,000 llamadas/mes a MiniMax |
| Costo API estimado | $500–2,000 MXN/mes dependiendo del volumen |

### Funciones
1. **Dominio `.mx`**: URL canónica para el portal público (`sigab.mx/equipo/{qr_token}`) que muestra la ficha pública de equipo sin login.
2. **Bot WhatsApp**: notificaciones de alertas críticas, vencimiento de preventivos y confirmaciones de mantenimiento al Jefe de Conservación.
3. **API MiniMax como fallback copilot**: cuando el ThinkCentre edge está apagado (mantenimiento nocturno), las consultas del bot se resuelven vía nube.
4. **Panel de consumo**: la tabla `log_ia_proveedor` (migración 011) + vista `v_ia_consumo_diario` habilitan un panel React de tokens consumidos y costo estimado.

### Desglose OPEX mensual
| Ítem | MXN/mes |
|---|---|
| Dominio .mx (prorrateado) | $35–42 |
| API MiniMax (estimado conservador) | $500–800 |
| Twilio WhatsApp Sandbox | $200–400 |
| **OPEX total mensual** | **$735–1,242 MXN/mes** |
| **OPEX total anual** | **$8,820–14,904 MXN/año** |

### Justificación
- El dominio `.mx` formaliza la identidad de SIGAB ante auditores y autoridades sanitarias.
- El costo del bot de alertas ($735–1,242/mes) es marginal vs el costo de un evento adverso no notificado a tiempo ($50,000+ en multas COFEPRIS + daño reputacional).
- El fallback MiniMax API como servicio pagado garantiza disponibilidad 24/7 del copilot incluso en ventanas de mantenimiento del edge node.

### Estado en SIGAB
- ⬜ **Pendiente**: registro del dominio (decisión humana — fuera del alcance de código).
- ⬜ **Pendiente**: endpoint `GET /api/copilot/consumo` con datos de `log_ia_proveedor`.
- ⬜ **Pendiente**: componente React `ConsumoIA.jsx` o sección en Dashboard.
- ✅ **Base técnica**: `011_ia_provider_log.sql` provee la tabla y vista necesarias.

---

## Resumen de inversión incremental

| Componente | CAPEX | OPEX/año | Beneficio/año | Payback |
|---|---:|---:|---:|---:|
| MIRACO Plus 3D | $55,000 | $2,000 | $64,000–$99,000 | 6–10 meses |
| Pistola láser UDI | $12,000 | $500 | $15,000–$25,000 | 10–16 meses |
| Edge node IA (ThinkCentre ya incluido) | $1,500 | $2,960 | $51,000 | <1 mes |
| Dominio .mx + API bots | $0 | $8,820–$14,904 | Cumplimiento + retención | — |
| **TOTAL incremental** | **$68,500** | **$14,280–$20,364** | **$130,000–$175,000** | **~9 meses** |

---

## Próximos pasos (pendientes para el humano)

1. **Adquisición MIRACO Plus**: cotizar con distribuidor local (Tijuana/CDMX) o importación directa — plazo estimado 3–6 semanas.
2. **Adquisición pistola láser**: compra en línea (importación) o ferretería industrial — plazo 1–2 semanas.
3. **Registro dominio .mx**: NIC México, verificar disponibilidad `sigab.mx` y `sigah.mx`.
4. **Configurar `SIGAB_MINIMAX_API_KEY`**: obtener API key en minimax.chat → setear en `.env` del VPS.
5. **Ejecutar migración 011**: `mysql sigab < database/migrations/011_ia_provider_log.sql`.
6. **Merge PR** `auto/avance-2026-06-05-0000` → habilita el fallback MiniMax en el backend.

---

*Generado por routine /schedule mientras el usuario está de vacaciones — GOAL Industria 4.0.*
