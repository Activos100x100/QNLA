from pydantic import BaseModel


class RankingItem(BaseModel):
    posicion: int
    participante_id: int
    nombre: str
    email: str
    puntos_totales: int
    aciertos_exactos: int
    aciertos_ganador: int
    partidos_pronosticados: int

    model_config = {"from_attributes": True}
