"""align qnla tables 2-7 to catalog

Revision ID: 20260516_03
Revises: 20260516_02
Create Date: 2026-05-16 18:45:00
"""
from alembic import op
import sqlalchemy as sa


revision = "20260516_03"
down_revision = "20260516_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 2) qnla_reglas_puntaje
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje RENAME COLUMN exacto_puntos TO puntos_exacto"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje RENAME COLUMN ganador_empate_puntos TO puntos_ganador"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje RENAME COLUMN fallo_puntos TO puntos_fallo"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN puntos_exacto TYPE SMALLINT"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN puntos_ganador TYPE SMALLINT"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN puntos_fallo TYPE SMALLINT"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE"))
    conn.execute(sa.text("UPDATE qnla_reglas_puntaje SET created_at = NOW() WHERE created_at IS NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN created_at SET NOT NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje DROP CONSTRAINT IF EXISTS uq_qnla_reglas_puntaje_torneo"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ADD CONSTRAINT uq_qnla_reglas_puntaje_torneo UNIQUE (torneo_id)"))

    # 3) qnla_fases
    conn.execute(sa.text("ALTER TABLE qnla_fases ALTER COLUMN nombre TYPE VARCHAR(50)"))
    conn.execute(sa.text("ALTER TABLE qnla_fases ALTER COLUMN orden TYPE SMALLINT"))
    conn.execute(sa.text("ALTER TABLE qnla_fases ADD COLUMN IF NOT EXISTS es_eliminatoria BOOLEAN"))
    conn.execute(sa.text("UPDATE qnla_fases SET es_eliminatoria = FALSE WHERE es_eliminatoria IS NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_fases ALTER COLUMN es_eliminatoria SET NOT NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_fases DROP CONSTRAINT IF EXISTS uq_qnla_fases_torneo_nombre"))
    conn.execute(sa.text("ALTER TABLE qnla_fases ADD CONSTRAINT uq_qnla_fases_torneo_nombre UNIQUE (torneo_id, nombre)"))

    # 4) qnla_grupos
    conn.execute(sa.text("ALTER TABLE qnla_grupos ALTER COLUMN nombre TYPE VARCHAR(5)"))
    conn.execute(sa.text("ALTER TABLE qnla_grupos DROP CONSTRAINT IF EXISTS uq_qnla_grupos_torneo_nombre"))
    conn.execute(sa.text("ALTER TABLE qnla_grupos ADD CONSTRAINT uq_qnla_grupos_torneo_nombre UNIQUE (torneo_id, nombre)"))

    # 5) qnla_selecciones
    conn.execute(sa.text("ALTER TABLE qnla_selecciones ALTER COLUMN bandera_url TYPE TEXT"))
    conn.execute(sa.text("ALTER TABLE qnla_selecciones DROP CONSTRAINT IF EXISTS uq_qnla_selecciones_torneo_nombre"))
    conn.execute(sa.text("ALTER TABLE qnla_selecciones ADD CONSTRAINT uq_qnla_selecciones_torneo_nombre UNIQUE (torneo_id, nombre)"))

    # 6) qnla_sedes
    conn.execute(sa.text("ALTER TABLE qnla_sedes ADD COLUMN IF NOT EXISTS torneo_id INTEGER"))
    conn.execute(sa.text("""
        UPDATE qnla_sedes s
        SET torneo_id = x.torneo_id
        FROM (
            SELECT sede_id, MIN(torneo_id) AS torneo_id
            FROM qnla_partidos
            WHERE sede_id IS NOT NULL
            GROUP BY sede_id
        ) x
        WHERE s.id = x.sede_id AND s.torneo_id IS NULL
    """))
    conn.execute(sa.text("""
        UPDATE qnla_sedes
        SET torneo_id = (SELECT MIN(id) FROM qnla_torneos)
        WHERE torneo_id IS NULL
    """))
    conn.execute(sa.text("ALTER TABLE qnla_sedes ALTER COLUMN torneo_id SET NOT NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_sedes ALTER COLUMN nombre TYPE VARCHAR(150)"))
    conn.execute(sa.text("ALTER TABLE qnla_sedes DROP CONSTRAINT IF EXISTS qnla_sedes_torneo_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_sedes ADD CONSTRAINT qnla_sedes_torneo_id_fkey FOREIGN KEY (torneo_id) REFERENCES qnla_torneos(id) ON DELETE CASCADE"))

    # 7) qnla_partidos
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD COLUMN IF NOT EXISTS grupo_id INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos RENAME COLUMN fecha_hora TO fecha_partido"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN goles_local TYPE SMALLINT"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN goles_visitante TYPE SMALLINT"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD COLUMN IF NOT EXISTS finalizado BOOLEAN"))
    conn.execute(sa.text("UPDATE qnla_partidos SET finalizado = (goles_local IS NOT NULL AND goles_visitante IS NOT NULL) WHERE finalizado IS NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN finalizado SET NOT NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE"))
    conn.execute(sa.text("UPDATE qnla_partidos SET updated_at = NOW() WHERE updated_at IS NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN updated_at SET NOT NULL"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS qnla_partidos_grupo_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD CONSTRAINT qnla_partidos_grupo_id_fkey FOREIGN KEY (grupo_id) REFERENCES qnla_grupos(id) ON DELETE SET NULL"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS qnla_partidos_fase_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD CONSTRAINT qnla_partidos_fase_id_fkey FOREIGN KEY (fase_id) REFERENCES qnla_fases(id) ON DELETE CASCADE"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS qnla_partidos_sede_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD CONSTRAINT qnla_partidos_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES qnla_sedes(id) ON DELETE CASCADE"))

    # Completar posibles nulos heredados antes de forzar NOT NULL
    conn.execute(sa.text("""
        UPDATE qnla_partidos p
        SET fase_id = x.fase_id
        FROM (
            SELECT torneo_id, MIN(id) AS fase_id
            FROM qnla_fases
            GROUP BY torneo_id
        ) x
        WHERE p.fase_id IS NULL AND p.torneo_id = x.torneo_id
    """))
    conn.execute(sa.text("""
        UPDATE qnla_partidos p
        SET sede_id = x.sede_id
        FROM (
            SELECT torneo_id, MIN(id) AS sede_id
            FROM qnla_sedes
            GROUP BY torneo_id
        ) x
        WHERE p.sede_id IS NULL AND p.torneo_id = x.torneo_id
    """))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN fase_id SET NOT NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN sede_id SET NOT NULL"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP COLUMN IF EXISTS estado"))
    conn.execute(sa.text("DROP TYPE IF EXISTS estado_partido"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS ck_qnla_partidos_equipos_distintos"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD CONSTRAINT ck_qnla_partidos_equipos_distintos CHECK (seleccion_local_id <> seleccion_visitante_id)"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS ck_qnla_partidos_goles_validos"))
    conn.execute(sa.text("""
        ALTER TABLE qnla_partidos
        ADD CONSTRAINT ck_qnla_partidos_goles_validos
        CHECK ((goles_local IS NULL AND goles_visitante IS NULL) OR (goles_local >= 0 AND goles_visitante >= 0))
    """))

    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_qnla_partidos_torneo_fecha ON qnla_partidos (torneo_id, fecha_partido)"))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_qnla_partidos_torneo_fecha"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS ck_qnla_partidos_goles_validos"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS ck_qnla_partidos_equipos_distintos"))

    conn.execute(sa.text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_partido') THEN CREATE TYPE estado_partido AS ENUM ('PROGRAMADO','EN_JUEGO','FINALIZADO'); END IF; END $$;"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD COLUMN IF NOT EXISTS estado estado_partido"))
    conn.execute(sa.text("UPDATE qnla_partidos SET estado = CASE WHEN finalizado THEN 'FINALIZADO'::estado_partido ELSE 'PROGRAMADO'::estado_partido END WHERE estado IS NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN estado SET NOT NULL"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS qnla_partidos_sede_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD CONSTRAINT qnla_partidos_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES qnla_sedes(id) ON DELETE SET NULL"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS qnla_partidos_fase_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ADD CONSTRAINT qnla_partidos_fase_id_fkey FOREIGN KEY (fase_id) REFERENCES qnla_fases(id) ON DELETE SET NULL"))

    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP CONSTRAINT IF EXISTS qnla_partidos_grupo_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP COLUMN IF EXISTS grupo_id"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP COLUMN IF EXISTS updated_at"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos DROP COLUMN IF EXISTS finalizado"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN goles_local TYPE INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos ALTER COLUMN goles_visitante TYPE INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_partidos RENAME COLUMN fecha_partido TO fecha_hora"))

    conn.execute(sa.text("ALTER TABLE qnla_sedes DROP CONSTRAINT IF EXISTS qnla_sedes_torneo_id_fkey"))
    conn.execute(sa.text("ALTER TABLE qnla_sedes DROP COLUMN IF EXISTS torneo_id"))
    conn.execute(sa.text("ALTER TABLE qnla_sedes ALTER COLUMN nombre TYPE VARCHAR(200)"))

    conn.execute(sa.text("ALTER TABLE qnla_selecciones DROP CONSTRAINT IF EXISTS uq_qnla_selecciones_torneo_nombre"))
    conn.execute(sa.text("ALTER TABLE qnla_selecciones ALTER COLUMN bandera_url TYPE VARCHAR(500)"))

    conn.execute(sa.text("ALTER TABLE qnla_grupos DROP CONSTRAINT IF EXISTS uq_qnla_grupos_torneo_nombre"))
    conn.execute(sa.text("ALTER TABLE qnla_grupos ALTER COLUMN nombre TYPE VARCHAR(10)"))

    conn.execute(sa.text("ALTER TABLE qnla_fases DROP CONSTRAINT IF EXISTS uq_qnla_fases_torneo_nombre"))
    conn.execute(sa.text("ALTER TABLE qnla_fases DROP COLUMN IF EXISTS es_eliminatoria"))
    conn.execute(sa.text("ALTER TABLE qnla_fases ALTER COLUMN orden TYPE INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_fases ALTER COLUMN nombre TYPE VARCHAR(100)"))

    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje DROP CONSTRAINT IF EXISTS uq_qnla_reglas_puntaje_torneo"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje DROP COLUMN IF EXISTS created_at"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN puntos_exacto TYPE INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN puntos_ganador TYPE INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje ALTER COLUMN puntos_fallo TYPE INTEGER"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje RENAME COLUMN puntos_exacto TO exacto_puntos"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje RENAME COLUMN puntos_ganador TO ganador_empate_puntos"))
    conn.execute(sa.text("ALTER TABLE qnla_reglas_puntaje RENAME COLUMN puntos_fallo TO fallo_puntos"))
