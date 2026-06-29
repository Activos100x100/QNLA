"""
Modelo SQLAlchemy para FTRA_LOGS.
Logs del sistema.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Log(Base):
    """Modelo ORM para tabla FTRA_LOGS."""
    
    __tablename__ = "ftra_logs"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"))
    nivel: Mapped[Optional[str]] = mapped_column(String(20))
    modulo: Mapped[Optional[str]] = mapped_column(String(100))
    mensaje: Mapped[Optional[str]] = mapped_column(Text)
    detalle: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped[Optional["Factura"]] = relationship("Factura", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<Log id={self.id} nivel={self.nivel}>"
