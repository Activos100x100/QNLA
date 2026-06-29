from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class PronosticoCreate(BaseModel):
    partido_id: int
    goles_local: int
    goles_visitante: int

    @model_validator(mode="after")
    def goles_no_negativos(self) -> "PronosticoCreate":
        if self.goles_local < 0 or self.goles_visitante < 0:
            raise ValueError("Los goles no pueden ser negativos")
        return self


class PronosticoOut(BaseModel):
    id: int
    participante_id: int
    partido_id: int
    goles_local: int
    goles_visitante: int
    puntos_obtenidos: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
