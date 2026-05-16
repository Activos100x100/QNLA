from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Pronostico(Base):
    __tablename__ = "qnla_pronosticos"
    __table_args__ = (
        UniqueConstraint("participante_id", "partido_id", name="uq_pronostico_participante_partido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    participante_id: Mapped[int] = mapped_column(ForeignKey("qnla_participantes.id", ondelete="CASCADE"), nullable=False, index=True)
    partido_id: Mapped[int] = mapped_column(ForeignKey("qnla_partidos.id", ondelete="CASCADE"), nullable=False, index=True)
    goles_local: Mapped[int] = mapped_column(Integer, nullable=False)
    goles_visitante: Mapped[int] = mapped_column(Integer, nullable=False)
    puntos_obtenidos: Mapped[int | None] = mapped_column(Integer, nullable=True)
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

    participante: Mapped["Participante"] = relationship(back_populates="pronosticos")
    partido: Mapped["Partido"] = relationship(back_populates="pronosticos")
