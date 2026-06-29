"""
Modelo SQLAlchemy para FTRA_FACTURA_LINEAS.
Líneas de detalle de facturas.
"""

from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Integer, BigInteger, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FacturaLinea(Base):
    """Modelo ORM para tabla FTRA_FACTURA_LINEAS."""
    
    __tablename__ = "ftra_factura_lineas"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    orden_linea: Mapped[Optional[int]] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    cantidad: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    precio_unitario: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    descuento: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    porcentaje_iva: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    importe_iva: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="lineas")
    
    def __repr__(self) -> str:
        return f"<FacturaLinea id={self.id} factura_id={self.factura_id}>"
