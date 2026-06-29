"""
Dependencias FastAPI para autenticación.
Uso en routers protegidos: `usuario: dict = Depends(require_auth)`
"""

from typing import Optional
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse

from app.services.auth_service import COOKIE_NAME, verificar_token_sesion


def get_current_user(request: Request) -> Optional[dict]:
    """
    Extrae y valida el token de sesión de la cookie.
    Devuelve el payload del usuario o None si no hay sesión válida.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verificar_token_sesion(token)


def require_auth(usuario: Optional[dict] = Depends(get_current_user)) -> dict:
    """
    Dependencia que exige sesión activa.
    Lanza RedirectResponse a /login si no hay sesión.
    """
    if usuario is None:
        raise _AuthRedirect()
    return usuario


class _AuthRedirect(Exception):
    """Excepción interna que dispara la redirección al login."""
    pass
