# SIGAB V2.0 — Guion de Demostración Ejecutiva
**Destinatario:** Ing. Carlos Oswaldo — Subjefe de Conservación de Equipos Médicos (HGR No.1 IMSS Tijuana)
**Sede de reunión:** **Café Quijarro — Tijuana**
**Fecha y hora:** **Viernes 17 de abril de 2026 · 12:00 h**
**Duración objetivo:** 40-45 minutos (5 min contexto + 20 min demo + 10 min documentos + 5-10 min próximos pasos)
**Flujo del día:** 12:00 h Quijarro (Asus) → 14:00 h traslado a Clínica 1 → 14:00-16:30 h instalación ThinkCentre (ver `OPERACION/Checklist_Instalacion_ThinkCentre_Clinica1.md`)

---

## Nota de contexto: setup split Asus ↔ ThinkCentre

- **Para la reunión en Quijarro**: la demo corre en la **laptop Asus** de Gustavo. El stack SIGAB está replicado localmente en la Asus (Docker Compose) — idéntico al del ThinkCentre.
- **El Lenovo ThinkCentre M720q** se **queda instalado en la oficina de Conservación de Clínica 1** al salir de Quijarro. Desde ese momento es el **servidor de producción** durante el fin de semana 17-19 abril.
- **Durante la presentación del martes 21-abr** la demo en vivo se conecta al ThinkCentre de Clínica 1 por WhatsApp video + Ray-Ban Meta Display — mostrando datos reales capturados durante el fin de semana.

---

## 0 · Preparación previa (11:30 h, 30 min antes de llegar a Quijarro)

| Check | Acción |
|---|---|
| ☐ | **Laptop Asus** conectada con cargador (Quijarro tiene tomas en mesas de la ventana) |
| ☐ | Tethering celular listo por si el WiFi de Quijarro falla (SIGAB NO requiere internet, es buen respaldo para correo) |
| ☐ | Backend activo en la Asus: `http://localhost:8000/health` → `{"status":"ok"}` |
| ☐ | Frontend activo en la Asus: `http://localhost:5173` abierto en Chrome (pestaña fija) |
| ☐ | Ollama corriendo en la Asus: `curl http://localhost:11434/api/tags` responde con modelos |
| ☐ | Sesión iniciada con **ADMIN001 / ${ADMIN_PASSWORD}** (ya logueado antes de llegar) |
| ☐ | Documentos abiertos en pestañas:<br>• `ESTUDIOS_ECONOMICOS/SIGAB_Resumen_Ejecutivo_Carlos_Oswaldo.pdf` (impreso + digital)<br>• `ESTUDIOS_ECONOMICOS/SIGAB_Modelo_Financiero.xlsx`<br>• `SIGAB_DocInversionista_v3_Template.docx`<br>• `SIGAB_Presentacion_Ejecutiva.pdf`<br>• Este guion |
| ☐ | **3 copias impresas del Resumen Ejecutivo** (una para Carlos, dos de respaldo) |
| ☐ | USB con toda la documentación (por si Carlos quiere llevarse copia digital) |
| ☐ | ThinkCentre M720q en la mochila + cables HDMI/Ethernet/corriente (para instalar después) |
| ☐ | Cerrar apps innecesarias (Slack, notificaciones, VS Code si no se usa) |
| ☐ | Modo "No molestar" en el teléfono durante la demo |
| ☐ | Zoom de Chrome al 110 % para que Carlos lea cómodamente desde el otro lado de la mesa |

**Credenciales para demo (no compartir):**
```
Matrícula: ADMIN001
Password : ${ADMIN_PASSWORD}
URL      : http://localhost:5173
```

---

## 1 · Apertura (3 min)

> *"Ing. Carlos, muchas gracias por recibirme aquí en Quijarro. En los próximos 40 minutos le voy a mostrar tres cosas:*
> 1. ***SIGAB V2.0** corriendo end-to-end desde esta laptop Asus — idéntico a como operará en Clínica 1.*
> 2. ***El Resumen Ejecutivo impreso** con el modelo de negocio Asset-Light, los números (VPN +$493k, TIR 32.58%) y la propuesta concreta.*
> 3. ***Un plan de instalación hoy mismo** en la oficina de Conservación: salimos de aquí a Clínica 1 a las 14:00 h y dejo el micro-servidor Lenovo ThinkCentre operando antes de las 16:30.*
>
> *Todo lo que verá corre **100 % on-premise** — cero datos salen del hospital, cumple NOM-016, NOM-240, ISO-13485 y LFPDPPP. Al final del fin de semana tendremos datos reales capturados por su personal, que presentaré el martes en la universidad con su nombre como socio técnico clave del piloto."*

**Puntos clave a mencionar:**
- SIGAB cumple con **NOM-016**, **NOM-240** e **ISO-13485**
- Todo el stack es **software libre y ejecución local** → cero dependencia de internet
- Diseñado específicamente para el flujo operativo del HGR No.1

---

## 2 · Demo en vivo — Flujo operativo completo (15 min)

### 2.1 — Login e identidad del sistema (1 min)
- Abrir `http://localhost:5173`
- **Destacar:** pantalla de login con branding IMSS, matrícula como identificador (no email)
- Ingresar `ADMIN001` / `${ADMIN_PASSWORD}` → Dashboard

### 2.2 — Dashboard & KPIs (2 min)
- Pestaña **Dashboard**
- **Señalar:**
  - KPIs en tiempo real: equipos operativos, en mantenimiento, alertas activas
  - Gráficos de distribución por área y estado
  - Mapa hospitalario con geolocalización de equipos críticos
  - Alertas vivas con código de color (verde/amber/rojo/slate)
- **Frase clave:** *"Todo esto se actualiza vía SSE — ustedes no necesitan recargar la página cuando un técnico cierra una orden."*

### 2.3 — Inventario de Equipos (2 min)
- Pestaña **Equipos**
- **Mostrar:**
  - Tabla con filtros (área, estado, marca, modelo)
  - Clic en un equipo → detalle con historial
  - Generación de **código QR** por equipo → el técnico lo escanea y ve la ficha pública
- **Mencionar:** *"Cada QR es único y trazable. El escaneo queda registrado en el log de auditoría NOM-016."*

### 2.4 — Órdenes de Servicio (3 min) ⭐ CORE
- Pestaña **Órdenes**
- **Flujo de demo:**
  1. Crear orden nueva → seleccionar equipo → falla reportada
  2. Mostrar estados: `abierta` → `asignada` → `en_proceso` → `cerrada`
  3. Abrir una orden existente → ver tab de **Evidencias** (fotos antes/durante/después)
  4. Abrir tab de **Materiales** → refacciones consumidas
  5. Generar **PDF de la orden** → se descarga el reporte formal
- **Frase clave:** *"Este PDF es el mismo que imprime el taller hoy, pero con trazabilidad digital completa."*

### 2.5 — Mantenimiento Preventivo (2 min)
- Pestaña **Preventivos**
- **Mostrar:**
  - Calendario con preventivos programados
  - Cumplimiento mensual por área
  - Alerta cuando un preventivo está vencido
- **Mencionar:** *"El sistema le avisa al técnico responsable 7 días antes — y al subjefe si pasa de la fecha."*

### 2.6 — Tecnovigilancia NOM-240 (1.5 min)
- Pestaña **Tecnovigilancia**
- **Mostrar:**
  - Registro de eventos adversos con equipos médicos
  - Reporte a COFEPRIS prellenado
- **Frase clave:** *"Aquí cumplimos NOM-240 sin depender del papel — el reporte a COFEPRIS se genera con un clic."*

### 2.7 — SIGAB Copilot (IA local) (1.5 min) ⭐ DIFERENCIADOR
- Pestaña **Copilot**
- **Preguntar al asistente:**
  - *"¿Cuántos equipos están fuera de servicio en UCI?"*
  - *"Muéstrame las órdenes de servicio de esta semana"*
- **Frase clave:** *"Esta IA corre 100 % local con Ollama + Gemma. Cero datos salen del hospital. Cumple con privacidad PHI."*

### 2.8 — Auditoría & Trazabilidad NOM-016 (2 min)
- Pestaña **Auditoría**
- **Mostrar:**
  - Log inalterable con **hash encadenado SHA-256** (cada registro apunta al previo)
  - Botón **"Verificar cadena"** → valida toda la trazabilidad
- **Frase clave:** *"Si un auditor del IMSS pregunta 'quién modificó qué y cuándo', aquí está. Y la cadena no se puede alterar sin que el sistema lo detecte."*

### 2.9 — Reportes ejecutivos (1 min)
- Pestaña **Reportes**
- Generar reporte mensual → descarga Excel/PDF
- **Mencionar:** los indicadores clave para el informe a Nivel Central

---

## 3 · Revisión de documentos (8 min)

### 3.1 — Documento del Inversionista (3 min)
**Archivo:** `SIGAB_DocInversionista_v3_Template.docx`
- Abrir en Word
- Recorrer rápidamente:
  - Resumen ejecutivo
  - Problema que resuelve SIGAB
  - Proyección financiera
  - Plan de implementación

### 3.2 — Presentación Ejecutiva PDF (3 min)
**Archivo:** `SIGAB_Presentacion_Ejecutiva.pdf`
- Abrir en visor PDF
- Mostrar slides clave:
  - Arquitectura técnica on-premise
  - Cumplimiento normativo (NOM-016, NOM-240, ISO-13485)
  - Módulos y funcionalidades

### 3.3 — Documento recomendado adicional: **Plan Go-Live** (2 min)
**Archivo:** `PLAN_GO_LIVE_15ABR2026.md`
- Abrir en VS Code o editor markdown
- Mostrar:
  - Cronograma de implementación
  - Checklist de puesta en producción
  - Plan de capacitación al personal de Conservación

---

## 4 · Cierre y próximos pasos (5 min)

### Propuesta concreta al Ing. Carlos Oswaldo

> *"Ing., lo que le propongo es:*
>
> 1. **HOY 14:00-16:30** — Instalamos el **ThinkCentre M720q en la oficina de Conservación de Clínica 1**. Ya viene pre-configurado con todo el stack. Al salir queda operando como servidor de producción.
> 2. **Viernes 17:00 - Lunes 08:00** — Su personal de guardia empieza a capturar órdenes reales vía WhatsApp con OpenClaw. Meta mínima: 20 eventos en 60 horas. Usted y yo monitoreamos remotamente.
> 3. **Lunes 20-abr 08:00-16:00** — Auditoría conjunta del fin de semana. Le entrego Reporte de Auditoría firmado con los indicadores reales.
> 4. **Martes 21-abr** — Presento la experiencia en la universidad **citando a HGR No.1 IMSS Tijuana como cliente ancla validado**. Su nombre aparece como Socio Técnico del proyecto (con su autorización).
> 5. **Semanas 2-4** — Pilotaje extendido con 20-30 equipos reales de su inventario. Capacitación formal al equipo de técnicos (2 sesiones de 2 h).
> 6. **Mes 2** — Go-Live completo con trazabilidad NOM-016 desde día 1.
>
> *Todo esto sin que ustedes tengan que comprar licencias ni infraestructura nueva — corre en el ThinkCentre que ya tienen."*

### Preguntas probables y respuestas preparadas

| Pregunta | Respuesta |
|---|---|
| ¿Qué pasa si se va la luz? | La BD es MySQL local; al restaurar energía el sistema recupera sin pérdida. El log encadenado detecta cualquier corrupción. |
| ¿Se puede usar desde celular? | Sí — el frontend es responsive. Ya lo probamos en 375px de ancho. Además el QR se escanea desde cualquier cámara. |
| ¿Cómo migramos el inventario actual? | Importación masiva desde Excel. Tenemos script de migración probado. |
| ¿Quién da soporte? | Yo mismo durante el pilotaje. Después, documentación técnica + capacitación para que el equipo del hospital sea autosuficiente. |
| ¿Cuánto cuesta? | El software es gratuito (open-source interno). Solo requiere el servidor que ya tienen. El costo real es el tiempo de implementación. |

### Materiales a dejar con el Ing.

1. ☐ **`SIGAB_Resumen_Ejecutivo_Carlos_Oswaldo.pdf`** (copia impresa + digital en USB) — ⭐ PRIORIDAD
2. ☐ `SIGAB_DocInversionista_v3_Template.docx` (USB)
3. ☐ `SIGAB_Presentacion_Ejecutiva.pdf` (USB)
4. ☐ `PLAN_GO_LIVE_15ABR2026.md` (exportar a PDF)
5. ☐ Tarjeta con la **URL del dashboard de Clínica 1** (una vez configurada la IP fija) + credenciales temporales de Carlos
6. ☐ Mi número de WhatsApp + correo para incidencias del fin de semana

---

## 5 · Troubleshooting durante la demo

| Síntoma | Solución rápida |
|---|---|
| Login no responde | Verificar `curl http://localhost:8000/health` en otra terminal |
| Dashboard vacío | Refrescar con **Ctrl+Shift+R** (sin caché) |
| Modal cortado | Ya corregido en Fase 2 — si aparece, hacer scroll dentro del modal |
| Sidebar no abre en móvil | Botón hamburguesa arriba a la izquierda |
| Copilot no responde | Verificar Ollama: `curl http://localhost:11434/api/tags` — si falla, saltar la demo de Copilot y decir *"está en modo hot-reload"* |

---

## 6 · Notas post-demo (llenar después)

- Nivel de interés (1-5): ___
- Preguntas que hizo: _______________
- Compromisos asumidos: _______________
- Próximo contacto: _______________

---

## 7 · Traslado Quijarro → Clínica 1 (12:45 → 14:00 h)

- 12:45 — Cierre formal en Quijarro, pago de consumos, última foto con Carlos si aplica.
- 13:00 — Salir rumbo a Clínica 1 con el ThinkCentre en mochila acolchonada.
- 13:45 — Arribo a Clínica 1, saludo a personal de Conservación.
- 14:00 — Inicio del procedimiento de instalación → ver `OPERACION/Checklist_Instalacion_ThinkCentre_Clinica1.md`.

---

## 8 · Checkpoint final (domingo 19-abr 22:00 h)

Antes de dormir el domingo, confirmar:

- [ ] ≥ 20 eventos capturados en la BD del ThinkCentre (datos del fin de semana).
- [ ] Los 3 backups automáticos (sáb, dom, lun 02:00) están en disco.
- [ ] Carlos Oswaldo conformado con el piloto (vía WhatsApp).
- [ ] Capturas y reportes listos para la presentación del martes 21-abr.

---

*Documento preparado para la presentación ejecutiva de SIGAB V2.0 — 17 abril 2026 · 12:00 h · Café Quijarro + Instalación Clínica 1 HGR No.1 IMSS Tijuana.*
