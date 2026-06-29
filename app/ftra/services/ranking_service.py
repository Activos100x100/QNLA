"""Servicio de ranking para un torneo."""
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.ftra.models.participante import Participante
from app.ftra.models.pronostico import Pronostico
from app.ftra.models.partido import Partido
from app.ftra.schemas.ranking import RankingItem


def _datos_participantes(torneo_id: int, db: Session) -> dict[int, dict]:
    """Devuelve {participante_id: {nombre, email, telefono, ciudad, rol}} aplicando los mismos JOINs que el listado de participantes."""
    rows = db.execute(
        text(
            """
            SELECT
                p.id,
                p.nombre        AS p_nombre,
                p.alias         AS p_alias,
                p.email         AS p_email,
                p.empleado_id   AS empleado_id,
                e.nombre        AS e_nombre,
                e.apellidos     AS e_apellidos,
                e.telefono      AS e_telefono,
                c.name          AS ciudad,
                ea.departamento_id AS departamento_id,
                d.nombre        AS departamento_nombre,
                ro.cod_activo   AS cod_activo
            FROM qnla_participantes p
            LEFT JOIN empleados e ON e.id = p.empleado_id
            LEFT JOIN (
                SELECT DISTINCT ON (empleado_id)
                       empleado_id, ciudad_id, departamento_id
                FROM empleado_asignacion
                ORDER BY empleado_id,
                         (fecha_fin IS NULL) DESC,
                         fecha_inicio DESC
            ) ea ON ea.empleado_id = e.id
            LEFT JOIN ciudad c ON c.id = ea.ciudad_id
            LEFT JOIN departamento d ON d.id = ea.departamento_id
            LEFT JOIN (
                SELECT DISTINCT ON (empleado_id)
                       empleado_id, cod_activo
                FROM rider_operativo
                ORDER BY empleado_id,
                         (fecha_fin IS NULL) DESC,
                         COALESCE(activo, false) DESC,
                         fecha_inicio DESC
            ) ro ON ro.empleado_id = e.id
            WHERE p.torneo_id = :tid
            """
        ),
        {"tid": torneo_id},
    ).mappings().all()

    out: dict[int, dict] = {}
    for r in rows:
        nombre_completo = " ".join(x for x in [r["e_nombre"], r["e_apellidos"]] if x).strip()
        if not nombre_completo:
            nombre_completo = r["p_nombre"] or r["p_alias"] or (
                f"Empleado #{r['empleado_id']}" if r["empleado_id"] else f"Participante #{r['id']}"
            )
        if r["departamento_id"] == 7:
            rol = r["cod_activo"] or "Rider"
        else:
            rol = r["departamento_nombre"] or ("Administración" if r["empleado_id"] else "")

        out[r["id"]] = {
            "nombre": nombre_completo,
            "email": (r["p_email"] or ""),
            "telefono": (r["e_telefono"] or "").strip(),
            "ciudad": r["ciudad"] or "",
            "rol": rol,
        }
    return out


def calcular_ranking(torneo_id: int, db: Session) -> list[RankingItem]:
    """Devuelve el ranking completo del torneo, ordenado por puntos DESC, exactos DESC."""

    participantes = db.scalars(
        select(Participante).where(
            Participante.torneo_id == torneo_id,
            Participante.activo == True,
        )
    ).all()

    datos = _datos_participantes(torneo_id, db)
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

        info = datos.get(p.id, {"nombre": f"Participante #{p.id}", "email": "", "telefono": "", "ciudad": "", "rol": ""})

        resultado.append(
            RankingItem(
                posicion=0,  # se asigna abajo
                participante_id=p.id,
                nombre=info["nombre"],
                email=info["email"],
                telefono=info["telefono"],
                ciudad=info["ciudad"],
                rol=info["rol"],
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
