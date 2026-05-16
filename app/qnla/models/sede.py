from __future__ import annotations

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Sede(Base):
    __tablename__ = "qnla_sedes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    pais: Mapped[str] = mapped_column(String(100), nullable=False)
    capacidad: Mapped[int | None] = mapped_column(Integer, nullable=True)

    torneo: Mapped["Torneo"] = relationship(back_populates="sedes")

    partidos: Mapped[list["Partido"]] = relationship(back_populates="sede")
