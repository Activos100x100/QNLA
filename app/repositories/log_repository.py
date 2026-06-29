"""
Repository para FTRA_LOGS.
CRUD para logs del sistema.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.log import Log


class LogRepository:
    """Repository para Log."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, log: Log) -> Log:
        """Crea un nuevo registro de log."""
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def obtener_por_id(self, log_id: int) -> Optional[Log]:
        """Obtiene un log por ID."""
        return self.db.get(Log, log_id)
    
    def obtener_por_factura(self, factura_id: int) -> List[Log]:
        """Obtiene logs de una factura."""
        return self.db.scalars(
            select(Log).where(Log.factura_id == factura_id)
            .order_by(Log.created_at.desc())
        ).all()
    
    def obtener_por_nivel(self, nivel: str) -> List[Log]:
        """Obtiene logs de un nivel específico (ERROR, WARNING, INFO, DEBUG)."""
        return self.db.scalars(
            select(Log).where(Log.nivel == nivel)
            .order_by(Log.created_at.desc())
        ).all()
    
    def obtener_por_modulo(self, modulo: str) -> List[Log]:
        """Obtiene logs de un módulo específico."""
        return self.db.scalars(
            select(Log).where(Log.modulo == modulo)
            .order_by(Log.created_at.desc())
        ).all()
    
    def obtener_ultimos(self, limite: int = 100) -> List[Log]:
        """Obtiene últimos logs."""
        return self.db.scalars(
            select(Log).order_by(Log.created_at.desc()).limit(limite)
        ).all()
    
    def obtener_errores(self, limite: int = 50) -> List[Log]:
        """Obtiene últimos errores."""
        return self.db.scalars(
            select(Log).where(Log.nivel == "ERROR")
            .order_by(Log.created_at.desc())
            .limit(limite)
        ).all()
    
    def eliminar(self, log_id: int) -> bool:
        """Elimina un log."""
        log = self.obtener_por_id(log_id)
        if not log:
            return False
        self.db.delete(log)
        self.db.commit()
        return True
    
    def limpiar_antiguos(self, dias: int = 30) -> int:
        """Elimina logs más antiguos que X días (para mantener la BD limpia)."""
        from datetime import datetime, timedelta, timezone
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)
        logs = self.db.scalars(
            select(Log).where(Log.created_at < fecha_limite)
        ).all()
        for log in logs:
            self.db.delete(log)
        self.db.commit()
        return len(logs)
