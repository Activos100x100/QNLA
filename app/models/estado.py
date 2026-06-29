"""
Modelo SQLAlchemy para FTRA_ESTADOS.
Estados de las facturas.
"""

from typing import Optional, List
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Estado(Base):
    """Modelo ORM para tabla FTRA_ESTADOS."""
    
    __tablename__ = "ftra_estados"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(20))
    orden: Mapped[Optional[int]] = mapped_column(Integer)
    es_final: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    # Relaciones
    facturas: Mapped[List["Factura"]] = relationship("Factura", back_populates="estado", cascade="all, delete-orphan")
    historiales_estado_anterior: Mapped[List["FacturaHistorial"]] = relationship("FacturaHistorial", foreign_keys="FacturaHistorial.estado_anterior_id", back_populates="estado_anterior")
    historiales_estado_nuevo: Mapped[List["FacturaHistorial"]] = relationship("FacturaHistorial", foreign_keys="FacturaHistorial.estado_nuevo_id", back_populates="estado_nuevo")
    
    def __repr__(self) -> str:
        return f"<Estado id={self.id} nombre={self.nombre}>"
