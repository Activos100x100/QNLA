"""
Servicio para FTRA_CONFIGURACION.
Lógica de negocio para gestión de configuración del sistema.
"""

from typing import List, Optional, Any
from sqlalchemy.orm import Session
from app.models.configuracion import Configuracion
from app.repositories.configuracion_repository import ConfiguracionRepository
from app.schemas.factura_schemas import ConfiguracionCreate, ConfiguracionUpdate


class ConfiguracionService:
    """Servicio para Configuracion."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConfiguracionRepository(db)
    
    def crear_configuracion(self, datos: ConfiguracionCreate) -> Configuracion:
        """Crea una nueva configuración."""
        # Validar que no exista otra con la misma clave
        existente = self.repo.obtener_por_clave(datos.clave)
        if existente:
            raise ValueError(f"Ya existe una configuración con clave '{datos.clave}'")
        
        config = Configuracion(**datos.dict())
        return self.repo.crear(config)
    
    def obtener_configuracion(self, config_id: int) -> Optional[Configuracion]:
        """Obtiene una configuración."""
        return self.repo.obtener_por_id(config_id)
    
    def obtener_valor(self, clave: str, default: Any = None) -> Any:
        """Obtiene el valor de una configuración por clave."""
        return self.repo.obtener_valor(clave, default)
    
    def establecer_valor(self, clave: str, valor: str, descripcion: str = None) -> Configuracion:
        """Establece o actualiza una configuración."""
        return self.repo.establecer(clave, valor, descripcion)
    
    def obtener_todas(self) -> List[Configuracion]:
        """Obtiene todas las configuraciones."""
        return self.repo.obtener_todos()
    
    def actualizar_configuracion(self, config_id: int, datos: ConfiguracionUpdate) -> Configuracion:
        """Actualiza una configuración."""
        config = self.repo.obtener_por_id(config_id)
        if not config:
            raise ValueError("Configuración no encontrada")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(config_id, **actualizaciones)
    
    def eliminar_configuracion(self, config_id: int) -> bool:
        """Elimina una configuración."""
        config = self.repo.obtener_por_id(config_id)
        if not config:
            raise ValueError("Configuración no encontrada")
        
        return self.repo.eliminar(config_id)
    
    def obtener_configuraciones_por_prefijo(self, prefijo: str) -> List[Configuracion]:
        """Obtiene todas las configuraciones que empiezan con un prefijo."""
        todas = self.repo.obtener_todos()
        return [c for c in todas if c.clave.startswith(prefijo)]
