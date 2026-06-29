"""Dependencias de autenticación para la quiniela usando sesión Google existente."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.ftra.database import get_db
from app.ftra.models.participante import Participante


def get_current_participante(
    request: Request,
    db: Session = Depends(get_db),
) -> Participante:
    email = (request.headers.get("x-user-email") or "").strip().lower()
    if not email:
        try:
            email = (request.session.get("user_email") or "").strip().lower()
        except Exception:
            email = ""

    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario Google no identificado")

    participante = db.scalars(
        select(Participante).where(
            func.lower(Participante.email) == email,
            Participante.activo == True,
        )
    ).first()

    if not participante or not participante.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no registrado en la quiniela")

    return participante


def get_admin_participante(
    current: Participante = Depends(get_current_participante),
) -> Participante:
    if not current.es_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol de administrador")
    return current
