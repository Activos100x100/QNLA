"""
Router para gestionar correcciones y retroalimentación del usuario.
NOTA: Este router está actualmente deshabilitado porque depende de modelos 
que pertenecen al proyecto QNLA, no a FTRA.
Si necesitas esta funcionalidad, implementa los modelos correspondientes.
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/correcciones",
    tags=["Correcciones y Aprendizaje (Deshabilitado)"]
)

# TODO: Implementar endpoints cuando los modelos de QNLA estén disponibles
