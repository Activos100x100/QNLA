"""
Modelo SQLAlchemy para rtos_meses_semanas.
"""

from typing import Optional
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RtosMesSemana(Base):
    """Semanas dentro de un mes operativo."""

    __tablename__ = "rtos_meses_semanas"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mes_operativo_id: Mapped[int] = mapped_column(Integer, ForeignKey("rtos_meses_operativos.id"), nullable=False)
    iso_year: Mapped[int] = mapped_column(Integer, nullable=False)
    iso_week: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_semana_mes: Mapped[int] = mapped_column(Integer, nullable=False)
