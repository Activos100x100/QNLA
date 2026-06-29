"""
Repository para FTRA_FACTURA_COMENTARIOS.
CRUD para comentarios de facturas.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.factura_comentario import FacturaComentario


class FacturaComentarioRepository:
    """Repository para FacturaComentario."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, comentario: FacturaComentario) -> FacturaComentario:
        """Crea un nuevo comentario en factura."""
        self.db.add(comentario)
        self.db.commit()
        self.db.refresh(comentario)
        return comentario
    
    def obtener_por_id(self, comentario_id: int) -> Optional[FacturaComentario]:
        """Obtiene un comentario por ID."""
        return self.db.get(FacturaComentario, comentario_id)
    
    def obtener_por_factura(self, factura_id: int) -> List[FacturaComentario]:
        """Obtiene comentarios principales de una factura."""
        return self.db.scalars(
            select(FacturaComentario).where(
                and_(
                    FacturaComentario.factura_id == factura_id,
                    FacturaComentario.comentario_padre_id.is_(None)
                )
            ).order_by(FacturaComentario.created_at.desc())
        ).all()
    
    def obtener_respuestas(self, comentario_id: int) -> List[FacturaComentario]:
        """Obtiene respuestas de un comentario."""
        return self.db.scalars(
            select(FacturaComentario).where(
                FacturaComentario.comentario_padre_id == comentario_id
            ).order_by(FacturaComentario.created_at.asc())
        ).all()
    
    def obtener_no_resueltos(self, factura_id: int) -> List[FacturaComentario]:
        """Obtiene comentarios no resueltos."""
        return self.db.scalars(
            select(FacturaComentario).where(
                and_(
                    FacturaComentario.factura_id == factura_id,
                    FacturaComentario.resuelto == False,
                    FacturaComentario.comentario_padre_id.is_(None)
                )
            ).order_by(FacturaComentario.created_at.desc())
        ).all()
    
    def actualizar(self, comentario_id: int, **kwargs) -> Optional[FacturaComentario]:
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
    
    def eliminar(self, comentario_id: int) -> bool:
        """Elimina un comentario."""
        comentario = self.obtener_por_id(comentario_id)
        if not comentario:
            return False
        self.db.delete(comentario)
        self.db.commit()
        return True
    
    def contar_no_resueltos(self, factura_id: int) -> int:
        """Cuenta comentarios no resueltos de una factura."""
        return len(self.obtener_no_resueltos(factura_id))
