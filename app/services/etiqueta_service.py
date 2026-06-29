"""
Servicio para FTRA_ETIQUETAS.
Lógica de negocio para gestión de etiquetas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.etiqueta import Etiqueta
from app.repositories.etiqueta_repository import EtiquetaRepository
from app.schemas.factura_schemas import EtiquetaCreate, EtiquetaUpdate


class EtiquetaService:
    """Servicio para Etiqueta."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = EtiquetaRepository(db)
    
    def crear_etiqueta(self, empresa_id: int, datos: EtiquetaCreate) -> Etiqueta:
        """Crea una nueva etiqueta."""
        etiqueta = Etiqueta(empresa_id=empresa_id, **datos.dict())
        return self.repo.crear(etiqueta)
    
    def obtener_etiqueta(self, etiqueta_id: int) -> Optional[Etiqueta]:
        """Obtiene una etiqueta."""
        return self.repo.obtener_por_id(etiqueta_id)
    
    def obtener_etiquetas_empresa(self, empresa_id: int, activas_solo: bool = True) -> List[Etiqueta]:
        """Obtiene etiquetas de una empresa."""
        return self.repo.obtener_por_empresa(empresa_id, activas_solo=activas_solo)
    
    def buscar_etiqueta(self, empresa_id: int, nombre: str) -> Optional[Etiqueta]:
        """Busca una etiqueta por nombre."""
        return self.repo.obtener_por_nombre(empresa_id, nombre)
    
    def actualizar_etiqueta(self, etiqueta_id: int, datos: EtiquetaUpdate) -> Etiqueta:
        """Actualiza una etiqueta."""
        etiqueta = self.repo.obtener_por_id(etiqueta_id)
        if not etiqueta:
            raise ValueError("Etiqueta no encontrada")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(etiqueta_id, **actualizaciones)
    
    def eliminar_etiqueta(self, etiqueta_id: int) -> bool:
        """Elimina una etiqueta."""
        etiqueta = self.repo.obtener_por_id(etiqueta_id)
        if not etiqueta:
            raise ValueError("Etiqueta no encontrada")
        
        return self.repo.eliminar(etiqueta_id)
    
    def desactivar_etiqueta(self, etiqueta_id: int) -> Etiqueta:
        """Desactiva una etiqueta."""
        return self.actualizar_etiqueta(etiqueta_id, EtiquetaUpdate(activa=False))
    
    def activar_etiqueta(self, etiqueta_id: int) -> Etiqueta:
        """Activa una etiqueta."""
        return self.actualizar_etiqueta(etiqueta_id, EtiquetaUpdate(activa=True))
