"""
Servicio para FTRA_DRIVE_CARPETAS.
Lógica de negocio para gestión de carpetas de Google Drive.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.drive_carpeta import DriveCarpeta
from app.repositories.drive_carpeta_repository import DriveCarpetaRepository
from app.schemas.factura_schemas import DriveCarpetaCreate, DriveCarpetaUpdate


class DriveCarpetaService:
    """Servicio para DriveCarpeta."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = DriveCarpetaRepository(db)
    
    def crear_carpeta(self, empresa_id: int, datos: DriveCarpetaCreate) -> DriveCarpeta:
        """Crea una nueva carpeta de Google Drive."""
        carpeta = DriveCarpeta(empresa_id=empresa_id, **datos.dict())
        return self.repo.crear(carpeta)
    
    def obtener_carpeta(self, carpeta_id: int) -> Optional[DriveCarpeta]:
        """Obtiene una carpeta."""
        return self.repo.obtener_por_id(carpeta_id)
    
    def obtener_carpetas_empresa(self, empresa_id: int) -> List[DriveCarpeta]:
        """Obtiene carpetas de una empresa."""
        return self.repo.obtener_por_empresa(empresa_id)
    
    def obtener_carpeta_periodo(self, empresa_id: int, anio: int, mes: int) -> Optional[DriveCarpeta]:
        """Obtiene carpeta para un período específico."""
        return self.repo.obtener_por_periodo(empresa_id, anio, mes)
    
    def actualizar_carpeta(self, carpeta_id: int, datos: DriveCarpetaUpdate) -> DriveCarpeta:
        """Actualiza una carpeta."""
        carpeta = self.repo.obtener_por_id(carpeta_id)
        if not carpeta:
            raise ValueError("Carpeta no encontrada")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(carpeta_id, **actualizaciones)
    
    def eliminar_carpeta(self, carpeta_id: int) -> bool:
        """Elimina una carpeta."""
        carpeta = self.repo.obtener_por_id(carpeta_id)
        if not carpeta:
            raise ValueError("Carpeta no encontrada")
        
        return self.repo.eliminar(carpeta_id)
