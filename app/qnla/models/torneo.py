from __future__ import annotations

from datetime import date, datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Date, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Torneo(Base):
    __tablename__ = "qnla_torneos"
    __table_args__ = (
        CheckConstraint("fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio", name="ck_qnla_torneos_fechas"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    anio: Mapped[int] = mapped_column(nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    cierre_inscripcion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones
    reglas: Mapped["ReglasPuntaje | None"] = relationship(
        back_populates="torneo",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )
    fases: Mapped[list["Fase"]] = relationship(back_populates="torneo", cascade="all, delete-orphan")
    grupos: Mapped[list["Grupo"]] = relationship(back_populates="torneo", cascade="all, delete-orphan")
    selecciones: Mapped[list["Seleccion"]] = relationship(back_populates="torneo", cascade="all, delete-orphan")
    sedes: Mapped[list["Sede"]] = relationship(back_populates="torneo", cascade="all, delete-orphan")
    partidos: Mapped[list["Partido"]] = relationship(back_populates="torneo", cascade="all, delete-orphan")
    participantes: Mapped[list["Participante"]] = relationship(back_populates="torneo", cascade="all, delete-orphan")
