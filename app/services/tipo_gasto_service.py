"""
Servicio para FTRA_TIPOS_GASTO.
Lógica de negocio para gestión de tipos de gasto.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.tipo_gasto import TipoGasto
from app.repositories.tipo_gasto_repository import TipoGastoRepository
from app.schemas.factura_schemas import TipoGastoCreate, TipoGastoUpdate


class TipoGastoService:
    """Servicio para TipoGasto."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = TipoGastoRepository(db)
    
    def crear_tipo_gasto(self, datos: TipoGastoCreate) -> TipoGasto:
        """Crea un nuevo tipo de gasto."""
        existente = self.repo.obtener_por_nombre(datos.nombre)
        if existente:
            raise ValueError(f"Ya existe un tipo de gasto con nombre '{datos.nombre}'")
        
        tipo_gasto = TipoGasto(**datos.dict())
        return self.repo.crear(tipo_gasto)
    
    def obtener_tipo_gasto(self, tipo_gasto_id: int) -> Optional[TipoGasto]:
        """Obtiene un tipo de gasto por ID."""
        tipo_gasto = self.repo.obtener_por_id(tipo_gasto_id)
        if not tipo_gasto:
            raise ValueError("Tipo de gasto no encontrado")
        return tipo_gasto
    
    def obtener_todos(self) -> List[TipoGasto]:
        """Obtiene todos los tipos de gasto."""
        return self.repo.obtener_todos()
    
    def actualizar_tipo_gasto(self, tipo_gasto_id: int, datos: TipoGastoUpdate) -> TipoGasto:
        """Actualiza un tipo de gasto."""
        tipo_gasto = self.repo.obtener_por_id(tipo_gasto_id)
        if not tipo_gasto:
            raise ValueError("Tipo de gasto no encontrado")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(tipo_gasto_id, **actualizaciones)
    
    def eliminar_tipo_gasto(self, tipo_gasto_id: int) -> bool:
        """Elimina un tipo de gasto."""
        tipo_gasto = self.repo.obtener_por_id(tipo_gasto_id)
        if not tipo_gasto:
            raise ValueError("Tipo de gasto no encontrado")
        
        if tipo_gasto.facturas:
            raise ValueError("No se puede eliminar un tipo de gasto que tiene facturas asociadas")
        
        return self.repo.eliminar(tipo_gasto_id)
