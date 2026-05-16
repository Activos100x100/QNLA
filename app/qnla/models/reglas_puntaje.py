from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import SmallInteger, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.qnla.database import Base


class ReglasPuntaje(Base):
    __tablename__ = "qnla_reglas_puntaje"
    __table_args__ = (
        UniqueConstraint("torneo_id", name="uq_qnla_reglas_puntaje_torneo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    torneo_id: Mapped[int] = mapped_column(ForeignKey("qnla_torneos.id", ondelete="CASCADE"), nullable=False, index=True)
    puntos_exacto: Mapped[int] = mapped_column(SmallInteger, default=3, nullable=False)
    puntos_ganador: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    puntos_fallo: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    torneo: Mapped["Torneo"] = relationship(back_populates="reglas")
