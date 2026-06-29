"""
Servicio principal para FTRA_FACTURAS.
Orquestación completa del procesamiento de facturas.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.factura import Factura
from app.repositories.factura_repository import FacturaRepository
from app.repositories.factura_linea_repository import FacturaLineaRepository
from app.repositories.factura_historial_repository import FacturaHistorialRepository
from app.schemas.factura_schemas import FacturaCreate, FacturaUpdate


class FacturaService:
    """Servicio principal para Factura."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = FacturaRepository(db)
        self.repo_lineas = FacturaLineaRepository(db)
        self.repo_historial = FacturaHistorialRepository(db)
    
    def crear_factura(self, datos: FacturaCreate) -> Factura:
        """Crea una nueva factura."""
        # Validar que no exista otra con el mismo número
        if datos.numero_factura:
            existente = self.repo.obtener_por_numero(datos.empresa_id, datos.numero_factura)
            if existente:
                raise ValueError(f"Ya existe una factura con número {datos.numero_factura}")
        
        factura = Factura(**datos.dict())
        return self.repo.crear(factura)
    
    def obtener_factura(self, factura_id: int) -> Optional[Factura]:
        """Obtiene una factura por ID."""
        factura = self.repo.obtener_por_id(factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")
        return factura
    
    def obtener_facturas_empresa(self, empresa_id: int, limite: int = 100) -> List[Factura]:
        """Obtiene facturas de una empresa."""
        return self.repo.obtener_por_empresa(empresa_id, limite=limite)
    
    def obtener_facturas_proveedor(self, empresa_id: int, proveedor_id: int) -> List[Factura]:
        """Obtiene facturas de un proveedor."""
        return self.repo.obtener_por_proveedor(empresa_id, proveedor_id)
    
    def obtener_pendientes_revision(self, empresa_id: int) -> List[Factura]:
        """Obtiene facturas pendientes de revisión."""
        return self.repo.obtener_pendientes_revision(empresa_id)
    
    def obtener_pendientes_contabilizacion(self, empresa_id: int) -> List[Factura]:
        """Obtiene facturas pendientes de contabilizar."""
        return self.repo.obtener_pendientes_contabilizacion(empresa_id)
    
    def actualizar_factura(self, factura_id: int, datos: FacturaUpdate) -> Factura:
        """Actualiza una factura."""
        factura = self.repo.obtener_por_id(factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")
        
        actualizaciones = datos.dict(exclude_unset=True)
        return self.repo.actualizar(factura_id, **actualizaciones)
    
    def marcar_revisada(self, factura_id: int) -> Factura:
        """Marca una factura como revisada."""
        return self.actualizar_factura(factura_id, FacturaUpdate(revisada=True))
    
    def marcar_contabilizada(self, factura_id: int) -> Factura:
        """Marca una factura como contabilizada."""
        return self.actualizar_factura(factura_id, FacturaUpdate(contabilizada=True))
    
    def marcar_favorita(self, factura_id: int) -> Factura:
        """Marca una factura como favorita."""
        return self.actualizar_factura(factura_id, FacturaUpdate(favorita=True))
    
    def cambiar_estado(self, factura_id: int, nuevo_estado_id: int, usuario_id: int = None, comentario: str = None) -> Factura:
        """Cambia el estado de una factura y registra en historial."""
        factura = self.repo.obtener_por_id(factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")
        
        estado_anterior_id = factura.estado_id
        
        # Actualizar factura
        factura = self.repo.actualizar(factura_id, estado_id=nuevo_estado_id)
        
        # Registrar en historial
        from app.models.factura_historial import FacturaHistorial
        historial = FacturaHistorial(
            factura_id=factura_id,
            estado_anterior_id=estado_anterior_id,
            estado_nuevo_id=nuevo_estado_id,
            usuario_id=usuario_id,
            comentario=comentario
        )
        self.repo_historial.crear(historial)
        
        return factura
    
    def eliminar_factura(self, factura_id: int) -> bool:
        """Elimina una factura."""
        factura = self.repo.obtener_por_id(factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")
        
        # Eliminar líneas asociadas
        self.repo_lineas.eliminar_por_factura(factura_id)
        
        return self.repo.eliminar(factura_id)
    
    def obtener_estadisticas_empresa(self, empresa_id: int) -> dict:
        """Obtiene estadísticas de facturas de una empresa."""
        total_facturas = self.repo.contar_por_empresa(empresa_id)
        sin_revisar = self.repo.contar_sin_revisar(empresa_id)
        sin_contabilizar = self.repo.contar_sin_contabilizar(empresa_id)
        total_importe = self.repo.obtener_total_por_empresa(empresa_id)
        
        return {
            "total_facturas": total_facturas,
            "pendientes_revision": sin_revisar,
            "pendientes_contabilizacion": sin_contabilizar,
            "total_importe": float(total_importe),
            "revisadas": total_facturas - sin_revisar,
            "contabilizadas": total_facturas - sin_contabilizar,
        }
