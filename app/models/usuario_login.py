"""
Modelo SQLAlchemy para la tabla pre-existente `usuarios_login`.
Esta tabla es gestionada por el sistema ERP externo; FTRA sólo la lee.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UsuarioLogin(Base):
    """
    Modelo de sólo lectura sobre la tabla `usuarios_login`.
    No gestionada por migraciones FTRA.
    """

    __tablename__ = "usuarios_login"
    __table_args__ = {"extend_existing": True}

    usuario_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empleado_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    dni_nie: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    password_salt: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    creado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_recuperacion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expiracion_token: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
