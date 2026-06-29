"""Lógica de cálculo de puntos — 100 % Python, sin SQL."""
from __future__ import annotations

from typing import Optional


def calcular_puntos(
    *,
    goles_local_real: int,
    goles_visitante_real: int,
    goles_local_prono: int,
    goles_visitante_prono: int,
    puntos_exacto: int = 3,
    puntos_ganador: int = 1,
    puntos_fallo: int = 0,
) -> int:
    """Devuelve los puntos obtenidos por un pronóstico.

    Reglas:
    - Exacto (mismo marcador)            → puntos_exacto  (default 3)
    - Ganador/empate correcto (no exact) → puntos_ganador (default 1)
    - Fallo                               → puntos_fallo   (default 0)
    """
    if goles_local_real == goles_local_prono and goles_visitante_real == goles_visitante_prono:
        return puntos_exacto

    resultado_real = _resultado(goles_local_real, goles_visitante_real)
    resultado_prono = _resultado(goles_local_prono, goles_visitante_prono)

    if resultado_real == resultado_prono:
        return puntos_ganador

    return puntos_fallo


def _resultado(goles_local: int, goles_visitante: int) -> str:
    """Devuelve 'L' (local), 'E' (empate) o 'V' (visitante)."""
    if goles_local > goles_visitante:
        return "L"
    if goles_local < goles_visitante:
        return "V"
    return "E"


def recalcular_pronostico(
    pronostico,
    partido,
    reglas,
) -> Optional[int]:
    """Recalcula puntos de un Pronostico ORM dado el Partido y ReglasPuntaje.

    Devuelve None si el partido no tiene resultado todavía.
    """
    if partido.goles_local is None or partido.goles_visitante is None:
        return None

    return calcular_puntos(
        goles_local_real=partido.goles_local,
        goles_visitante_real=partido.goles_visitante,
        goles_local_prono=pronostico.goles_local,
        goles_visitante_prono=pronostico.goles_visitante,
        puntos_exacto=reglas.puntos_exacto if reglas else 3,
        puntos_ganador=reglas.puntos_ganador if reglas else 1,
        puntos_fallo=reglas.puntos_fallo if reglas else 0,
    )
