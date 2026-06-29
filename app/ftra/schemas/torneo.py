from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, AliasChoices, model_validator


class TorneoCreate(BaseModel):
    nombre: str
    anio: int
    descripcion: Optional[str] = None
    admin: Optional[str] = None
    activo: bool = True
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cierre_inscripcion: Optional[datetime] = None
    puntos_exacto: int = Field(default=3, validation_alias=AliasChoices("puntos_exacto", "exacto_puntos"))
    puntos_ganador: int = Field(default=1, validation_alias=AliasChoices("puntos_ganador", "ganador_empate_puntos"))
    puntos_fallo: int = Field(default=0, validation_alias=AliasChoices("puntos_fallo", "fallo_puntos"))

    @model_validator(mode="after")
    def validar_rango_fechas(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return self


class TorneoUpdate(BaseModel):
    nombre: Optional[str] = None
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    admin: Optional[str] = None
    activo: Optional[bool] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cierre_inscripcion: Optional[datetime] = None

    @model_validator(mode="after")
    def validar_rango_fechas(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return self


class TorneoOut(BaseModel):
    id: int
    nombre: str
    anio: int
    descripcion: Optional[str]
    admin: Optional[str]
    activo: bool
    fecha_inicio: Optional[date]
    fecha_fin: Optional[date]
    cierre_inscripcion: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReglasPuntajeUpdate(BaseModel):
    puntos_exacto: int = Field(default=3, ge=0)
    puntos_ganador: int = Field(default=1, ge=0)
    puntos_fallo: int = Field(default=0, ge=0)
