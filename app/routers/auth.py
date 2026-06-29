"""
Router de autenticación: login / logout.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.auth_service import (
    COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    autenticar_usuario,
    crear_token_sesion,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Se inyecta desde main.py tras crear el jinja_env
_jinja_env: Environment | None = None


def set_jinja_env(env: Environment) -> None:
    global _jinja_env
    _jinja_env = env


# ---------------------------------------------------------------------------
# Dependencia de sesión de BD
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /login
# ---------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request, error: str = ""):
    """Renderiza el formulario de login."""
    assert _jinja_env is not None, "jinja_env no configurado en auth router"
    return _jinja_env.get_template("login.html").render(
        error=error,
        request=request,
    )


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login", include_in_schema=False)
async def login_submit(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    dni_nie: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    """Procesa credenciales y establece cookie de sesión."""
    usuario = autenticar_usuario(db, dni_nie.strip(), password)

    if usuario is None:
        assert _jinja_env is not None
        return HTMLResponse(
            content=_jinja_env.get_template("login.html").render(
                error="DNI/NIE o contraseña incorrectos.",
                dni_nie=dni_nie,
                request=request,
            ),
            status_code=401,
        )

    token = crear_token_sesion(usuario, db)
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,  # Cambiar a True en producción con HTTPS
    )
    return response


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post("/logout", include_in_schema=False)
async def logout():
    """Borra la cookie de sesión y redirige al login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax")
    return response


@router.get("/logout", include_in_schema=False)
async def logout_get():
    """Soporte GET /logout para enlaces directos."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax")
    return response
