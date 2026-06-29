"""
Router API para FTRA_CLIENTES.
Endpoints para gestión de clientes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cliente_service import ClienteService
from app.schemas.factura_schemas import ClienteCreate, ClienteUpdate

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


def get_cliente_service(db: Session = Depends(get_db)) -> ClienteService:
    return ClienteService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_cliente(empresa_id: int, datos: ClienteCreate, service: ClienteService = Depends(get_cliente_service)):
    """Crea un nuevo cliente."""
    try:
        cliente = service.crear_cliente(empresa_id, datos)
        return {"exito": True, "cliente_id": cliente.id, "mensaje": "Cliente creado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{cliente_id}")
async def obtener_cliente(cliente_id: int, service: ClienteService = Depends(get_cliente_service)):
    """Obtiene un cliente."""
    try:
        cliente = service.obtener_cliente(cliente_id)
        if not cliente:
            raise ValueError("Cliente no encontrado")
        return {"exito": True, "cliente_id": cliente.id, "nombre": cliente.nombre}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/empresa/{empresa_id}")
async def obtener_clientes(empresa_id: int, activos_solo: bool = True, service: ClienteService = Depends(get_cliente_service)):
    """Obtiene clientes de una empresa."""
    try:
        clientes = service.obtener_clientes_empresa(empresa_id, activos_solo=activos_solo)
        return {"exito": True, "cantidad": len(clientes), "clientes": [{"id": c.id, "nombre": c.nombre} for c in clientes]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{cliente_id}")
async def actualizar_cliente(cliente_id: int, datos: ClienteUpdate, service: ClienteService = Depends(get_cliente_service)):
    """Actualiza un cliente."""
    try:
        cliente = service.actualizar_cliente(cliente_id, datos)
        return {"exito": True, "cliente_id": cliente.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{cliente_id}")
async def eliminar_cliente(cliente_id: int, service: ClienteService = Depends(get_cliente_service)):
    """Elimina un cliente."""
    try:
        if service.eliminar_cliente(cliente_id):
            return {"exito": True, "mensaje": "Cliente eliminado exitosamente"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
