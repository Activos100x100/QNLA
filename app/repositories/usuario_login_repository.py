"""
Repositorio para `usuarios_login`.
Operaciones de sólo lectura; la tabla es gestionada externamente.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.usuario_login import UsuarioLogin

logger = logging.getLogger(__name__)


class UsuarioLoginRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_dni(self, dni_nie: str) -> Optional[UsuarioLogin]:
        """Devuelve el usuario activo con ese DNI/NIE, o None si no existe."""
        try:
            return (
                self._session.query(UsuarioLogin)
                .filter(
                    UsuarioLogin.dni_nie == dni_nie.upper().strip(),
                    UsuarioLogin.activo.is_(True),
                )
                .first()
            )
        except Exception:
            logger.exception("Error al buscar usuario por DNI: %s", dni_nie)
            return None
