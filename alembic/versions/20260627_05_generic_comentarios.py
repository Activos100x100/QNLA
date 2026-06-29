"""Add comentarios system - generic comments for any entity

Revision ID: 20260627_05_generic
Revises: 20260602_04
Create Date: 2026-06-27 16:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "20260627_05_generic"
down_revision = "20260602_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detectar tipo de BD
    conn = op.get_bind()
    dialect = conn.dialect.name
    
    # Defaults de timestamp según BD
    if dialect == 'postgresql':
        created_at_default = sa.text("NOW()")
        updated_at_default = sa.text("NOW()")
    else:  # SQLite
        created_at_default = sa.text("CURRENT_TIMESTAMP")
        updated_at_default = sa.text("CURRENT_TIMESTAMP")
    
    # Create comentarios table - GENERIC (sin FK a facturas)
    # Usa entity_type + entity_id para referenciar cualquier entidad
    op.create_table(
        "comentarios",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),  # "factura", "pedido", etc.
        sa.Column("entity_id", sa.Integer(), nullable=False),  # ID de la factura/pedido/etc.
        sa.Column("usuario_id", sa.String(length=255), nullable=False),
        sa.Column("usuario_nombre", sa.String(length=255), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="informacion"),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("comentarios.id", ondelete="CASCADE"), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="pendiente"),
        sa.Column("resuelto_por", sa.String(length=255), nullable=True),
        sa.Column("resuelto_en", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=created_at_default),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=updated_at_default),
    )

    # Create indices
    op.create_index("ix_comentarios_entity", "comentarios", ["entity_type", "entity_id"])
    op.create_index("ix_comentarios_usuario_id", "comentarios", ["usuario_id"])
    op.create_index("ix_comentarios_parent_id", "comentarios", ["parent_id"])
    op.create_index("ix_comentarios_estado", "comentarios", ["estado"])
    op.create_index("ix_comentarios_tipo", "comentarios", ["tipo"])
    op.create_index("ix_comentarios_created_at", "comentarios", ["created_at"])

    # Add CHECK constraints (solo en PostgreSQL)
    if dialect == 'postgresql':
        op.create_check_constraint(
            "ck_comentarios_tipo",
            "comentarios",
            "tipo IN ('informacion', 'revision', 'incidencia', 'aprobacion', 'rechazo')"
        )
        op.create_check_constraint(
            "ck_comentarios_estado",
            "comentarios",
            "estado IN ('pendiente', 'resuelto')"
        )

    # Create comentarios_auditoria table
    op.create_table(
        "comentarios_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("comentario_id", sa.Integer(), sa.ForeignKey("comentarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.String(length=255), nullable=False),
        sa.Column("usuario_nombre", sa.String(length=255), nullable=False),
        sa.Column("accion", sa.String(length=50), nullable=False),
        sa.Column("cambios_anteriores", sa.Text(), nullable=True),
        sa.Column("cambios_nuevos", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=created_at_default),
    )

    # Create indices
    op.create_index("ix_comentarios_auditoria_comentario_id", "comentarios_auditoria", ["comentario_id"])
    op.create_index("ix_comentarios_auditoria_entity", "comentarios_auditoria", ["entity_type", "entity_id"])
    op.create_index("ix_comentarios_auditoria_usuario_id", "comentarios_auditoria", ["usuario_id"])
    op.create_index("ix_comentarios_auditoria_accion", "comentarios_auditoria", ["accion"])
    op.create_index("ix_comentarios_auditoria_created_at", "comentarios_auditoria", ["created_at"])


def downgrade() -> None:
    # Detectar tipo de BD
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Drop indices
    op.drop_index("ix_comentarios_auditoria_created_at", table_name="comentarios_auditoria")
    op.drop_index("ix_comentarios_auditoria_accion", table_name="comentarios_auditoria")
    op.drop_index("ix_comentarios_auditoria_usuario_id", table_name="comentarios_auditoria")
    op.drop_index("ix_comentarios_auditoria_entity", table_name="comentarios_auditoria")
    op.drop_index("ix_comentarios_auditoria_comentario_id", table_name="comentarios_auditoria")
    op.drop_table("comentarios_auditoria")

    # Drop CHECK constraints (solo en PostgreSQL)
    if dialect == 'postgresql':
        op.drop_constraint("ck_comentarios_estado", "comentarios", type_="check")
        op.drop_constraint("ck_comentarios_tipo", "comentarios", type_="check")

    # Drop indices
    op.drop_index("ix_comentarios_created_at", table_name="comentarios")
    op.drop_index("ix_comentarios_tipo", table_name="comentarios")
    op.drop_index("ix_comentarios_estado", table_name="comentarios")
    op.drop_index("ix_comentarios_parent_id", table_name="comentarios")
    op.drop_index("ix_comentarios_usuario_id", table_name="comentarios")
    op.drop_index("ix_comentarios_entity", table_name="comentarios")
    op.drop_table("comentarios")
