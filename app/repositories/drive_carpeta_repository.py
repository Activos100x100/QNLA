"""
Repository para FTRA_DRIVE_CARPETAS.
CRUD para carpetas de Google Drive.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.drive_carpeta import DriveCarpeta


class DriveCarpetaRepository:
    """Repository para DriveCarpeta."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, drive_carpeta: DriveCarpeta) -> DriveCarpeta:
        """Crea una nueva carpeta de Drive."""
        self.db.add(drive_carpeta)
        self.db.commit()
        self.db.refresh(drive_carpeta)
        return drive_carpeta
    
    def obtener_por_id(self, carpeta_id: int) -> Optional[DriveCarpeta]:
        """Obtiene una carpeta por ID."""
        return self.db.get(DriveCarpeta, carpeta_id)
    
    def obtener_por_empresa(self, empresa_id: int) -> List[DriveCarpeta]:
        """Obtiene carpetas de una empresa."""
        return self.db.scalars(
            select(DriveCarpeta).where(DriveCarpeta.empresa_id == empresa_id)
            .order_by(DriveCarpeta.anio.desc(), DriveCarpeta.mes.desc())
        ).all()
    
    def obtener_por_periodo(self, empresa_id: int, anio: int, mes: int) -> Optional[DriveCarpeta]:
        """Obtiene carpeta de un período específico."""
        return self.db.scalar(
            select(DriveCarpeta).where(
                and_(
                    DriveCarpeta.empresa_id == empresa_id,
                    DriveCarpeta.anio == anio,
                    DriveCarpeta.mes == mes
                )
            )
        )
    
    def obtener_por_folder_id(self, google_drive_folder_id: str) -> Optional[DriveCarpeta]:
        """Obtiene carpeta por ID de Google Drive."""
        return self.db.scalar(
            select(DriveCarpeta).where(
                DriveCarpeta.google_drive_folder_id == google_drive_folder_id
            )
        )
    
    def actualizar(self, carpeta_id: int, **kwargs) -> Optional[DriveCarpeta]:
        """Actualiza una carpeta."""
        carpeta = self.obtener_por_id(carpeta_id)
        if not carpeta:
            return None
        for key, value in kwargs.items():
            if hasattr(carpeta, key):
                setattr(carpeta, key, value)
        self.db.commit()
        self.db.refresh(carpeta)
        return carpeta
    
    def eliminar(self, carpeta_id: int) -> bool:
        """Elimina una carpeta."""
        carpeta = self.obtener_por_id(carpeta_id)
        if not carpeta:
            return False
        self.db.delete(carpeta)
        self.db.commit()
        return True
