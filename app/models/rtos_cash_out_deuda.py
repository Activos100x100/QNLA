from datetime import date, datetime
from typing import Optional
from sqlalchemy import Integer, Float, String, DateTime, Date, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RtosCashOutDeuda(Base):
    """Deudas de riders por semana."""

    __tablename__ = "rtos_cash_out_deuda"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    iso_year: Mapped[int] = mapped_column(Integer, nullable=False)
    iso_week: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_reporte: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    importe_deuda: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    notificado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fecha_notificacion: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    fecha_inicio_semana: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    meta_error_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_error_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
