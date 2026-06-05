# Decisión IA — Minimax M3 (plan vs. tokens) + justificación del servidor GE on-premise

> **Tipo:** Análisis de decisión + material para ficha técnica de venta.
> **Fecha:** Junio 2026 · **Estado:** Recomendación lista para validar.
> **HGR No.1 IMSS Tijuana — NOM-016 / NOM-240 / ISO-13485.**

---

## 1. Contexto

SIGAH usa IA en dos planos:
- **Local (on-premise):** modelos OSS chicos en el servidor del hospital, para **datos sensibles**.
- **Nube (Minimax):** modelo frontera para razonamiento pesado, búsqueda web de manuales,
  multimodal (imagen/video) y el agente **Hermes** (dev/IT).

Este documento decide **(A)** qué modelo de Minimax usar, **(B)** si conviene **plan mensual o
tokens (API pago por uso)**, y **(C)** cómo el **servidor GE** reduce costos de dominio, nube de
datos y tokens.

---

## 2. Minimax M3 — qué es y por qué importa (verificado jun-2026)

**Minimax M3** salió el **31 de mayo de 2026** (anuncio 1-jun). Es el salto que mencionaste:

| Característica | Detalle |
|----------------|---------|
| Multimodal nativo | **Texto + imagen + video** de entrada, texto de salida |
| Contexto | **1,000,000 de tokens** (1M) — atención dispersa MSA |
| Agéntico | BrowseComp **83.5**, supera a Opus 4.7 (79.3) → fuerte para Hermes y búsqueda web |
| Código/Matemáticas | ~95% en ambos (percentiles 91 y 86) |
| Pesos | **Open-weight** (disponible incluso en Ollama) → opción futura de auto-hospedar |
| Costo | **5–10% del costo** de GPT-5.5 / Gemini 3.1 Pro para rendimiento comparable |

**Para SIGAH esto es ideal:** lo multimodal sirve para analizar **fotos de equipos/etiquetas y
videos de fallas** que mandan los médicos por WhatsApp; el contexto 1M permite cargar manuales
completos; y lo agéntico potencia a Hermes.

> Nota: las tablas de LMArena para M3 aún estaban "pendientes" a inicios de junio; los puestos
> top que circulan vienen de benchmarks de coding/agente, donde M3 sí está en la cima por costo.

### 2.1 Precios M3 (API pago por uso)

- **Estándar:** **$0.60 / 1M tokens entrada** · **$2.40 / 1M tokens salida**.
- **Promo de lanzamiento (~50% off):** ≈ $0.30 entrada · $1.20 salida.
- Tier por contexto (≤512K vs >512K) en la API directa de Minimax.

### 2.2 Planes mensuales (Agent)

- **Agent básico:** **$19/mes** ≈ 10,000 créditos (~30 tareas agénticas).
- **Agent pro:** **$69/mes** ≈ 40,000 créditos (~120 tareas).
- Plan *lightning* gratuito para pruebas.

> (Mencionaste $20 y $50; los precios oficiales vigentes son **$19 y $69**.)

---

## 3. Decisión clave: ¿Plan mensual o Tokens (API)? 

### 3.1 Cómo usa SIGAH la nube (patrón de consumo)

El **grueso del trabajo corre LOCAL** (app, BD, bot, inferencia chica). La nube Minimax es la
**excepción**, no la regla. Dos perfiles muy distintos:

| Consumidor | Patrón | Naturaleza |
|------------|--------|------------|
| **SIGAB Bot (WhatsApp)** | Muchas consultas chicas, esporádicas (1 pregunta = 1 llamada) | Por llamada |
| **Hermes (dev/IT)** | Pocas tareas, multi-paso, autónomas (diagnosticar bug → reparar → deploy) | Por "tarea" agéntica |

### 3.2 Matemática de punto de equilibrio

Una tarea agéntica típica de Hermes ≈ 50K entrada + 10K salida.
- Costo por tarea (estándar) ≈ (0.05 × $0.60) + (0.01 × $2.40) = **~$0.054** (con promo ~$0.03).
- 30 tareas/mes por tokens ≈ **$1.6–2.7**. El **plan básico cuesta $19** por esas mismas ~30.
- Una consulta de WhatsApp (~3K entrada + 0.5K salida) ≈ **$0.003** → **1,000 consultas ≈ $3**.

**Conclusión numérica:** con volumen bajo/medio (un hospital arrancando), **tokens es 5–10×
más barato** que el plan mensual.

### 3.3 Recomendación para SIGAB

> ✅ **Default: API pago por uso (tokens) con M3 + tope de presupuesto duro.**

**Por qué tokens es el mejor caso para SIGAB hoy:**
1. **Volumen incierto y esporádico** — pagás solo lo que usás; sin desperdicio de cuota fija.
2. **M3 es barato** — miles de consultas cuestan pocos dólares.
3. **Sin compromiso** mientras se valida con el primer hospital.
4. **Granular y auditable** — cada llamada queda en `log_actividad` con su costo.

**Cómo se controla el riesgo de "presupuesto que se sale" (tu preocupación):**
- **Tope mensual duro** en la cuenta Minimax + alertas al 50/80/100%.
- **Ruteo a local primero:** el backend manda a la nube **solo** lo que no puede resolver el
  modelo local → minimiza llamadas pagas por diseño (ver §4).
- **Caché de respuestas** frecuentes (manuales ya consultados) para no re-pagar.

**Cuándo migrar a plan mensual:**
- Cuando el consumo medido **supere el punto de equilibrio** (~$19/mes ≈ 350+ tareas Hermes o
  uso intensivo sostenido), o
- Si Hermes empieza a usar el **runtime de agente** de la plataforma (navegador/sandbox
  incluidos), donde el plan aporta más que solo tokens.

> 📌 **Regla práctica:** empezar con **tokens + tope**; revisar el gasto real cada mes; cambiar a
> plan solo cuando los números lo justifiquen. Decisión basada en datos, no en suposiciones.

---

## 4. Justificación del servidor GE en la ficha técnica (ahorro real)

La ficha técnica de venta lista 3 herramientas a comprar **+ servidor**. La propuesta:
**reutilizar la PC GE (Xeon) como servidor on-premise reemplaza la línea "servidor"** y, además,
**elimina costos recurrentes de nube y dominio**.

### 4.1 Herramientas de la ficha técnica (propuesta)

| # | Herramienta | Función | ¿Se compra? |
|---|-------------|---------|-------------|
| 1 | **Pistola lectora QR / código de barras** (Zebra) | Escanear equipos en campo, alta rápida | ✅ Sí |
| 2 | **Grabadora láser** | Grabar etiquetas QR permanentes en equipos (trazabilidad NOM-016) | ✅ Sí |
| 3 | **Scanner de documentos** | Digitalizar formatos físicos, manuales, reportes | ✅ Sí |
| 4 | **Servidor on-premise** | Hostear BD + app + bot + IA local | ♻️ **Reusar PC GE → $0** |

### 4.2 Lo que se EVITA pagar al usar la PC GE

| Costo evitado | Alternativa cara | Con servidor GE |
|---------------|------------------|-----------------|
| **Servidor nuevo** | Lenovo/Dell server $13,500–60,000 MXN | **$0** (activo existente) |
| **Hosting/dominio público** | VPS + dominio $200–1,500 MXN/mes | **$0** (dominio interno LAN) |
| **Nube para datos** | Almacenamiento + BD gestionada en nube | **$0** (datos locales, + cumple NOM/ISO) |
| **Tokens excesivos** | Todo el razonamiento en la nube | **Mínimo** (inferencia local resuelve el grueso; nube solo lo pesado) |

### 4.3 Argumento de venta (para la landing/ficha técnica)

> "SIGAH corre **dentro del hospital**, sobre un servidor que el hospital ya posee. Sus datos
> clínicos **nunca salen** de sus instalaciones (NOM-016/NOM-240/ISO-13485), no paga renta de
> nube ni de dominio, y la IA pesada se contrata **por uso** con tope de presupuesto — sin
> sorpresas. La inteligencia local resuelve la mayoría de consultas sin costo por token."

Esto convierte una **limitación** (hardware viejo) en un **diferenciador comercial**: menor costo
total de propiedad (TCO) + soberanía de datos.

---

## 5. Resumen de decisiones

| Pregunta | Decisión |
|----------|----------|
| ¿Qué modelo de nube? | **Minimax M3** (multimodal, 1M ctx, agéntico, barato) |
| ¿Plan o tokens? | **Tokens (API pago por uso) + tope duro**; plan solo si el volumen lo justifica |
| ¿Servidor? | **Reusar PC GE** → reemplaza compra de servidor y costos de nube/dominio |
| ¿IA local? | Modelos OSS chicos (Gemma/Qwen 7-8B) para datos sensibles; nube solo lo pesado |

---

## Fuentes (jun-2026)

- [MiniMax M3 — Frontier Coding, 1M Context, Native Multimodality (oficial)](https://www.minimax.io/blog/minimax-m3)
- [MiniMax M3 debuts, eclipsing GPT-5.5 and Gemini 3.1 Pro… (VentureBeat)](https://venturebeat.com/technology/minimax-m3-debuts-eclipsing-gpt-5-5-and-gemini-3-1-pro-on-key-benchmark-performance-for-just-5-10-of-the-cost)
- [MiniMax M3 API Pricing 2026 (pricepertoken)](https://pricepertoken.com/pricing-page/model/minimax-minimax-m3)
- [MiniMax M3 — pricing & benchmarks (OpenRouter)](https://openrouter.ai/minimax/minimax-m3)
- [MiniMax API Docs — Product Pricing / Pay as You Go](https://platform.minimax.io/docs/pricing/overview)

_Documento vivo. Se actualiza con el consumo real medido tras el arranque._
