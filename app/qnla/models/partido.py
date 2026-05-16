from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Integer,
    SmallInteger,
    Boolean,
    ForeignKey,
    DateTime,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Partido(Base):
    __tablename__ = "qnla_partidos"
    __table_args__ = (
        CheckConstraint("seleccion_local_id <> seleccion_visitante_id", name="ck_qnla_partidos_equipos_distintos"),
        CheckConstraint(
            "(goles_local IS NULL AND goles_visitante IS NULL) OR (goles_local >= 0 AND goles_visitante >= 0)",
            name="ck_qnla_partidos_goles_validos",
        ),
        Index("ix_qnla_partidos_torneo_fecha", "torneo_id", "fecha_partido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    fase_id: Mapped[int] = mapped_column(ForeignKey("qnla_fases.id", ondelete="CASCADE"), nullable=False, index=True)
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("qnla_grupos.id", ondelete="SET NULL"), nullable=True, index=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("qnla_sedes.id", ondelete="CASCADE"), nullable=False, index=True)
    seleccion_local_id: Mapped[int] = mapped_column(ForeignKey("qnla_selecciones.id", ondelete="RESTRICT"), nullable=False, index=True)
    seleccion_visitante_id: Mapped[int] = mapped_column(ForeignKey("qnla_selecciones.id", ondelete="RESTRICT"), nullable=False, index=True)

    fecha_partido: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cierre_pronostico: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    goles_local: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    goles_visitante: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    finalizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones
    torneo: Mapped["Torneo"] = relationship(back_populates="partidos")
    fase: Mapped["Fase"] = relationship(back_populates="partidos")
    grupo: Mapped["Grupo | None"] = relationship(back_populates="partidos")
    sede: Mapped["Sede"] = relationship(back_populates="partidos")
    seleccion_local: Mapped["Seleccion"] = relationship(
        foreign_keys=[seleccion_local_id], back_populates="partidos_local"
    )
    seleccion_visitante: Mapped["Seleccion"] = relationship(
        foreign_keys=[seleccion_visitante_id], back_populates="partidos_visitante"
    )
    pronosticos: Mapped[list["Pronostico"]] = relationship(back_populates="partido", cascade="all, delete-orphan")
