"""Tests para utils/iso8601.py — lógica pura, sin DB."""
import sys
import os
from datetime import datetime, date, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.iso8601 import now_iso, format_datetime, serialize_row


class TestNowIso:
    def test_retorna_string(self):
        resultado = now_iso()
        assert isinstance(resultado, str)

    def test_contiene_zona_utc(self):
        resultado = now_iso()
        # ISO 8601 UTC tiene +00:00 o Z al final
        assert "+00:00" in resultado or resultado.endswith("Z")

    def test_es_parseable(self):
        resultado = now_iso()
        dt = datetime.fromisoformat(resultado)
        assert dt.tzinfo is not None


class TestFormatDatetime:
    def test_datetime_con_tz(self):
        dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        resultado = format_datetime(dt)
        assert "2024-06-01" in resultado

    def test_datetime_sin_tz(self):
        dt = datetime(2024, 6, 1, 12, 0, 0)
        resultado = format_datetime(dt)
        assert "2024-06-01" in resultado

    def test_none_retorna_none(self):
        assert format_datetime(None) is None

    def test_date_object(self):
        d = date(2024, 6, 1)
        resultado = format_datetime(d)
        assert "2024-06-01" in resultado

    def test_string_pasado_directo(self):
        s = "2024-06-01"
        resultado = format_datetime(s)
        assert resultado == s


class TestSerializeRow:
    def test_none_retorna_none(self):
        assert serialize_row(None) is None

    def test_row_sin_datetimes(self):
        row = {"id": 1, "nombre": "Ventilador", "estado": "operativo"}
        resultado = serialize_row(row)
        assert resultado == row

    def test_row_con_datetime(self):
        dt = datetime(2024, 6, 1, 10, 30, tzinfo=timezone.utc)
        row = {"id": 1, "created_at": dt, "nombre": "ECG"}
        resultado = serialize_row(row)
        assert isinstance(resultado["created_at"], str)
        assert "2024-06-01" in resultado["created_at"]
        assert resultado["nombre"] == "ECG"
        assert resultado["id"] == 1

    def test_row_con_date(self):
        d = date(2024, 6, 1)
        row = {"fecha": d, "equipo_id": 5}
        resultado = serialize_row(row)
        assert isinstance(resultado["fecha"], str)
        assert "2024-06-01" in resultado["fecha"]

    def test_valores_no_datetime_preservados(self):
        row = {"count": 42, "activo": True, "nombre": None}
        resultado = serialize_row(row)
        assert resultado["count"] == 42
        assert resultado["activo"] is True
        assert resultado["nombre"] is None
