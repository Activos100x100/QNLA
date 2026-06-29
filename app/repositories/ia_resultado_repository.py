"""
Repository para FTRA_IA_RESULTADOS.
CRUD para resultados de IA.
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.ia_resultado import IaResultado


class IaResultadoRepository:
    """Repository para IaResultado."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, resultado: IaResultado) -> IaResultado:
        """Crea un nuevo resultado de IA."""
        self.db.add(resultado)
        self.db.commit()
        self.db.refresh(resultado)
        return resultado
    
    def obtener_por_id(self, resultado_id: int) -> Optional[IaResultado]:
        """Obtiene un resultado por ID."""
        return self.db.get(IaResultado, resultado_id)
    
    def obtener_por_factura(self, factura_id: int) -> Optional[IaResultado]:
        """Obtiene resultado IA de una factura."""
        return self.db.scalar(
            select(IaResultado).where(IaResultado.factura_id == factura_id)
            .order_by(IaResultado.created_at.desc())
        )
    
    def obtener_ultimos_por_factura(self, factura_id: int, limite: int = 5) -> List[IaResultado]:
        """Obtiene últimos resultados de una factura."""
        return self.db.scalars(
            select(IaResultado).where(IaResultado.factura_id == factura_id)
            .order_by(IaResultado.created_at.desc())
            .limit(limite)
        ).all()
    
    def obtener_por_modelo(self, modelo_ia: str) -> List[IaResultado]:
        """Obtiene resultados de un modelo específico."""
        return self.db.scalars(
            select(IaResultado).where(IaResultado.modelo_ia == modelo_ia)
            .order_by(IaResultado.created_at.desc())
        ).all()
    
    def obtener_coste_total(self) -> Decimal:
        """Calcula coste total de todos los procesamientos IA."""
        resultado = self.db.scalar(select(func.sum(IaResultado.coste)))
        return resultado or Decimal("0")
    
    def actualizar(self, resultado_id: int, **kwargs) -> Optional[IaResultado]:
        """Actualiza un resultado."""
        resultado = self.obtener_por_id(resultado_id)
        if not resultado:
            return None
        for key, value in kwargs.items():
            if hasattr(resultado, key):
                setattr(resultado, key, value)
        self.db.commit()
        self.db.refresh(resultado)
        return resultado
    
    def eliminar(self, resultado_id: int) -> bool:
        """Elimina un resultado."""
        resultado = self.obtener_por_id(resultado_id)
        if not resultado:
            return False
        self.db.delete(resultado)
        self.db.commit()
        return True
