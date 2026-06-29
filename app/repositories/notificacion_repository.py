"""
Repository para FTRA_NOTIFICACIONES.
CRUD para notificaciones del sistema.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion


class NotificacionRepository:
    """Repository para Notificacion."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, notificacion: Notificacion) -> Notificacion:
        """Crea una nueva notificación."""
        self.db.add(notificacion)
        self.db.commit()
        self.db.refresh(notificacion)
        return notificacion
    
    def obtener_por_id(self, notificacion_id: int) -> Optional[Notificacion]:
        """Obtiene una notificación por ID."""
        return self.db.get(Notificacion, notificacion_id)
    
    def obtener_por_usuario(self, usuario_id: int) -> List[Notificacion]:
        """Obtiene notificaciones de un usuario."""
        return self.db.scalars(
            select(Notificacion).where(Notificacion.usuario_id == usuario_id)
            .order_by(Notificacion.created_at.desc())
        ).all()
    
    def obtener_no_leidas(self, usuario_id: int) -> List[Notificacion]:
        """Obtiene notificaciones no leídas de un usuario."""
        return self.db.scalars(
            select(Notificacion).where(
                and_(
                    Notificacion.usuario_id == usuario_id,
                    Notificacion.leida == False
                )
            ).order_by(Notificacion.created_at.desc())
        ).all()
    
    def obtener_por_factura(self, factura_id: int) -> List[Notificacion]:
        """Obtiene notificaciones relacionadas a una factura."""
        return self.db.scalars(
            select(Notificacion).where(Notificacion.factura_id == factura_id)
            .order_by(Notificacion.created_at.desc())
        ).all()
    
    def marcar_como_leida(self, notificacion_id: int) -> Optional[Notificacion]:
        """Marca una notificación como leída."""
        notificacion = self.obtener_por_id(notificacion_id)
        if notificacion:
            notificacion.leida = True
            self.db.commit()
            self.db.refresh(notificacion)
        return notificacion
    
    def marcar_todas_leidas(self, usuario_id: int) -> int:
        """Marca todas las notificaciones de un usuario como leídas."""
        notificaciones = self.obtener_no_leidas(usuario_id)
        for notif in notificaciones:
            notif.leida = True
        self.db.commit()
        return len(notificaciones)
    
    def actualizar(self, notificacion_id: int, **kwargs) -> Optional[Notificacion]:
        """Actualiza una notificación."""
        notificacion = self.obtener_por_id(notificacion_id)
        if not notificacion:
            return None
        for key, value in kwargs.items():
            if hasattr(notificacion, key):
                setattr(notificacion, key, value)
        self.db.commit()
        self.db.refresh(notificacion)
        return notificacion
    
    def eliminar(self, notificacion_id: int) -> bool:
        """Elimina una notificación."""
        notificacion = self.obtener_por_id(notificacion_id)
        if not notificacion:
            return False
        self.db.delete(notificacion)
        self.db.commit()
        return True
    
    def contar_no_leidas(self, usuario_id: int) -> int:
        """Cuenta notificaciones no leídas de un usuario."""
        return len(self.obtener_no_leidas(usuario_id))
