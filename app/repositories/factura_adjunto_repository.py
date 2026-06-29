"""
Repository para FTRA_FACTURA_ADJUNTOS.
CRUD para adjuntos de facturas.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.factura_adjunto import FacturaAdjunto


class FacturaAdjuntoRepository:
    """Repository para FacturaAdjunto."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, adjunto: FacturaAdjunto) -> FacturaAdjunto:
        """Crea un nuevo adjunto."""
        self.db.add(adjunto)
        self.db.commit()
        self.db.refresh(adjunto)
        return adjunto
    
    def obtener_por_id(self, adjunto_id: int) -> Optional[FacturaAdjunto]:
        """Obtiene un adjunto por ID."""
        return self.db.get(FacturaAdjunto, adjunto_id)
    
    def obtener_por_factura(self, factura_id: int) -> List[FacturaAdjunto]:
        """Obtiene adjuntos de una factura."""
        return self.db.scalars(
            select(FacturaAdjunto).where(FacturaAdjunto.factura_id == factura_id)
            .order_by(FacturaAdjunto.created_at.desc())
        ).all()
    
    def obtener_por_tipo(self, factura_id: int, tipo_documento: str) -> List[FacturaAdjunto]:
        """Obtiene adjuntos de un tipo específico."""
        return self.db.scalars(
            select(FacturaAdjunto).where(
                (FacturaAdjunto.factura_id == factura_id) &
                (FacturaAdjunto.tipo_documento == tipo_documento)
            )
        ).all()
    
    def obtener_por_drive_file_id(self, google_drive_file_id: str) -> Optional[FacturaAdjunto]:
        """Obtiene adjunto por ID de Google Drive."""
        return self.db.scalar(
            select(FacturaAdjunto).where(
                FacturaAdjunto.google_drive_file_id == google_drive_file_id
            )
        )
    
    def actualizar(self, adjunto_id: int, **kwargs) -> Optional[FacturaAdjunto]:
        """Actualiza un adjunto."""
        adjunto = self.obtener_por_id(adjunto_id)
        if not adjunto:
            return None
        for key, value in kwargs.items():
            if hasattr(adjunto, key):
                setattr(adjunto, key, value)
        self.db.commit()
        self.db.refresh(adjunto)
        return adjunto
    
    def eliminar(self, adjunto_id: int) -> bool:
        """Elimina un adjunto."""
        adjunto = self.obtener_por_id(adjunto_id)
        if not adjunto:
            return False
        self.db.delete(adjunto)
        self.db.commit()
        return True
    
    def eliminar_por_factura(self, factura_id: int) -> int:
        """Elimina todos los adjuntos de una factura."""
        adjuntos = self.obtener_por_factura(factura_id)
        for adjunto in adjuntos:
            self.db.delete(adjunto)
        self.db.commit()
        return len(adjuntos)
