"""
Modelos SQLAlchemy para FTRA (Facturas).
Exporta todos los modelos ORM para la aplicación.
"""

from app.models.empresa import Empresa
from app.models.estado import Estado
from app.models.tipo_gasto import TipoGasto
from app.models.configuracion import Configuracion
from app.models.proveedor import Proveedor
from app.models.cliente import Cliente
from app.models.etiqueta import Etiqueta
from app.models.drive_carpeta import DriveCarpeta
from app.models.factura import Factura
from app.models.factura_linea import FacturaLinea
from app.models.factura_etiqueta import FacturaEtiqueta
from app.models.factura_comentario import FacturaComentario
from app.models.factura_adjunto import FacturaAdjunto
from app.models.factura_historial import FacturaHistorial
from app.models.ocr_resultado import OcrResultado
from app.models.ia_resultado import IaResultado
from app.models.auditoria import Auditoria
from app.models.notificacion import Notificacion
from app.models.log import Log
from app.models.comentario import Comentario, ComentarioAuditoria
from app.models.usuario_login import UsuarioLogin
from app.models.empleado_asignacion import EmpleadoAsignacion
from app.models.rider_operativo import RiderOperativo
from app.models.rtos_mes_operativo import RtosMesOperativo
from app.models.rtos_mes_semana import RtosMesSemana
from app.models.rtos_cash_out_deuda import RtosCashOutDeuda

__all__ = [
    # Maestros
    "Empresa",
    "Estado",
    "TipoGasto",
    "Configuracion",
    
    # Entidades
    "Proveedor",
    "Cliente",
    "Etiqueta",
    "DriveCarpeta",
    
    # Facturas y detalles
    "Factura",
    "FacturaLinea",
    "FacturaEtiqueta",
    "FacturaComentario",
    "FacturaAdjunto",
    "FacturaHistorial",
    
    # Procesamiento
    "OcrResultado",
    "IaResultado",
    
    # Auditoría y Notificaciones
    "Auditoria",
    "Notificacion",
    "Log",
    
    # Sistema genérico de comentarios
    "Comentario",
    "ComentarioAuditoria",
    # Auth
    "UsuarioLogin",
    # Rider
    "EmpleadoAsignacion",
    "RiderOperativo",
    # RTO (Cash Out)
    "RtosMesOperativo",
    "RtosMesSemana",
    "RtosCashOutDeuda",
]
