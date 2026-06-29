"""
Servicios de la aplicación FTRA.
Capa de lógica de negocio que orquesta repositories.
"""

# Maestros
from app.services.empresa_service import EmpresaService
from app.services.estado_service import EstadoService
from app.services.tipo_gasto_service import TipoGastoService
from app.services.configuracion_service import ConfiguracionService

# Entidades
from app.services.proveedor_service import ProveedorService
from app.services.cliente_service import ClienteService
from app.services.etiqueta_service import EtiquetaService
from app.services.drive_carpeta_service import DriveCarpetaService

# Facturas
from app.services.factura_service import FacturaService

# Sistema genérico
from app.services.comentarios_service import ComentariosService

__all__ = [
    # Maestros
    "EmpresaService",
    "EstadoService",
    "TipoGastoService",
    "ConfiguracionService",
    
    # Entidades
    "ProveedorService",
    "ClienteService",
    "EtiquetaService",
    "DriveCarpetaService",
    
    # Facturas
    "FacturaService",
    
    # Sistema genérico
    "ComentariosService",
]
