"""
Modelo SQLAlchemy para la tabla `empleado_asignacion`.
Relación entre empleados, departamentos y puestos.
"""

from datetime import date
from typing import Optional
from sqlalchemy import Integer, BigInteger, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EmpleadoAsignacion(Base):
    """Asignaciones actuales de empleados a departamentos."""

    __tablename__ = "empleado_asignacion"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(BigInteger, index=True)
    departamento_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ciudad_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    convenio_tramo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    puesto_sueldo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
