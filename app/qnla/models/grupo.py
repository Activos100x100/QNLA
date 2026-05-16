from __future__ import annotations

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Grupo(Base):
    __tablename__ = "qnla_grupos"
    __table_args__ = (
        UniqueConstraint("torneo_id", "nombre", name="uq_qnla_grupos_torneo_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(5), nullable=False)  # A, B, C…

    torneo: Mapped["Torneo"] = relationship(back_populates="grupos")
    selecciones: Mapped[list["Seleccion"]] = relationship(back_populates="grupo")
    partidos: Mapped[list["Partido"]] = relationship(back_populates="grupo")
