"""
Servicio para FTRA_EMPRESAS.
Lógica de negocio para gestión de empresas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.empresa import Empresa
from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.factura_schemas import EmpresaCreate, EmpresaUpdate


class EmpresaService:
    """Servicio para Empresa."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmpresaRepository(db)
    
    def crear_empresa(self, datos: EmpresaCreate) -> Empresa:
        """Crea una nueva empresa."""
        # Validar que no exista otra con el mismo CIF
        if datos.cif:
            existente = self.repo.obtener_por_cif(datos.cif)
            if existente:
                raise ValueError(f"Ya existe una empresa con CIF {datos.cif}")
        
        empresa = Empresa(**datos.dict())
        return self.repo.crear(empresa)
    
    def obtener_empresa(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por ID."""
        empresa = self.repo.obtener_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa no encontrada")
        return empresa
    
    def obtener_todas(self, activas_solo: bool = False) -> List[Empresa]:
        """Obtiene todas las empresas."""
        return self.repo.obtener_todos(activos_solo=activas_solo)
    
    def actualizar_empresa(self, empresa_id: int, datos: EmpresaUpdate) -> Empresa:
        """Actualiza una empresa."""
        empresa = self.repo.obtener_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa no encontrada")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(empresa_id, **actualizaciones)
    
    def eliminar_empresa(self, empresa_id: int) -> bool:
        """Elimina una empresa."""
        empresa = self.repo.obtener_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa no encontrada")
        
        # Verificar que no tenga dependencias (proveedores, clientes, etc.)
        if empresa.proveedores or empresa.clientes:
            raise ValueError("No se puede eliminar una empresa con dependencias")
        
        return self.repo.eliminar(empresa_id)
    
    def contar_empresas(self, activas_solo: bool = False) -> int:
        """Cuenta empresas."""
        return self.repo.contar(activos_solo=activas_solo)
