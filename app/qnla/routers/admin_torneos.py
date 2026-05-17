"""CRUD de torneos (solo admins)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.qnla.database import get_db
from app.qnla.models.torneo import Torneo
from app.qnla.models.reglas_puntaje import ReglasPuntaje
from app.qnla.models.participante import Participante
from app.qnla.models.fase import Fase
from app.qnla.models.grupo import Grupo
from app.qnla.models.seleccion import Seleccion
from app.qnla.models.sede import Sede
from app.qnla.models.partido import Partido
from app.qnla.models.pronostico import Pronostico
from app.qnla.schemas.torneo import TorneoCreate, TorneoUpdate, TorneoOut, ReglasPuntajeUpdate

router = APIRouter(prefix="/api/torneos", tags=["api-torneos"])

public_router = APIRouter(prefix="/api/torneos-public", tags=["api-torneos-public"])


def _identity_candidates(request: Request) -> list[str]:
    values: list[str] = []
    header_name = (request.headers.get("x-user-name") or "").strip().lower()
    header_email = (request.headers.get("x-user-email") or "").strip().lower()
    if header_name:
        values.append(header_name)
    if header_email:
        values.append(header_email)
    try:
        session_name = (request.session.get("user_name") or "").strip().lower()
        session_email = (request.session.get("user_email") or "").strip().lower()
    except Exception:
        session_name = ""
        session_email = ""
    if session_name:
        values.append(session_name)
    if session_email:
        values.append(session_email)
    return list(dict.fromkeys(values))


def _is_torneo_admin(db: Session, identities: list[str], torneo_id: int | None = None) -> bool:
    if not identities:
        return False
    stmt = select(Torneo)
    if torneo_id is not None:
        stmt = stmt.where(Torneo.id == torneo_id)
    torneos = db.scalars(stmt).all()
    for t in torneos:
        admin_value = (getattr(t, "admin", None) or "").strip().lower()
        if admin_value and admin_value in identities:
            return True
    return False


def get_torneo_admin_access(request: Request, db: Session = Depends(get_db)) -> bool:
    identities = _identity_candidates(request)
    if _is_torneo_admin(db, identities):
        return True
    raise HTTPException(status_code=403, detail="Se requiere rol de administrador del torneo")


def get_torneo_admin_access_torneo(
    torneo_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> bool:
    identities = _identity_candidates(request)
    if _is_torneo_admin(db, identities, torneo_id=torneo_id):
        return True
    raise HTTPException(status_code=403, detail="No eres administrador de este torneo")


@public_router.get("/admin-mode")
def torneo_admin_mode(request: Request, db: Session = Depends(get_db)):
    identities = _identity_candidates(request)
    is_admin = _is_torneo_admin(db, identities)
    return {"is_admin": is_admin}


@public_router.get("/activos", response_model=list[TorneoOut])
def listar_torneos_activos(db: Session = Depends(get_db)):
    """Endpoint público: devuelve torneos con activo=True."""
    return db.scalars(
        select(Torneo).where(Torneo.activo == True).order_by(Torneo.anio.desc())
    ).all()


@public_router.get("/{torneo_id}/reglas")
def obtener_reglas_torneo(torneo_id: int, db: Session = Depends(get_db)):
    reglas = db.scalars(
        select(ReglasPuntaje).where(ReglasPuntaje.torneo_id == torneo_id)
    ).first()
    if not reglas:
        return {
            "torneo_id": torneo_id,
            "puntos_exacto": 3,
            "puntos_ganador": 1,
            "puntos_fallo": 0,
        }
    return {
        "torneo_id": torneo_id,
        "puntos_exacto": reglas.puntos_exacto,
        "puntos_ganador": reglas.puntos_ganador,
        "puntos_fallo": reglas.puntos_fallo,
    }


@router.get("/", response_model=list[TorneoOut])
def listar_torneos(db: Session = Depends(get_db)):
    return db.scalars(select(Torneo).order_by(Torneo.anio.desc())).all()


@router.post("/", response_model=TorneoOut, status_code=status.HTTP_201_CREATED)
def crear_torneo(
    request: Request,
    payload: TorneoCreate,
    db: Session = Depends(get_db),
):
    inferred_admin = payload.admin or (request.headers.get("x-user-name") or request.headers.get("x-user-email") or "").strip()
    torneo = Torneo(
        nombre=payload.nombre,
        anio=payload.anio,
        descripcion=payload.descripcion,
        admin=inferred_admin or None,
        activo=payload.activo,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        cierre_inscripcion=payload.cierre_inscripcion,
    )
    db.add(torneo)
    db.flush()

    reglas = ReglasPuntaje(
        torneo_id=torneo.id,
        puntos_exacto=payload.puntos_exacto,
        puntos_ganador=payload.puntos_ganador,
        puntos_fallo=payload.puntos_fallo,
    )
    db.add(reglas)
    db.commit()
    db.refresh(torneo)
    return torneo


@router.get("/{torneo_id}", response_model=TorneoOut)
def obtener_torneo(torneo_id: int, db: Session = Depends(get_db)):
    torneo = db.get(Torneo, torneo_id)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return torneo


@router.patch("/{torneo_id}", response_model=TorneoOut)
def actualizar_torneo(
    torneo_id: int,
    payload: TorneoUpdate,
    db: Session = Depends(get_db),

):
    torneo = db.get(Torneo, torneo_id)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    updates = payload.model_dump(exclude_unset=True)
    fecha_inicio_nueva = updates.get("fecha_inicio", torneo.fecha_inicio)
    fecha_fin_nueva = updates.get("fecha_fin", torneo.fecha_fin)
    if fecha_inicio_nueva and fecha_fin_nueva and fecha_fin_nueva < fecha_inicio_nueva:
        raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")

    for field, value in updates.items():
        setattr(torneo, field, value)
    db.commit()
    db.refresh(torneo)
    return torneo


@router.patch("/{torneo_id}/reglas")
def actualizar_reglas_torneo(
    torneo_id: int,
    payload: ReglasPuntajeUpdate,
    db: Session = Depends(get_db),
):
    torneo = db.get(Torneo, torneo_id)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    reglas = db.scalars(
        select(ReglasPuntaje).where(ReglasPuntaje.torneo_id == torneo_id)
    ).first()

    if not reglas:
        reglas = ReglasPuntaje(
            torneo_id=torneo_id,
            puntos_exacto=payload.puntos_exacto,
            puntos_ganador=payload.puntos_ganador,
            puntos_fallo=payload.puntos_fallo,
        )
        db.add(reglas)
    else:
        reglas.puntos_exacto = payload.puntos_exacto
        reglas.puntos_ganador = payload.puntos_ganador
        reglas.puntos_fallo = payload.puntos_fallo

    db.commit()
    db.refresh(reglas)
    return {
        "torneo_id": torneo_id,
        "puntos_exacto": reglas.puntos_exacto,
        "puntos_ganador": reglas.puntos_ganador,
        "puntos_fallo": reglas.puntos_fallo,
    }


@router.delete("/{torneo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_torneo(
    torneo_id: int,
    db: Session = Depends(get_db),
):
    torneo = db.get(Torneo, torneo_id)
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    # Limpieza explícita de dependencias para asegurar borrado total
    # incluso en esquemas legacy donde los CASCADE puedan no estar completos.
    db.execute(
        delete(Pronostico).where(
            Pronostico.partido_id.in_(select(Partido.id).where(Partido.torneo_id == torneo_id))
        )
    )
    db.execute(
        delete(Pronostico).where(
            Pronostico.participante_id.in_(
                select(Participante.id).where(Participante.torneo_id == torneo_id)
            )
        )
    )
    db.execute(delete(Partido).where(Partido.torneo_id == torneo_id))
    db.execute(delete(ReglasPuntaje).where(ReglasPuntaje.torneo_id == torneo_id))
    db.execute(delete(Seleccion).where(Seleccion.torneo_id == torneo_id))
    db.execute(delete(Sede).where(Sede.torneo_id == torneo_id))
    db.execute(delete(Grupo).where(Grupo.torneo_id == torneo_id))
    db.execute(delete(Fase).where(Fase.torneo_id == torneo_id))
    db.execute(delete(Participante).where(Participante.torneo_id == torneo_id))
    db.delete(torneo)
    db.commit()


# ── Participantes del torneo ────────────────────────────────────────────────

@router.get("/{torneo_id}/participantes")
def listar_participantes(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(Participante).where(Participante.torneo_id == torneo_id)).all()
    return [{"id": p.id, "nombre": p.nombre, "email": p.email, "es_admin": p.es_admin, "activo": p.activo} for p in rows]


@router.post("/{torneo_id}/participantes", status_code=status.HTTP_201_CREATED)
def crear_participante(
    torneo_id: int,
    nombre: str,
    email: str,
    es_admin: bool = False,
    db: Session = Depends(get_db),
):
    existing = db.scalars(
        select(Participante).where(Participante.torneo_id == torneo_id, Participante.email == email.lower())
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un participante con ese email en este torneo")

    p = Participante(
        torneo_id=torneo_id,
        nombre=nombre,
        email=email.lower(),
        password_hash=f"google:{email.lower()}",
        es_admin=es_admin,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "nombre": p.nombre, "email": p.email}


# ── Fases y grupos ──────────────────────────────────────────────────────────

@router.post("/{torneo_id}/fases", status_code=status.HTTP_201_CREATED)
def crear_fase(
    torneo_id: int,
    nombre: str,
    orden: int = 0,
    es_eliminatoria: bool = False,
    db: Session = Depends(get_db),
):
    fase = Fase(torneo_id=torneo_id, nombre=nombre, orden=orden, es_eliminatoria=es_eliminatoria)
    db.add(fase)
    db.commit()
    db.refresh(fase)
    return {"id": fase.id, "nombre": fase.nombre, "orden": fase.orden, "es_eliminatoria": fase.es_eliminatoria}


@router.post("/{torneo_id}/grupos", status_code=status.HTTP_201_CREATED)
def crear_grupo(torneo_id: int, nombre: str, db: Session = Depends(get_db)):
    grupo = Grupo(torneo_id=torneo_id, nombre=nombre)
    db.add(grupo)
    db.commit()
    db.refresh(grupo)
    return {"id": grupo.id, "nombre": grupo.nombre}


# ── Selecciones ─────────────────────────────────────────────────────────────

@router.get("/{torneo_id}/selecciones")
def listar_selecciones(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(Seleccion).where(Seleccion.torneo_id == torneo_id)).all()
    return [{"id": s.id, "nombre": s.nombre, "codigo_fifa": s.codigo_fifa, "grupo_id": s.grupo_id} for s in rows]


@router.post("/{torneo_id}/selecciones", status_code=status.HTTP_201_CREATED)
def crear_seleccion(
    torneo_id: int,
    nombre: str,
    codigo_fifa: str,
    grupo_id: int | None = None,
    bandera_url: str | None = None,
    db: Session = Depends(get_db),
):
    s = Seleccion(torneo_id=torneo_id, nombre=nombre, codigo_fifa=codigo_fifa.upper()[:3], grupo_id=grupo_id, bandera_url=bandera_url)
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "nombre": s.nombre, "codigo_fifa": s.codigo_fifa}


# ── Sedes ────────────────────────────────────────────────────────────────────

@router.get("/{torneo_id}/sedes")
def listar_sedes(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(Sede).where(Sede.torneo_id == torneo_id)).all()
    return [{"id": s.id, "nombre": s.nombre, "ciudad": s.ciudad, "pais": s.pais} for s in rows]


@router.post("/{torneo_id}/sedes", status_code=status.HTTP_201_CREATED)
def crear_sede(
    torneo_id: int,
    nombre: str,
    ciudad: str,
    pais: str,
    capacidad: int | None = None,
    db: Session = Depends(get_db),
):
    sede = Sede(torneo_id=torneo_id, nombre=nombre, ciudad=ciudad, pais=pais, capacidad=capacidad)
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return {"id": sede.id, "nombre": sede.nombre, "ciudad": sede.ciudad}
