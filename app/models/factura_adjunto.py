"""
Modelo SQLAlchemy para FTRA_FACTURA_ADJUNTOS.
Adjuntos (archivos) asociados a facturas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FacturaAdjunto(Base):
    """Modelo ORM para tabla FTRA_FACTURA_ADJUNTOS."""
    
    __tablename__ = "ftra_factura_adjuntos"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    nombre_archivo: Mapped[Optional[str]] = mapped_column(String(255))
    tipo_documento: Mapped[Optional[str]] = mapped_column(String(50))
    mime_type: Mapped[Optional[str]] = mapped_column(String(150))
    tamano_archivo: Mapped[Optional[int]] = mapped_column(BigInteger)
    google_drive_file_id: Mapped[Optional[str]] = mapped_column(Text)
    google_drive_url: Mapped[Optional[str]] = mapped_column(Text)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    usuario_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="adjuntos")
    
    def __repr__(self) -> str:
        return f"<FacturaAdjunto id={self.id} nombre={self.nombre_archivo}>"
