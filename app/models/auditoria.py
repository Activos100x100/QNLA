"""
Modelo SQLAlchemy para FTRA_AUDITORIA.
Auditoría de cambios en facturas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Auditoria(Base):
    """Modelo ORM para tabla FTRA_AUDITORIA."""
    
    __tablename__ = "ftra_auditoria"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"))
    usuario_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    accion: Mapped[Optional[str]] = mapped_column(String(100))
    tabla_afectada: Mapped[Optional[str]] = mapped_column(String(100))
    registro_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    valor_anterior: Mapped[Optional[dict]] = mapped_column(JSON)
    valor_nuevo: Mapped[Optional[dict]] = mapped_column(JSON)
    direccion_ip: Mapped[Optional[str]] = mapped_column(String(50))
    navegador: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped[Optional["Factura"]] = relationship("Factura", back_populates="auditoria")
    
    def __repr__(self) -> str:
        return f"<Auditoria id={self.id} accion={self.accion}>"
