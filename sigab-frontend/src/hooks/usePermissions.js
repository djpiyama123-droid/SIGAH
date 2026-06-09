/**
 * usePermissions — Espejo del backend auth/permissions.py.
 *
 * Mantener sincronizado con:
 *   sigab-backend/auth/permissions.py → ROLE_PERMISSIONS
 *
 * Uso:
 *   const { can, campos } = usePermissions();
 *   if (can('delete_equipo')) { ... }
 */
import { useAuth } from '../context/AuthContext';

// Espejo exacto de ROLE_PERMISSIONS en auth/permissions.py
const ROLE_PERMISSIONS = {
  view_public: new Set([
    'biomedico', 'supervisor', 'jefe_servicio',
    'jefe_conservacion', 'jefe_biomedica', 'almacen', 'admin',
  ]),
  view_confidential: new Set([
    'biomedico', 'supervisor', 'jefe_servicio',
    'jefe_conservacion', 'jefe_biomedica', 'admin',
  ]),
  create_equipo: new Set([
    'supervisor', 'jefe_servicio', 'jefe_conservacion',
    'jefe_biomedica', 'admin',
  ]),
  edit_equipo: new Set([
    'biomedico', 'supervisor', 'jefe_servicio',
    'jefe_conservacion', 'jefe_biomedica', 'admin',
  ]),
  delete_equipo: new Set([
    'jefe_conservacion', 'jefe_biomedica', 'admin',
  ]),
  regenerar_qr: new Set([
    'supervisor', 'jefe_servicio', 'jefe_conservacion',
    'jefe_biomedica', 'admin',
  ]),
  admin_usuarios: new Set([
    'jefe_biomedica', 'admin',
  ]),
};

// Campos editables por biomedico (subconjunto restringido)
const CAMPOS_BIOMEDICO_EDITABLES = new Set([
  'estado', 'ubicacion', 'piso', 'area',
  'fecha_ultimo_mantenimiento', 'pos_x', 'pos_y',
]);

// Campos confidenciales que no deben mostrarse en vista pública QR
const CAMPOS_CONFIDENCIALES = new Set([
  'numero_contrato', 'numero_contrato_servicio', 'proveedor_servicio',
  'fecha_compra', 'fecha_instalacion', 'clase_cofepris',
  'vida_util_anios', 'created_at', 'updated_at',
]);

export function usePermissions() {
  const { user } = useAuth();
  const rol = user?.rol ?? null;

  /**
   * Devuelve true si el usuario actual tiene permiso para `action`.
   * view_public es true incluso para anónimos.
   */
  function can(action) {
    if (action === 'view_public') return true;
    if (!rol) return false;
    return ROLE_PERMISSIONS[action]?.has(rol) ?? false;
  }

  /**
   * Devuelve el conjunto de campos que el usuario puede editar
   * en el formulario de equipo (espejo de allowed_update_fields).
   */
  function allowedUpdateFields() {
    if (rol === 'biomedico') return new Set(CAMPOS_BIOMEDICO_EDITABLES);
    // Todos los demás roles autorizados para edit_equipo reciben el set completo
    return null; // null = sin restricción (el backend valida el subconjunto)
  }

  /**
   * True si el campo NO debe mostrarse en la vista pública de escaneo QR.
   */
  function esConfidencial(campo) {
    return CAMPOS_CONFIDENCIALES.has(campo);
  }

  return {
    can,
    allowedUpdateFields,
    esConfidencial,
    rol,
    // Atajos comunes
    esAdmin: rol === 'admin',
    esJefe: rol === 'jefe_biomedica' || rol === 'jefe_conservacion' || rol === 'jefe_servicio',
    esBiomedico: rol === 'biomedico',
    esAlmacen: rol === 'almacen',
    esSupervisor: rol === 'supervisor',
  };
}
