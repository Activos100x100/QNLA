"""
Modelo SQLAlchemy para FTRA_NOTIFICACIONES.
Notificaciones del sistema.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Notificacion(Base):
    """Modelo ORM para tabla FTRA_NOTIFICACIONES."""
    
    __tablename__ = "ftra_notificaciones"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    factura_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"))
    titulo: Mapped[Optional[str]] = mapped_column(String(255))
    mensaje: Mapped[Optional[str]] = mapped_column(Text)
    tipo: Mapped[Optional[str]] = mapped_column(String(50))
    leida: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped[Optional["Factura"]] = relationship("Factura", back_populates="notificaciones")
    
    def __repr__(self) -> str:
        return f"<Notificacion id={self.id} titulo={self.titulo}>"
