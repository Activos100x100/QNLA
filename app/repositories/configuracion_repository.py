"""
Repository para FTRA_CONFIGURACION.
CRUD para configuración del sistema.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.configuracion import Configuracion


class ConfiguracionRepository:
    """Repository para Configuracion."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, configuracion: Configuracion) -> Configuracion:
        """Crea una nueva configuración."""
        self.db.add(configuracion)
        self.db.commit()
        self.db.refresh(configuracion)
        return configuracion
    
    def obtener_por_id(self, config_id: int) -> Optional[Configuracion]:
        """Obtiene una configuración por ID."""
        return self.db.get(Configuracion, config_id)
    
    def obtener_por_clave(self, clave: str) -> Optional[Configuracion]:
        """Obtiene una configuración por clave."""
        return self.db.scalar(select(Configuracion).where(Configuracion.clave == clave))
    
    def obtener_valor(self, clave: str, default: str = None) -> Optional[str]:
        """Obtiene el valor de una clave de configuración."""
        config = self.obtener_por_clave(clave)
        return config.valor if config else default
    
    def obtener_todos(self) -> List[Configuracion]:
        """Obtiene todas las configuraciones."""
        return self.db.scalars(select(Configuracion).order_by(Configuracion.clave)).all()
    
    def establecer(self, clave: str, valor: str, descripcion: str = None) -> Configuracion:
        """Establece o actualiza una configuración."""
        config = self.obtener_por_clave(clave)
        if config:
            config.valor = valor
            if descripcion:
                config.descripcion = descripcion
        else:
            config = Configuracion(clave=clave, valor=valor, descripcion=descripcion)
            self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def eliminar(self, config_id: int) -> bool:
        """Elimina una configuración."""
        config = self.obtener_por_id(config_id)
        if not config:
            return False
        self.db.delete(config)
        self.db.commit()
        return True
