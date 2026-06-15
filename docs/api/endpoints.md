# SIGAB API — Referencia de Endpoints

> **Base URL:** `http://localhost:8000/api`  
> **Autenticación:** Bearer Token (JWT) en header `Authorization`  
> **Content-Type:** `application/json`

---

## Autenticación (`/api/auth`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/auth/login` | Iniciar sesión con matrícula y contraseña | ❌ |
| `GET` | `/auth/me` | Obtener datos del usuario autenticado | ✅ |
| `POST` | `/auth/change-password` | Cambiar contraseña | ✅ |

**Login — Request:**
```json
{ "matricula": "ADMIN001", "password": "${ADMIN_PASSWORD}" }
```

**Login — Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "nombre": "Gustavo", "rol": "admin" }
}
```

---

## Dashboard (`/api/dashboard`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/dashboard/resumen` | KPIs generales (equipos, órdenes, alertas) |
| `GET` | `/dashboard/equipos` | Listado de equipos con filtros |
| `GET` | `/dashboard/mapa` | Zonas del hospital con equipos agrupados |
| `GET` | `/dashboard/fiabilidad` | Métricas MTBF/MTTR y disponibilidad |

**Parámetros de `/dashboard/equipos`:**
- `estado` — Filtrar por estado (`operativo`, `en_mantenimiento`, `fuera_servicio`)
- `area` — Filtrar por área hospitalaria
- `piso` — Filtrar por piso
- `buscar` — Búsqueda por nombre, serie, marca o modelo

---

## Equipos (`/api/equipos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/equipos` | Listado paginado con filtros |
| `GET` | `/equipos/{id}` | Detalle de un equipo |
| `POST` | `/equipos/` | Crear equipo nuevo |
| `PUT` | `/equipos/{id}` | Actualizar equipo |
| `DELETE` | `/equipos/{id}` | Eliminar equipo |
| `PATCH` | `/equipos/{id}/posicion` | Actualizar posición en mapa |
| `GET` | `/equipos/{id}/historial` | Historial de actividad |
| `POST` | `/equipos/{id}/imagen` | Subir imagen (multipart) |
| `GET` | `/equipos/areas/catalogo` | Catálogo de áreas |
| `GET` | `/equipos/zonas/catalogo` | Catálogo de zonas |

---

## Órdenes de Servicio (`/api/ordenes`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/ordenes` | Listado con filtros por estado/tipo |
| `GET` | `/ordenes/{id}` | Detalle con materiales y evidencias |
| `POST` | `/ordenes` | Crear nueva orden |
| `PUT` | `/ordenes/{id}/cerrar` | Cerrar orden |
| `PUT` | `/ordenes/{id}/estado` | Cambiar estado |
| `PUT` | `/ordenes/{id}/finalizar` | Finalizar con resolución |
| `POST` | `/ordenes/{id}/evidencia` | Subir evidencia fotográfica |
| `POST` | `/ordenes/ocr-scan` | Escanear formato físico con OCR |
| `GET` | `/ordenes/{id}/pdf` | Descargar PDF de la orden |

---

## Casillas CENEVAL (`/api/casillas`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/casillas/{orden_id}` | Obtener casillas de una OS |
| `POST` | `/casillas/{orden_id}` | Crear/actualizar casillas |
| `POST` | `/casillas/ocr/{orden_id}` | OCR de formato físico |
| `GET` | `/casillas/resumen/dominio` | Resumen por dominio |

---

## Alertas (`/api/alertas`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/alertas` | Todas las alertas |
| `GET` | `/alertas/pendientes` | Solo alertas no leídas |
| `PUT` | `/alertas/{id}/leer` | Marcar como leída |
| `PUT` | `/alertas/leer-todas` | Marcar todas como leídas |

---

## Trazabilidad (`/api/trazabilidad`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/trazabilidad` | Historial de movimientos |
| `GET` | `/trazabilidad/equipo/{id}` | Movimientos de un equipo |
| `POST` | `/trazabilidad` | Registrar traslado |

---

## Preventivos (`/api/preventivos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/preventivos` | Listado de preventivos programados |
| `PUT` | `/preventivos/{id}/ejecutar` | Marcar como ejecutado |

---

## Reportes (`/api/reportes`)

| Método | Ruta | Descripción | Formato |
|--------|------|-------------|---------|
| `GET` | `/reportes/diario` | Reporte del día | JSON |
| `GET` | `/reportes/equipos-criticos` | Equipos con alta criticidad | JSON |
| `GET` | `/reportes/historial?mes=4&anio=2026` | Historial mensual | JSON |
| `GET` | `/reportes/diario/pdf` | Reporte diario en PDF | blob |
| `GET` | `/reportes/diario/excel` | Reporte diario en Excel | blob |
| `GET` | `/reportes/historial/pdf?mes=4&anio=2026` | Historial en PDF | blob |
| `GET` | `/reportes/historial/excel?mes=4&anio=2026` | Historial en Excel | blob |

---

## Tecnovigilancia NOM-240 (`/api/tecnovigilancia`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/tecnovigilancia` | Listado de eventos adversos |
| `GET` | `/tecnovigilancia/{id}` | Detalle de evento |
| `POST` | `/tecnovigilancia` | Crear evento adverso |
| `PUT` | `/tecnovigilancia/{id}/estado` | Cambiar estado |
| `PUT` | `/tecnovigilancia/{id}/investigar` | Registrar investigación |
| `POST` | `/tecnovigilancia/{id}/escalar` | Escalar a COFEPRIS |
| `PUT` | `/tecnovigilancia/{id}/cerrar` | Cerrar con conclusión |
| `POST` | `/tecnovigilancia/{id}/evidencia` | Subir evidencia |
| `GET` | `/tecnovigilancia/{id}/pdf` | Descargar reporte NOM-240 |

---

## Copilot IA (`/api/copilot`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/copilot/estado` | Estado del modelo local |
| `GET` | `/copilot/prompts-rapidos` | Sugerencias de preguntas |
| `POST` | `/copilot/diagnostico` | Solicitar diagnóstico IA |
| `POST` | `/copilot/causa-raiz` | Análisis de causa raíz |
| `GET` | `/copilot/resumen-ia` | Resumen ejecutivo generado |
| `POST` | `/copilot/chat` | Chat streaming (SSE) |

---

## Almacén (`/api/almacen`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/almacen/` | Listado de refacciones |
| `POST` | `/almacen/` | Crear refacción |
| `PUT` | `/almacen/{id}/ajustar` | Ajustar stock |

**Parámetros de filtro:** `busqueda`, `stock_bajo=true`

---

## Metrología (`/api/metrologia`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/metrologia/` | Listado de calibraciones |
| `POST` | `/metrologia/` | Registrar nueva calibración |

---

## Capacitaciones (`/api/capacitaciones`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/capacitaciones/` | Listado de registros de formación |
| `POST` | `/capacitaciones/` | Crear registro de capacitación |

---

## Auditoría NOM-016 (`/api/auditoria`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/auditoria/` | Log de auditoría con hashes SHA-256 |
| `GET` | `/auditoria/verificar` | Verificar integridad de la cadena |
| `GET` | `/auditoria/pdf` | Descargar bitácora en PDF |

---

## Checklists NOM-016 (`/api/checklists`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/checklists/templates` | Plantillas de verificación |
| `GET` | `/checklists/resultados` | Historial de compliance |
| `POST` | `/checklists/ejecutar` | Ejecutar y certificar checklist |

---

## Health Check

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del sistema |

**Response:** `{ "status": "ok", "sistema": "SIGAB", "modo": "on-premise" }`

---

## Códigos de Error Comunes

| Código | Significado |
|--------|-------------|
| `401` | Token ausente, expirado o inválido |
| `403` | Permisos insuficientes para la operación |
| `404` | Recurso no encontrado |
| `422` | Datos de entrada inválidos (validación Pydantic) |
| `500` | Error interno del servidor |
