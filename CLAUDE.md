# SIGAH — Claude Code Project Context

## Proyecto
**SIGAH — Sistema Integral de Activos Hospitalarios**
Plataforma SaaS B2B multi-tenant para gestión de activos biomédicos hospitalarios.
NOM-016 / NOM-240 / ISO-13485

**Este repositorio es la plataforma SIGAH SaaS** — multi-tenant, cloud-native (Hetzner).
La instancia on-premise para HGR No.1 IMSS Tijuana vive en el repo legacy SIGAB (`/mnt/c/Users/djpiy/Desktop/Bioingeneria/SIGAB`).

## Stack Tecnológico
- **Backend**: FastAPI + Python 3.12 + MySQL 8.0
- **Frontend**: React 19 + Vite + Tailwind CSS
- **IA**: arquitectura híbrida — Gemini 2.5 Flash-Lite + Claude Sonnet 4.6
- **Infraestructura**: Hetzner Cloud (CX32/CX42) + Edge Nodes por hospital
- **Contenedores**: Docker Compose

## Estructura del Proyecto
```
sigah-backend/      # FastAPI routes, services, models
sigah-frontend/     # React pages, components, hooks
sigah-bot/          # Bot de notificaciones
migrations/         # SQL migrations
docs/               # Documentación estratégica SIGAH
  adr/              # Architecture Decision Records
  notas/            # Notas de sesión (vault Obsidian)
  sprints/          # Planning de sprints
.claude/skills/     # Skills del proyecto
.agents/skills/     # Skills mattpocock instaladas
```

## Fases de desarrollo SIGAH SaaS
- **Fase 0 (actual):** Constitución legal S. de R.L. de C.V. + RESICO PM, rebrand, infra Hetzner
- **Fase 1:** columna `tenant_id` en todas las tablas + tabla `hospitales` (tenants)
- **Fase 2:** dependencia `get_current_tenant` en FastAPI + filtrado JWT por `hospital_id`
- **Fase 3:** rol SuperAdmin + panel `/admin-global`
- **Fase 4:** despliegue en Hetzner + Edge Nodes
- **Fase 5:** módulo de Formatos (4 plantillas NOM)
- **Fase 6:** facturación SaaS (Setup Fee + mensualidad), CFDI 4.0 vía PAC

## Convenciones
- Todos los textos en **español mexicano** (UI y mensajes)
- Toast notifications con `toast.success/error/loading`
- Colores de estado: emerald=operativo, amber=mantenimiento, red=fuera_servicio, slate=baja
- Máquinas de estado con dict `TRANSICIONES` en backend
- Audit trail en tabla `log_actividad` para NOM-016
- **Paleta SIGAH**: azul (#006CB7), azul oscuro (#00497D), verde biomédico (emerald-600)

## Skills disponibles (invocar con /)
| Skill | Uso |
|---|---|
| `/grill-me` | Interrogatorio antes de construir algo nuevo |
| `/grill-with-docs` | Grill-me + actualiza CONTEXT.md y ADRs |
| `/to-prd` | Convierte conversación en PRD |
| `/to-issues` | Rompe plan en issues |
| `/triage` | Triaje de bugs/features |
| `/tdd` | Desarrollo TDD |
| `/diagnose` | Debug disciplinado |
| `/prototype` | Prototipo desechable |
| `/handoff` | Compacta sesión para handoff |
| `/zoom-out` | Vista de alto nivel |
| `/caveman` | Modo ultra-comprimido |
