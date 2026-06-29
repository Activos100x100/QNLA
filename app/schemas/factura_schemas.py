"""
Esquemas Pydantic para validación de datos.
Define las estructuras de solicitud y respuesta de la API.
Incluye soporte para niveles de confianza en campos.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============= CAMPO CON CONFIANZA =============

class CampoConConfianza(BaseModel):
    """Base para campos que incluyen confianza."""
    valor: Optional[str] = None
    confianza: int = Field(100, ge=0, le=100)  # Porcentaje 0-100
    
    def es_confiable(self, umbral: int = 85) -> bool:
        """Verifica si el nivel de confianza es aceptable."""
        return self.confianza >= umbral


class CampoNumericoConConfianza(BaseModel):
    """Campo numérico con confianza."""
    valor: Optional[Decimal] = None
    confianza: int = Field(100, ge=0, le=100)
    
    def es_confiable(self, umbral: int = 85) -> bool:
        """Verifica si el nivel de confianza es aceptable."""
        return self.confianza >= umbral


class CampoFechaConConfianza(BaseModel):
    """Campo de fecha con confianza."""
    valor: Optional[date] = None
    confianza: int = Field(100, ge=0, le=100)
    
    def es_confiable(self, umbral: int = 85) -> bool:
        """Verifica si el nivel de confianza es aceptable."""
        return self.confianza >= umbral


# ============= PROVEEDOR =============

class ProveedorBase(BaseModel):
    """Datos base del proveedor."""
    nombre: str = Field(..., min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class ProveedorCreate(ProveedorBase):
    """Esquema para crear un proveedor."""
    pass


class ProveedorUpdate(BaseModel):
    """Esquema para actualizar un proveedor."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class ProveedorResponse(ProveedorBase):
    """Esquema de respuesta del proveedor."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= CLIENTE =============

class ClienteBase(BaseModel):
    """Datos base del cliente."""
    nombre: str = Field(..., min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)


class ClienteCreate(ClienteBase):
    """Esquema para crear un cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Esquema para actualizar un cliente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)


class ClienteResponse(ClienteBase):
    """Esquema de respuesta del cliente."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= LÍNEA DE FACTURA =============

class LineaFacturaBase(BaseModel):
    """Datos base de una línea de factura."""
    descripcion: str = Field(..., min_length=1)
    cantidad: Decimal = Field(..., decimal_places=2, gt=0)
    precio_unitario: Decimal = Field(..., decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    numero_linea: Optional[int] = None


class LineaFacturaCreate(LineaFacturaBase):
    """Esquema para crear una línea de factura."""
    pass


class LineaFacturaUpdate(BaseModel):
    """Esquema para actualizar una línea de factura."""
    descripcion: Optional[str] = Field(None, min_length=1)
    cantidad: Optional[Decimal] = Field(None, decimal_places=2, gt=0)
    precio_unitario: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    numero_linea: Optional[int] = None


class LineaFacturaResponse(LineaFacturaBase):
    """Esquema de respuesta de línea de factura."""
    id: int
    factura_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LineaFacturaConConfianza(BaseModel):
    """Línea de factura con niveles de confianza."""
    descripcion: CampoConConfianza
    cantidad: CampoNumericoConConfianza
    precio_unitario: CampoNumericoConConfianza
    tipo_iva: CampoConConfianza
    total: CampoNumericoConConfianza
    numero_linea: Optional[int] = None


# ============= FACTURA =============

class FacturaBase(BaseModel):
    """Datos base de una factura."""
    numero: str = Field(..., min_length=1, max_length=50)
    serie: Optional[str] = Field(None, max_length=10)
    fecha: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: int
    cliente_id: int
    base_imponible: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    iva: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    irpf: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    forma_pago: Optional[str] = Field(None, max_length=50)
    iban: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None
    archivo_original: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field("procesada", max_length=50)


class FacturaCreate(FacturaBase):
    """Esquema para crear una factura."""
    pass


class FacturaUpdate(BaseModel):
    """Esquema para actualizar una factura."""
    numero: Optional[str] = Field(None, min_length=1, max_length=50)
    serie: Optional[str] = Field(None, max_length=10)
    fecha: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    base_imponible: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    iva: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    irpf: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    forma_pago: Optional[str] = Field(None, max_length=50)
    iban: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=50)


class FacturaResponse(FacturaBase):
    """Esquema de respuesta completa de una factura."""
    id: int
    texto_ocr: Optional[str] = None
    json_extraido: Optional[str] = None
    lineas: List[LineaFacturaResponse] = []
    proveedor: Optional[ProveedorResponse] = None
    cliente: Optional[ClienteResponse] = None
    created_at: datetime
    updated_at: datetime
    procesada_en: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FacturaResponseSimple(BaseModel):
    """Esquema simplificado de respuesta de factura."""
    id: int
    numero: str
    fecha: Optional[date] = None
    total: Optional[Decimal] = None
    estado: str
    proveedor_id: int
    cliente_id: int
    tiene_campos_bajo_confianza: bool = False
    
    class Config:
        from_attributes = True


# ============= FACTURA CON CONFIANZA =============

class FacturaConConfianza(BaseModel):
    """Factura con niveles de confianza para cada campo."""
    
    # Proveedor con confianza
    proveedor: dict  # {nombre: {valor, confianza}, cif: {valor, confianza}, ...}
    
    # Cliente con confianza
    cliente: dict  # {nombre: {valor, confianza}, cif: {valor, confianza}, ...}
    
    # Datos de factura con confianza
    factura: dict  # {numero: {valor, confianza}, fecha: {valor, confianza}, ...}
    
    # Líneas con confianza
    lineas: List[LineaFacturaConConfianza]


# ============= HISTORIAL =============

class HistorialFacturaCreate(BaseModel):
    """Esquema para crear un registro de historial."""
    factura_id: int
    accion: str = Field(..., min_length=1, max_length=50)
    campo_modificado: Optional[str] = Field(None, max_length=100)
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    descripcion: Optional[str] = None


class HistorialFacturaResponse(BaseModel):
    """Esquema de respuesta del historial."""
    id: int
    factura_id: int
    accion: str
    campo_modificado: Optional[str]
    valor_anterior: Optional[str]
    valor_nuevo: Optional[str]
    descripcion: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= ERRORES =============

class ErrorProcesamiento(BaseModel):
    """Esquema para registrar errores de procesamiento."""
    nombre_archivo: str = Field(..., min_length=1, max_length=500)
    ruta_archivo: Optional[str] = Field(None, max_length=500)
    tipo_error: str = Field(..., min_length=1, max_length=100)
    mensaje_error: str = Field(..., min_length=1)
    stack_trace: Optional[str] = None


class ErrorProcesimientoResponse(ErrorProcesamiento):
    """Esquema de respuesta de error."""
    id: int
    resuelto: bool
    nota_resolucion: Optional[str]
    created_at: datetime
    resuelto_en: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= RESPUESTAS GENERALES =============

class MensajeRespuesta(BaseModel):
    """Esquema genérico de respuesta con mensaje."""
    exito: bool
    mensaje: str
    datos: Optional[dict] = None


class ErrorRespuesta(BaseModel):
    """Esquema de respuesta de error."""
    exito: bool = False
    mensaje: str
    detalles: Optional[str] = None


# ============= DATOS DE PROCESAMIENTO =============

class DatosExtraidos(BaseModel):
    """
    Esquema que representa los datos extraídos de una factura por el OCR y la IA.
    Este es el formato que debe retornar OpenAI.
    """
    proveedor: ProveedorBase
    cliente: ClienteBase
    factura: FacturaBase
    lineas: List[LineaFacturaCreate]


class ReporteConfianza(BaseModel):
    """Reporte de confianza de una factura."""
    factura_id: int
    promedio_confianza: float
    campos_bajo_confianza: List[dict]  # {campo: nombre, confianza: valor, tipo: tipo_campo}
    confiable: bool



# ============= PROVEEDOR =============

class ProveedorBase(BaseModel):
    """Datos base del proveedor."""
    nombre: str = Field(..., min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class ProveedorCreate(ProveedorBase):
    """Esquema para crear un proveedor."""
    pass


class ProveedorUpdate(BaseModel):
    """Esquema para actualizar un proveedor."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class ProveedorResponse(ProveedorBase):
    """Esquema de respuesta del proveedor."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= CLIENTE =============

class ClienteBase(BaseModel):
    """Datos base del cliente."""
    nombre: str = Field(..., min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)


class ClienteCreate(ClienteBase):
    """Esquema para crear un cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Esquema para actualizar un cliente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)


class ClienteResponse(ClienteBase):
    """Esquema de respuesta del cliente."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= LÍNEA DE FACTURA =============

class LineaFacturaBase(BaseModel):
    """Datos base de una línea de factura."""
    descripcion: str = Field(..., min_length=1)
    cantidad: Decimal = Field(..., decimal_places=2, gt=0)
    precio_unitario: Decimal = Field(..., decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    numero_linea: Optional[int] = None


class LineaFacturaCreate(LineaFacturaBase):
    """Esquema para crear una línea de factura."""
    pass


class LineaFacturaUpdate(BaseModel):
    """Esquema para actualizar una línea de factura."""
    descripcion: Optional[str] = Field(None, min_length=1)
    cantidad: Optional[Decimal] = Field(None, decimal_places=2, gt=0)
    precio_unitario: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    numero_linea: Optional[int] = None


class LineaFacturaResponse(LineaFacturaBase):
    """Esquema de respuesta de línea de factura."""
    id: int
    factura_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= FACTURA =============

class FacturaBase(BaseModel):
    """Datos base de una factura."""
    numero: str = Field(..., min_length=1, max_length=50)
    serie: Optional[str] = Field(None, max_length=10)
    fecha: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: int
    cliente_id: int
    base_imponible: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    iva: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    irpf: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    forma_pago: Optional[str] = Field(None, max_length=50)
    iban: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None
    archivo_original: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field("procesada", max_length=50)


class FacturaCreate(FacturaBase):
    """Esquema para crear una factura."""
    pass


class FacturaUpdate(BaseModel):
    """Esquema para actualizar una factura."""
    numero: Optional[str] = Field(None, min_length=1, max_length=50)
    serie: Optional[str] = Field(None, max_length=10)
    fecha: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    base_imponible: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    iva: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    tipo_iva: Optional[str] = Field(None, max_length=10)
    irpf: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    total: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    forma_pago: Optional[str] = Field(None, max_length=50)
    iban: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=50)


class FacturaResponse(FacturaBase):
    """Esquema de respuesta completa de una factura."""
    id: int
    texto_ocr: Optional[str] = None
    json_extraido: Optional[str] = None
    lineas: List[LineaFacturaResponse] = []
    proveedor: Optional[ProveedorResponse] = None
    cliente: Optional[ClienteResponse] = None
    created_at: datetime
    updated_at: datetime
    procesada_en: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FacturaResponseSimple(BaseModel):
    """Esquema simplificado de respuesta de factura."""
    id: int
    numero: str
    fecha: Optional[date] = None
    total: Optional[Decimal] = None
    estado: str
    proveedor_id: int
    cliente_id: int
    
    class Config:
        from_attributes = True


# ============= HISTORIAL =============

class HistorialFacturaCreate(BaseModel):
    """Esquema para crear un registro de historial."""
    factura_id: int
    accion: str = Field(..., min_length=1, max_length=50)
    campo_modificado: Optional[str] = Field(None, max_length=100)
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    descripcion: Optional[str] = None


class HistorialFacturaResponse(BaseModel):
    """Esquema de respuesta del historial."""
    id: int
    factura_id: int
    accion: str
    campo_modificado: Optional[str]
    valor_anterior: Optional[str]
    valor_nuevo: Optional[str]
    descripcion: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= ERRORES =============

class ErrorProcesamiento(BaseModel):
    """Esquema para registrar errores de procesamiento."""
    nombre_archivo: str = Field(..., min_length=1, max_length=500)
    ruta_archivo: Optional[str] = Field(None, max_length=500)
    tipo_error: str = Field(..., min_length=1, max_length=100)
    mensaje_error: str = Field(..., min_length=1)
    stack_trace: Optional[str] = None


class ErrorProcesimientoResponse(ErrorProcesamiento):
    """Esquema de respuesta de error."""
    id: int
    resuelto: bool
    nota_resolucion: Optional[str]
    created_at: datetime
    resuelto_en: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= RESPUESTAS GENERALES =============

class MensajeRespuesta(BaseModel):
    """Esquema genérico de respuesta con mensaje."""
    exito: bool
    mensaje: str
    datos: Optional[dict] = None


class ErrorRespuesta(BaseModel):
    """Esquema de respuesta de error."""
    exito: bool = False
    mensaje: str
    detalles: Optional[str] = None


# ============= DATOS DE PROCESAMIENTO =============

class DatosExtraidos(BaseModel):
    """
    Esquema que representa los datos extraídos de una factura por el OCR y la IA.
    Este es el formato que debe retornar OpenAI.
    """
    proveedor: ProveedorBase
    cliente: ClienteBase
    factura: FacturaBase
    lineas: List[LineaFacturaCreate]


# ============= COMENTARIOS =============

class ComentarioCreate(BaseModel):
    """Esquema para crear un comentario."""
    entity_type: str = Field("factura", min_length=1, max_length=50)  # "factura", "pedido", "incidencia", etc.
    entity_id: int  # ID de la entidad
    texto: str = Field(..., min_length=1, max_length=5000)
    tipo: str = Field("informacion", pattern="^(informacion|revision|incidencia|aprobacion|rechazo)$")
    parent_id: Optional[int] = None  # Para respuestas


class ComentarioUpdate(BaseModel):
    """Esquema para actualizar un comentario."""
    texto: Optional[str] = Field(None, min_length=1, max_length=5000)
    tipo: Optional[str] = Field(None, pattern="^(informacion|revision|incidencia|aprobacion|rechazo)$")


class ComentarioResponse(BaseModel):
    """Esquema de respuesta de un comentario."""
    id: int
    entity_type: str
    entity_id: int
    usuario_id: str
    usuario_nombre: str
    texto: str
    tipo: str
    estado: str
    parent_id: Optional[int] = None
    respuestas: List["ComentarioResponse"] = []
    created_at: datetime
    updated_at: datetime
    resuelto_por: Optional[str] = None
    resuelto_en: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Forward ref para respuestas anidadas
ComentarioResponse.model_rebuild()


class ComentarioEstadisticas(BaseModel):
    """Estadísticas de comentarios de una entidad."""
    entity_type: str
    entity_id: int
    total_comentarios: int
    comentarios_pendientes: int
    comentarios_resueltos: int
    tipos_distribucion: dict  # {tipo: count}
    ultimos_comentarios: List[ComentarioResponse]


class ComentarioAuditoriaResponse(BaseModel):
    """Esquema de respuesta de auditoría de comentarios."""
    id: int
    comentario_id: int
    entity_type: str
    entity_id: int
    usuario_id: str
    usuario_nombre: str
    accion: str
    cambios_anteriores: Optional[str] = None
    cambios_nuevos: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= EMPRESA =============

class EmpresaBase(BaseModel):
    """Datos base de empresa."""
    nombre: str = Field(..., min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    activo: bool = True


class EmpresaCreate(EmpresaBase):
    """Esquema para crear empresa."""
    pass


class EmpresaUpdate(BaseModel):
    """Esquema para actualizar empresa."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    cif: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    activo: Optional[bool] = None


class EmpresaResponse(EmpresaBase):
    """Esquema de respuesta de empresa."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= ESTADO =============

class EstadoBase(BaseModel):
    """Datos base de estado."""
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    color: Optional[str] = Field(None, max_length=10)
    orden: int = 0
    es_final: bool = False


class EstadoCreate(EstadoBase):
    """Esquema para crear estado."""
    pass


class EstadoUpdate(BaseModel):
    """Esquema para actualizar estado."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    color: Optional[str] = None
    orden: Optional[int] = None
    es_final: Optional[bool] = None


class EstadoResponse(EstadoBase):
    """Esquema de respuesta de estado."""
    id: int
    
    class Config:
        from_attributes = True


# ============= TIPO_GASTO =============

class TipoGastoBase(BaseModel):
    """Datos base de tipo de gasto."""
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None


class TipoGastoCreate(TipoGastoBase):
    """Esquema para crear tipo de gasto."""
    pass


class TipoGastoUpdate(BaseModel):
    """Esquema para actualizar tipo de gasto."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None


class TipoGastoResponse(TipoGastoBase):
    """Esquema de respuesta de tipo de gasto."""
    id: int
    
    class Config:
        from_attributes = True


# ============= CONFIGURACION =============

class ConfiguracionBase(BaseModel):
    """Datos base de configuración."""
    clave: str = Field(..., min_length=1, max_length=100)
    valor: str
    descripcion: Optional[str] = None


class ConfiguracionCreate(ConfiguracionBase):
    """Esquema para crear configuración."""
    pass


class ConfiguracionUpdate(BaseModel):
    """Esquema para actualizar configuración."""
    valor: Optional[str] = None
    descripcion: Optional[str] = None


class ConfiguracionResponse(ConfiguracionBase):
    """Esquema de respuesta de configuración."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= ETIQUETA =============

class EtiquetaBase(BaseModel):
    """Datos base de etiqueta."""
    nombre: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, max_length=10)
    icono: Optional[str] = None
    activa: bool = True


class EtiquetaCreate(EtiquetaBase):
    """Esquema para crear etiqueta."""
    pass


class EtiquetaUpdate(BaseModel):
    """Esquema para actualizar etiqueta."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    icono: Optional[str] = None
    activa: Optional[bool] = None


class EtiquetaResponse(EtiquetaBase):
    """Esquema de respuesta de etiqueta."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= DRIVE_CARPETA =============

class DriveCarpetaBase(BaseModel):
    """Datos base de carpeta Google Drive."""
    nombre: str = Field(..., min_length=1, max_length=255)
    anio: Optional[int] = None
    mes: Optional[int] = Field(None, ge=1, le=12)
    google_drive_folder_id: str
    google_drive_url: Optional[str] = None


class DriveCarpetaCreate(DriveCarpetaBase):
    """Esquema para crear carpeta Google Drive."""
    pass


class DriveCarpetaUpdate(BaseModel):
    """Esquema para actualizar carpeta Google Drive."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    anio: Optional[int] = None
    mes: Optional[int] = Field(None, ge=1, le=12)
    google_drive_url: Optional[str] = None


class DriveCarpetaResponse(DriveCarpetaBase):
    """Esquema de respuesta de carpeta Google Drive."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
