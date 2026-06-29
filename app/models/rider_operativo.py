"""
Modelo SQLAlchemy para la tabla `rider_operativo`.
Información de riders activos.
"""

from datetime import date
from typing import Optional
from sqlalchemy import Integer, BigInteger, String, Boolean, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RiderOperativo(Base):
    """Datos de riders operativos."""

    __tablename__ = "rider_operativo"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(BigInteger, index=True)
    rider_id: Mapped[str] = mapped_column(String(50), nullable=False)
    cod_activo: Mapped[str] = mapped_column(String(100), nullable=False)
    ciudad_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
