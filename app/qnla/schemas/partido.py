from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class PartidoCreate(BaseModel):
    torneo_id: int
    fase_id: int
    grupo_id: Optional[int] = None
    sede_id: int
    seleccion_local_id: int
    seleccion_visitante_id: int
    fecha_partido: datetime
    cierre_pronostico: datetime

    @model_validator(mode="after")
    def equipos_distintos(self) -> "PartidoCreate":
        if self.seleccion_local_id == self.seleccion_visitante_id:
            raise ValueError("Local y visitante deben ser selecciones distintas")
        return self


class PartidoUpdate(BaseModel):
    fase_id: Optional[int] = None
    grupo_id: Optional[int] = None
    sede_id: Optional[int] = None
    seleccion_local_id: Optional[int] = None
    seleccion_visitante_id: Optional[int] = None
    fecha_partido: Optional[datetime] = None
    cierre_pronostico: Optional[datetime] = None
    finalizado: Optional[bool] = None


class ResultadoIn(BaseModel):
    goles_local: int
    goles_visitante: int
    recalcular: bool = True  # recalcular puntos automáticamente


class PartidoOut(BaseModel):
    id: int
    torneo_id: int
    fase_id: Optional[int]
    grupo_id: Optional[int]
    sede_id: Optional[int]
    seleccion_local_id: int
    seleccion_visitante_id: int
    seleccion_local_nombre: Optional[str] = None
    seleccion_visitante_nombre: Optional[str] = None
    fecha_partido: datetime
    cierre_pronostico: datetime
    goles_local: Optional[int]
    goles_visitante: Optional[int]
    finalizado: bool
    created_at: datetime

    model_config = {"from_attributes": True}
