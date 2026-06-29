"""
Modelo SQLAlchemy para FTRA_IA_RESULTADOS.
Resultados de procesamiento IA de facturas.
"""

from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, BigInteger, Integer, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class IaResultado(Base):
    """Modelo ORM para tabla FTRA_IA_RESULTADOS."""
    
    __tablename__ = "ftra_ia_resultados"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    proveedor_detectado: Mapped[Optional[str]] = mapped_column(String(255))
    cif_detectado: Mapped[Optional[str]] = mapped_column(String(30))
    numero_detectado: Mapped[Optional[str]] = mapped_column(String(100))
    fecha_detectada: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    total_detectado: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    modelo_ia: Mapped[Optional[str]] = mapped_column(String(100))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    respuesta_json: Mapped[Optional[dict]] = mapped_column(JSON)
    tokens_prompt: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_respuesta: Mapped[Optional[int]] = mapped_column(Integer)
    coste: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    tiempo_proceso: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    confianza_global: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="ia_resultados")
    
    def __repr__(self) -> str:
        return f"<IaResultado id={self.id} factura_id={self.factura_id}>"
