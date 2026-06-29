"""
Repositorio de acceso a datos para FTRA.
Exporta todos los repositories de la aplicación.
"""

from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.estado_repository import EstadoRepository
from app.repositories.tipo_gasto_repository import TipoGastoRepository
from app.repositories.configuracion_repository import ConfiguracionRepository
from app.repositories.proveedor_repository import ProveedorRepository
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.etiqueta_repository import EtiquetaRepository
from app.repositories.drive_carpeta_repository import DriveCarpetaRepository
from app.repositories.factura_repository import FacturaRepository
from app.repositories.factura_linea_repository import FacturaLineaRepository
from app.repositories.factura_comentario_repository import FacturaComentarioRepository
from app.repositories.factura_adjunto_repository import FacturaAdjuntoRepository
from app.repositories.factura_historial_repository import FacturaHistorialRepository
from app.repositories.ocr_resultado_repository import OcrResultadoRepository
from app.repositories.ia_resultado_repository import IaResultadoRepository
from app.repositories.auditoria_repository import AuditoriaRepository
from app.repositories.notificacion_repository import NotificacionRepository
from app.repositories.log_repository import LogRepository
from app.repositories.comentarios_repository import ComentariosRepository, ComentariosAuditoriaRepository

__all__ = [
    # Maestros
    "EmpresaRepository",
    "EstadoRepository",
    "TipoGastoRepository",
    "ConfiguracionRepository",
    
    # Entidades
    "ProveedorRepository",
    "ClienteRepository",
    "EtiquetaRepository",
    "DriveCarpetaRepository",
    
    # Facturas y detalles
    "FacturaRepository",
    "FacturaLineaRepository",
    "FacturaComentarioRepository",
    "FacturaAdjuntoRepository",
    "FacturaHistorialRepository",
    
    # Procesamiento
    "OcrResultadoRepository",
    "IaResultadoRepository",
    
    # Auditoría y Notificaciones
    "AuditoriaRepository",
    "NotificacionRepository",
    "LogRepository",
    
    # Sistema genérico de comentarios
    "ComentariosRepository",
    "ComentariosAuditoriaRepository",
]
