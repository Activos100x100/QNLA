"""
Modelo SQLAlchemy para FTRA_EMPRESAS.
Tabla maestra de empresas.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Boolean, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Empresa(Base):
    """Modelo ORM para tabla FTRA_EMPRESAS."""
    
    __tablename__ = "ftra_empresas"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cif: Mapped[Optional[str]] = mapped_column(String(20))
    direccion: Mapped[Optional[str]] = mapped_column(Text)
    telefono: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    activo: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    proveedores: Mapped[List["Proveedor"]] = relationship("Proveedor", back_populates="empresa", cascade="all, delete-orphan")
    clientes: Mapped[List["Cliente"]] = relationship("Cliente", back_populates="empresa", cascade="all, delete-orphan")
    etiquetas: Mapped[List["Etiqueta"]] = relationship("Etiqueta", back_populates="empresa", cascade="all, delete-orphan")
    drive_carpetas: Mapped[List["DriveCarpeta"]] = relationship("DriveCarpeta", back_populates="empresa", cascade="all, delete-orphan")
    facturas: Mapped[List["Factura"]] = relationship("Factura", back_populates="empresa", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Empresa id={self.id} nombre={self.nombre}>"
