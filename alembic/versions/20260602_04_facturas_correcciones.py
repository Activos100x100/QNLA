"""add facturas correcciones table

Revision ID: 20260602_04
Revises: 20260516_03
Create Date: 2026-06-02 12:30:00
"""
from alembic import op
import sqlalchemy as sa


revision = "20260602_04"
down_revision = "20260516_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ftra_facturas_correcciones",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("archivo", sa.String(length=255), nullable=True),
        sa.Column("emisor_nombre", sa.String(length=255), nullable=True),
        sa.Column("emisor_nif", sa.String(length=32), nullable=True),
        sa.Column("emisor_direccion", sa.Text(), nullable=True),
        sa.Column("receptor_nombre", sa.String(length=255), nullable=True),
        sa.Column("receptor_nif", sa.String(length=32), nullable=True),
        sa.Column("receptor_direccion", sa.Text(), nullable=True),
        sa.Column("numero_factura", sa.String(length=64), nullable=True),
        sa.Column("fecha", sa.String(length=32), nullable=True),
        sa.Column("fecha_vencimiento", sa.String(length=32), nullable=True),
        sa.Column("concepto", sa.Text(), nullable=True),
        sa.Column("base_imponible", sa.String(length=64), nullable=True),
        sa.Column("tipo_iva", sa.String(length=16), nullable=True),
        sa.Column("cuota_iva", sa.String(length=64), nullable=True),
        sa.Column("irpf", sa.String(length=64), nullable=True),
        sa.Column("total", sa.String(length=64), nullable=True),
        sa.Column("texto_crudo", sa.Text(), nullable=True),
        sa.Column("confianza", sa.String(length=16), nullable=True),
        sa.Column("validacion", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index(
        "ix_ftra_facturas_correcciones_created_at",
        "ftra_facturas_correcciones",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ftra_facturas_correcciones_archivo",
        "ftra_facturas_correcciones",
        ["archivo"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ftra_facturas_correcciones_archivo", table_name="ftra_facturas_correcciones")
    op.drop_index("ix_ftra_facturas_correcciones_created_at", table_name="ftra_facturas_correcciones")
    op.drop_table("ftra_facturas_correcciones")
