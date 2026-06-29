"""
Repository para FTRA_EMPRESAS.
CRUD básico para empresas.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.empresa import Empresa


class EmpresaRepository:
    """Repository para Empresa."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, empresa: Empresa) -> Empresa:
        """Crea una nueva empresa."""
        self.db.add(empresa)
        self.db.commit()
        self.db.refresh(empresa)
        return empresa
    
    def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por ID."""
        return self.db.get(Empresa, empresa_id)
    
    def obtener_todos(self, activos_solo: bool = False) -> List[Empresa]:
        """Obtiene todas las empresas."""
        query = select(Empresa)
        if activos_solo:
            query = query.where(Empresa.activo == True)
        return self.db.scalars(query.order_by(Empresa.nombre)).all()
    
    def obtener_por_cif(self, cif: str) -> Optional[Empresa]:
        """Obtiene una empresa por CIF."""
        return self.db.scalar(select(Empresa).where(Empresa.cif == cif))
    
    def actualizar(self, empresa_id: int, **kwargs) -> Optional[Empresa]:
        """Actualiza una empresa."""
        empresa = self.obtener_por_id(empresa_id)
        if not empresa:
            return None
        for key, value in kwargs.items():
            if hasattr(empresa, key):
                setattr(empresa, key, value)
        self.db.commit()
        self.db.refresh(empresa)
        return empresa
    
    def eliminar(self, empresa_id: int) -> bool:
        """Elimina una empresa."""
        empresa = self.obtener_por_id(empresa_id)
        if not empresa:
            return False
        self.db.delete(empresa)
        self.db.commit()
        return True
    
    def contar(self, activos_solo: bool = False) -> int:
        """Cuenta empresas."""
        query = select(Empresa)
        if activos_solo:
            query = query.where(Empresa.activo == True)
        return self.db.query(query.distinct().alias()).count()
