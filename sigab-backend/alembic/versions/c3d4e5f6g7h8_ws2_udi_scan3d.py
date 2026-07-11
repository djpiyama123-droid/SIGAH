"""WS-2: UDI láser en equipos + tabla scan3d_registros (MIRACO Plus)

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-06-04 00:00:00.000000

Operacionaliza dos componentes de Industria 4.0 en SIGAB:
  1. Pistola grabadora láser — campo `udi_code` y `laser_grabado_at` en `equipos`
  2. Escáner de metrología MIRACO Plus — tabla `scan3d_registros`
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar campos UDI a tabla equipos
    op.add_column(
        "equipos",
        sa.Column("udi_code", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "equipos",
        sa.Column("laser_grabado_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_equipos_udi_code", "equipos", ["udi_code"], unique=False)

    # 2. Crear tabla de registros de escaneo 3D (MIRACO Plus)
    op.create_table(
        "scan3d_registros",
        sa.Column(
            "id",
            mysql.INTEGER(unsigned=True),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "equipo_id",
            mysql.INTEGER(unsigned=True),
            sa.ForeignKey("equipos.id"),
            nullable=False,
        ),
        sa.Column("archivo_ref", sa.String(length=512), nullable=True),
        sa.Column("formato_archivo", sa.String(length=20), nullable=True),
        sa.Column("mediciones_json", sa.Text(), nullable=True),
        sa.Column(
            "resultado",
            sa.String(length=30),
            nullable=False,
            server_default="conforme",
        ),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "tecnico_id",
            mysql.INTEGER(unsigned=True),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
        sa.Column("fecha_scan", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_scan3d_equipo_id", "scan3d_registros", ["equipo_id"])
    op.create_index("ix_scan3d_fecha_scan", "scan3d_registros", ["fecha_scan"])


def downgrade() -> None:
    op.drop_table("scan3d_registros")
    op.drop_index("ix_equipos_udi_code", table_name="equipos")
    op.drop_column("equipos", "laser_grabado_at")
    op.drop_column("equipos", "udi_code")
