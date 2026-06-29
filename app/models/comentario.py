"""
Modelo SQLAlchemy para comentarios genéricos de cualquier entidad.
Sistema de colaboración y auditoría para comentarios.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Comentario(Base):
    """
    Modelo para comentarios genéricos en cualquier entidad (facturas, pedidos, incidencias, etc.).
    Permite que múltiples usuarios colaboren con comentarios, respuestas, y tipos.
    """
    __tablename__ = "ftra_comentarios"
    __table_args__ = (
        Index("ix_comentarios_entity", "entity_type", "entity_id"),
        Index("ix_comentarios_usuario_id", "usuario_id"),
        Index("ix_comentarios_parent_id", "parent_id"),
        Index("ix_comentarios_estado", "estado"),
        Index("ix_comentarios_tipo", "tipo"),
        Index("ix_comentarios_created_at", "created_at"),
        CheckConstraint(
            "tipo IN ('informacion', 'revision', 'incidencia', 'aprobacion', 'rechazo')",
            name="ck_comentarios_tipo"
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'resuelto')",
            name="ck_comentarios_estado"
        ),
    )

    # ========== Campos Principales ==========
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Soporte genérico para múltiples tipos de entidades
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "factura", "pedido", "incidencia", etc.
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # ID de la entidad
    
    usuario_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # FK a usuarios/empleados
    usuario_nombre: Mapped[str] = mapped_column(String(255), nullable=False)  # Cache del nombre del usuario
    
    # ========== Contenido ==========
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ========== Tipo de Comentario ==========
    # Tipos: información, revisión, incidencia, aprobación, rechazo
    tipo: Mapped[str] = mapped_column(
        String(20),
        default="informacion",
        nullable=False,
        index=True
    )
    
    # ========== Respuestas Anidadas ==========
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("ftra_comentarios.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # ========== Estado ==========
    estado: Mapped[str] = mapped_column(
        String(20),
        default="pendiente",
        nullable=False,
        index=True
    )
    resuelto_por: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # ========== Auditoría ==========
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # ========== Relaciones ==========
    # Comentarios secundarios (respuestas)
    respuestas: Mapped[list["Comentario"]] = relationship(
        back_populates="padre",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    
    # Comentario padre
    padre: Mapped["Comentario | None"] = relationship(
        remote_side=[id],
        back_populates="respuestas",
        foreign_keys=[parent_id]
    )

    def __repr__(self) -> str:
        return f"<Comentario(id={self.id}, entity={self.entity_type}#{self.entity_id}, tipo={self.tipo}, estado={self.estado})>"

    def marcar_resuelto(self, usuario_id: str, usuario_nombre: str) -> None:
        """Marca el comentario como resuelto."""
        self.estado = "resuelto"
        self.resuelto_por = usuario_nombre
        self.resuelto_en = datetime.now(timezone.utc)

    def marcar_pendiente(self) -> None:
        """Marca el comentario como pendiente."""
        self.estado = "pendiente"
        self.resuelto_por = None
        self.resuelto_en = None

    @property
    def tiene_respuestas(self) -> bool:
        """Verifica si el comentario tiene respuestas."""
        return len(self.respuestas) > 0

    @property
    def es_principal(self) -> bool:
        """Verifica si es un comentario principal (sin padre)."""
        return self.parent_id is None

    @property
    def es_respuesta(self) -> bool:
        """Verifica si es una respuesta (tiene padre)."""
        return self.parent_id is not None


class ComentarioAuditoria(Base):
    """
    Tabla de auditoría para comentarios.
    Registra todas las acciones: creación, edición, marcado como resuelto.
    """
    __tablename__ = "ftra_comentarios_auditoria"
    __table_args__ = (
        Index("ix_comentarios_auditoria_comentario_id", "comentario_id"),
        Index("ix_comentarios_auditoria_entity", "entity_type", "entity_id"),
        Index("ix_comentarios_auditoria_usuario_id", "usuario_id"),
        Index("ix_comentarios_auditoria_accion", "accion"),
        Index("ix_comentarios_auditoria_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    comentario_id: Mapped[int] = mapped_column(
        ForeignKey("ftra_comentarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Soporte genérico para múltiples tipos de entidades
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    usuario_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    usuario_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Tipo de acción: crear, editar, resolver, reabrirDISCOUNT
    accion: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Detalles de qué cambió
    cambios_anteriores: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    cambios_nuevos: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<ComentarioAuditoria(id={self.id}, comentario_id={self.comentario_id}, accion={self.accion})>"
