"""
Repository para FTRA_TIPOS_GASTO.
CRUD para tipos de gasto.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.tipo_gasto import TipoGasto


class TipoGastoRepository:
    """Repository para TipoGasto."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, tipo_gasto: TipoGasto) -> TipoGasto:
        """Crea un nuevo tipo de gasto."""
        self.db.add(tipo_gasto)
        self.db.commit()
        self.db.refresh(tipo_gasto)
        return tipo_gasto
    
    def obtener_por_id(self, tipo_gasto_id: int) -> Optional[TipoGasto]:
        """Obtiene un tipo de gasto por ID."""
        return self.db.get(TipoGasto, tipo_gasto_id)
    
    def obtener_todos(self) -> List[TipoGasto]:
        """Obtiene todos los tipos de gasto."""
        return self.db.scalars(select(TipoGasto).order_by(TipoGasto.nombre)).all()
    
    def obtener_por_nombre(self, nombre: str) -> Optional[TipoGasto]:
        """Obtiene un tipo de gasto por nombre."""
        return self.db.scalar(select(TipoGasto).where(TipoGasto.nombre == nombre))
    
    def actualizar(self, tipo_gasto_id: int, **kwargs) -> Optional[TipoGasto]:
        """Actualiza un tipo de gasto."""
        tipo_gasto = self.obtener_por_id(tipo_gasto_id)
        if not tipo_gasto:
            return None
        for key, value in kwargs.items():
            if hasattr(tipo_gasto, key):
                setattr(tipo_gasto, key, value)
        self.db.commit()
        self.db.refresh(tipo_gasto)
        return tipo_gasto
    
    def eliminar(self, tipo_gasto_id: int) -> bool:
        """Elimina un tipo de gasto."""
        tipo_gasto = self.obtener_por_id(tipo_gasto_id)
        if not tipo_gasto:
            return False
        self.db.delete(tipo_gasto)
        self.db.commit()
        return True
