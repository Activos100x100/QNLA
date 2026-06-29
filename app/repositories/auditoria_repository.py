"""
Repository para FTRA_AUDITORIA.
CRUD para auditoría de cambios.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.auditoria import Auditoria


class AuditoriaRepository:
    """Repository para Auditoria."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, auditoria: Auditoria) -> Auditoria:
        """Crea un nuevo registro de auditoría."""
        self.db.add(auditoria)
        self.db.commit()
        self.db.refresh(auditoria)
        return auditoria
    
    def obtener_por_id(self, auditoria_id: int) -> Optional[Auditoria]:
        """Obtiene un registro de auditoría por ID."""
        return self.db.get(Auditoria, auditoria_id)
    
    def obtener_por_factura(self, factura_id: int) -> List[Auditoria]:
        """Obtiene auditoría de una factura."""
        return self.db.scalars(
            select(Auditoria).where(Auditoria.factura_id == factura_id)
            .order_by(Auditoria.created_at.desc())
        ).all()
    
    def obtener_por_usuario(self, usuario_id: int) -> List[Auditoria]:
        """Obtiene cambios realizados por un usuario."""
        return self.db.scalars(
            select(Auditoria).where(Auditoria.usuario_id == usuario_id)
            .order_by(Auditoria.created_at.desc())
        ).all()
    
    def obtener_por_accion(self, accion: str) -> List[Auditoria]:
        """Obtiene registros de una acción específica."""
        return self.db.scalars(
            select(Auditoria).where(Auditoria.accion == accion)
            .order_by(Auditoria.created_at.desc())
        ).all()
    
    def obtener_ultimos(self, limite: int = 100) -> List[Auditoria]:
        """Obtiene últimos registros de auditoría."""
        return self.db.scalars(
            select(Auditoria).order_by(Auditoria.created_at.desc()).limit(limite)
        ).all()
    
    def eliminar(self, auditoria_id: int) -> bool:
        """Elimina un registro de auditoría."""
        auditoria = self.obtener_por_id(auditoria_id)
        if not auditoria:
            return False
        self.db.delete(auditoria)
        self.db.commit()
        return True
