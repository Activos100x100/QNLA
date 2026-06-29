"""
Repositorio para obtener deuda de riders en Cash Out.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.rtos_mes_operativo import RtosMesOperativo
from app.models.rtos_mes_semana import RtosMesSemana
from app.models.rtos_cash_out_deuda import RtosCashOutDeuda

logger = logging.getLogger(__name__)


class CashOutRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_mes_operativo_vigente(self) -> Optional[RtosMesOperativo]:
        """Obtiene el mes operativo actual (no cerrado)."""
        try:
            return (
                self._session.query(RtosMesOperativo)
                .filter(RtosMesOperativo.cerrado.is_(False))
                .order_by(RtosMesOperativo.anio.desc(), RtosMesOperativo.mes.desc())
                .first()
            )
        except Exception:
            logger.exception("Error al obtener mes operativo vigente")
            return None

    def obtener_semanas_mes(self, mes_operativo_id: int) -> List[RtosMesSemana]:
        """Obtiene todas las semanas de un mes operativo."""
        try:
            return (
                self._session.query(RtosMesSemana)
                .filter(RtosMesSemana.mes_operativo_id == mes_operativo_id)
                .order_by(RtosMesSemana.numero_semana_mes)
                .all()
            )
        except Exception:
            logger.exception("Error al obtener semanas del mes: %s", mes_operativo_id)
            return []

    def obtener_deuda_rider_por_semana(self, empleado_id: int) -> Dict[str, Any]:
        """
        Obtiene la deuda de un rider desglosada por semana en el mes operativo vigente.
        
        Retorna:
        {
            "mes_operativo": {"id": 1, "nombre": "Enero 2026"},
            "total": 1500.00,
            "semanas": [
                {"numero": 1, "iso_year": 2026, "iso_week": 1, "importe": 375.00},
                {"numero": 2, "iso_year": 2026, "iso_week": 2, "importe": 375.00},
                ...
            ]
        }
        """
        try:
            # Obtener mes operativo vigente
            mes = self.obtener_mes_operativo_vigente()
            if not mes:
                return {
                    "mes_operativo": None,
                    "total": 0.0,
                    "semanas": [],
                    "error": "No hay mes operativo vigente"
                }

            # Obtener semanas del mes
            semanas = self.obtener_semanas_mes(mes.id)
            if not semanas:
                return {
                    "mes_operativo": {
                        "id": mes.id,
                        "nombre": mes.nombre,
                        "mes": mes.mes,
                        "anio": mes.anio,
                    },
                    "total": 0.0,
                    "semanas": [],
                    "error": "El mes no tiene semanas"
                }

            # Para cada semana, obtener la deuda
            deudas_por_semana = []
            total_deuda = 0.0

            for semana in semanas:
                deuda = (
                    self._session.query(RtosCashOutDeuda)
                    .filter(
                        and_(
                            RtosCashOutDeuda.empleado_id == empleado_id,
                            RtosCashOutDeuda.iso_year == semana.iso_year,
                            RtosCashOutDeuda.iso_week == semana.iso_week,
                        )
                    )
                    .first()
                )

                importe = 0.0
                if deuda:
                    importe = deuda.importe_deuda or 0.0

                deudas_por_semana.append({
                    "numero": semana.numero_semana_mes,
                    "iso_year": semana.iso_year,
                    "iso_week": semana.iso_week,
                    "importe": importe,
                })
                total_deuda += importe

            return {
                "mes_operativo": {
                    "id": mes.id,
                    "nombre": mes.nombre,
                    "mes": mes.mes,
                    "anio": mes.anio,
                },
                "total": total_deuda,
                "semanas": deudas_por_semana,
            }

        except Exception:
            logger.exception("Error al obtener deuda del rider: %s", empleado_id)
            return {
                "mes_operativo": None,
                "total": 0.0,
                "semanas": [],
                "error": "Error al consultar deuda"
            }
