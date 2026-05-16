from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.qnla.models.torneo import Torneo


class TorneosRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Torneo]:
        return self.db.scalars(select(Torneo).order_by(Torneo.anio.desc())).all()

    def get(self, torneo_id: int) -> Torneo | None:
        return self.db.get(Torneo, torneo_id)

    def save(self, torneo: Torneo) -> Torneo:
        self.db.add(torneo)
        self.db.commit()
        self.db.refresh(torneo)
        return torneo

    def delete(self, torneo: Torneo) -> None:
        self.db.delete(torneo)
        self.db.commit()
