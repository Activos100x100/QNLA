from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class Participante(Base):
    __tablename__ = "qnla_participantes"
    __table_args__ = (
        UniqueConstraint("torneo_id", "email", name="uq_participante_torneo_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    es_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    torneo: Mapped["Torneo"] = relationship(back_populates="participantes")
    pronosticos: Mapped[list["Pronostico"]] = relationship(back_populates="participante", cascade="all, delete-orphan")
