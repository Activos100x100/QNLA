from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.ftra.database import Base


class FacturaCorreccion(Base):
    __tablename__ = "ftra_facturas_correcciones"
    __table_args__ = (
        Index("ix_ftra_facturas_correcciones_created_at", "created_at"),
        Index("ix_ftra_facturas_correcciones_archivo", "archivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    archivo: Mapped[str | None] = mapped_column(String(255), nullable=True)

    emisor_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emisor_nif: Mapped[str | None] = mapped_column(String(32), nullable=True)
    emisor_direccion: Mapped[str | None] = mapped_column(Text, nullable=True)

    receptor_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receptor_nif: Mapped[str | None] = mapped_column(String(32), nullable=True)
    receptor_direccion: Mapped[str | None] = mapped_column(Text, nullable=True)

    numero_factura: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fecha: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fecha_vencimiento: Mapped[str | None] = mapped_column(String(32), nullable=True)
    concepto: Mapped[str | None] = mapped_column(Text, nullable=True)

    base_imponible: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tipo_iva: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cuota_iva: Mapped[str | None] = mapped_column(String(64), nullable=True)
    irpf: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total: Mapped[str | None] = mapped_column(String(64), nullable=True)

    texto_crudo: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str | None] = mapped_column(String(16), nullable=True)
    validacion: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
