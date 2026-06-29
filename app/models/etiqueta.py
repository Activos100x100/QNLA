"""
Modelo SQLAlchemy para FTRA_ETIQUETAS.
Etiquetas para clasificar facturas.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, TIMESTAMP, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Etiqueta(Base):
    """Modelo ORM para tabla FTRA_ETIQUETAS."""
    
    __tablename__ = "ftra_etiquetas"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20))
    icono: Mapped[Optional[str]] = mapped_column(String(100))
    activa: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="etiquetas")
    facturas: Mapped[List["Factura"]] = relationship("Factura", secondary="ftra_factura_etiquetas", back_populates="etiquetas")
    
    def __repr__(self) -> str:
        return f"<Etiqueta id={self.id} nombre={self.nombre}>"
