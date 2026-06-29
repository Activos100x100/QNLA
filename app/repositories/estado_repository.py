"""
Repository para FTRA_ESTADOS.
CRUD para estados de facturas.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.estado import Estado


class EstadoRepository:
    """Repository para Estado."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, estado: Estado) -> Estado:
        """Crea un nuevo estado."""
        self.db.add(estado)
        self.db.commit()
        self.db.refresh(estado)
        return estado
    
    def obtener_por_id(self, estado_id: int) -> Optional[Estado]:
        """Obtiene un estado por ID."""
        return self.db.get(Estado, estado_id)
    
    def obtener_todos(self) -> List[Estado]:
        """Obtiene todos los estados ordenados por orden."""
        return self.db.scalars(
            select(Estado).order_by(Estado.orden)
        ).all()
    
    def obtener_por_nombre(self, nombre: str) -> Optional[Estado]:
        """Obtiene un estado por nombre."""
        return self.db.scalar(select(Estado).where(Estado.nombre == nombre))
    
    def obtener_finales(self) -> List[Estado]:
        """Obtiene estados finales."""
        return self.db.scalars(
            select(Estado).where(Estado.es_final == True).order_by(Estado.orden)
        ).all()
    
    def actualizar(self, estado_id: int, **kwargs) -> Optional[Estado]:
        """Actualiza un estado."""
        estado = self.obtener_por_id(estado_id)
        if not estado:
            return None
        for key, value in kwargs.items():
            if hasattr(estado, key):
                setattr(estado, key, value)
        self.db.commit()
        self.db.refresh(estado)
        return estado
    
    def eliminar(self, estado_id: int) -> bool:
        """Elimina un estado."""
        estado = self.obtener_por_id(estado_id)
        if not estado:
            return False
        self.db.delete(estado)
        self.db.commit()
        return True
