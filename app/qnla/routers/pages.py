"""Vistas HTML del panel de quiniela."""
from __future__ import annotations

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.qnla.database import get_db
from app.qnla.models.torneo import Torneo
from app.qnla.schemas.torneo import TorneoOut

router = APIRouter(prefix="/qnla", tags=["qnla-pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def qnla_home():
    return RedirectResponse("/qnla/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("qnla/dashboard.html", {"request": request, "is_admin": admin})


@router.get("/partidos", response_class=HTMLResponse)
def partidos_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("qnla/partidos.html", {"request": request, "is_admin": admin})


@router.get("/admin/resultados", response_class=HTMLResponse)
def resultados_page(request: Request):
    return templates.TemplateResponse("qnla/resultado_form.html", {"request": request, "is_admin": True})


@router.get("/ranking", response_class=HTMLResponse)
def ranking_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("qnla/ranking.html", {"request": request, "is_admin": admin})


@router.get("/admin/participantes", response_class=HTMLResponse)
def participantes_page(request: Request):
    return templates.TemplateResponse("qnla/participantes.html", {"request": request, "is_admin": True})


@router.get("/admin/torneos", response_class=HTMLResponse)
def torneos_page(request: Request):
    return templates.TemplateResponse("qnla/admin_torneos.html", {"request": request, "is_admin": True})


@router.get("/estadisticas", response_class=HTMLResponse)
def estadisticas_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("qnla/estadisticas.html", {"request": request, "is_admin": admin})


@router.get("/torneos/activos", response_model=list[TorneoOut])
def torneos_activos(db: Session = Depends(get_db)):
    """Retorna lista de torneos activos en JSON para el dashboard."""
    stmt = select(Torneo).where(Torneo.activo == True).order_by(Torneo.anio.desc())
    torneos = db.scalars(stmt).all()
    return [TorneoOut.model_validate(t) for t in torneos]
