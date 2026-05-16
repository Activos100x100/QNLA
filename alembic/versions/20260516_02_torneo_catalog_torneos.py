"""align qnla_torneos catalog fields

Revision ID: 20260516_02
Revises: 20260516_01
Create Date: 2026-05-16 18:10:00
"""
from alembic import op
import sqlalchemy as sa


revision = "20260516_02"
down_revision = "20260516_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # nombre VARCHAR(100)
    conn.execute(sa.text("ALTER TABLE qnla_torneos ALTER COLUMN nombre TYPE VARCHAR(100)"))

    # fecha_inicio / fecha_fin como DATE
    conn.execute(sa.text("ALTER TABLE qnla_torneos ALTER COLUMN fecha_inicio TYPE DATE USING fecha_inicio::date"))
    conn.execute(sa.text("ALTER TABLE qnla_torneos ALTER COLUMN fecha_fin TYPE DATE USING fecha_fin::date"))

    # cierre_inscripcion (si no existe)
    conn.execute(
        sa.text(
            """
            ALTER TABLE qnla_torneos
            ADD COLUMN IF NOT EXISTS cierre_inscripcion TIMESTAMP WITH TIME ZONE NULL
            """
        )
    )

    # check constraint fecha_fin >= fecha_inicio
    conn.execute(sa.text("ALTER TABLE qnla_torneos DROP CONSTRAINT IF EXISTS ck_qnla_torneos_fechas"))
    conn.execute(
        sa.text(
            """
            ALTER TABLE qnla_torneos
            ADD CONSTRAINT ck_qnla_torneos_fechas
            CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("ALTER TABLE qnla_torneos DROP CONSTRAINT IF EXISTS ck_qnla_torneos_fechas"))
    conn.execute(sa.text("ALTER TABLE qnla_torneos DROP COLUMN IF EXISTS cierre_inscripcion"))

    # revertimos fecha_* a timestamp con zona
    conn.execute(sa.text("ALTER TABLE qnla_torneos ALTER COLUMN fecha_inicio TYPE TIMESTAMP WITH TIME ZONE USING fecha_inicio::timestamp"))
    conn.execute(sa.text("ALTER TABLE qnla_torneos ALTER COLUMN fecha_fin TYPE TIMESTAMP WITH TIME ZONE USING fecha_fin::timestamp"))

    conn.execute(sa.text("ALTER TABLE qnla_torneos ALTER COLUMN nombre TYPE VARCHAR(200)"))
