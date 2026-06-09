"""Tests para auth/permissions.py — sin base de datos, lógica pura."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth.permissions import (
    can,
    filter_equipo_publico,
    allowed_update_fields,
    CAMPOS_CONFIDENCIALES,
    CAMPOS_BIOMEDICO_EDITABLES,
    CAMPOS_EDITABLES_TODOS,
)


# ── can() ────────────────────────────────────────────────────────
class TestCan:
    def test_anonimo_puede_view_public(self):
        assert can(None, "view_public") is True

    def test_anonimo_no_puede_edit(self):
        assert can(None, "edit_equipo") is False

    def test_admin_puede_todo(self):
        admin = {"rol": "admin"}
        for accion in ["view_public", "view_confidential", "create_equipo",
                        "edit_equipo", "delete_equipo", "regenerar_qr", "admin_usuarios"]:
            assert can(admin, accion) is True, f"admin debería poder: {accion}"

    def test_biomedico_no_puede_crear_equipo(self):
        bio = {"rol": "biomedico"}
        assert can(bio, "create_equipo") is False

    def test_biomedico_puede_edit(self):
        bio = {"rol": "biomedico"}
        assert can(bio, "edit_equipo") is True

    def test_biomedico_no_puede_eliminar(self):
        bio = {"rol": "biomedico"}
        assert can(bio, "delete_equipo") is False

    def test_almacen_no_puede_delete(self):
        almacen = {"rol": "almacen"}
        assert can(almacen, "delete_equipo") is False

    def test_rol_inexistente_denegado(self):
        fake = {"rol": "intruso"}
        assert can(fake, "create_equipo") is False

    def test_accion_inexistente_denegada(self):
        admin = {"rol": "admin"}
        assert can(admin, "accion_que_no_existe") is False

    def test_sin_campo_rol_denegado(self):
        user_sin_rol = {"id": 1, "nombre": "Test"}
        assert can(user_sin_rol, "edit_equipo") is False


# ── filter_equipo_publico() ──────────────────────────────────────
class TestFilterEquipoPublico:
    def test_elimina_campos_confidenciales(self):
        equipo = {
            "id": 1,
            "nombre": "Ventilador XYZ",
            "serie": "SN-001",
            "numero_contrato": "CONT-2024-001",
            "fecha_compra": "2024-01-15",
            "proveedor_servicio": "MedTech SA",
            "clase_cofepris": "III",
        }
        resultado = filter_equipo_publico(equipo)
        for campo in CAMPOS_CONFIDENCIALES:
            assert campo not in resultado, f"campo confidencial visible: {campo}"
        assert resultado["id"] == 1
        assert resultado["nombre"] == "Ventilador XYZ"
        assert resultado["serie"] == "SN-001"

    def test_equipo_none_retorna_none(self):
        assert filter_equipo_publico(None) is None

    def test_equipo_sin_confidenciales_intacto(self):
        equipo = {"id": 5, "nombre": "Monitor ECG", "estado": "operativo"}
        resultado = filter_equipo_publico(equipo)
        assert resultado == equipo


# ── allowed_update_fields() ──────────────────────────────────────
class TestAllowedUpdateFields:
    def test_biomedico_solo_campos_limitados(self):
        bio = {"rol": "biomedico"}
        campos = allowed_update_fields(bio)
        assert campos == CAMPOS_BIOMEDICO_EDITABLES
        assert "nombre" not in campos
        assert "marca" not in campos
        assert "estado" in campos
        assert "ubicacion" in campos

    def test_admin_accede_a_todos_los_campos(self):
        admin = {"rol": "admin"}
        campos = allowed_update_fields(admin)
        assert campos == CAMPOS_EDITABLES_TODOS

    def test_supervisor_accede_a_todos_los_campos(self):
        sup = {"rol": "supervisor"}
        campos = allowed_update_fields(sup)
        assert campos == CAMPOS_EDITABLES_TODOS

    def test_retorna_copia_no_mutacion(self):
        bio = {"rol": "biomedico"}
        c1 = allowed_update_fields(bio)
        c1.add("campo_extra")
        c2 = allowed_update_fields(bio)
        assert "campo_extra" not in c2
