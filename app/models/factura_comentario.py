"""
Modelo SQLAlchemy para FTRA_FACTURA_COMENTARIOS.
Comentarios específicos de facturas (diferentes al sistema genérico).
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FacturaComentario(Base):
    """Modelo ORM para tabla FTRA_FACTURA_COMENTARIOS."""
    
    __tablename__ = "ftra_factura_comentarios"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    usuario_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    comentario_padre_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_factura_comentarios.id"))
    tipo: Mapped[Optional[str]] = mapped_column(String(30))
    comentario: Mapped[str] = mapped_column(Text, nullable=False)
    resuelto: Mapped[Optional[bool]] = mapped_column(Boolean)
    fecha_resolucion: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="comentarios")
    comentario_padre: Mapped[Optional["FacturaComentario"]] = relationship("FacturaComentario", remote_side=[id], back_populates="respuestas")
    respuestas: Mapped[List["FacturaComentario"]] = relationship("FacturaComentario", remote_side=[comentario_padre_id], back_populates="comentario_padre", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<FacturaComentario id={self.id} factura_id={self.factura_id}>"
