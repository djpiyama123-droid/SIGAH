"""
Tests unitarios WS-2 — UDI + escaneo 3D (MIRACO Plus)

Cubre:
  - Modelo Scan3DRegistro: campos y defaults
  - Lógica de validación de mediciones JSON en routes/scan3d.py
  - Campos UDI en modelo Equipo
"""

import json
import pytest
from datetime import datetime, timezone


# ── Modelo Scan3DRegistro ─────────────────────────────────────────

def test_scan3d_modelo_campos_requeridos():
    """Scan3DRegistro debe instanciarse con equipo_id y fecha_scan por default."""
    from models.scan3d import Scan3DRegistro

    scan = Scan3DRegistro(equipo_id=1)
    assert scan.equipo_id == 1
    assert scan.resultado == "conforme"
    assert scan.archivo_ref is None
    assert scan.mediciones_json is None
    assert scan.observaciones is None
    assert isinstance(scan.fecha_scan, datetime)
    assert isinstance(scan.created_at, datetime)


def test_scan3d_mediciones_json_es_string():
    """mediciones_json debe ser un string JSON para compatibilidad MySQL TEXT."""
    from models.scan3d import Scan3DRegistro

    mediciones = json.dumps({"largo_mm": 350, "ancho_mm": 280})
    scan = Scan3DRegistro(equipo_id=1, mediciones_json=mediciones)
    assert scan.mediciones_json == mediciones
    parsed = json.loads(scan.mediciones_json)
    assert parsed["largo_mm"] == 350


def test_scan3d_resultado_default():
    """El resultado por defecto debe ser 'conforme'."""
    from models.scan3d import Scan3DRegistro

    scan = Scan3DRegistro(equipo_id=5)
    assert scan.resultado == "conforme"


def test_scan3d_resultado_no_conforme():
    """Debe aceptar 'no_conforme' sin error."""
    from models.scan3d import Scan3DRegistro

    scan = Scan3DRegistro(equipo_id=5, resultado="no_conforme")
    assert scan.resultado == "no_conforme"


# ── Modelo Equipo — campos UDI ────────────────────────────────────

def test_equipo_udi_fields_existen():
    """El modelo Equipo debe tener los campos udi_code y laser_grabado_at."""
    from models.equipo import Equipo
    import inspect

    # Verificar mediante model_fields de SQLModel
    fields = Equipo.model_fields
    assert "udi_code" in fields, "Falta campo udi_code en Equipo"
    assert "laser_grabado_at" in fields, "Falta campo laser_grabado_at en Equipo"


def test_equipo_udi_defaults_none():
    """Los campos UDI deben ser None por defecto (para retrocompat con equipos existentes)."""
    from models.equipo import Equipo

    eq = Equipo(
        serie="TEST-001",
        nombre="Monitor",
        marca="GE",
        modelo="B650",
        ubicacion="Urgencias",
    )
    assert eq.udi_code is None
    assert eq.laser_grabado_at is None


def test_equipo_udi_code_set():
    """udi_code debe aceptar un código UDI GS1 válido."""
    from models.equipo import Equipo

    udi = "01084700010046001724103110GTIN00"
    eq = Equipo(
        serie="TEST-002",
        nombre="Monitor",
        marca="GE",
        modelo="B650",
        ubicacion="UCI",
        udi_code=udi,
        laser_grabado_at=datetime(2026, 6, 4, 10, 30, 0, tzinfo=timezone.utc),
    )
    assert eq.udi_code == udi
    assert eq.laser_grabado_at.year == 2026


# ── Validación de resultados en route ────────────────────────────

def test_resultados_validos_constante():
    """El set de resultados válidos en scan3d.py debe incluir los tres estados."""
    import importlib.util, pathlib

    # Leer la constante directamente del módulo sin importarlo completo
    src = pathlib.Path(__file__).parent.parent / "routes" / "scan3d.py"
    text = src.read_text()
    assert '"conforme"' in text
    assert '"no_conforme"' in text
    assert '"pendiente_revision"' in text


def test_migracion_revision_id():
    """La migración WS-2 debe tener el revision id correcto y apuntar a b2c3d4e5f6g7."""
    import pathlib

    src = pathlib.Path(__file__).parent.parent / "alembic" / "versions" / "c3d4e5f6g7h8_ws2_udi_scan3d.py"
    assert src.exists(), "Archivo de migración WS-2 no encontrado"
    text = src.read_text()
    assert 'revision: str = "c3d4e5f6g7h8"' in text
    assert 'down_revision' in text
    assert '"b2c3d4e5f6g7"' in text
    assert "udi_code" in text
    assert "scan3d_registros" in text
