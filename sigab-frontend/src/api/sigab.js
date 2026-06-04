/**
 * @module api/sigab
 * @description Cliente HTTP centralizado del frontend SIGAB.
 *
 * Provee un objeto `api` con métodos para todos los endpoints del backend.
 * Utiliza Axios con interceptores automáticos para:
 * - Inyección del token JWT en cada request (header Authorization)
 * - Extracción de `response.data` (evita `.data.data` en cada llamada)
 * - Gestión de blobs para descargas PDF/Excel (responseType: 'blob')
 *
 * Patrón de uso:
 *   import { api } from '../api/sigab';
 *   const equipos = await api.getEquipos({ estado: 'operativo' });
 *
 * @requires axios
 */
import axios from 'axios';

// Cliente axios con proxy via Vite (/api → localhost:8000/api)
const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor de petición para agregar el token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de respuesta para manejar 401
client.interceptors.response.use(
  (res) => res.data,
  async (err) => {
    if (err.response?.status === 401) {
      // Opcional: manejar lógica de refresh_token aquí
      // Por ahora deslogueamos (redirección se maneja a nivel router)
      const isAuthError = err.config.url.startsWith('/auth');
      if (!isAuthError) {
         console.warn('No autorizado, token expirado o inválido.');
         localStorage.removeItem('token');
         localStorage.removeItem('user');
         window.location.href = '/login';
      }
    }
    console.error('SIGAB API Error:', err.response?.status, err.config?.url);
    return Promise.reject(err);
  }
);

export const api = {
  // ── Auth ──────────────────────────────────────────────────
  login: (data) => client.post('/auth/login', data),
  getMe: () => client.get('/auth/me'),
  changePassword: (data) => client.post('/auth/change-password', data),

  // ── Dashboard ─────────────────────────────────────────────
  getDashboard: () => client.get('/dashboard/resumen'),
  getDashboardEquipos: (params = {}) =>
    client.get('/dashboard/equipos', { params }),
  getMapaEquipos: () => client.get('/dashboard/mapa'),
  getFiabilidad: () => client.get('/dashboard/fiabilidad'),

  // ── Equipos ───────────────────────────────────────────────
  getEquipos: (params = {}) => client.get('/equipos', { params }),
  getEquipo: (id) => client.get(`/equipos/${id}`),
  crearEquipo: (data) => client.post('/equipos/', data),
  updateEquipo: (id, data) => client.put(`/equipos/${id}`, data),
  eliminarEquipo: (id) => client.delete(`/equipos/${id}`),
  updateEquipoPosicion: (id, data) => client.patch(`/equipos/${id}/posicion`, data),
  getAreasCatalogo: () => client.get('/equipos/areas/catalogo'),
  getZonasCatalogo: () => client.get('/equipos/zonas/catalogo'),
  getHistorialEquipo: (id) => client.get(`/equipos/${id}/historial`),
  subirImagenEquipo: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post(`/equipos/${id}/imagen`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // ── Órdenes ───────────────────────────────────────────────
  getOrdenes: (params = {}) => client.get('/ordenes', { params }),
  getArchivosHistoricos: (params = {}) => client.get('/ordenes/archivos-historicos', { params }),
  getOrden: (id) => client.get(`/ordenes/${id}`),
  crearOrden: (data) => client.post('/ordenes', data),
  cerrarOrden: (id) => client.put(`/ordenes/${id}/cerrar`),
  cambiarEstadoOrden: (id, estado) =>
    client.put(`/ordenes/${id}/estado`, { estado }),
  subirEvidenciaOrden: (id, tipo, descripcion, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post(`/ordenes/${id}/evidencia?tipo=${tipo}&descripcion=${descripcion}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  scanOCR: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/ordenes/ocr-scan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  finalizarOrden: (id, data) => client.put(`/ordenes/${id}/finalizar`, data),
  getPdfOrdenUrl: (id) => `${client.defaults.baseURL}/ordenes/${id}/pdf`,

  // ── Casillas CENEVAL (Conservación) ──────────────────────
  getCasillas: (ordenId) => client.get(`/casillas/${ordenId}`),
  upsertCasillas: (ordenId, data) => client.post(`/casillas/${ordenId}`, data),
  ocrCasillas: (ordenId, file) => {
    const formData = new FormData();
    formData.append('foto', file);
    return client.post(`/casillas/ocr/${ordenId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
  },
  getResumenCasillas: () => client.get('/casillas/resumen/dominio'),
  // Helper para uso directo por URL desde OrdenCasillasForm
  post: (url, data) => client.post(url, data),
  postForm: (url, formData) =>
    client.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 }),

  // ── Alertas ───────────────────────────────────────────────
  getAlertas: (params = {}) => client.get('/alertas', { params }),
  getAlertasPendientes: () => client.get('/alertas/pendientes'),
  marcarLeida: (id) => client.put(`/alertas/${id}/leer`),
  marcarTodasLeidas: () => client.put('/alertas/leer-todas'),

  // ── Trazabilidad ──────────────────────────────────────────
  getTrazabilidad: (params = {}) => client.get('/trazabilidad', { params }),
  getTrazabilidadEquipo: (id) => client.get(`/trazabilidad/equipo/${id}`),
  registrarTraslado: (data) => client.post('/trazabilidad', data),

  // ── Preventivos ───────────────────────────────────────────
  getPreventivos: (params = {}) => client.get('/preventivos', { params }),
  ejecutarPreventivo: (id) => client.put(`/preventivos/${id}/ejecutar`),

  // ── Reservas ──────────────────────────────────────────────
  getReservas: () => client.get('/reservas'),
  crearReserva: (data) => client.post('/reservas', data),

  // ── Reportes ──────────────────────────────────────────────
  getReporteDiario: () => client.get('/reportes/diario'),
  getEquiposCriticos: () => client.get('/reportes/equipos-criticos'),
  getHistorialOrdenes: (mes, anio) =>
    client.get('/reportes/historial', { params: { mes, anio } }),

  // ── Exportación PDF / Excel ────────────────────────────────
  descargarReporteDiarioPdf:   () => client.get('/reportes/diario/pdf',     { responseType: 'blob' }),
  descargarReporteDiarioExcel: () => client.get('/reportes/diario/excel',   { responseType: 'blob' }),
  descargarHistorialPdf:   (mes, anio) => client.get('/reportes/historial/pdf',   { responseType: 'blob', params: { mes, anio } }),
  descargarHistorialExcel: (mes, anio) => client.get('/reportes/historial/excel', { responseType: 'blob', params: { mes, anio } }),

  // ── Tecnovigilancia (NOM-240) ─────────────────────────────────
  getEventos: (params = {}) => client.get('/tecnovigilancia', { params }),
  getEvento: (id) => client.get(`/tecnovigilancia/${id}`),
  crearEvento: (data) => client.post('/tecnovigilancia', data),
  cambiarEstadoEvento: (id, estado) =>
    client.put(`/tecnovigilancia/${id}/estado`, { estado }),
  investigarEvento: (id, data) =>
    client.put(`/tecnovigilancia/${id}/investigar`, data),
  escalarEvento: (id, folio_cofepris) =>
    client.post(`/tecnovigilancia/${id}/escalar`, { folio_cofepris }),
  cerrarEvento: (id, conclusion) =>
    client.put(`/tecnovigilancia/${id}/cerrar`, { conclusion }),
  subirEvidenciaEvento: (id, tipo, descripcion, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post(
      `/tecnovigilancia/${id}/evidencia?tipo=${tipo}&descripcion=${encodeURIComponent(descripcion)}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },
  descargarPdfNom240: (id) =>
    client.get(`/tecnovigilancia/${id}/pdf`, { responseType: 'blob' }),

  // ── SIGAB Copilot (IA Local Gemma + fallback MiniMax) ─────────
  getCopilotEstado: () => client.get('/copilot/estado'),
  getCopilotEstadoEdge: () => client.get('/copilot/estado-edge'),
  getCopilotPromptsRapidos: () => client.get('/copilot/prompts-rapidos'),
  copilotDiagnostico: (data) => client.post('/copilot/diagnostico', data),
  copilotCausaRaiz: (data) => client.post('/copilot/causa-raiz', data),
  copilotResumenIa: () => client.get('/copilot/resumen-ia'),
  copilotVision: (data) => client.post('/copilot/vision', data),
  // El chat usa fetch nativo por streaming SSE (no axios)
  // Ver: chatStreamUrl en la página Copilot
  getCopilotChatUrl: () => '/api/copilot/chat',

  // ── Almacén de Refacciones ─────────────────────────────────
  getAlmacen: (params = {}) => client.get('/almacen/', { params }),
  crearRefaccion: (data) => client.post('/almacen/', data),
  ajustarStock: (id, data) => client.put(`/almacen/${id}/ajustar`, data),

  // ── Metrología y Calibración ───────────────────────────────
  getMetrologia: () => client.get('/metrologia/'),
  crearCalibracion: (data) => client.post('/metrologia/', data),

  // ── Capacitación de Personal ───────────────────────────────
  getCapacitaciones: () => client.get('/capacitaciones/'),
  crearCapacitacion: (data) => client.post('/capacitaciones/', data),

  // ── Auditoría NOM-016 ──────────────────────────────────────
  getAuditLogs: () => client.get('/auditoria/'),
  verificarCadena: () => client.get('/auditoria/verificar'),
  descargarBitacoraPdf: () => client.get('/auditoria/pdf', { responseType: 'blob' }),

  // ── Checklists NOM-016 ─────────────────────────────────────
  getChecklistTemplates: () => client.get('/checklists/templates'),
  getChecklistResultados: () => client.get('/checklists/resultados'),
  ejecutarChecklist: (data) => client.post('/checklists/ejecutar', data),
};
