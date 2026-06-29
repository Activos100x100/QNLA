"""
Repository para FTRA_OCR_RESULTADOS.
CRUD para resultados de OCR.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ocr_resultado import OcrResultado


class OcrResultadoRepository:
    """Repository para OcrResultado."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, resultado: OcrResultado) -> OcrResultado:
        """Crea un nuevo resultado de OCR."""
        self.db.add(resultado)
        self.db.commit()
        self.db.refresh(resultado)
        return resultado
    
    def obtener_por_id(self, resultado_id: int) -> Optional[OcrResultado]:
        """Obtiene un resultado por ID."""
        return self.db.get(OcrResultado, resultado_id)
    
    def obtener_por_factura(self, factura_id: int) -> Optional[OcrResultado]:
        """Obtiene resultado OCR de una factura."""
        return self.db.scalar(
            select(OcrResultado).where(OcrResultado.factura_id == factura_id)
            .order_by(OcrResultado.created_at.desc())
        )
    
    def obtener_ultimos_por_factura(self, factura_id: int, limite: int = 5) -> List[OcrResultado]:
        """Obtiene últimos resultados de una factura."""
        return self.db.scalars(
            select(OcrResultado).where(OcrResultado.factura_id == factura_id)
            .order_by(OcrResultado.created_at.desc())
            .limit(limite)
        ).all()
    
    def actualizar(self, resultado_id: int, **kwargs) -> Optional[OcrResultado]:
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
