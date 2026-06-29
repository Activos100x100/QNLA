"""Endpoints de pronósticos para participantes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.ftra.database import get_db
from app.ftra.models.partido import Partido
from app.ftra.models.participante import Participante
from app.ftra.models.pronostico import Pronostico
from app.ftra.schemas.pronostico import PronosticoCreate, PronosticoOut
from app.ftra.routers.deps import get_current_participante

router = APIRouter(prefix="/ftra/pronosticos", tags=["ftra-pronosticos"])


@router.get("/me")
def yo(current: Participante = Depends(get_current_participante)):
    return {
        "id": current.id,
        "email": current.email,
        "nombre": current.nombre,
        "torneo_id": current.torneo_id,
        "es_admin": current.es_admin,
    }


@router.get("/torneo/{torneo_id}", response_model=list[PronosticoOut])
def mis_pronosticos(
    torneo_id: int,
    db: Session = Depends(get_db),
    current: Participante = Depends(get_current_participante),
):
    if current.torneo_id != torneo_id:
        raise HTTPException(status_code=403, detail="No perteneces a este torneo")
    return db.scalars(
        select(Pronostico).where(Pronostico.participante_id == current.id)
    ).all()


@router.post("/", response_model=PronosticoOut, status_code=status.HTTP_201_CREATED)
def crear_o_actualizar_pronostico(
    payload: PronosticoCreate,
    db: Session = Depends(get_db),
    current: Participante = Depends(get_current_participante),
):
    partido = db.get(Partido, payload.partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    if partido.torneo_id != current.torneo_id:
        raise HTTPException(status_code=403, detail="El partido no pertenece a tu torneo")
    if datetime.now(timezone.utc) >= partido.cierre_pronostico.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=409, detail="El plazo de pronóstico está cerrado")
    if partido.finalizado:
        raise HTTPException(status_code=409, detail="No se puede pronosticar un partido finalizado")

    existing = db.scalars(
        select(Pronostico).where(
            Pronostico.participante_id == current.id,
            Pronostico.partido_id == payload.partido_id,
        )
    ).first()

    if existing:
        existing.goles_local = payload.goles_local
        existing.goles_visitante = payload.goles_visitante
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    prono = Pronostico(
        participante_id=current.id,
        partido_id=payload.partido_id,
        goles_local=payload.goles_local,
        goles_visitante=payload.goles_visitante,
    )
    db.add(prono)
    db.commit()
    db.refresh(prono)
    return prono


@router.get("/partido/{partido_id}", response_model=PronosticoOut)
def mi_pronostico_partido(
    partido_id: int,
    db: Session = Depends(get_db),
    current: Participante = Depends(get_current_participante),
):
    prono = db.scalars(
        select(Pronostico).where(
            Pronostico.participante_id == current.id,
            Pronostico.partido_id == partido_id,
        )
    ).first()
    if not prono:
        raise HTTPException(status_code=404, detail="Pronóstico no encontrado")
    return prono


@router.get("/estadisticas/{torneo_id}")
def estadisticas_pronosticos(torneo_id: int, db: Session = Depends(get_db)):
    """Estadísticas públicas de pronósticos por partido de un torneo."""
    partidos = db.scalars(
        select(Partido).where(Partido.torneo_id == torneo_id).order_by(Partido.fecha_partido)
    ).all()

    resultado = []
    for partido in partidos:
        pronos = db.scalars(
            select(Pronostico).where(Pronostico.partido_id == partido.id)
        ).all()

        total = len(pronos)
        apuestan_local = sum(1 for p in pronos if p.goles_local > p.goles_visitante)
        apuestan_empate = sum(1 for p in pronos if p.goles_local == p.goles_visitante)
        apuestan_visitante = sum(1 for p in pronos if p.goles_local < p.goles_visitante)

        def pct(n): return round(n * 100 / total, 1) if total > 0 else 0

        participantes_data = []
        for prono in sorted(pronos, key=lambda p: (p.participante.nombre or "") if p.participante else ""):
            participantes_data.append({
                "nombre": (prono.participante.nombre if prono.participante and prono.participante.nombre else "–"),
                "goles_local": prono.goles_local,
                "goles_visitante": prono.goles_visitante,
                "puntos_obtenidos": prono.puntos_obtenidos,
            })

        resultado.append({
            "partido_id": partido.id,
            "local": partido.seleccion_local.nombre if partido.seleccion_local else "?",
            "visitante": partido.seleccion_visitante.nombre if partido.seleccion_visitante else "?",
            "fecha_partido": partido.fecha_partido.isoformat() if partido.fecha_partido else None,
            "finalizado": partido.finalizado,
            "goles_local_real": partido.goles_local,
            "goles_visitante_real": partido.goles_visitante,
            "total_pronosticos": total,
            "apuestan_local": apuestan_local,
            "apuestan_empate": apuestan_empate,
            "apuestan_visitante": apuestan_visitante,
            "pct_local": pct(apuestan_local),
            "pct_empate": pct(apuestan_empate),
            "pct_visitante": pct(apuestan_visitante),
            "participantes": participantes_data,
        })

    return resultado
