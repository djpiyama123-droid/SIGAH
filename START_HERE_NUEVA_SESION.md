# START HERE — Nueva Sesión Claude Code SIGAB

> Lee este archivo **primero** en cada sesión automatizada o manual antes de editar cualquier código.

---

## Repositorio
- **Proyecto:** SIGAB — Sistema Integral de Gestión de Activos Biomédicos V2.0
- **Hospital:** HGR No. 1, IMSS Tijuana, B.C., México
- **Stack:** FastAPI + Python 3.12 / React 19 + Vite + Tailwind / MySQL 8.0 / Ollama edge IA
- **Repo GitHub:** `djpiyama123-droid/sigah` (privado)

---

## GOAL Activo (Industria 4.0)

Profundizar la justificación e implementar en SIGAB 4 componentes I4.0:

1. **Escáner MIRACO Plus** — metrología 3D, escaneo de activos biomédicos
2. **Pistola grabadora láser** — marcado UDI permanente, trazabilidad GS1
3. **Nodo edge IA (Ollama)** — Lenovo ThinkCentre M720q con fallback MiniMax cloud
4. **Dominio .mx + API IA bots** — presencia web + NLP para bot WhatsApp

Ver detalle económico y técnico en: **`JUSTIFICACION_INVERSION.md`**

---

## Workstreams y Estado

| WS | Nombre | Estado | Siguiente acción |
|----|--------|--------|-----------------|
| WS-1 | Justificación inversión (ROI/CAPEX-OPEX) | Base en `JUSTIFICACION_INVERSION.md` | Actualizar con datos reales de piloto |
| WS-2 | Trazabilidad activos (UDI + escaneo 3D) | Pendiente | SQL migration + endpoints + badge |
| WS-3 | Integración nodo edge IA + fallback cloud | **COMPLETADO** (2026-06-04) | Ver PR `auto/avance-2026-06-04-0001` |
| WS-4 | Costos dominio + panel consumo tokens | Pendiente | Tabla `ia_token_log` + Dashboard widget |
| WS-5 | Calidad continua (tests/lint/docs) | Continuo | pytest para `/edge-status` |

---

## Reglas Duras (NUNCA olvidar)

1. **PROHIBIDO desplegar.** No ejecutar `deploy.sh`, `deploy-vps.sh`, ssh/rsync al VPS `129.121.100.147`.
2. **PROHIBIDO push a main/master.** Siempre crear rama `auto/avance-AAAA-MM-DD-HHMM`.
3. No reescribir historia, no force push, no tocar `.env` ni credenciales reales.
4. Ante ambigüedad: documentar en el PR, no adivinar.

---

## Orientación Rápida de Archivos

```
SIGAH/
├── JUSTIFICACION_INVERSION.md   ← WS-1: ROI/CAPEX-OPEX de 4 componentes I4.0
├── START_HERE_NUEVA_SESION.md   ← Este archivo
├── PROMPT_ANCLA.md              ← Estado del GOAL y bitácora de sesiones
├── CLAUDE.md                    ← Contexto stack, skills, convenciones
│
├── sigab-backend/
│   ├── config.py                ← Vars de entorno (incluye MINIMAX_*, AI_PROVIDER)
│   ├── services/gemma_service.py ← IA edge+cloud (WS-3 implementado)
│   └── routes/copilot.py        ← Endpoints IA (incluye /edge-status)
│
├── sigab-frontend/src/pages/
│   ├── Metrologia.jsx           ← Pendiente: badge escaneo 3D (WS-2)
│   ├── Equipos.jsx              ← Pendiente: badge UDI grabado (WS-2)
│   └── Dashboard.jsx            ← Pendiente: panel consumo tokens IA (WS-4)
│
└── docs/
    ├── estudios_economicos/     ← Costos, VPN, TIR, inversión inicial
    └── estudios_tecnicos/       ← Sección 3.2 maquinaria y equipo
```

---

## Antes de Empezar Cada Sesión

```bash
git status
git branch -a
git log --oneline -10
# Verificar ramas auto/avance-* previas para no duplicar trabajo
```

---

## Convenciones del Proyecto

- Idioma UI: **español mexicano**
- Toast: `toast.success/error/loading`
- Colores estado: `emerald`=operativo, `amber`=mantenimiento, `red`=fuera_servicio, `slate`=baja
- Audit trail: tabla `log_actividad` con SHA-256 encadenado
- Máquinas de estado: dict `TRANSICIONES` en backend
- Folios: `SIGAB-HGR1-YYYYMMDD-HHMM-NNNN`
