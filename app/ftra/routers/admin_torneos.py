"""CRUD de torneos (solo admins)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func

from app.ftra.database import get_db
from app.ftra.models.torneo import Torneo
from app.ftra.models.reglas_puntaje import ReglasPuntaje
from app.ftra.models.participante import Participante
from app.ftra.models.fase import Fase
from app.ftra.models.grupo import Grupo
from app.ftra.models.seleccion import Seleccion
from app.ftra.models.sede import Sede
from app.ftra.models.partido import Partido
from app.ftra.models.pronostico import Pronostico
from app.ftra.schemas.torneo import TorneoCreate, TorneoUpdate, TorneoOut, ReglasPuntajeUpdate


# ── Schemas para configuración del torneo (carga manual) ────────────────────

class FaseIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=50)
    orden: int = 0
    es_eliminatoria: bool = False


class GrupoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=5)


class SedeIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    ciudad: str = Field(min_length=1, max_length=100)
    pais: str = Field(min_length=1, max_length=100)
    capacidad: Optional[int] = None


class SeleccionIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    codigo_fifa: str = Field(min_length=2, max_length=3)
    grupo_id: Optional[int] = None
    bandera_url: Optional[str] = None

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
def listar_participantes(
    torneo_id: int,
    q: str = "",
    db: Session = Depends(get_db),
):
    """Lista todos los empleados de alta con su estado de participación en el torneo.

    - Empleado "de alta" = tiene una asignación vigente (fecha_inicio <= hoy y (fecha_fin IS NULL o >= hoy)).
    - Si `q` se proporciona, filtra por nombre o apellidos (LIKE case-insensitive).
    """
    from sqlalchemy import text

    qlike = f"%{q.strip().lower()}%" if q and q.strip() else None

    rows = db.execute(
        text(
            """
            WITH ea_actual AS (
                SELECT DISTINCT ON (ea.empleado_id)
                       ea.empleado_id, ea.ciudad_id, ea.departamento_id
                FROM empleado_asignacion ea
                WHERE (ea.fecha_inicio IS NULL OR ea.fecha_inicio::date <= CURRENT_DATE)
                  AND (ea.fecha_fin    IS NULL OR ea.fecha_fin::date    >= CURRENT_DATE)
                ORDER BY ea.empleado_id,
                         (ea.fecha_fin IS NULL) DESC,
                         ea.fecha_inicio DESC NULLS LAST,
                         ea.id DESC
            ),
            ro_actual AS (
                SELECT DISTINCT ON (empleado_id)
                       empleado_id, cod_activo
                FROM rider_operativo
                ORDER BY empleado_id,
                         (fecha_fin IS NULL) DESC,
                         COALESCE(activo, false) DESC,
                         fecha_inicio DESC NULLS LAST
            )
            SELECT
                e.id            AS empleado_id,
                e.nombre        AS e_nombre,
                e.apellidos     AS e_apellidos,
                e.telefono      AS e_telefono,
                c.name          AS ciudad,
                ea.departamento_id AS departamento_id,
                d.nombre        AS departamento_nombre,
                ro.cod_activo   AS cod_activo,
                p.id            AS participante_id,
                p.activo        AS participante_activo,
                p.es_admin      AS p_es_admin
            FROM empleados e
            JOIN ea_actual ea       ON ea.empleado_id = e.id
            LEFT JOIN ciudad c      ON c.id = ea.ciudad_id
            LEFT JOIN departamento d ON d.id = ea.departamento_id
            LEFT JOIN ro_actual ro  ON ro.empleado_id = e.id
            LEFT JOIN qnla_participantes p
                   ON p.empleado_id = e.id AND p.torneo_id = :tid
            WHERE (:qlike IS NULL
                   OR LOWER(COALESCE(e.nombre, '') || ' ' || COALESCE(e.apellidos, '')) LIKE :qlike)
            ORDER BY e.nombre, e.apellidos
            """
        ),
        {"tid": torneo_id, "qlike": qlike},
    ).mappings().all()

    out = []
    for r in rows:
        nombre_completo = " ".join(
            x for x in [r["e_nombre"], r["e_apellidos"]] if x
        ).strip() or f"Empleado #{r['empleado_id']}"

        if r["departamento_id"] == 7:
            rol = r["cod_activo"] or "Rider"
        else:
            rol = r["departamento_nombre"] or "Administración"

        out.append({
            "empleado_id": r["empleado_id"],
            "participante_id": r["participante_id"],
            "nombre": nombre_completo,
            "telefono": (r["e_telefono"] or "").strip(),
            "ciudad": r["ciudad"] or "",
            "rol": rol,
            "es_admin": bool(r["p_es_admin"]) if r["p_es_admin"] is not None else False,
            # Si no existe registro, lo consideramos activo por defecto (alta = participante).
            "activo": bool(r["participante_activo"]) if r["participante_activo"] is not None else True,
        })
    return out


def _get_or_create_participante(torneo_id: int, empleado_id: int, db: Session) -> Participante:
    """Upsert: devuelve el Participante existente o crea uno enlazado al empleado."""
    p = db.scalars(
        select(Participante).where(
            Participante.torneo_id == torneo_id,
            Participante.empleado_id == empleado_id,
        )
    ).first()
    if p:
        return p

    from sqlalchemy import text
    row = db.execute(
        text("SELECT nombre, apellidos FROM empleados WHERE id = :eid"),
        {"eid": empleado_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    nombre = " ".join(x for x in [row["nombre"], row["apellidos"]] if x).strip() or f"Empleado #{empleado_id}"
    # email sintético único por empleado/torneo para satisfacer el unique
    email = f"empleado-{empleado_id}@ftra.local"

    p = Participante(
        torneo_id=torneo_id,
        empleado_id=empleado_id,
        nombre=nombre,
        email=email,
        password_hash=f"empleado:{empleado_id}",
        es_admin=False,
        activo=True,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{torneo_id}/participantes/empleado/{empleado_id}/suspender")
def suspender_participante(
    torneo_id: int,
    empleado_id: int,
    db: Session = Depends(get_db),
):
    """Alterna el estado activo del participante (upsert si aún no existe)."""
    p = _get_or_create_participante(torneo_id, empleado_id, db)
    p.activo = not p.activo
    db.commit()
    return {"participante_id": p.id, "activo": p.activo}


@router.delete("/{torneo_id}/participantes/empleado/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_participante(
    torneo_id: int,
    empleado_id: int,
    db: Session = Depends(get_db),
):
    """Elimina el registro de participación (con sus pronósticos)."""
    p = db.scalars(
        select(Participante).where(
            Participante.torneo_id == torneo_id,
            Participante.empleado_id == empleado_id,
        )
    ).first()
    if p:
        db.delete(p)
        db.commit()
    return None


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

@router.get("/{torneo_id}/fases")
def listar_fases(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Fase).where(Fase.torneo_id == torneo_id).order_by(Fase.orden, Fase.id)
    ).all()
    return [
        {"id": f.id, "nombre": f.nombre, "orden": f.orden, "es_eliminatoria": f.es_eliminatoria}
        for f in rows
    ]


@router.post("/{torneo_id}/fases", status_code=status.HTTP_201_CREATED)
def crear_fase(
    torneo_id: int,
    payload: FaseIn,
    db: Session = Depends(get_db),
):
    if not db.get(Torneo, torneo_id):
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    fase = Fase(
        torneo_id=torneo_id,
        nombre=payload.nombre.strip(),
        orden=payload.orden,
        es_eliminatoria=payload.es_eliminatoria,
    )
    db.add(fase)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una fase con ese nombre en el torneo")
    db.refresh(fase)
    return {"id": fase.id, "nombre": fase.nombre, "orden": fase.orden, "es_eliminatoria": fase.es_eliminatoria}


@router.delete("/{torneo_id}/fases/{fase_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_fase(torneo_id: int, fase_id: int, db: Session = Depends(get_db)):
    fase = db.get(Fase, fase_id)
    if not fase or fase.torneo_id != torneo_id:
        raise HTTPException(status_code=404, detail="Fase no encontrada")
    db.delete(fase)
    db.commit()


@router.get("/{torneo_id}/grupos")
def listar_grupos(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Grupo).where(Grupo.torneo_id == torneo_id).order_by(Grupo.nombre)
    ).all()
    return [{"id": g.id, "nombre": g.nombre} for g in rows]


@router.post("/{torneo_id}/grupos", status_code=status.HTTP_201_CREATED)
def crear_grupo(torneo_id: int, payload: GrupoIn, db: Session = Depends(get_db)):
    if not db.get(Torneo, torneo_id):
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    grupo = Grupo(torneo_id=torneo_id, nombre=payload.nombre.strip().upper())
    db.add(grupo)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un grupo con ese nombre en el torneo")
    db.refresh(grupo)
    return {"id": grupo.id, "nombre": grupo.nombre}


@router.delete("/{torneo_id}/grupos/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_grupo(torneo_id: int, grupo_id: int, db: Session = Depends(get_db)):
    grupo = db.get(Grupo, grupo_id)
    if not grupo or grupo.torneo_id != torneo_id:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    db.delete(grupo)
    db.commit()


# ── Selecciones ─────────────────────────────────────────────────────────────

@router.get("/{torneo_id}/selecciones")
def listar_selecciones(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Seleccion).where(Seleccion.torneo_id == torneo_id).order_by(Seleccion.nombre)
    ).all()
    return [
        {"id": s.id, "nombre": s.nombre, "codigo_fifa": s.codigo_fifa, "grupo_id": s.grupo_id}
        for s in rows
    ]


@router.post("/{torneo_id}/selecciones", status_code=status.HTTP_201_CREATED)
def crear_seleccion(
    torneo_id: int,
    payload: SeleccionIn,
    db: Session = Depends(get_db),
):
    if not db.get(Torneo, torneo_id):
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    s = Seleccion(
        torneo_id=torneo_id,
        nombre=payload.nombre.strip(),
        codigo_fifa=payload.codigo_fifa.strip().upper()[:3],
        grupo_id=payload.grupo_id,
        bandera_url=payload.bandera_url,
    )
    db.add(s)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una selección con ese nombre en el torneo")
    db.refresh(s)
    return {"id": s.id, "nombre": s.nombre, "codigo_fifa": s.codigo_fifa, "grupo_id": s.grupo_id}


@router.delete("/{torneo_id}/selecciones/{seleccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_seleccion(torneo_id: int, seleccion_id: int, db: Session = Depends(get_db)):
    s = db.get(Seleccion, seleccion_id)
    if not s or s.torneo_id != torneo_id:
        raise HTTPException(status_code=404, detail="Selección no encontrada")
    db.delete(s)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: la selección tiene partidos asociados")


# ── Sedes ────────────────────────────────────────────────────────────────────

@router.get("/{torneo_id}/sedes")
def listar_sedes(torneo_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Sede).where(Sede.torneo_id == torneo_id).order_by(Sede.nombre)
    ).all()
    return [
        {"id": s.id, "nombre": s.nombre, "ciudad": s.ciudad, "pais": s.pais, "capacidad": s.capacidad}
        for s in rows
    ]


@router.post("/{torneo_id}/sedes", status_code=status.HTTP_201_CREATED)
def crear_sede(
    torneo_id: int,
    payload: SedeIn,
    db: Session = Depends(get_db),
):
    if not db.get(Torneo, torneo_id):
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    sede = Sede(
        torneo_id=torneo_id,
        nombre=payload.nombre.strip(),
        ciudad=payload.ciudad.strip(),
        pais=payload.pais.strip(),
        capacidad=payload.capacidad,
    )
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return {"id": sede.id, "nombre": sede.nombre, "ciudad": sede.ciudad, "pais": sede.pais, "capacidad": sede.capacidad}


@router.delete("/{torneo_id}/sedes/{sede_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sede(torneo_id: int, sede_id: int, db: Session = Depends(get_db)):
    sede = db.get(Sede, sede_id)
    if not sede or sede.torneo_id != torneo_id:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    db.delete(sede)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: la sede tiene partidos asociados")


# ── Resumen de configuración del torneo ─────────────────────────────────────

@router.get("/{torneo_id}/resumen")
def resumen_torneo(torneo_id: int, db: Session = Depends(get_db)):
    if not db.get(Torneo, torneo_id):
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    def _count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model).where(model.torneo_id == torneo_id)) or 0)

    partidos_jugados = int(
        db.scalar(
            select(func.count()).select_from(Partido).where(
                Partido.torneo_id == torneo_id, Partido.finalizado == True
            )
        )
        or 0
    )

    return {
        "torneo_id": torneo_id,
        "fases": _count(Fase),
        "grupos": _count(Grupo),
        "sedes": _count(Sede),
        "selecciones": _count(Seleccion),
        "participantes": _count(Participante),
        "partidos": _count(Partido),
        "partidos_finalizados": partidos_jugados,
    }

