"""Rename comentarios tables with FTRA_ prefix

Revision ID: 20260627_06_rename
Revises: 20260627_05_generic
Create Date: 2026-06-27 17:00:00
"""
from alembic import op


revision = "20260627_06_rename"
down_revision = "20260627_05_generic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detectar tipo de BD
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Renombrar tabla comentarios
    if dialect == 'postgresql':
        # PostgreSQL
        op.execute("ALTER TABLE comentarios RENAME TO ftra_comentarios;")
        op.execute("ALTER TABLE comentarios_auditoria RENAME TO ftra_comentarios_auditoria;")
        
        # Renombrar índices
        op.execute("ALTER INDEX ix_comentarios_entity RENAME TO ix_ftra_comentarios_entity;")
        op.execute("ALTER INDEX ix_comentarios_usuario_id RENAME TO ix_ftra_comentarios_usuario_id;")
        op.execute("ALTER INDEX ix_comentarios_parent_id RENAME TO ix_ftra_comentarios_parent_id;")
        op.execute("ALTER INDEX ix_comentarios_estado RENAME TO ix_ftra_comentarios_estado;")
        op.execute("ALTER INDEX ix_comentarios_tipo RENAME TO ix_ftra_comentarios_tipo;")
        op.execute("ALTER INDEX ix_comentarios_created_at RENAME TO ix_ftra_comentarios_created_at;")
        
        op.execute("ALTER INDEX ix_comentarios_auditoria_comentario_id RENAME TO ix_ftra_comentarios_auditoria_comentario_id;")
        op.execute("ALTER INDEX ix_comentarios_auditoria_entity RENAME TO ix_ftra_comentarios_auditoria_entity;")
        op.execute("ALTER INDEX ix_comentarios_auditoria_usuario_id RENAME TO ix_ftra_comentarios_auditoria_usuario_id;")
        op.execute("ALTER INDEX ix_comentarios_auditoria_accion RENAME TO ix_ftra_comentarios_auditoria_accion;")
        op.execute("ALTER INDEX ix_comentarios_auditoria_created_at RENAME TO ix_ftra_comentarios_auditoria_created_at;")
        
        # Renombrar restricciones
        op.execute("ALTER TABLE ftra_comentarios RENAME CONSTRAINT ck_comentarios_tipo TO ck_ftra_comentarios_tipo;")
        op.execute("ALTER TABLE ftra_comentarios RENAME CONSTRAINT ck_comentarios_estado TO ck_ftra_comentarios_estado;")
        
    else:
        # SQLite no soporta RENAME TABLE directamente, usar ALTER TABLE
        op.execute("ALTER TABLE comentarios RENAME TO ftra_comentarios;")
        op.execute("ALTER TABLE comentarios_auditoria RENAME TO ftra_comentarios_auditoria;")


def downgrade() -> None:
    # Detectar tipo de BD
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Revertir renombramientos
    if dialect == 'postgresql':
        # Revertir tabla comentarios
        op.execute("ALTER TABLE ftra_comentarios RENAME TO comentarios;")
        op.execute("ALTER TABLE ftra_comentarios_auditoria RENAME TO comentarios_auditoria;")
        
        # Revertir índices
        op.execute("ALTER INDEX ix_ftra_comentarios_entity RENAME TO ix_comentarios_entity;")
        op.execute("ALTER INDEX ix_ftra_comentarios_usuario_id RENAME TO ix_comentarios_usuario_id;")
        op.execute("ALTER INDEX ix_ftra_comentarios_parent_id RENAME TO ix_comentarios_parent_id;")
        op.execute("ALTER INDEX ix_ftra_comentarios_estado RENAME TO ix_comentarios_estado;")
        op.execute("ALTER INDEX ix_ftra_comentarios_tipo RENAME TO ix_comentarios_tipo;")
        op.execute("ALTER INDEX ix_ftra_comentarios_created_at RENAME TO ix_comentarios_created_at;")
        
        op.execute("ALTER INDEX ix_ftra_comentarios_auditoria_comentario_id RENAME TO ix_comentarios_auditoria_comentario_id;")
        op.execute("ALTER INDEX ix_ftra_comentarios_auditoria_entity RENAME TO ix_comentarios_auditoria_entity;")
        op.execute("ALTER INDEX ix_ftra_comentarios_auditoria_usuario_id RENAME TO ix_comentarios_auditoria_usuario_id;")
        op.execute("ALTER INDEX ix_ftra_comentarios_auditoria_accion RENAME TO ix_comentarios_auditoria_accion;")
        op.execute("ALTER INDEX ix_ftra_comentarios_auditoria_created_at RENAME TO ix_comentarios_auditoria_created_at;")
        
        # Revertir restricciones
        op.execute("ALTER TABLE comentarios RENAME CONSTRAINT ck_ftra_comentarios_tipo TO ck_comentarios_tipo;")
        op.execute("ALTER TABLE comentarios RENAME CONSTRAINT ck_ftra_comentarios_estado TO ck_comentarios_estado;")
        
    else:
        # SQLite
        op.execute("ALTER TABLE ftra_comentarios RENAME TO comentarios;")
        op.execute("ALTER TABLE ftra_comentarios_auditoria RENAME TO comentarios_auditoria;")
