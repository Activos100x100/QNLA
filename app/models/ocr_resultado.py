"""
Modelo SQLAlchemy para FTRA_OCR_RESULTADOS.
Resultados de OCR de facturas.
"""

from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, BigInteger, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OcrResultado(Base):
    """Modelo ORM para tabla FTRA_OCR_RESULTADOS."""
    
    __tablename__ = "ftra_ocr_resultados"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    motor_ocr: Mapped[Optional[str]] = mapped_column(String(100))
    version_motor: Mapped[Optional[str]] = mapped_column(String(50))
    texto_extraido: Mapped[Optional[str]] = mapped_column(Text)
    confianza_media: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tiempo_proceso: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="ocr_resultados")
    
    def __repr__(self) -> str:
        return f"<OcrResultado id={self.id} factura_id={self.factura_id}>"
