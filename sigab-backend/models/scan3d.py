"""
Modelo de registros de escaneo 3D — MIRACO Plus (metrología dimensional)

Cada fila representa un escaneo de metrología 3D realizado sobre un equipo
biomédico con el escáner MIRACO Plus. Almacena la referencia al archivo de
nube de puntos, las dimensiones clave medidas (JSON) y quién lo realizó.
"""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects import mysql
import sqlalchemy as sa
from typing import Optional
from datetime import datetime, timezone


class Scan3DRegistro(SQLModel, table=True):
    __tablename__ = "scan3d_registros"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True),
    )
    equipo_id: int = Field(
        sa_column=Column(
            mysql.INTEGER(unsigned=True),
            sa.ForeignKey("equipos.id"),
            nullable=False,
            index=True,
        )
    )
    # Referencia al archivo de nube de puntos (ruta local o URL)
    archivo_ref: Optional[str] = Field(
        default=None,
        sa_column=Column(mysql.VARCHAR(512), nullable=True),
    )
    # Formato: STL, PLY, OBJ, E57, XYZ, etc.
    formato_archivo: Optional[str] = Field(default=None, max_length=20)
    # Dimensiones clave medidas (JSON libre). Ej: {"largo_mm": 450, "ancho_mm": 300, ...}
    mediciones_json: Optional[str] = Field(
        default=None,
        sa_column=Column(mysql.TEXT, nullable=True),
    )
    # Resultado global de la inspección metrológica
    resultado: str = Field(default="conforme", max_length=30)
    # Resultado: "conforme" | "no_conforme" | "pendiente_revision"
    observaciones: Optional[str] = Field(
        default=None,
        sa_column=Column(mysql.TEXT, nullable=True),
    )
    tecnico_id: Optional[int] = Field(
        default=None,
        sa_column=Column(mysql.INTEGER(unsigned=True), sa.ForeignKey("usuarios.id"), nullable=True),
    )
    fecha_scan: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(mysql.DATETIME, nullable=False, index=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(mysql.DATETIME, nullable=False),
    )
