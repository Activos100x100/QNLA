"""
Modelo SQLAlchemy para FTRA_CLIENTES.
Clientes para facturas.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Cliente(Base):
    """Modelo ORM para tabla FTRA_CLIENTES."""
    
    __tablename__ = "ftra_clientes"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cif: Mapped[Optional[str]] = mapped_column(String(20))
    direccion: Mapped[Optional[str]] = mapped_column(Text)
    codigo_postal: Mapped[Optional[str]] = mapped_column(String(15))
    ciudad: Mapped[Optional[str]] = mapped_column(String(100))
    provincia: Mapped[Optional[str]] = mapped_column(String(100))
    pais: Mapped[Optional[str]] = mapped_column(String(100))
    telefono: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    activo: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="clientes")
    facturas: Mapped[List["Factura"]] = relationship("Factura", back_populates="cliente")
    
    def __repr__(self) -> str:
        return f"<Cliente id={self.id} nombre={self.nombre}>"
