"""
Repository para FTRA_CLIENTES.
CRUD para clientes con búsqueda avanzada.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.cliente import Cliente


class ClienteRepository:
    """Repository para Cliente."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, cliente: Cliente) -> Cliente:
        """Crea un nuevo cliente."""
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
    
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        """Obtiene un cliente por ID."""
        return self.db.get(Cliente, cliente_id)
    
    def obtener_por_empresa(self, empresa_id: int, activos_solo: bool = False) -> List[Cliente]:
        """Obtiene clientes de una empresa."""
        query = select(Cliente).where(Cliente.empresa_id == empresa_id)
        if activos_solo:
            query = query.where(Cliente.activo == True)
        return self.db.scalars(query.order_by(Cliente.nombre)).all()
    
    def obtener_por_cif(self, empresa_id: int, cif: str) -> Optional[Cliente]:
        """Obtiene un cliente por CIF."""
        return self.db.scalar(
            select(Cliente).where(
                and_(
                    Cliente.empresa_id == empresa_id,
                    Cliente.cif == cif
                )
            )
        )
    
    def obtener_por_nombre(self, empresa_id: int, nombre: str) -> Optional[Cliente]:
        """Obtiene un cliente por nombre."""
        return self.db.scalar(
            select(Cliente).where(
                and_(
                    Cliente.empresa_id == empresa_id,
                    Cliente.nombre == nombre
                )
            )
        )
    
    def buscar(self, empresa_id: int, termino: str) -> List[Cliente]:
        """Busca clientes por nombre, CIF o email."""
        termino_busqueda = f"%{termino}%"
        return self.db.scalars(
            select(Cliente).where(
                and_(
                    Cliente.empresa_id == empresa_id,
                    (
                        Cliente.nombre.ilike(termino_busqueda) |
                        Cliente.cif.ilike(termino_busqueda) |
                        Cliente.email.ilike(termino_busqueda)
                    )
                )
            )
        ).all()
    
    def actualizar(self, cliente_id: int, **kwargs) -> Optional[Cliente]:
        """Actualiza un cliente."""
        cliente = self.obtener_por_id(cliente_id)
        if not cliente:
            return None
        for key, value in kwargs.items():
            if hasattr(cliente, key):
                setattr(cliente, key, value)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
    
    def eliminar(self, cliente_id: int) -> bool:
        """Elimina un cliente."""
        cliente = self.obtener_por_id(cliente_id)
        if not cliente:
            return False
        self.db.delete(cliente)
        self.db.commit()
        return True
    
    def contar_por_empresa(self, empresa_id: int, activos_solo: bool = False) -> int:
        """Cuenta clientes de una empresa."""
        query = select(Cliente).where(Cliente.empresa_id == empresa_id)
        if activos_solo:
            query = query.where(Cliente.activo == True)
        return len(self.db.scalars(query).all())
