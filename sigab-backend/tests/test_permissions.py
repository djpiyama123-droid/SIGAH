"""
Tests unitarios para auth/permissions.py.

Sin dependencias de BD ni red — la lógica de permisos es Python puro.
Ejecutar con: cd sigab-backend && pytest tests/test_permissions.py -v
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.permissions import (
    can,
    filter_equipo_publico,
    allowed_update_fields,
    CAMPOS_CONFIDENCIALES,
    CAMPOS_BIOMEDICO_EDITABLES,
    CAMPOS_EDITABLES_TODOS,
    ROLE_PERMISSIONS,
)

# ── Fixtures helpers ──────────────────────────────────────────────

def user(rol: str) -> dict:
    return {"id": 1, "rol": rol, "nombre": "Test", "activo": True}


# ── can() ─────────────────────────────────────────────────────────

class TestCan:
    def test_view_public_sin_usuario(self):
        assert can(None, "view_public") is True

    def test_view_public_con_cualquier_rol(self):
        for rol in ROLE_PERMISSIONS["view_public"]:
            assert can(user(rol), "view_public") is True

    def test_view_confidential_biomedico(self):
        assert can(user("biomedico"), "view_confidential") is True

    def test_view_confidential_almacen_denegado(self):
        assert can(user("almacen"), "view_confidential") is False

    def test_create_equipo_supervisor(self):
        assert can(user("supervisor"), "create_equipo") is True

    def test_create_equipo_biomedico_denegado(self):
        assert can(user("biomedico"), "create_equipo") is False

    def test_delete_equipo_admin(self):
        assert can(user("admin"), "delete_equipo") is True

    def test_delete_equipo_supervisor_denegado(self):
        assert can(user("supervisor"), "delete_equipo") is False

    def test_admin_usuarios_solo_jefe_y_admin(self):
        assert can(user("jefe_biomedica"), "admin_usuarios") is True
        assert can(user("admin"), "admin_usuarios") is True
        assert can(user("supervisor"), "admin_usuarios") is False
        assert can(user("biomedico"), "admin_usuarios") is False

    def test_regenerar_qr_permisos(self):
        roles_con_permiso = {"supervisor", "jefe_servicio", "jefe_conservacion", "jefe_biomedica", "admin"}
        for rol in roles_con_permiso:
            assert can(user(rol), "regenerar_qr") is True, f"Fallo en rol: {rol}"
        assert can(user("biomedico"), "regenerar_qr") is False
        assert can(user("almacen"), "regenerar_qr") is False

    def test_accion_desconocida_deniega(self):
        assert can(user("admin"), "accion_que_no_existe") is False

    def test_usuario_sin_rol_deniega(self):
        assert can({"id": 1, "nombre": "Sin Rol"}, "view_confidential") is False

    def test_usuario_none_en_accion_privada(self):
        assert can(None, "create_equipo") is False


# ── filter_equipo_publico() ───────────────────────────────────────

class TestFilterEquipoPublico:
    BASE_EQUIPO = {
        "id": 42,
        "nombre": "Ventilador Puritan Bennett 840",
        "serie": "SN-12345",
        "inventario": "INV-001",
        "estado": "operativo",
        "area": "UCI",
        "piso": "2",
        # campos confidenciales:
        "numero_contrato": "CTR-2024-001",
        "numero_contrato_servicio": "SVC-001",
        "proveedor_servicio": "Medline S.A.",
        "fecha_compra": "2022-01-15",
        "fecha_instalacion": "2022-01-20",
        "clase_cofepris": "III",
        "vida_util_anios": 10,
        "created_at": "2022-01-20T10:00:00",
        "updated_at": "2024-06-01T09:00:00",
    }

    def test_elimina_campos_confidenciales(self):
        resultado = filter_equipo_publico(self.BASE_EQUIPO)
        for campo in CAMPOS_CONFIDENCIALES:
            assert campo not in resultado, f"Campo confidencial expuesto: {campo}"

    def test_preserva_campos_publicos(self):
        resultado = filter_equipo_publico(self.BASE_EQUIPO)
        assert resultado["id"] == 42
        assert resultado["nombre"] == "Ventilador Puritan Bennett 840"
        assert resultado["estado"] == "operativo"
        assert resultado["area"] == "UCI"

    def test_no_muta_original(self):
        original = dict(self.BASE_EQUIPO)
        filter_equipo_publico(original)
        assert "numero_contrato" in original

    def test_equipo_vacio_devuelve_vacio(self):
        assert filter_equipo_publico({}) == {}

    def test_equipo_none_devuelve_none(self):
        assert filter_equipo_publico(None) is None


# ── allowed_update_fields() ───────────────────────────────────────

class TestAllowedUpdateFields:
    def test_biomedico_set_restringido(self):
        campos = allowed_update_fields(user("biomedico"))
        assert campos == CAMPOS_BIOMEDICO_EDITABLES
        assert "nombre" not in campos
        assert "serie" not in campos

    def test_biomedico_puede_cambiar_estado(self):
        campos = allowed_update_fields(user("biomedico"))
        assert "estado" in campos
        assert "ubicacion" in campos

    def test_supervisor_set_completo(self):
        campos = allowed_update_fields(user("supervisor"))
        assert campos == CAMPOS_EDITABLES_TODOS

    def test_admin_set_completo(self):
        campos = allowed_update_fields(user("admin"))
        assert campos == CAMPOS_EDITABLES_TODOS

    def test_jefe_biomedica_set_completo(self):
        campos = allowed_update_fields(user("jefe_biomedica"))
        assert campos == CAMPOS_EDITABLES_TODOS

    def test_devuelve_copia_no_referencia(self):
        campos = allowed_update_fields(user("biomedico"))
        campos.add("campo_extra")
        assert "campo_extra" not in CAMPOS_BIOMEDICO_EDITABLES


# ── Integridad del módulo ─────────────────────────────────────────

class TestIntegridadModulo:
    def test_todos_los_roles_en_view_public_tienen_view_confidential(self):
        """view_confidential debe ser subconjunto de view_public (todo quien ve detalles puede ver básico)."""
        for rol in ROLE_PERMISSIONS["view_confidential"]:
            assert rol in ROLE_PERMISSIONS["view_public"], f"Rol {rol} en view_confidential pero no en view_public"

    def test_delete_equipo_subconjunto_de_create(self):
        """Quien puede borrar siempre puede crear (privilegio mayor implica menor)."""
        for rol in ROLE_PERMISSIONS["delete_equipo"]:
            assert rol in ROLE_PERMISSIONS["create_equipo"], f"Rol {rol} puede borrar pero no crear"

    def test_campos_biomedico_son_subconjunto_de_todos(self):
        assert CAMPOS_BIOMEDICO_EDITABLES.issubset(CAMPOS_EDITABLES_TODOS)

    def test_campos_confidenciales_no_en_editables(self):
        """Un campo confidencial no debería ser editable por biomedico (principio mínimo privilegio)."""
        intersection = CAMPOS_CONFIDENCIALES & CAMPOS_BIOMEDICO_EDITABLES
        assert not intersection, f"Campos confidenciales editables por biomedico: {intersection}"
