"""
Repository para FTRA_FACTURAS.
CRUD completo para facturas con búsqueda y filtrado avanzado.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session
from app.models.factura import Factura


class FacturaRepository:
    """Repository para Factura."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, factura: Factura) -> Factura:
        """Crea una nueva factura."""
        self.db.add(factura)
        self.db.commit()
        self.db.refresh(factura)
        return factura
    
    def obtener_por_id(self, factura_id: int) -> Optional[Factura]:
        """Obtiene una factura por ID."""
        return self.db.get(Factura, factura_id)
    
    def obtener_por_numero(self, empresa_id: int, numero_factura: str) -> Optional[Factura]:
        """Obtiene una factura por número."""
        return self.db.scalar(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.numero_factura == numero_factura
                )
            )
        )
    
    def obtener_por_empresa(self, empresa_id: int, limite: int = 100) -> List[Factura]:
        """Obtiene facturas de una empresa."""
        return self.db.scalars(
            select(Factura).where(Factura.empresa_id == empresa_id)
            .order_by(Factura.created_at.desc())
            .limit(limite)
        ).all()
    
    def obtener_por_proveedor(self, empresa_id: int, proveedor_id: int) -> List[Factura]:
        """Obtiene facturas de un proveedor."""
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.proveedor_id == proveedor_id
                )
            ).order_by(Factura.fecha_factura.desc())
        ).all()
    
    def obtener_por_estado(self, empresa_id: int, estado_id: int) -> List[Factura]:
        """Obtiene facturas por estado."""
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.estado_id == estado_id
                )
            ).order_by(Factura.fecha_factura.desc())
        ).all()
    
    def obtener_por_rango_fechas(self, empresa_id: int, fecha_inicio: date, fecha_fin: date) -> List[Factura]:
        """Obtiene facturas en un rango de fechas."""
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.fecha_factura >= fecha_inicio,
                    Factura.fecha_factura <= fecha_fin
                )
            ).order_by(Factura.fecha_factura.desc())
        ).all()
    
    def obtener_pendientes_revision(self, empresa_id: int) -> List[Factura]:
        """Obtiene facturas sin revisar."""
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.revisada == False
                )
            ).order_by(Factura.fecha_factura.desc())
        ).all()
    
    def obtener_pendientes_contabilizacion(self, empresa_id: int) -> List[Factura]:
        """Obtiene facturas sin contabilizar."""
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.contabilizada == False
                )
            ).order_by(Factura.fecha_factura.desc())
        ).all()
    
    def obtener_favoritas(self, empresa_id: int) -> List[Factura]:
        """Obtiene facturas marcadas como favoritas."""
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.favorita == True
                )
            ).order_by(Factura.fecha_factura.desc())
        ).all()
    
    def buscar(self, empresa_id: int, termino: str) -> List[Factura]:
        """Busca facturas por número, proveedor o CIF."""
        termino_busqueda = f"%{termino}%"
        return self.db.scalars(
            select(Factura).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    (
                        Factura.numero_factura.ilike(termino_busqueda) |
                        Factura.codigo_factura.ilike(termino_busqueda)
                    )
                )
            )
        ).all()
    
    def actualizar(self, factura_id: int, **kwargs) -> Optional[Factura]:
        """Actualiza una factura."""
        factura = self.obtener_por_id(factura_id)
        if not factura:
            return None
        for key, value in kwargs.items():
            if hasattr(factura, key):
                setattr(factura, key, value)
        self.db.commit()
        self.db.refresh(factura)
        return factura
    
    def eliminar(self, factura_id: int) -> bool:
        """Elimina una factura."""
        factura = self.obtener_por_id(factura_id)
        if not factura:
            return False
        self.db.delete(factura)
        self.db.commit()
        return True
    
    def contar_por_empresa(self, empresa_id: int) -> int:
        """Cuenta facturas de una empresa."""
        return self.db.scalar(
            select(func.count(Factura.id)).where(Factura.empresa_id == empresa_id)
        ) or 0
    
    def contar_sin_revisar(self, empresa_id: int) -> int:
        """Cuenta facturas sin revisar."""
        return self.db.scalar(
            select(func.count(Factura.id)).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.revisada == False
                )
            )
        ) or 0
    
    def contar_sin_contabilizar(self, empresa_id: int) -> int:
        """Cuenta facturas sin contabilizar."""
        return self.db.scalar(
            select(func.count(Factura.id)).where(
                and_(
                    Factura.empresa_id == empresa_id,
                    Factura.contabilizada == False
                )
            )
        ) or 0
    
    def obtener_total_por_empresa(self, empresa_id: int) -> Decimal:
        """Obtiene total de facturas de una empresa."""
        resultado = self.db.scalar(
            select(func.sum(Factura.total)).where(Factura.empresa_id == empresa_id)
        )
        return resultado or Decimal("0")
