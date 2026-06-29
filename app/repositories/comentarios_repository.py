"""
Repository para gestión de comentarios de entidades.
Métodos CRUD y consultas especializadas (soporte genérico para cualquier entidad).
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.comentario import Comentario, ComentarioAuditoria


class ComentariosRepository:
    """Repository para Comentario (genérico para cualquier entidad)."""

    def __init__(self, db: Session):
        self.db = db

    # ========== CREAR ==========
    def crear(self, comentario: Comentario) -> Comentario:
        """Crea un nuevo comentario."""
        self.db.add(comentario)
        self.db.commit()
        self.db.refresh(comentario)
        return comentario

    # ========== LEER ==========
    def obtener_por_id(self, comentario_id: int) -> Optional[Comentario]:
        """Obtiene un comentario por ID."""
        return self.db.get(Comentario, comentario_id)

    def obtener_por_entidad(self, entity_type: str, entity_id: int) -> List[Comentario]:
        """Obtiene todos los comentarios principales de una entidad (sin respuestas anidadas)."""
        return self.db.scalars(
            select(Comentario)
            .where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.parent_id.is_(None)
                )
            )
            .order_by(Comentario.created_at.desc())
        ).all()

    def obtener_con_respuestas(self, entity_type: str, entity_id: int) -> List[Comentario]:
        """Obtiene comentarios principales con sus respuestas."""
        comentarios = self.obtener_por_entidad(entity_type, entity_id)
        # SQLAlchemy carga automáticamente las relaciones
        return comentarios

    def obtener_pendientes(self, entity_type: str, entity_id: int) -> List[Comentario]:
        """Obtiene comentarios pendientes de una entidad."""
        return self.db.scalars(
            select(Comentario)
            .where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.estado == "pendiente",
                    Comentario.parent_id.is_(None)
                )
            )
            .order_by(Comentario.created_at.desc())
        ).all()

    def obtener_por_tipo(self, entity_type: str, entity_id: int, tipo: str) -> List[Comentario]:
        """Obtiene comentarios de un tipo específico."""
        return self.db.scalars(
            select(Comentario)
            .where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.tipo == tipo,
                    Comentario.parent_id.is_(None)
                )
            )
            .order_by(Comentario.created_at.desc())
        ).all()

    def obtener_respuestas(self, comentario_id: int) -> List[Comentario]:
        """Obtiene todas las respuestas de un comentario."""
        return self.db.scalars(
            select(Comentario)
            .where(Comentario.parent_id == comentario_id)
            .order_by(Comentario.created_at.asc())
        ).all()

    # ========== ACTUALIZAR ==========
    def actualizar(self, comentario_id: int, **kwargs) -> Optional[Comentario]:
        """Actualiza un comentario."""
        comentario = self.obtener_por_id(comentario_id)
        if not comentario:
            return None
        for key, value in kwargs.items():
            if hasattr(comentario, key):
                setattr(comentario, key, value)
        self.db.commit()
        self.db.refresh(comentario)
        return comentario

    def marcar_resuelto(self, comentario_id: int, usuario_id: str, usuario_nombre: str) -> Optional[Comentario]:
        """Marca un comentario como resuelto."""
        comentario = self.obtener_por_id(comentario_id)
        if not comentario:
            return None
        comentario.marcar_resuelto(usuario_id, usuario_nombre)
        self.db.commit()
        self.db.refresh(comentario)
        return comentario

    def marcar_pendiente(self, comentario_id: int) -> Optional[Comentario]:
        """Marca un comentario como pendiente."""
        comentario = self.obtener_por_id(comentario_id)
        if not comentario:
            return None
        comentario.marcar_pendiente()
        self.db.commit()
        self.db.refresh(comentario)
        return comentario

    # ========== ELIMINAR ==========
    def eliminar(self, comentario_id: int) -> bool:
        """Elimina un comentario y sus respuestas."""
        comentario = self.obtener_por_id(comentario_id)
        if not comentario:
            return False
        self.db.delete(comentario)
        self.db.commit()
        return True

    # ========== ANALÍTICA ==========
    def contar_por_entidad(self, entity_type: str, entity_id: int) -> int:
        """Cuenta comentarios principales de una entidad."""
        return self.db.scalar(
            select(func.count(Comentario.id)).where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.parent_id.is_(None)
                )
            )
        ) or 0

    def contar_pendientes(self, entity_type: str, entity_id: int) -> int:
        """Cuenta comentarios pendientes de una entidad."""
        return self.db.scalar(
            select(func.count(Comentario.id)).where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.estado == "pendiente",
                    Comentario.parent_id.is_(None)
                )
            )
        ) or 0

    def contar_resueltos(self, entity_type: str, entity_id: int) -> int:
        """Cuenta comentarios resueltos de una entidad."""
        return self.db.scalar(
            select(func.count(Comentario.id)).where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.estado == "resuelto",
                    Comentario.parent_id.is_(None)
                )
            )
        ) or 0

    def obtener_distribucion_tipos(self, entity_type: str, entity_id: int) -> dict:
        """Obtiene distribución de comentarios por tipo."""
        resultados = self.db.execute(
            select(Comentario.tipo, func.count(Comentario.id).label("cantidad"))
            .where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.parent_id.is_(None)
                )
            )
            .group_by(Comentario.tipo)
        )
        return {row[0]: row[1] for row in resultados}

    def obtener_ultimos(self, entity_type: str, entity_id: int, limite: int = 5) -> List[Comentario]:
        """Obtiene últimos comentarios principales."""
        return self.db.scalars(
            select(Comentario)
            .where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.entity_id == entity_id,
                    Comentario.parent_id.is_(None)
                )
            )
            .order_by(Comentario.created_at.desc())
            .limit(limite)
        ).all()

    def entidades_con_comentarios_pendientes(self, entity_type: str) -> List[dict]:
        """Obtiene todas las entidades (de un tipo) que tienen comentarios pendientes."""
        resultados = self.db.execute(
            select(
                Comentario.entity_id,
                func.count(Comentario.id).label("cantidad_pendientes")
            )
            .where(
                and_(
                    Comentario.entity_type == entity_type,
                    Comentario.estado == "pendiente",
                    Comentario.parent_id.is_(None)
                )
            )
            .group_by(Comentario.entity_id)
        )
        return [{"entity_id": row[0], "cantidad_pendientes": row[1]} for row in resultados]


class ComentariosAuditoriaRepository:
    """Repository para ComentarioAuditoria."""

    def __init__(self, db: Session):
        self.db = db

    def registrar(self, auditoria: ComentarioAuditoria) -> ComentarioAuditoria:
        """Registra una acción de auditoría."""
        self.db.add(auditoria)
        self.db.commit()
        self.db.refresh(auditoria)
        return auditoria

    def obtener_por_comentario(self, comentario_id: int) -> List[ComentarioAuditoria]:
        """Obtiene historial de auditoría de un comentario."""
        return self.db.scalars(
            select(ComentarioAuditoria)
            .where(ComentarioAuditoria.comentario_id == comentario_id)
            .order_by(ComentarioAuditoria.created_at.desc())
        ).all()

    def obtener_por_entidad(self, entity_type: str, entity_id: int) -> List[ComentarioAuditoria]:
        """Obtiene historial de auditoría de una entidad."""
        return self.db.scalars(
            select(ComentarioAuditoria)
            .where(
                and_(
                    ComentarioAuditoria.entity_type == entity_type,
                    ComentarioAuditoria.entity_id == entity_id
                )
            )
            .order_by(ComentarioAuditoria.created_at.desc())
        ).all()

    def obtener_por_usuario(self, usuario_id: str) -> List[ComentarioAuditoria]:
        """Obtiene historial de acciones de un usuario."""
        return self.db.scalars(
            select(ComentarioAuditoria)
            .where(ComentarioAuditoria.usuario_id == usuario_id)
            .order_by(ComentarioAuditoria.created_at.desc())
        ).all()

    def obtener_por_accion(self, entity_type: str, entity_id: int, accion: str) -> List[ComentarioAuditoria]:
        """Obtiene cambios de una acción específica."""
        return self.db.scalars(
            select(ComentarioAuditoria)
            .where(
                and_(
                    ComentarioAuditoria.entity_type == entity_type,
                    ComentarioAuditoria.entity_id == entity_id,
                    ComentarioAuditoria.accion == accion
                )
            )
            .order_by(ComentarioAuditoria.created_at.desc())
        ).all()
