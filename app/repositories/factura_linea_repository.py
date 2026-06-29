"""
Repository para FTRA_FACTURA_LINEAS.
CRUD para líneas de facturas.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.factura_linea import FacturaLinea


class FacturaLineaRepository:
    """Repository para FacturaLinea."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, linea: FacturaLinea) -> FacturaLinea:
        """Crea una nueva línea de factura."""
        self.db.add(linea)
        self.db.commit()
        self.db.refresh(linea)
        return linea
    
    def obtener_por_id(self, linea_id: int) -> Optional[FacturaLinea]:
        """Obtiene una línea por ID."""
        return self.db.get(FacturaLinea, linea_id)
    
    def obtener_por_factura(self, factura_id: int) -> List[FacturaLinea]:
        """Obtiene todas las líneas de una factura."""
        return self.db.scalars(
            select(FacturaLinea).where(FacturaLinea.factura_id == factura_id)
            .order_by(FacturaLinea.orden_linea)
        ).all()
    
    def actualizar(self, linea_id: int, **kwargs) -> Optional[FacturaLinea]:
        """Actualiza una línea."""
        linea = self.obtener_por_id(linea_id)
        if not linea:
            return None
        for key, value in kwargs.items():
            if hasattr(linea, key):
                setattr(linea, key, value)
        self.db.commit()
        self.db.refresh(linea)
        return linea
    
    def eliminar(self, linea_id: int) -> bool:
        """Elimina una línea."""
        linea = self.obtener_por_id(linea_id)
        if not linea:
            return False
        self.db.delete(linea)
        self.db.commit()
        return True
    
    def eliminar_por_factura(self, factura_id: int) -> int:
        """Elimina todas las líneas de una factura."""
        lineas = self.obtener_por_factura(factura_id)
        for linea in lineas:
            self.db.delete(linea)
        self.db.commit()
        return len(lineas)
