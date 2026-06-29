"""
Modelos SQLAlchemy para la aplicación de procesamiento de facturas.
Define la estructura de todas las tablas en PostgreSQL con prefijo FTRA_.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

Base = declarative_base()


class Proveedor(Base):
    """
    Modelo para almacenar información de proveedores.
    Contiene datos del vendedor de la factura.
    """
    __tablename__ = "FTRA_proveedores"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    cif = Column(String(20), unique=True, index=True)
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(120))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    facturas = relationship("Factura", back_populates="proveedor")
    
    def __repr__(self) -> str:
        return f"<Proveedor(id={self.id}, nombre='{self.nombre}', cif='{self.cif}')>"


class Cliente(Base):
    """
    Modelo para almacenar información de clientes.
    Contiene datos del comprador de la factura.
    """
    __tablename__ = "FTRA_clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    cif = Column(String(20), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    facturas = relationship("Factura", back_populates="cliente")
    
    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', cif='{self.cif}')>"


class Factura(Base):
    """
    Modelo para almacenar facturas procesadas.
    Contiene toda la información de la factura extraída y validada.
    Incluye niveles de confianza para cada campo.
    """
    __tablename__ = "FTRA_facturas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Datos de la factura
    numero = Column(String(50), nullable=False, index=True)
    serie = Column(String(10))
    fecha = Column(Date, index=True)
    fecha_vencimiento = Column(Date)
    
    # Referencias a proveedor y cliente
    proveedor_id = Column(Integer, ForeignKey("FTRA_proveedores.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("FTRA_clientes.id"), nullable=False)
    
    # Importes (usando Numeric para precisión decimal)
    base_imponible = Column(Numeric(12, 2))
    iva = Column(Numeric(12, 2))
    tipo_iva = Column(String(10))  # Ej: "21%", "10%"
    irpf = Column(Numeric(12, 2))
    total = Column(Numeric(12, 2), index=True)
    
    # Forma de pago e IBAN
    forma_pago = Column(String(50))
    iban = Column(String(50))
    
    # Observaciones
    observaciones = Column(Text)
    
    # Ruta del archivo original
    archivo_original = Column(String(500))
    
    # Estado de procesamiento
    estado = Column(String(50), default="procesada", index=True)  # procesada, editada, validada, error
    texto_ocr = Column(Text)  # Texto completo extraído por OCR
    json_extraido = Column(Text)  # JSON bruto extraído por IA
    json_confianza = Column(Text)  # JSON con niveles de confianza de cada campo
    
    # Bandera de confianza baja
    tiene_campos_bajo_confianza = Column(Boolean, default=False)  # True si hay campos < 85%
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    procesada_en = Column(DateTime)
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="facturas")
    cliente = relationship("Cliente", back_populates="facturas")
    lineas = relationship("LineaFactura", back_populates="factura", cascade="all, delete-orphan")
    historial = relationship("HistorialFactura", back_populates="factura", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Factura(id={self.id}, numero='{self.numero}', fecha={self.fecha}, total={self.total})>"


class LineaFactura(Base):
    """
    Modelo para almacenar líneas individuales de una factura.
    Cada factura puede tener múltiples líneas con conceptos diferentes.
    """
    __tablename__ = "FTRA_lineas_factura"
    
    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("FTRA_facturas.id"), nullable=False)
    
    # Datos de la línea
    descripcion = Column(Text, nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    tipo_iva = Column(String(10))
    total = Column(Numeric(12, 2))
    
    # Orden de la línea
    numero_linea = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    factura = relationship("Factura", back_populates="lineas")
    
    def __repr__(self) -> str:
        return f"<LineaFactura(id={self.id}, factura_id={self.factura_id}, descripcion='{self.descripcion[:50]}...')>"


class HistorialFactura(Base):
    """
    Modelo para mantener un registro de todos los cambios realizados en una factura.
    Permite auditoría y trazabilidad de modificaciones.
    """
    __tablename__ = "FTRA_historial_facturas"
    
    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("FTRA_facturas.id"), nullable=False)
    
    # Información del cambio
    accion = Column(String(50), nullable=False)  # creada, editada, validada, etc.
    campo_modificado = Column(String(100))  # Campo que se cambió (si aplica)
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)
    descripcion = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    factura = relationship("Factura", back_populates="historial")
    
    def __repr__(self) -> str:
        return f"<HistorialFactura(id={self.id}, factura_id={self.factura_id}, accion='{self.accion}')>"


class ErrorProcesamiento(Base):
    """
    Modelo para registrar errores ocurridos durante el procesamiento de facturas.
    Útil para debugging y auditoría de fallos.
    """
    __tablename__ = "FTRA_errores_procesamiento"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información del archivo procesado
    nombre_archivo = Column(String(500), nullable=False)
    ruta_archivo = Column(String(500))
    
    # Información del error
    tipo_error = Column(String(100), nullable=False)  # OCR, AI, Validación, etc.
    mensaje_error = Column(Text, nullable=False)
    stack_trace = Column(Text)
    
    # Estado
    resuelto = Column(Boolean, default=False)
    nota_resolucion = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resuelto_en = Column(DateTime)
    
    def __repr__(self) -> str:
        return f"<ErrorProcesamiento(id={self.id}, tipo='{self.tipo_error}', archivo='{self.nombre_archivo}')>"


class CorreccionAprendizaje(Base):
    """
    Modelo para almacenar correcciones realizadas por usuarios.
    El sistema analiza estos datos para mejorar futuras extracciones
    del mismo proveedor y campo.
    """
    __tablename__ = "FTRA_correcciones_aprendizaje"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Referencias a factura y proveedor
    factura_id = Column(Integer, ForeignKey("FTRA_facturas.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("FTRA_proveedores.id"), nullable=False)
    
    # Información de la corrección
    campo_nombre = Column(String(100), nullable=False, index=True)  # Ej: "cif", "direccion", "total"
    categoria = Column(String(50), nullable=False, index=True)  # Ej: "proveedor", "cliente", "factura"
    
    # Valores
    valor_extraido = Column(Text, nullable=False)  # Valor que la IA extrajo incorrectamente
    valor_correcto = Column(Text, nullable=False)  # Valor correcto según el usuario
    
    # Confianza original
    confianza_original = Column(Integer)  # Confianza que la IA tenía (0-100)
    
    # Información para aprendizaje
    es_patron_frecuente = Column(Boolean, default=False)  # TRUE si este error se repite
    veces_ocurrido = Column(Integer, default=1)  # Cuántas veces se ha visto este error
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    factura = relationship("Factura")
    proveedor = relationship("Proveedor")
    
    def __repr__(self) -> str:
        return f"<CorreccionAprendizaje(id={self.id}, proveedor_id={self.proveedor_id}, campo='{self.campo_nombre}', confianza_original={self.confianza_original})>"
