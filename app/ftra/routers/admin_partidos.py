"""CRUD de partidos y carga de resultados (solo admins)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.ftra.database import get_db
from app.ftra.models.partido import Partido
from app.ftra.models.pronostico import Pronostico
from app.ftra.models.reglas_puntaje import ReglasPuntaje
from app.ftra.models.participante import Participante
from app.ftra.schemas.partido import PartidoCreate, PartidoUpdate, PartidoOut, ResultadoIn
from app.ftra.routers.deps import get_admin_participante
from app.ftra.services.puntos_service import recalcular_pronostico

router = APIRouter(prefix="/ftra/admin/partidos", tags=["ftra-admin-partidos"])


def _enrich(partido: Partido) -> dict:
    return {
        "id": partido.id,
        "torneo_id": partido.torneo_id,
        "fase_id": partido.fase_id,
        "grupo_id": partido.grupo_id,
        "sede_id": partido.sede_id,
        "seleccion_local_id": partido.seleccion_local_id,
        "seleccion_visitante_id": partido.seleccion_visitante_id,
        "seleccion_local_nombre": partido.seleccion_local.nombre if partido.seleccion_local else None,
        "seleccion_visitante_nombre": partido.seleccion_visitante.nombre if partido.seleccion_visitante else None,
        "fecha_partido": partido.fecha_partido,
        "cierre_pronostico": partido.cierre_pronostico,
        "goles_local": partido.goles_local,
        "goles_visitante": partido.goles_visitante,
        "finalizado": partido.finalizado,
        "created_at": partido.created_at,
    }


@router.get("/torneo/{torneo_id}")
def listar_partidos(torneo_id: int, db: Session = Depends(get_db)):
    partidos = db.scalars(
        select(Partido).where(Partido.torneo_id == torneo_id).order_by(Partido.fecha_partido)
    ).all()
    return [_enrich(p) for p in partidos]


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_partido(
    payload: PartidoCreate,
    db: Session = Depends(get_db),
):
    partido = Partido(**payload.model_dump())
    db.add(partido)
    db.commit()
    db.refresh(partido)
    return _enrich(partido)


@router.patch("/{partido_id}")
def actualizar_partido(
    partido_id: int,
    payload: PartidoUpdate,
    db: Session = Depends(get_db),
):
    partido = db.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(partido, field, value)
    db.commit()
    db.refresh(partido)
    return _enrich(partido)


@router.delete("/{partido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_partido(partido_id: int, db: Session = Depends(get_db)):
    partido = db.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    db.delete(partido)
    db.commit()


@router.post("/{partido_id}/resultado")
def cargar_resultado(
    partido_id: int,
    payload: ResultadoIn,
    db: Session = Depends(get_db),
):
    """Carga el resultado de un partido y opcionalmente recalcula puntos."""
    partido = db.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido.goles_local = payload.goles_local
    partido.goles_visitante = payload.goles_visitante
    partido.finalizado = True

    puntos_calculados = 0

    if payload.recalcular:
        reglas = db.scalars(
            select(ReglasPuntaje).where(ReglasPuntaje.torneo_id == partido.torneo_id)
        ).first()

        pronosticos = db.scalars(
            select(Pronostico).where(Pronostico.partido_id == partido_id)
        ).all()

        for prono in pronosticos:
            pts = recalcular_pronostico(prono, partido, reglas)
            prono.puntos_obtenidos = pts
            if pts is not None:
                puntos_calculados += 1

    db.commit()
    return {
        "ok": True,
        "partido_id": partido_id,
        "resultado": f"{payload.goles_local}-{payload.goles_visitante}",
        "pronosticos_recalculados": puntos_calculados,
    }


@router.post("/torneo/{torneo_id}/recalcular")
def recalcular_torneo(
    torneo_id: int,
    db: Session = Depends(get_db),
):
    """Recalcula todos los puntos de los partidos finalizados del torneo."""
    partidos = db.scalars(
        select(Partido).where(
            Partido.torneo_id == torneo_id,
            Partido.finalizado == True,
        )
    ).all()

    reglas = db.scalars(
        select(ReglasPuntaje).where(ReglasPuntaje.torneo_id == torneo_id)
    ).first()

    total = 0
    for partido in partidos:
        pronosticos = db.scalars(select(Pronostico).where(Pronostico.partido_id == partido.id)).all()
        for prono in pronosticos:
            prono.puntos_obtenidos = recalcular_pronostico(prono, partido, reglas)
            total += 1

    db.commit()
    return {"ok": True, "pronosticos_actualizados": total}
