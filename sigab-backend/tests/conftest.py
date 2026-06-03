"""
conftest.py — Pre-mockea dependencias del sistema que no están disponibles
en entornos CI sin librerías nativas (aiomysql, cryptography/cffi).
Esto permite testear la lógica de negocio sin MySQL ni extensiones C.
"""
import sys
from unittest.mock import MagicMock

# Mockear antes de que cualquier módulo del proyecto sea importado
for mod in (
    "aiomysql",
    "cryptography",
    "cryptography.hazmat",
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.primitives.serialization",
    "cryptography.hazmat.primitives.hashes",
    "cryptography.hazmat.bindings",
    "cryptography.hazmat.bindings._rust",
    "pymysql",
    "pymysql.connections",
    "pymysql._auth",
    "pymysql.converters",
    "google.generativeai",
    "sqlmodel",
    "sqlalchemy",
):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
