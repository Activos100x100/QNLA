"""Seed inicial de ejemplo para FTRA.

Uso (opcional):
  python -m app.ftra.seed
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from app.ftra.database import SessionLocal, Base, engine
from app.ftra.models.torneo import Torneo
from app.ftra.models.reglas_puntaje import ReglasPuntaje
from app.ftra.models.fase import Fase
from app.ftra.models.grupo import Grupo
from app.ftra.models.seleccion import Seleccion
from app.ftra.models.sede import Sede


FASES_MUNDIAL_2026: list[tuple[str, int, bool]] = [
    ("Fase de Grupos", 1, False),
    ("32avos", 2, True),
    ("Octavos", 3, True),
    ("Cuartos", 4, True),
    ("Semis", 5, True),
    ("3er Puesto", 6, True),
    ("Final", 7, True),
]

GRUPOS_MUNDIAL_2026 = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

SELECCIONES_MUNDIAL_2026: dict[str, list[tuple[str, str]]] = {
    "A": [("México", "MEX"), ("Estados Unidos", "USA"), ("Canadá", "CAN"), ("Costa Rica", "CRC")],
    "B": [("Argentina", "ARG"), ("Uruguay", "URU"), ("Chile", "CHI"), ("Paraguay", "PAR")],
    "C": [("Brasil", "BRA"), ("Colombia", "COL"), ("Ecuador", "ECU"), ("Perú", "PER")],
    "D": [("España", "ESP"), ("Portugal", "POR"), ("Italia", "ITA"), ("Croacia", "CRO")],
    "E": [("Francia", "FRA"), ("Alemania", "GER"), ("Países Bajos", "NED"), ("Bélgica", "BEL")],
    "F": [("Inglaterra", "ENG"), ("Suiza", "SUI"), ("Dinamarca", "DEN"), ("Polonia", "POL")],
    "G": [("Marruecos", "MAR"), ("Senegal", "SEN"), ("Túnez", "TUN"), ("Egipto", "EGY")],
    "H": [("Nigeria", "NGA"), ("Camerún", "CMR"), ("Ghana", "GHA"), ("Costa de Marfil", "CIV")],
    "I": [("Japón", "JPN"), ("Corea del Sur", "KOR"), ("Irán", "IRN"), ("Arabia Saudita", "KSA")],
    "J": [("Australia", "AUS"), ("Nueva Zelanda", "NZL"), ("Qatar", "QAT"), ("Emiratos Árabes Unidos", "UAE")],
    "K": [("Serbia", "SRB"), ("Austria", "AUT"), ("República Checa", "CZE"), ("Ucrania", "UKR")],
    "L": [("Turquía", "TUR"), ("Suecia", "SWE"), ("Noruega", "NOR"), ("Grecia", "GRE")],
}

SEDES_MUNDIAL_2026: list[tuple[str, str, str, int]] = [
    # México (3)
    ("Estadio Azteca", "Ciudad de México", "México", 87000),
    ("Estadio Akron", "Guadalajara", "México", 48000),
    ("Estadio BBVA", "Monterrey", "México", 53000),
    # Canadá (2)
    ("BC Place", "Vancouver", "Canadá", 54000),
    ("BMO Field", "Toronto", "Canadá", 45000),
    # Estados Unidos (11)
    ("MetLife Stadium", "New York/New Jersey", "Estados Unidos", 82500),
    ("SoFi Stadium", "Los Angeles", "Estados Unidos", 70000),
    ("AT&T Stadium", "Dallas", "Estados Unidos", 80000),
    ("NRG Stadium", "Houston", "Estados Unidos", 72200),
    ("Lumen Field", "Seattle", "Estados Unidos", 69000),
    ("Levi's Stadium", "San Francisco Bay Area", "Estados Unidos", 68500),
    ("Mercedes-Benz Stadium", "Atlanta", "Estados Unidos", 71000),
    ("Lincoln Financial Field", "Philadelphia", "Estados Unidos", 69500),
    ("Hard Rock Stadium", "Miami", "Estados Unidos", 65300),
    ("Gillette Stadium", "Boston", "Estados Unidos", 65800),
    ("Arrowhead Stadium", "Kansas City", "Estados Unidos", 76400),
]

TORNEO_FECHA_INICIO = date(2026, 6, 11)
TORNEO_FECHA_FIN = date(2026, 7, 19)
TORNEO_CIERRE_INSCRIPCION = datetime(2026, 6, 10, 23, 59, tzinfo=timezone.utc)


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        torneo = db.query(Torneo).filter(Torneo.nombre == "Mundial 2026", Torneo.anio == 2026).first()
        if not torneo:
            torneo = Torneo(
                nombre="Mundial 2026",
                anio=2026,
                descripcion="Quiniela oficial",
                fecha_inicio=TORNEO_FECHA_INICIO,
                fecha_fin=TORNEO_FECHA_FIN,
                cierre_inscripcion=TORNEO_CIERRE_INSCRIPCION,
            )
            db.add(torneo)
            db.flush()
        else:
            torneo.descripcion = torneo.descripcion or "Quiniela oficial"
            if not torneo.fecha_inicio:
                torneo.fecha_inicio = TORNEO_FECHA_INICIO
            if not torneo.fecha_fin:
                torneo.fecha_fin = TORNEO_FECHA_FIN
            if not torneo.cierre_inscripcion:
                torneo.cierre_inscripcion = TORNEO_CIERRE_INSCRIPCION

        # Reglas 1:1 por torneo
        reglas = db.query(ReglasPuntaje).filter(ReglasPuntaje.torneo_id == torneo.id).first()
        if not reglas:
            reglas = ReglasPuntaje(
                torneo_id=torneo.id,
                puntos_exacto=3,
                puntos_ganador=1,
                puntos_fallo=0,
            )
            db.add(reglas)
        else:
            reglas.puntos_exacto = 3
            reglas.puntos_ganador = 1
            reglas.puntos_fallo = 0

        # Fases (7)
        for nombre, orden, es_eliminatoria in FASES_MUNDIAL_2026:
            fase = db.query(Fase).filter(Fase.torneo_id == torneo.id, Fase.nombre == nombre).first()
            if not fase:
                fase = Fase(
                    torneo_id=torneo.id,
                    nombre=nombre,
                    orden=orden,
                    es_eliminatoria=es_eliminatoria,
                )
                db.add(fase)
            else:
                fase.orden = orden
                fase.es_eliminatoria = es_eliminatoria

        # Grupos (A-L)
        for nombre_grupo in GRUPOS_MUNDIAL_2026:
            grupo = db.query(Grupo).filter(Grupo.torneo_id == torneo.id, Grupo.nombre == nombre_grupo).first()
            if not grupo:
                db.add(Grupo(torneo_id=torneo.id, nombre=nombre_grupo))

        db.flush()

        grupos = db.query(Grupo).filter(Grupo.torneo_id == torneo.id).all()
        grupos_por_nombre = {g.nombre: g for g in grupos}

        # Selecciones (48)
        for nombre_grupo, selecciones in SELECCIONES_MUNDIAL_2026.items():
            grupo = grupos_por_nombre.get(nombre_grupo)
            grupo_id = grupo.id if grupo else None

            for nombre_seleccion, codigo_fifa in selecciones:
                seleccion = db.query(Seleccion).filter(
                    Seleccion.torneo_id == torneo.id,
                    Seleccion.nombre == nombre_seleccion,
                ).first()

                if not seleccion:
                    seleccion = Seleccion(
                        torneo_id=torneo.id,
                        nombre=nombre_seleccion,
                        codigo_fifa=codigo_fifa,
                        grupo_id=grupo_id,
                    )
                    db.add(seleccion)
                else:
                    seleccion.codigo_fifa = codigo_fifa
                    seleccion.grupo_id = grupo_id

        # Sedes (16)
        for nombre, ciudad, pais, capacidad in SEDES_MUNDIAL_2026:
            sede = db.query(Sede).filter(Sede.torneo_id == torneo.id, Sede.nombre == nombre).first()
            if not sede:
                sede = Sede(
                    torneo_id=torneo.id,
                    nombre=nombre,
                    ciudad=ciudad,
                    pais=pais,
                    capacidad=capacidad,
                )
                db.add(sede)
            else:
                sede.ciudad = ciudad
                sede.pais = pais
                sede.capacidad = capacidad

        db.commit()
        print("✅ Seed completado: Mundial 2026 (7 fases, 12 grupos, 48 selecciones, 16 sedes)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
