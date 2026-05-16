"""Servicio de ranking para un torneo."""
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.qnla.models.participante import Participante
from app.qnla.models.pronostico import Pronostico
from app.qnla.models.partido import Partido
from app.qnla.schemas.ranking import RankingItem


def calcular_ranking(torneo_id: int, db: Session) -> list[RankingItem]:
    """Devuelve el ranking completo del torneo, ordenado por puntos DESC, exactos DESC."""

    participantes = db.scalars(
        select(Participante).where(
            Participante.torneo_id == torneo_id,
            Participante.activo == True,
        )
    ).all()

    resultado: list[RankingItem] = []

    for p in participantes:
        pronosticos = db.scalars(
            select(Pronostico).where(Pronostico.participante_id == p.id)
        ).all()

        puntos_totales = 0
        aciertos_exactos = 0
        aciertos_ganador = 0
        partidos_pronosticados = 0

        for prono in pronosticos:
            partido: Partido | None = db.get(Partido, prono.partido_id)
            if partido is None or not partido.finalizado:
                continue
            if prono.puntos_obtenidos is None:
                continue

            partidos_pronosticados += 1
            puntos_totales += prono.puntos_obtenidos

            if (
                prono.goles_local == partido.goles_local
                and prono.goles_visitante == partido.goles_visitante
            ):
                aciertos_exactos += 1
            elif prono.puntos_obtenidos > 0:
                aciertos_ganador += 1

        resultado.append(
            RankingItem(
                posicion=0,  # se asigna abajo
                participante_id=p.id,
                nombre=p.nombre,
                email=p.email,
                puntos_totales=puntos_totales,
                aciertos_exactos=aciertos_exactos,
                aciertos_ganador=aciertos_ganador,
                partidos_pronosticados=partidos_pronosticados,
            )
        )

    # Ordenar: puntos DESC, exactos DESC
    resultado.sort(key=lambda r: (-r.puntos_totales, -r.aciertos_exactos))

    for i, item in enumerate(resultado, start=1):
        item.posicion = i

    return resultado
