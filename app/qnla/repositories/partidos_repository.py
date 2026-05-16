from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.qnla.models.partido import Partido


class PartidosRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_torneo(self, torneo_id: int) -> list[Partido]:
        return self.db.scalars(select(Partido).where(Partido.torneo_id == torneo_id).order_by(Partido.fecha_partido)).all()

    def get(self, partido_id: int) -> Partido | None:
        return self.db.get(Partido, partido_id)

    def save(self, partido: Partido) -> Partido:
        self.db.add(partido)
        self.db.commit()
        self.db.refresh(partido)
        return partido

    def delete(self, partido: Partido) -> None:
        self.db.delete(partido)
        self.db.commit()
