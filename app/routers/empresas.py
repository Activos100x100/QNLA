"""
Router API para FTRA_EMPRESAS.
Endpoints para gestión de empresas maestras.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.empresa_service import EmpresaService
from app.schemas.factura_schemas import EmpresaCreate, EmpresaUpdate

router = APIRouter(prefix="/api/empresas", tags=["empresas"])


def get_empresa_service(db: Session = Depends(get_db)) -> EmpresaService:
    """Obtiene instancia del servicio de empresas."""
    return EmpresaService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_empresa(datos: EmpresaCreate, service: EmpresaService = Depends(get_empresa_service)):
    """Crea una nueva empresa."""
    try:
        empresa = service.crear_empresa(datos)
        return {"exito": True, "empresa_id": empresa.id, "mensaje": "Empresa creada exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{empresa_id}")
async def obtener_empresa(empresa_id: int, service: EmpresaService = Depends(get_empresa_service)):
    """Obtiene una empresa por ID."""
    try:
        empresa = service.obtener_empresa(empresa_id)
        return {"exito": True, "empresa_id": empresa.id, "nombre": empresa.nombre, "cif": empresa.cif}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/")
async def obtener_todas(activas_solo: bool = False, service: EmpresaService = Depends(get_empresa_service)):
    """Obtiene todas las empresas."""
    try:
        empresas = service.obtener_todas(activas_solo=activas_solo)
        return {"exito": True, "cantidad": len(empresas), "empresas": [{"id": e.id, "nombre": e.nombre} for e in empresas]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{empresa_id}")
async def actualizar_empresa(empresa_id: int, datos: EmpresaUpdate, service: EmpresaService = Depends(get_empresa_service)):
    """Actualiza una empresa."""
    try:
        empresa = service.actualizar_empresa(empresa_id, datos)
        return {"exito": True, "empresa_id": empresa.id, "mensaje": "Empresa actualizada exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{empresa_id}")
async def eliminar_empresa(empresa_id: int, service: EmpresaService = Depends(get_empresa_service)):
    """Elimina una empresa."""
    try:
        if service.eliminar_empresa(empresa_id):
            return {"exito": True, "mensaje": "Empresa eliminada exitosamente"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
