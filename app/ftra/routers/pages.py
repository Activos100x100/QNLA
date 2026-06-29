"""Vistas HTML del panel de quiniela."""
from __future__ import annotations

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.ftra.database import get_db
from app.models.torneo import Torneo
from app.ftra.schemas.torneo import TorneoOut

router = APIRouter(prefix="/ftra", tags=["ftra-pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def ftra_home():
    return RedirectResponse("/ftra/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("ftra/dashboard.html", {"request": request, "is_admin": admin})


@router.get("/partidos", response_class=HTMLResponse)
def partidos_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("ftra/partidos.html", {"request": request, "is_admin": admin})


@router.get("/admin/resultados", response_class=HTMLResponse)
def resultados_page(request: Request):
    return templates.TemplateResponse("ftra/resultado_form.html", {"request": request, "is_admin": True})


@router.get("/ranking", response_class=HTMLResponse)
def ranking_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("ftra/ranking.html", {"request": request, "is_admin": admin})


@router.get("/admin/participantes", response_class=HTMLResponse)
def participantes_page(request: Request):
    return templates.TemplateResponse("ftra/participantes.html", {"request": request, "is_admin": True})


@router.get("/admin/torneos", response_class=HTMLResponse)
def torneos_page(request: Request):
    return templates.TemplateResponse("ftra/admin_torneos.html", {"request": request, "is_admin": True})


@router.get("/estadisticas", response_class=HTMLResponse)
def estadisticas_page(request: Request, admin: bool = Query(default=False)):
    return templates.TemplateResponse("ftra/estadisticas.html", {"request": request, "is_admin": admin})


@router.get("/facturas", response_class=HTMLResponse)
def facturas_page(request: Request):
    return templates.TemplateResponse("cargar.html", {"request": request})


@router.get("/diagnostico-ocr-ia", response_class=HTMLResponse)
def diagnostico_ocr_ia_page(request: Request):
    """Página de diagnóstico transparente OCR/IA con 3 columnas."""
    return templates.TemplateResponse("diagnostico_ocr_ia.html", {"request": request})


@router.get("/torneos/activos", response_model=list[TorneoOut])
def torneos_activos(db: Session = Depends(get_db)):
    """Retorna lista de torneos activos en JSON para el dashboard."""
    stmt = select(Torneo).where(Torneo.activo == True).order_by(Torneo.anio.desc())
    torneos = db.scalars(stmt).all()
    return [TorneoOut.model_validate(t) for t in torneos]
