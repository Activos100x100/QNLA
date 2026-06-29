"""
Servicio para FTRA_CLIENTES.
Lógica de negocio para gestión de clientes.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.factura_schemas import ClienteCreate, ClienteUpdate


class ClienteService:
    """Servicio para Cliente."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ClienteRepository(db)
    
    def crear_cliente(self, empresa_id: int, datos: ClienteCreate) -> Cliente:
        """Crea un nuevo cliente."""
        # Validar duplicado de CIF
        if datos.cif:
            existente = self.repo.obtener_por_cif(empresa_id, datos.cif)
            if existente:
                raise ValueError(f"Ya existe un cliente con CIF {datos.cif} en esta empresa")
        
        cliente = Cliente(empresa_id=empresa_id, **datos.dict())
        return self.repo.crear(cliente)
    
    def obtener_cliente(self, cliente_id: int) -> Optional[Cliente]:
        """Obtiene un cliente."""
        return self.repo.obtener_por_id(cliente_id)
    
    def obtener_clientes_empresa(self, empresa_id: int, activos_solo: bool = True) -> List[Cliente]:
        """Obtiene clientes de una empresa."""
        return self.repo.obtener_por_empresa(empresa_id, activos_solo=activos_solo)
    
    def buscar_clientes(self, empresa_id: int, termino: str) -> List[Cliente]:
        """Busca clientes por nombre, CIF o email."""
        return self.repo.buscar(empresa_id, termino)
    
    def actualizar_cliente(self, cliente_id: int, datos: ClienteUpdate) -> Cliente:
        """Actualiza un cliente."""
        cliente = self.repo.obtener_por_id(cliente_id)
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(cliente_id, **actualizaciones)
    
    def eliminar_cliente(self, cliente_id: int) -> bool:
        """Elimina un cliente."""
        cliente = self.repo.obtener_por_id(cliente_id)
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        if cliente.facturas:
            raise ValueError("No se puede eliminar un cliente que tiene facturas asociadas")
        
        return self.repo.eliminar(cliente_id)
