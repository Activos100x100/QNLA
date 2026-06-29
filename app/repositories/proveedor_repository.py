"""
Repository para FTRA_PROVEEDORES.
CRUD para proveedores con búsqueda avanzada.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.proveedor import Proveedor


class ProveedorRepository:
    """Repository para Proveedor."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, proveedor: Proveedor) -> Proveedor:
        """Crea un nuevo proveedor."""
        self.db.add(proveedor)
        self.db.commit()
        self.db.refresh(proveedor)
        return proveedor
    
    def obtener_por_id(self, proveedor_id: int) -> Optional[Proveedor]:
        """Obtiene un proveedor por ID."""
        return self.db.get(Proveedor, proveedor_id)
    
    def obtener_por_empresa(self, empresa_id: int, activos_solo: bool = False) -> List[Proveedor]:
        """Obtiene proveedores de una empresa."""
        query = select(Proveedor).where(Proveedor.empresa_id == empresa_id)
        if activos_solo:
            query = query.where(Proveedor.activo == True)
        return self.db.scalars(query.order_by(Proveedor.nombre)).all()
    
    def obtener_por_cif(self, empresa_id: int, cif: str) -> Optional[Proveedor]:
        """Obtiene un proveedor por CIF."""
        return self.db.scalar(
            select(Proveedor).where(
                and_(
                    Proveedor.empresa_id == empresa_id,
                    Proveedor.cif == cif
                )
            )
        )
    
    def obtener_por_nombre(self, empresa_id: int, nombre: str) -> Optional[Proveedor]:
        """Obtiene un proveedor por nombre."""
        return self.db.scalar(
            select(Proveedor).where(
                and_(
                    Proveedor.empresa_id == empresa_id,
                    Proveedor.nombre == nombre
                )
            )
        )
    
    def buscar(self, empresa_id: int, termino: str) -> List[Proveedor]:
        """Busca proveedores por nombre, CIF o email."""
        termino_busqueda = f"%{termino}%"
        return self.db.scalars(
            select(Proveedor).where(
                and_(
                    Proveedor.empresa_id == empresa_id,
                    (
                        Proveedor.nombre.ilike(termino_busqueda) |
                        Proveedor.cif.ilike(termino_busqueda) |
                        Proveedor.email.ilike(termino_busqueda)
                    )
                )
            )
        ).all()
    
    def actualizar(self, proveedor_id: int, **kwargs) -> Optional[Proveedor]:
        """Actualiza un proveedor."""
        proveedor = self.obtener_por_id(proveedor_id)
        if not proveedor:
            return None
        for key, value in kwargs.items():
            if hasattr(proveedor, key):
                setattr(proveedor, key, value)
        self.db.commit()
        self.db.refresh(proveedor)
        return proveedor
    
    def eliminar(self, proveedor_id: int) -> bool:
        """Elimina un proveedor."""
        proveedor = self.obtener_por_id(proveedor_id)
        if not proveedor:
            return False
        self.db.delete(proveedor)
        self.db.commit()
        return True
    
    def contar_por_empresa(self, empresa_id: int, activos_solo: bool = False) -> int:
        """Cuenta proveedores de una empresa."""
        query = select(Proveedor).where(Proveedor.empresa_id == empresa_id)
        if activos_solo:
            query = query.where(Proveedor.activo == True)
        return len(self.db.scalars(query).all())
