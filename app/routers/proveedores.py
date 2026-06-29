"""
Router API para FTRA_PROVEEDORES.
Endpoints para gestión de proveedores.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.proveedor_service import ProveedorService
from app.schemas.factura_schemas import ProveedorCreate, ProveedorUpdate

router = APIRouter(prefix="/api/proveedores", tags=["proveedores"])


def get_proveedor_service(db: Session = Depends(get_db)) -> ProveedorService:
    return ProveedorService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_proveedor(empresa_id: int, datos: ProveedorCreate, service: ProveedorService = Depends(get_proveedor_service)):
    """Crea un nuevo proveedor."""
    try:
        proveedor = service.crear_proveedor(empresa_id, datos)
        return {"exito": True, "proveedor_id": proveedor.id, "mensaje": "Proveedor creado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{proveedor_id}")
async def obtener_proveedor(proveedor_id: int, service: ProveedorService = Depends(get_proveedor_service)):
    """Obtiene un proveedor."""
    try:
        proveedor = service.obtener_proveedor(proveedor_id)
        if not proveedor:
            raise ValueError("Proveedor no encontrado")
        return {"exito": True, "proveedor_id": proveedor.id, "nombre": proveedor.nombre}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/empresa/{empresa_id}")
async def obtener_proveedores(empresa_id: int, activos_solo: bool = True, service: ProveedorService = Depends(get_proveedor_service)):
    """Obtiene proveedores de una empresa."""
    try:
        proveedores = service.obtener_proveedores_empresa(empresa_id, activos_solo=activos_solo)
        return {"exito": True, "cantidad": len(proveedores), "proveedores": [{"id": p.id, "nombre": p.nombre} for p in proveedores]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{proveedor_id}")
async def actualizar_proveedor(proveedor_id: int, datos: ProveedorUpdate, service: ProveedorService = Depends(get_proveedor_service)):
    """Actualiza un proveedor."""
    try:
        proveedor = service.actualizar_proveedor(proveedor_id, datos)
        return {"exito": True, "proveedor_id": proveedor.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{proveedor_id}")
async def eliminar_proveedor(proveedor_id: int, service: ProveedorService = Depends(get_proveedor_service)):
    """Elimina un proveedor."""
    try:
        if service.eliminar_proveedor(proveedor_id):
            return {"exito": True, "mensaje": "Proveedor eliminado exitosamente"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
