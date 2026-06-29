"""
Repositorio para información de riders.
"""

import logging
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.empleado_asignacion import EmpleadoAsignacion
from app.models.rider_operativo import RiderOperativo

logger = logging.getLogger(__name__)

# Constante: departamento_id de riders
RIDER_DEPARTMENT_ID = 7


class RiderRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_asignacion_activa(self, empleado_id: int) -> Optional[EmpleadoAsignacion]:
        """Obtiene la asignación actual del empleado (sin fecha_fin o con fecha_fin futura)."""
        try:
            return (
                self._session.query(EmpleadoAsignacion)
                .filter(
                    EmpleadoAsignacion.empleado_id == empleado_id,
                    (EmpleadoAsignacion.fecha_fin.is_(None)) |
                    (EmpleadoAsignacion.fecha_fin >= date.today()),
                )
                .order_by(EmpleadoAsignacion.fecha_inicio.desc())
                .first()
            )
        except Exception:
            logger.exception("Error al obtener asignación de empleado: %s", empleado_id)
            return None

    def es_rider(self, empleado_id: int) -> bool:
        """Verifica si el empleado es rider (departamento_id = 7)."""
        asignacion = self.obtener_asignacion_activa(empleado_id)
        if asignacion is None:
            return False
        return asignacion.departamento_id == RIDER_DEPARTMENT_ID

    def obtener_rider_operativo(self, empleado_id: int) -> Optional[RiderOperativo]:
        """Obtiene datos del rider operativo activo."""
        try:
            return (
                self._session.query(RiderOperativo)
                .filter(
                    RiderOperativo.empleado_id == empleado_id,
                    RiderOperativo.activo.is_(True),
                )
                .first()
            )
        except Exception:
            logger.exception("Error al obtener rider operativo: %s", empleado_id)
            return None
