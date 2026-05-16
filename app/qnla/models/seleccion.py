from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Seleccion(Base):
    __tablename__ = "qnla_selecciones"
    __table_args__ = (
        UniqueConstraint("torneo_id", "nombre", name="uq_qnla_selecciones_torneo_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("qnla_grupos.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo_fifa: Mapped[str] = mapped_column(String(3), nullable=False)
    bandera_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    torneo: Mapped["Torneo"] = relationship(back_populates="selecciones")
    grupo: Mapped["Grupo | None"] = relationship(back_populates="selecciones")

    partidos_local: Mapped[list["Partido"]] = relationship(
        "Partido", foreign_keys="Partido.seleccion_local_id", back_populates="seleccion_local"
    )
    partidos_visitante: Mapped[list["Partido"]] = relationship(
        "Partido", foreign_keys="Partido.seleccion_visitante_id", back_populates="seleccion_visitante"
    )
