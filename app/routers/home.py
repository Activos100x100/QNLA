"""
Router de la pantalla de inicio (home) post-login.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["home"])

_jinja_env: Environment | None = None


def set_jinja_env(env: Environment) -> None:
    global _jinja_env
    _jinja_env = env


@router.get("/home", response_class=HTMLResponse, include_in_schema=False)
async def home_page(request: Request):
    assert _jinja_env is not None

    usuario = request.state.usuario if hasattr(request.state, "usuario") else {}
    nombre = usuario.get("nombre", "") if usuario else ""
    es_rider = usuario.get("es_rider", False) if usuario else False
    cod_activo = usuario.get("cod_activo", "") if usuario else ""
    rider_id = usuario.get("rider_id", "") if usuario else ""
    deuda_total = usuario.get("deuda_total", 0.0) if usuario else 0.0
    deuda_semanas = usuario.get("deuda_semanas", []) if usuario else []

    hora = datetime.now().hour
    if 6 <= hora < 14:
        saludo = "Buenos días"
    elif 14 <= hora < 21:
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"

    return _jinja_env.get_template("home.html").render(
        saludo=saludo,
        nombre=nombre,
        es_rider=es_rider,
        cod_activo=cod_activo,
        rider_id=rider_id,
        deuda_total=deuda_total,
        deuda_semanas=deuda_semanas,
        request=request,
    )
