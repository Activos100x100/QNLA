"""
Modelo SQLAlchemy para FTRA_FACTURA_HISTORIAL.
Historial de cambios de estado de facturas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FacturaHistorial(Base):
    """Modelo ORM para tabla FTRA_FACTURA_HISTORIAL."""
    
    __tablename__ = "ftra_factura_historial"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    estado_anterior_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_estados.id"))
    estado_nuevo_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_estados.id"))
    usuario_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    comentario: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="historial")
    estado_anterior: Mapped[Optional["Estado"]] = relationship("Estado", foreign_keys=[estado_anterior_id], back_populates="historiales_estado_anterior")
    estado_nuevo: Mapped[Optional["Estado"]] = relationship("Estado", foreign_keys=[estado_nuevo_id], back_populates="historiales_estado_nuevo")
    
    def __repr__(self) -> str:
        return f"<FacturaHistorial id={self.id} factura_id={self.factura_id}>"
