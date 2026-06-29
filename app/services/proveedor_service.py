"""
Servicio para FTRA_PROVEEDORES.
Lógica de negocio para gestión de proveedores.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.proveedor import Proveedor
from app.repositories.proveedor_repository import ProveedorRepository
from app.schemas.factura_schemas import ProveedorCreate, ProveedorUpdate


class ProveedorService:
    """Servicio para Proveedor."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProveedorRepository(db)
    
    def crear_proveedor(self, empresa_id: int, datos: ProveedorCreate) -> Proveedor:
        """Crea un nuevo proveedor."""
        # Validar duplicado de CIF
        if datos.cif:
            existente = self.repo.obtener_por_cif(empresa_id, datos.cif)
            if existente:
                raise ValueError(f"Ya existe un proveedor con CIF {datos.cif} en esta empresa")
        
        proveedor = Proveedor(empresa_id=empresa_id, **datos.dict())
        return self.repo.crear(proveedor)
    
    def obtener_proveedor(self, proveedor_id: int) -> Optional[Proveedor]:
        """Obtiene un proveedor."""
        return self.repo.obtener_por_id(proveedor_id)
    
    def obtener_proveedores_empresa(self, empresa_id: int, activos_solo: bool = True) -> List[Proveedor]:
        """Obtiene proveedores de una empresa."""
        return self.repo.obtener_por_empresa(empresa_id, activos_solo=activos_solo)
    
    def buscar_proveedores(self, empresa_id: int, termino: str) -> List[Proveedor]:
        """Busca proveedores por nombre, CIF o email."""
        return self.repo.buscar(empresa_id, termino)
    
    def actualizar_proveedor(self, proveedor_id: int, datos: ProveedorUpdate) -> Proveedor:
        """Actualiza un proveedor."""
        proveedor = self.repo.obtener_por_id(proveedor_id)
        if not proveedor:
            raise ValueError("Proveedor no encontrado")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(proveedor_id, **actualizaciones)
    
    def eliminar_proveedor(self, proveedor_id: int) -> bool:
        """Elimina un proveedor."""
        proveedor = self.repo.obtener_por_id(proveedor_id)
        if not proveedor:
            raise ValueError("Proveedor no encontrado")
        
        if proveedor.facturas:
            raise ValueError("No se puede eliminar un proveedor que tiene facturas asociadas")
        
        return self.repo.eliminar(proveedor_id)
