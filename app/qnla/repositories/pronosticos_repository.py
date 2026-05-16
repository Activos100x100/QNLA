from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.qnla.models.pronostico import Pronostico


class PronosticosRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_participante(self, participante_id: int) -> list[Pronostico]:
        return self.db.scalars(select(Pronostico).where(Pronostico.participante_id == participante_id)).all()

    def get_by_participante_partido(self, participante_id: int, partido_id: int) -> Pronostico | None:
        return self.db.scalars(
            select(Pronostico).where(
                Pronostico.participante_id == participante_id,
                Pronostico.partido_id == partido_id,
            )
        ).first()

    def save(self, pronostico: Pronostico) -> Pronostico:
        self.db.add(pronostico)
        self.db.commit()
        self.db.refresh(pronostico)
        return pronostico
