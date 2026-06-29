"""
Modelo SQLAlchemy para FTRA_DRIVE_CARPETAS.
Carpetas de Google Drive asociadas a empresas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DriveCarpeta(Base):
    """Modelo ORM para tabla FTRA_DRIVE_CARPETAS."""
    
    __tablename__ = "ftra_drive_carpetas"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    anio: Mapped[Optional[int]] = mapped_column(Integer)
    mes: Mapped[Optional[int]] = mapped_column(Integer)
    google_drive_folder_id: Mapped[str] = mapped_column(Text, nullable=False)
    google_drive_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="drive_carpetas")
    
    def __repr__(self) -> str:
        return f"<DriveCarpeta id={self.id} nombre={self.nombre}>"
