"""
Modelo SQLAlchemy para FTRA_FACTURAS.
Tabla principal de facturas.
"""

from datetime import datetime, date, timezone
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Text, TIMESTAMP, DATE, ForeignKey, Boolean, BigInteger, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Factura(Base):
    """Modelo ORM para tabla FTRA_FACTURAS."""
    
    __tablename__ = "ftra_facturas"
    
    # Columnas
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ftra_empresas.id"), nullable=False)
    empleado_id: Mapped[Optional[int]] = mapped_column(BigInteger)  # FK a tabla externa empleados
    proveedor_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_proveedores.id"))
    cliente_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_clientes.id"))
    estado_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_estados.id"))
    tipo_gasto_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ftra_tipos_gasto.id"))
    codigo_factura: Mapped[Optional[str]] = mapped_column(String(100))
    numero_factura: Mapped[Optional[str]] = mapped_column(String(100))
    serie: Mapped[Optional[str]] = mapped_column(String(50))
    fecha_factura: Mapped[Optional[date]] = mapped_column(DATE)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(DATE)
    fecha_subida: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    base_imponible: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    iva: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    porcentaje_iva: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    irpf: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    confianza_ia: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    revisada: Mapped[Optional[bool]] = mapped_column(Boolean)
    contabilizada: Mapped[Optional[bool]] = mapped_column(Boolean)
    favorita: Mapped[Optional[bool]] = mapped_column(Boolean)
    responsable_id: Mapped[Optional[int]] = mapped_column(BigInteger)  # FK a usuarios
    google_drive_file_id: Mapped[Optional[str]] = mapped_column(Text)
    google_drive_folder_id: Mapped[Optional[str]] = mapped_column(Text)
    google_drive_url: Mapped[Optional[str]] = mapped_column(Text)
    nombre_archivo: Mapped[Optional[str]] = mapped_column(Text)
    mime_type: Mapped[Optional[str]] = mapped_column(String(150))
    hash_sha256: Mapped[Optional[str]] = mapped_column(Text)
    tamano_archivo: Mapped[Optional[int]] = mapped_column(BigInteger)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)  # FK a usuarios
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="facturas")
    proveedor: Mapped[Optional["Proveedor"]] = relationship("Proveedor", back_populates="facturas")
    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="facturas")
    estado: Mapped[Optional["Estado"]] = relationship("Estado", back_populates="facturas")
    tipo_gasto: Mapped[Optional["TipoGasto"]] = relationship("TipoGasto", back_populates="facturas")
    
    lineas: Mapped[List["FacturaLinea"]] = relationship("FacturaLinea", back_populates="factura", cascade="all, delete-orphan")
    etiquetas: Mapped[List["Etiqueta"]] = relationship("Etiqueta", secondary="ftra_factura_etiquetas", back_populates="facturas")
    comentarios: Mapped[List["FacturaComentario"]] = relationship("FacturaComentario", back_populates="factura", cascade="all, delete-orphan")
    adjuntos: Mapped[List["FacturaAdjunto"]] = relationship("FacturaAdjunto", back_populates="factura", cascade="all, delete-orphan")
    historial: Mapped[List["FacturaHistorial"]] = relationship("FacturaHistorial", back_populates="factura", cascade="all, delete-orphan")
    ocr_resultados: Mapped[List["OcrResultado"]] = relationship("OcrResultado", back_populates="factura", cascade="all, delete-orphan")
    ia_resultados: Mapped[List["IaResultado"]] = relationship("IaResultado", back_populates="factura", cascade="all, delete-orphan")
    auditoria: Mapped[List["Auditoria"]] = relationship("Auditoria", back_populates="factura", cascade="all, delete-orphan")
    notificaciones: Mapped[List["Notificacion"]] = relationship("Notificacion", back_populates="factura", cascade="all, delete-orphan")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="factura", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Factura id={self.id} numero={self.numero_factura}>"
