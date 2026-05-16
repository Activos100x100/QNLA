from __future__ import annotations

from sqlalchemy import String, SmallInteger, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Fase(Base):
    __tablename__ = "qnla_fases"
    __table_args__ = (
        UniqueConstraint("torneo_id", "nombre", name="uq_qnla_fases_torneo_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    orden: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    es_eliminatoria: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    torneo: Mapped["Torneo"] = relationship(back_populates="fases")
    partidos: Mapped[list["Partido"]] = relationship(back_populates="fase")
