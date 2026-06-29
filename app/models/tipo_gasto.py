"""
Modelo SQLAlchemy para FTRA_TIPOS_GASTO.
Tipos de gastos para facturas.
"""

from typing import Optional, List
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TipoGasto(Base):
    """Modelo ORM para tabla FTRA_TIPOS_GASTO."""
    
    __tablename__ = "ftra_tipos_gasto"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relaciones
    facturas: Mapped[List["Factura"]] = relationship("Factura", back_populates="tipo_gasto")
    
    def __repr__(self) -> str:
        return f"<TipoGasto id={self.id} nombre={self.nombre}>"
