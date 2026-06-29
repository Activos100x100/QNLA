"""Endpoint de ranking por torneo."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ftra.database import get_db
from app.ftra.schemas.ranking import RankingItem
from app.ftra.services.ranking_service import calcular_ranking

router = APIRouter(prefix="/ftra", tags=["ftra-ranking"])


@router.get("/ranking/{torneo_id}", response_model=list[RankingItem])
def ranking(torneo_id: int, db: Session = Depends(get_db)):
    """Ranking público del torneo. No requiere autenticación."""
    return calcular_ranking(torneo_id, db)
