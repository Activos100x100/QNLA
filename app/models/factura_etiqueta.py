"""
Modelo SQLAlchemy para FTRA_FACTURA_ETIQUETAS.
Relación M2M entre facturas y etiquetas.
"""

from sqlalchemy import ForeignKey, BigInteger, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class FacturaEtiqueta(Base):
    """Modelo ORM para tabla FTRA_FACTURA_ETIQUETAS (Asociación M2M)."""
    
    __tablename__ = "ftra_factura_etiquetas"
    __table_args__ = (
        PrimaryKeyConstraint("factura_id", "etiqueta_id"),
    )
    
    # Columnas (componen la PK)
    factura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_facturas.id"), nullable=False)
    etiqueta_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_etiquetas.id"), nullable=False)
    
    def __repr__(self) -> str:
        return f"<FacturaEtiqueta factura_id={self.factura_id} etiqueta_id={self.etiqueta_id}>"
