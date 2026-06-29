"""
Repository para FTRA_FACTURA_HISTORIAL.
CRUD para historial de cambios de estado.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.factura_historial import FacturaHistorial


class FacturaHistorialRepository:
    """Repository para FacturaHistorial."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, historial: FacturaHistorial) -> FacturaHistorial:
        """Crea un nuevo registro de historial."""
        self.db.add(historial)
        self.db.commit()
        self.db.refresh(historial)
        return historial
    
    def obtener_por_id(self, historial_id: int) -> Optional[FacturaHistorial]:
        """Obtiene un registro de historial por ID."""
        return self.db.get(FacturaHistorial, historial_id)
    
    def obtener_por_factura(self, factura_id: int) -> List[FacturaHistorial]:
        """Obtiene historial de una factura."""
        return self.db.scalars(
            select(FacturaHistorial).where(FacturaHistorial.factura_id == factura_id)
            .order_by(FacturaHistorial.created_at.desc())
        ).all()
    
    def obtener_ultimo_estado(self, factura_id: int) -> Optional[FacturaHistorial]:
        """Obtiene el último cambio de estado."""
        return self.db.scalar(
            select(FacturaHistorial).where(FacturaHistorial.factura_id == factura_id)
            .order_by(FacturaHistorial.created_at.desc())
        )
    
    def obtener_por_usuario(self, usuario_id: int) -> List[FacturaHistorial]:
        """Obtiene cambios realizados por un usuario."""
        return self.db.scalars(
            select(FacturaHistorial).where(FacturaHistorial.usuario_id == usuario_id)
            .order_by(FacturaHistorial.created_at.desc())
        ).all()
    
    def actualizar(self, historial_id: int, **kwargs) -> Optional[FacturaHistorial]:
        """Actualiza un registro de historial."""
        historial = self.obtener_por_id(historial_id)
        if not historial:
            return None
        for key, value in kwargs.items():
            if hasattr(historial, key):
                setattr(historial, key, value)
        self.db.commit()
        self.db.refresh(historial)
        return historial
    
    def eliminar(self, historial_id: int) -> bool:
        """Elimina un registro de historial."""
        historial = self.obtener_por_id(historial_id)
        if not historial:
            return False
        self.db.delete(historial)
        self.db.commit()
        return True
