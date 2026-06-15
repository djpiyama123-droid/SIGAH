# Propuesta de Adquisición — Herramientas de Trazabilidad e Ingeniería Inversa (Industria 4.0)

> **Dirigido a:** Jefe de Conservación — Clínica No. 1, IMSS · **[Nombre por confirmar]**
> **Presenta:** Equipo SIGAB / Bioingeniería, con el respaldo del Subjefe de Conservación de Equipos Médicos, **Ing. Carlos Ramírez Oswaldo**.
> **Fecha:** Junio 2026 · **Estado:** Propuesta para autorización de cotización formal.
> **Marco normativo:** NOM-016-SSA3, NOM-240-SSA1, ISO 13485.

---

## 1. Resumen ejecutivo

Se solicita autorización para cotizar e integrar **tres herramientas** que llevan al área de Conservación a un esquema de **trazabilidad permanente** y **manufactura propia de refacciones** (Industria 4.0), conectadas directamente a la plataforma **SIGAB** que ya opera en el hospital:

| # | Herramienta | Función principal | Inversión estimada* |
|---|-------------|-------------------|---------------------|
| 1 | **Pistola grabadora láser portátil** | Marcado UDI/QR **permanente** en equipos, cables y refacciones (NOM-016) | ≈ $1,500 – 4,500 USD |
| 2 | **Escáner 3D RevoPoint MIRACO Plus** | Escaneo dimensional de piezas para **ingeniería inversa** de refacciones descontinuadas | ≈ $1,100 – 1,400 USD |
| 3 | **GPU dedicada (RTX 4090 24 GB o RTX 5070-class)** | Correr **IA local** en la HP Workstation para asistir el rediseño y mantener datos en sitio | ≈ $600 – 2,400 USD |

\* *Rangos de mercado a junio 2026, en USD. Sujetos a cotización formal con proveedor en México (ver §9 y Anexo A). No constituyen precio en firme.*

**El argumento central:** SIGAB **ya tiene el software listo** para recibir estas tres herramientas — los campos de UDI láser y el registro de escaneos 3D ya están implementados en la base de datos del sistema (ver §7). No estamos comprando equipo para "ver si se usa": estamos comprando el hardware que **cierra un flujo digital que ya existe**.

---

## 2. El problema que resuelve hoy

El área de Conservación enfrenta tres limitaciones concretas:

1. **El etiquetado actual no sobrevive el uso clínico.** Las etiquetas adhesivas y los QR impresos se despegan, se borran con la limpieza química y no resisten ciclos de esterilización ni abrasión. Un equipo sin identificador legible **rompe la trazabilidad** que exige la NOM-016.
2. **Las refacciones descontinuadas paran equipos.** Cuando una pieza plástica, un soporte o un componente mecánico se rompe y el fabricante ya no la vende (o la cotiza con meses de espera y a precio elevado), el equipo queda **fuera de servicio** esperando una pieza que quizá nunca llegue.
3. **La IA de apoyo depende de la nube.** Para que el sistema procese fotos, documentos y datos clínicos sin que esa información **salga del hospital** (requisito NOM/ISO), parte del cómputo de IA debe correr **localmente**.

Las tres herramientas propuestas atacan directamente estos tres puntos.

---

## 3. Herramienta 1 — Pistola grabadora láser portátil

### 3.1 Qué hace
Graba de forma **permanente** un identificador (código UDI, QR o DataMatrix GS1, número de serie) directamente sobre la superficie del equipo, en placas/etiquetas metálicas, en cables y en refacciones. A diferencia del adhesivo, el marcado láser **no se despega ni se borra**.

### 3.2 Para qué nos sirve en campo
- **Identificar equipo, cables y accesorios** con un código que dura toda la vida útil del activo.
- Marcar piezas pequeñas y herramienta del taller donde no cabe una etiqueta.
- Generar el **UDI (Unique Device Identifier)** que pide la trazabilidad moderna de dispositivos médicos, alimentando directamente el expediente del equipo en SIGAB.

### 3.3 Ventajas
- **Permanencia:** resiste limpieza, químicos, esterilización y abrasión — donde la etiqueta adhesiva falla.
- **Trazabilidad NOM-016 reforzada:** identificador inalterable + registro auditable de cuándo y quién lo grabó (SIGAB guarda `laser_grabado_at` y la entrada en `log_actividad`).
- **Portátil:** se marca el equipo *in situ*, sin moverlo de su área.
- **Antifraude / anti-extravío:** un código grabado no se puede sustituir ni "caer", lo que ayuda al control de inventario y a auditorías.

### 3.4 Consideraciones y contras (con honestidad)
- **Tipo de láser:** para marcar **metal** se requiere un **láser de fibra**; los grabadores de diodo económicos solo sirven bien en plástico/madera. Esto define el rango de precio.
- **Seguridad láser:** es equipo Clase 4 — exige **gafas de protección, capacitación del operador y extracción de humos** en el taller. Es un costo operativo menor pero obligatorio.
- **Criterio de marcado:** no se graba sobre superficies que comprometan la integridad o garantía del dispositivo; se marca el chasis, una placa o una etiqueta dedicada, respetando las marcas de seguridad del fabricante.
- **No marca equipo energizado ni superficies delicadas** (pantallas, sensores). Se opera con criterio biomédico.

---

## 4. Herramienta 2 — Escáner 3D RevoPoint MIRACO Plus

### 4.1 Qué hace
Es un escáner 3D portátil y autónomo que captura la **geometría exacta** de una pieza física y la convierte en una malla digital (formato PLY/STL). Sirve para hacer **ingeniería inversa**: digitalizar una refacción rota o descontinuada para poder reproducirla.

### 4.2 El flujo completo que habilita
Este es el corazón de la propuesta de manufactura propia:

```
  Pieza rota / descontinuada
          │
          ▼
  [1] Escaneo 3D con RevoPoint MIRACO Plus  →  malla PLY/STL + mediciones
          │
          ▼
  [2] Post-procesado en HP Workstation (Quadro/RTX A5000, 24 GB)
        - Limpieza de malla y reconstrucción CAD
        - Asistencia de IA: MiniMax (nube) + LLM open-source local
          orientados a CAD para pulir/parametrizar geometría
        - Modelado final en Autodesk Fusion 360 / SolidWorks
          │
          ▼
  [3] Fabricación
        - Impresión 3D propia (resina / FDM), o
        - Maquila externa para piezas que requieran otro material
          │
          ▼
  [4] Registro en SIGAB (tabla scan3d_registros):
      archivo, mediciones, resultado (conforme / no conforme), técnico
```

### 4.3 Ventajas
- **Reduce el tiempo muerto por refacción:** una pieza que antes paraba el equipo por meses se puede reproducir en días.
- **Independencia del fabricante** para componentes no críticos descontinuados.
- **Registro dimensional por equipo** en SIGAB (la tabla `scan3d_registros` ya existe): queda evidencia técnica de cada escaneo, útil para auditoría NOM-016 y para metrología.
- Sinergia con el módulo de **Metrología/Calibración** que SIGAB ya tiene en operación.

### 4.4 Consideraciones y contras (con honestidad)
- **Precisión:** el MIRACO Plus es excelente para ingeniería inversa de propósito general (clase ~0.05 mm), pero **no sustituye a una máquina de medición por coordenadas (CMM) certificada** para tolerancias críticas.
- **Superficies difíciles:** piezas muy reflejantes, oscuras o transparentes requieren un spray mateante antes de escanear.
- **El trabajo real está en el post-procesado:** escanear es rápido; convertir la malla en un CAD fabricable requiere la workstation, el software CAD y técnico capacitado. Por eso las Herramientas 2 y 3 van juntas.
- **Responsabilidad regulatoria:** una refacción fabricada por ingeniería inversa **debe validarse en forma y función** antes de instalarse. **No se reemplazan componentes críticos de seguridad** del dispositivo médico sin la validación y el respaldo correspondientes. El alcance inicial son piezas no críticas (soportes, carcasas, guías, sujetadores, perillas, tapas).

---

## 5. Herramienta 3 — GPU dedicada para IA local en la HP Workstation

### 5.1 Por qué se necesita
Para que SIGAB procese **localmente** los datos sensibles (fotos de equipos y etiquetas, documentos internos, historial clínico-técnico) sin que salgan del hospital, y para acelerar el post-procesado del escaneo 3D y el rediseño asistido por IA, el cuello de botella es la **GPU (VRAM + arquitectura)**.

### 5.2 Opciones (honestas sobre VRAM)

| Opción | VRAM | Consumo aprox. | Qué corre bien | Precio estimado |
|--------|------|----------------|----------------|-----------------|
| **RTX 5070** | 12 GB | ~250 W | LLMs 7–8B cuantizados, visión/OCR, aceleración CAD | ~$600–750 USD |
| **RTX 5070 Ti** | 16 GB | ~300 W | Lo anterior + contexto largo / modelos 14B ligeros | ~$800–950 USD |
| **RTX 4090** | **24 GB** | ~450 W | Modelos 14B–32B cuantizados, procesamiento 3D pesado | ~$1,800–2,400 USD |

> **Nota técnica:** la RTX 5070 viene con **12 GB** y la 5070 Ti con **16 GB**; no existe una variante de 18 GB. Para IA local, **más VRAM = modelos más grandes y mejor calidad**. La RTX 4090 (24 GB) es la opción de mayor capacidad; la 5070-class es más económica y de menor consumo, a costa de VRAM.

### 5.3 Ventajas
- **Soberanía de datos:** la IA sobre datos sensibles corre dentro del hospital (NOM-016/240, ISO-13485).
- **Sin costo recurrente por token** para el grueso del trabajo; la nube (MiniMax) queda solo para razonamiento pesado.
- **Acelera el flujo de la Herramienta 2** (limpieza de malla, parametrización CAD asistida por IA).

### 5.4 Consideraciones y contras (con honestidad)
- **Verificar la HP Workstation antes de comprar:** la RTX 4090 exige **~450 W**, conector **12VHPWR (16-pin)**, espacio de 3 slots y una fuente holgada. Hay que confirmar fuente, slot PCIe y enfriamiento del equipo. La 5070-class es más fácil de integrar.
- **Posible traslape con la A5000 existente:** si la HP Workstation ya tiene una **Quadro/RTX A5000 (24 GB)**, conviene **primero validar si esa tarjeta ya cubre la inferencia local** antes de comprar una segunda GPU. La recomendación es medir la carga real y, si hace falta, sumar la GPU dedicada para no duplicar capacidad.
- Las GPU de consumo (4090/5070) no traen memoria ECC ni drivers "pro" certificados; para inferencia esto normalmente no es problema.

---

## 6. Cumplimiento normativo

| Norma | Cómo aporta esta inversión |
|-------|----------------------------|
| **NOM-016-SSA3** (infraestructura y trazabilidad) | Marcado UDI permanente + registro auditable de escaneos e identificadores en SIGAB. |
| **NOM-240-SSA1** (tecnovigilancia) | Identificación inequívoca del equipo en reportes de incidentes y seguimiento. |
| **ISO 13485** | Control documentado del activo y de las piezas; evidencia dimensional y trazabilidad por equipo. |

Toda la actividad queda registrada en la bitácora de auditoría (`log_actividad`) que SIGAB ya mantiene como fuente única.

---

## 7. Diferenciador clave: el software YA está listo

No es una compra a futuro incierto. La plataforma SIGAB **ya tiene implementado** el lado digital que estas herramientas alimentan:

- **Campo `udi_code` y `laser_grabado_at`** en el expediente de cada equipo → reciben directamente el marcado de la pistola láser, con endpoint dedicado y registro de auditoría.
- **Tabla `scan3d_registros`** → almacena cada escaneo del RevoPoint (archivo, mediciones, resultado conforme/no conforme, técnico y fecha).
- **Módulo de Metrología/Calibración** en operación → marco natural para el registro dimensional.
- **Arquitectura de IA híbrida** (local + MiniMax en nube) ya diseñada → la GPU completa el lado local.

En otras palabras: **autorizar estas herramientas activa funcionalidad que el hospital ya tiene desarrollada y pagada en software.**

---

## 8. Presupuesto consolidado (estimado, a cotizar)

| Concepto | Estimado USD | Estimado MXN (aprox.)* |
|----------|-------------:|----------------------:|
| Pistola grabadora láser portátil (fibra, ~20–30 W) | $1,500 – 4,500 | $30,000 – 90,000 |
| Escáner 3D RevoPoint MIRACO Plus | $1,100 – 1,400 | $22,000 – 28,000 |
| GPU dedicada (según opción §5.2) | $600 – 2,400 | $12,000 – 48,000 |
| Consumibles/seguridad (gafas láser, spray mateante, extracción) | $150 – 400 | $3,000 – 8,000 |
| **Total estimado** | **$3,350 – 8,700** | **$67,000 – 174,000** |

\* *Tipo de cambio referencial ~$20 MXN/USD. Cifras orientativas para dimensionar la decisión; el monto en firme surge de la cotización formal.*

> **Comparativo de valor:** el costo de una sola refacción descontinuada importada con maquila urgente, más el tiempo de un equipo crítico fuera de servicio, puede acercarse al costo de todo este kit — que después sirve para **todos** los equipos del padrón.

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Precios cambian / proveedor no disponible en MX | Solicitar 2–3 cotizaciones formales antes de comprometer compra. |
| Curva de aprendizaje del escaneo y CAD | Capacitación inicial + arrancar con piezas no críticas sencillas. |
| GPU 4090 no cabe / fuente insuficiente en la HP Workstation | Verificar specs físicas primero; opción de respaldo 5070-class de menor consumo. |
| Refacción reproducida sin validar | Política clara: validación forma/función obligatoria; nunca componentes críticos de seguridad sin respaldo. |
| Seguridad láser | Equipo de protección + procedimiento + área ventilada antes del primer uso. |

---

## 10. Solicitud y siguiente paso

Se solicita al **Jefe de Conservación de la Clínica No. 1** la **autorización para levantar la cotización formal** de las tres herramientas, con el fin de:

1. Cerrar el flujo de **trazabilidad permanente** (pistola láser) ya soportado por SIGAB.
2. Habilitar la **manufactura propia de refacciones** descontinuadas (escáner 3D + workstation + IA).
3. Garantizar la **soberanía de datos** ejecutando la IA dentro del hospital (GPU local).

Quedamos a disposición para una demostración del flujo en SIGAB y para presentar las cotizaciones en firme una vez autorizado este paso.

---

## Anexo A — Puntos a confirmar antes de la versión final

- [ ] **Nombre y cargo exacto** del Jefe de Conservación destinatario (en el encabezado quedó como campo por confirmar).
- [ ] **Cotizaciones formales** (2–3 por herramienta) con proveedor en México — los precios de este documento son estimaciones de mercado, no precios en firme.
- [ ] **Specs de la HP Workstation** (modelo, fuente en watts, slot PCIe libre, si ya tiene la Quadro/RTX A5000) para decidir la GPU sin duplicar capacidad.
- [ ] **Potencia/tipo del láser** (fibra vs. diodo) según los materiales reales a marcar.
- [ ] Definir el **catálogo inicial de piezas** candidatas a ingeniería inversa (no críticas).

---

_Documento elaborado por el equipo SIGAB — Bioingeniería, Universidad Xochicalco / HGR No. 1 IMSS Tijuana. Versión borrador para revisión interna antes de su presentación formal._
