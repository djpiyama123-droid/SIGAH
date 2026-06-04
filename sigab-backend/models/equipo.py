from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects import mysql
from typing import Optional, List
from datetime import date, datetime, timezone

class Equipo(SQLModel, table=True):
    __tablename__ = "equipos"
    
    id: Optional[int] = Field(
        default=None, 
        sa_column=Column(mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    )
    serie: str = Field(index=True, unique=True)
    inventario: Optional[str] = None
    nombre: str
    marca: str
    modelo: str
    ubicacion: str
    piso: Optional[str] = None
    area: Optional[str] = None
    fotos: Optional[str] = None
    estado: str = Field(default="operativo")
    criticidad: str = Field(default="media")
    fecha_instalacion: Optional[date] = None
    fecha_ultimo_mantenimiento: Optional[date] = None
    fecha_proximo_mantenimiento: Optional[date] = None
    vida_util_anios: Optional[int] = None
    numero_contrato: Optional[str] = None
    proveedor_servicio: Optional[str] = None
    qr_code_path: Optional[str] = None
    # Auditoría
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(mysql.DATETIME, nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(mysql.DATETIME, nullable=False)
    )
    
    # Campos extendidos del mapa (AG-01 compatible)
    zona_id: Optional[int] = Field(default=None, foreign_key="zonas_mapa.id")
    pos_x: float = Field(default=50.0)
    pos_y: float = Field(default=50.0)
    imagen_url: Optional[str] = None
    tipo_equipo: str = Field(default="otro")
    clase_cofepris: str = Field(default="II")
    fecha_compra: Optional[date] = None
    numero_contrato_servicio: Optional[str] = None
    qr_token: Optional[str] = Field(default=None, index=True)
    # ── Industria 4.0: UDI + escaneo 3D MIRACO Plus ──────────────────
    # udi_code: código UDI-DI grabado con pistola láser (formato GS1-128 / GS1 DataMatrix)
    udi_code: Optional[str] = Field(default=None, index=True)
    # laser_grabado_at: fecha/hora en que se ejecutó el marcado láser
    laser_grabado_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(mysql.DATETIME, nullable=True),
    )
