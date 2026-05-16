"""init qnla schema

Revision ID: 20260516_01
Revises: None
Create Date: 2026-05-16 15:30:00
"""
from alembic import op
import sqlalchemy as sa

from app.qnla.database import Base
from app.qnla import models as qnla_models  # noqa: F401

revision = "20260516_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    conn = op.get_bind()
    for table_name in [
        "qnla_pronosticos",
        "qnla_participantes",
        "qnla_partidos",
        "qnla_selecciones",
        "qnla_sedes",
        "qnla_grupos",
        "qnla_fases",
        "qnla_reglas_puntaje",
        "qnla_torneos",
    ]:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS estado_partido"))
