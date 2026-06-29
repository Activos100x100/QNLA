"""
Modelo SQLAlchemy para FTRA_CONFIGURACION.
Configuración del sistema.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Configuracion(Base):
    """Modelo ORM para tabla FTRA_CONFIGURACION."""
    
    __tablename__ = "ftra_configuracion"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    valor: Mapped[Optional[str]] = mapped_column(Text)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<Configuracion id={self.id} clave={self.clave}>"
