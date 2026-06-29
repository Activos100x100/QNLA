"""
Inicialización del módulo de routers.
Expone los routers de la aplicación.
"""

from app.routers.comentarios import router as comentarios_router
from app.routers.facturas import router as facturas_router

__all__ = [
    "comentarios_router",
    "facturas_router",
]
