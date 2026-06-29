"""
Servicio para FTRA_ESTADOS.
Lógica de negocio para gestión de estados de facturas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.estado import Estado
from app.repositories.estado_repository import EstadoRepository
from app.schemas.factura_schemas import EstadoCreate, EstadoUpdate


class EstadoService:
    """Servicio para Estado."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = EstadoRepository(db)
    
    def crear_estado(self, datos: EstadoCreate) -> Estado:
        """Crea un nuevo estado."""
        # Validar que no exista otro con el mismo nombre
        existente = self.repo.obtener_por_nombre(datos.nombre)
        if existente:
            raise ValueError(f"Ya existe un estado con nombre '{datos.nombre}'")
        
        estado = Estado(**datos.dict())
        return self.repo.crear(estado)
    
    def obtener_estado(self, estado_id: int) -> Optional[Estado]:
        """Obtiene un estado por ID."""
        estado = self.repo.obtener_por_id(estado_id)
        if not estado:
            raise ValueError("Estado no encontrado")
        return estado
    
    def obtener_todos(self) -> List[Estado]:
        """Obtiene todos los estados."""
        return self.repo.obtener_todos()
    
    def obtener_estados_finales(self) -> List[Estado]:
        """Obtiene estados finales."""
        return self.repo.obtener_finales()
    
    def actualizar_estado(self, estado_id: int, datos: EstadoUpdate) -> Estado:
        """Actualiza un estado."""
        estado = self.repo.obtener_por_id(estado_id)
        if not estado:
            raise ValueError("Estado no encontrado")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(estado_id, **actualizaciones)
    
    def eliminar_estado(self, estado_id: int) -> bool:
        """Elimina un estado."""
        estado = self.repo.obtener_por_id(estado_id)
        if not estado:
            raise ValueError("Estado no encontrado")
        
        # Verificar que no tenga facturas
        if estado.facturas:
            raise ValueError("No se puede eliminar un estado que tiene facturas asociadas")
        
        return self.repo.eliminar(estado_id)
