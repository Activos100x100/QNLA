"""
Servicio para gestión de comentarios de entidades (genérico).
Lógica de negocio y orquestación.
"""

import json
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.comentario import Comentario, ComentarioAuditoria
from app.repositories.comentarios_repository import (
    ComentariosRepository,
    ComentariosAuditoriaRepository
)
from app.schemas.factura_schemas import (
    ComentarioCreate,
    ComentarioUpdate,
    ComentarioResponse,
    ComentarioEstadisticas,
    ComentarioAuditoriaResponse
)


class ComentariosService:
    """Servicio de comentarios (genérico para cualquier entidad)."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ComentariosRepository(db)
        self.repo_auditoria = ComentariosAuditoriaRepository(db)

    # ========== CREAR COMENTARIO ==========
    def crear_comentario(
        self,
        entity_type: str,
        entity_id: int,
        usuario_id: str,
        usuario_nombre: str,
        texto: str,
        tipo: str = "informacion",
        parent_id: Optional[int] = None
    ) -> ComentarioResponse:
        """Crea un nuevo comentario."""
        
        # Validar que si es respuesta, el padre existe
        if parent_id:
            padre = self.repo.obtener_por_id(parent_id)
            if not padre or padre.entity_type != entity_type or padre.entity_id != entity_id:
                raise ValueError("Comentario padre no encontrado o no pertenece a la entidad")
        
        # Crear comentario
        comentario = Comentario(
            entity_type=entity_type,
            entity_id=entity_id,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            texto=texto,
            tipo=tipo,
            parent_id=parent_id,
            estado="pendiente"
        )
        
        comentario = self.repo.crear(comentario)
        
        # Registrar en auditoría
        auditoria = ComentarioAuditoria(
            comentario_id=comentario.id,
            entity_type=entity_type,
            entity_id=entity_id,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion="crear",
            cambios_nuevos=json.dumps({
                "texto": texto,
                "tipo": tipo,
                "parent_id": parent_id
            })
        )
        self.repo_auditoria.registrar(auditoria)
        
        # Notificar si tiene respuestas pendientes
        if parent_id:
            # Notificar al autor del comentario padre
            pass
        
        return ComentarioResponse.model_validate(comentario)

    # ========== ACTUALIZAR COMENTARIO ==========
    def actualizar_comentario(
        self,
        comentario_id: int,
        usuario_id: str,
        usuario_nombre: str,
        **updates
    ) -> ComentarioResponse:
        """Actualiza un comentario."""
        comentario = self.repo.obtener_por_id(comentario_id)
        if not comentario:
            raise ValueError("Comentario no encontrado")
        
        # Registrar cambios anteriores
        cambios_anteriores = {}
        cambios_nuevos = {}
        
        for key, value in updates.items():
            if hasattr(comentario, key) and key not in ["id", "created_at", "updated_at"]:
                cambios_anteriores[key] = getattr(comentario, key)
                cambios_nuevos[key] = value
                setattr(comentario, key, value)
        
        if cambios_anteriores:
            self.db.commit()
            self.db.refresh(comentario)
            
            # Registrar en auditoría solo si hay cambios
            auditoria = ComentarioAuditoria(
                comentario_id=comentario_id,
                entity_type=comentario.entity_type,
                entity_id=comentario.entity_id,
                usuario_id=usuario_id,
                usuario_nombre=usuario_nombre,
                accion="editar",
                cambios_anteriores=json.dumps(cambios_anteriores),
                cambios_nuevos=json.dumps(cambios_nuevos)
            )
            self.repo_auditoria.registrar(auditoria)
        
        return ComentarioResponse.model_validate(comentario)

    # ========== RESOLVER COMENTARIO ==========
    def resolver_comentario(
        self,
        comentario_id: int,
        usuario_id: str,
        usuario_nombre: str
    ) -> ComentarioResponse:
        """Marca un comentario como resuelto."""
        comentario = self.repo.obtener_por_id(comentario_id)
        if not comentario:
            raise ValueError("Comentario no encontrado")
        
        comentario_anterior = {
            "estado": comentario.estado,
            "resuelto_por": comentario.resuelto_por,
            "resuelto_en": comentario.resuelto_en
        }
        
        comentario.marcar_resuelto(usuario_id, usuario_nombre)
        self.db.commit()
        self.db.refresh(comentario)
        
        # Registrar en auditoría
        auditoria = ComentarioAuditoria(
            comentario_id=comentario_id,
            entity_type=comentario.entity_type,
            entity_id=comentario.entity_id,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion="resolver",
            cambios_anteriores=json.dumps(comentario_anterior),
            cambios_nuevos=json.dumps({
                "estado": comentario.estado,
                "resuelto_por": comentario.resuelto_por,
                "resuelto_en": comentario.resuelto_en.isoformat()
            })
        )
        self.repo_auditoria.registrar(auditoria)
        
        return ComentarioResponse.model_validate(comentario)

    # ========== REABRIR COMENTARIO ==========
    def reabrircomentario(
        self,
        comentario_id: int,
        usuario_id: str,
        usuario_nombre: str
    ) -> ComentarioResponse:
        """Reabre un comentario resuelto."""
        comentario = self.repo.obtener_por_id(comentario_id)
        if not comentario:
            raise ValueError("Comentario no encontrado")
        
        comentario_anterior = {
            "estado": comentario.estado,
            "resuelto_por": comentario.resuelto_por,
            "resuelto_en": comentario.resuelto_en
        }
        
        comentario.marcar_pendiente()
        self.db.commit()
        self.db.refresh(comentario)
        
        # Registrar en auditoría
        auditoria = ComentarioAuditoria(
            comentario_id=comentario_id,
            entity_type=comentario.entity_type,
            entity_id=comentario.entity_id,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion="reabrirDISCOUNT",
            cambios_anteriores=json.dumps(comentario_anterior),
            cambios_nuevos=json.dumps({
                "estado": comentario.estado,
                "resuelto_por": None,
                "resuelto_en": None
            })
        )
        self.repo_auditoria.registrar(auditoria)
        
        return ComentarioResponse.model_validate(comentario)

    # ========== OBTENER COMENTARIOS ==========
    def obtener_comentarios_entidad(self, entity_type: str, entity_id: int) -> List[ComentarioResponse]:
        """Obtiene comentarios principales de una entidad con respuestas."""
        comentarios = self.repo.obtener_con_respuestas(entity_type, entity_id)
        return [ComentarioResponse.model_validate(c) for c in comentarios]

    def obtener_comentarios_pendientes(self, entity_type: str, entity_id: int) -> List[ComentarioResponse]:
        """Obtiene comentarios pendientes de una entidad."""
        comentarios = self.repo.obtener_pendientes(entity_type, entity_id)
        return [ComentarioResponse.model_validate(c) for c in comentarios]

    def obtener_respuestas(self, comentario_id: int) -> List[ComentarioResponse]:
        """Obtiene respuestas de un comentario."""
        respuestas = self.repo.obtener_respuestas(comentario_id)
        return [ComentarioResponse.model_validate(r) for r in respuestas]

    # ========== ELIMINAR COMENTARIO ==========
    def eliminar_comentario(self, comentario_id: int) -> bool:
        """Elimina un comentario y sus respuestas."""
        comentario = self.repo.obtener_por_id(comentario_id)
        if not comentario:
            raise ValueError("Comentario no encontrado")
        
        # Registrar eliminación en auditoría antes de borrar
        auditoria = ComentarioAuditoria(
            comentario_id=comentario_id,
            entity_type=comentario.entity_type,
            entity_id=comentario.entity_id,
            usuario_id="sistema",
            usuario_nombre="Sistema",
            accion="eliminar",
            cambios_anteriores=json.dumps({
                "texto": comentario.texto,
                "tipo": comentario.tipo,
                "estado": comentario.estado
            })
        )
        self.repo_auditoria.registrar(auditoria)
        
        return self.repo.eliminar(comentario_id)

    # ========== ESTADÍSTICAS ==========
    def obtener_estadisticas(self, entity_type: str, entity_id: int) -> ComentarioEstadisticas:
        """Obtiene estadísticas de comentarios."""
        total = self.repo.contar_por_entidad(entity_type, entity_id)
        pendientes = self.repo.contar_pendientes(entity_type, entity_id)
        resueltos = self.repo.contar_resueltos(entity_type, entity_id)
        distribucion = self.repo.obtener_distribucion_tipos(entity_type, entity_id)
        ultimos = self.repo.obtener_ultimos(entity_type, entity_id, 3)
        
        return ComentarioEstadisticas(
            entity_type=entity_type,
            entity_id=entity_id,
            total_comentarios=total,
            comentarios_pendientes=pendientes,
            comentarios_resueltos=resueltos,
            tipos_distribucion=distribucion,
            ultimos_comentarios=[ComentarioResponse.model_validate(c) for c in ultimos]
        )

    def tiene_pendientes(self, entity_type: str, entity_id: int) -> bool:
        """Verifica si hay comentarios pendientes."""
        return self.repo.contar_pendientes(entity_type, entity_id) > 0

    def entidades_con_pendientes(self, entity_type: str) -> List[int]:
        """Obtiene IDs de todas las entidades con comentarios pendientes."""
        resultados = self.repo.entidades_con_comentarios_pendientes(entity_type)
        return [r["entity_id"] for r in resultados]

    # ========== AUDITORÍA ==========
    def obtener_auditoria_comentario(self, comentario_id: int) -> List[ComentarioAuditoriaResponse]:
        """Obtiene historial de auditoría de un comentario."""
        auditorias = self.repo_auditoria.obtener_por_comentario(comentario_id)
        return [ComentarioAuditoriaResponse.model_validate(a) for a in auditorias]

    def obtener_auditoria_entidad(self, entity_type: str, entity_id: int) -> List[ComentarioAuditoriaResponse]:
        """Obtiene historial de auditoría de una entidad."""
        auditorias = self.repo_auditoria.obtener_por_entidad(entity_type, entity_id)
        return [ComentarioAuditoriaResponse.model_validate(a) for a in auditorias]

    def obtener_auditoria_usuario(self, usuario_id: str) -> List[ComentarioAuditoriaResponse]:
        """Obtiene historial de acciones de un usuario."""
        auditorias = self.repo_auditoria.obtener_por_usuario(usuario_id)
        return [ComentarioAuditoriaResponse.model_validate(a) for a in auditorias]
