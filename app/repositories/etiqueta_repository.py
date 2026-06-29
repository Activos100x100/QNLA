"""
Repository para FTRA_ETIQUETAS.
CRUD para etiquetas.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.etiqueta import Etiqueta


class EtiquetaRepository:
    """Repository para Etiqueta."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, etiqueta: Etiqueta) -> Etiqueta:
        """Crea una nueva etiqueta."""
        self.db.add(etiqueta)
        self.db.commit()
        self.db.refresh(etiqueta)
        return etiqueta
    
    def obtener_por_id(self, etiqueta_id: int) -> Optional[Etiqueta]:
        """Obtiene una etiqueta por ID."""
        return self.db.get(Etiqueta, etiqueta_id)
    
    def obtener_por_empresa(self, empresa_id: int, activas_solo: bool = False) -> List[Etiqueta]:
        """Obtiene etiquetas de una empresa."""
        query = select(Etiqueta).where(Etiqueta.empresa_id == empresa_id)
        if activas_solo:
            query = query.where(Etiqueta.activa == True)
        return self.db.scalars(query.order_by(Etiqueta.nombre)).all()
    
    def obtener_por_nombre(self, empresa_id: int, nombre: str) -> Optional[Etiqueta]:
        """Obtiene una etiqueta por nombre en una empresa."""
        return self.db.scalar(
            select(Etiqueta).where(
                and_(
                    Etiqueta.empresa_id == empresa_id,
                    Etiqueta.nombre == nombre
                )
            )
        )
    
    def actualizar(self, etiqueta_id: int, **kwargs) -> Optional[Etiqueta]:
        """Actualiza una etiqueta."""
        etiqueta = self.obtener_por_id(etiqueta_id)
        if not etiqueta:
            return None
        for key, value in kwargs.items():
            if hasattr(etiqueta, key):
                setattr(etiqueta, key, value)
        self.db.commit()
        self.db.refresh(etiqueta)
        return etiqueta
    
    def eliminar(self, etiqueta_id: int) -> bool:
        """Elimina una etiqueta."""
        etiqueta = self.obtener_por_id(etiqueta_id)
        if not etiqueta:
            return False
        self.db.delete(etiqueta)
        self.db.commit()
        return True
    
    def contar_por_empresa(self, empresa_id: int, activas_solo: bool = False) -> int:
        """Cuenta etiquetas de una empresa."""
        query = select(Etiqueta).where(Etiqueta.empresa_id == empresa_id)
        if activas_solo:
            query = query.where(Etiqueta.activa == True)
        return len(self.db.scalars(query).all())
