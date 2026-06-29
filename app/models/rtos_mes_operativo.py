"""
Modelo SQLAlchemy para rtos_meses_operativos.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RtosMesOperativo(Base):
    """Mes operativo de riders."""

    __tablename__ = "rtos_meses_operativos"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ciudad_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cerrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
