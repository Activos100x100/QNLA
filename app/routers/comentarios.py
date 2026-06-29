"""
Router FastAPI para comentarios de entidades.
Endpoints para crear, actualizar, resolver y obtener comentarios (soporte genérico).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.comentarios_service import ComentariosService
from app.schemas.factura_schemas import (
    ComentarioCreate,
    ComentarioUpdate,
    ComentarioResponse,
    ComentarioEstadisticas,
    ComentarioAuditoriaResponse
)

router = APIRouter(prefix="/api/comentarios", tags=["comentarios"])


# ========== CREAR COMENTARIO ==========

@router.post("/", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario(
    datos: ComentarioCreate,
    usuario_id: str = "usuario_default",  # En producción: obtener de JWT
    usuario_nombre: str = "Usuario",  # En producción: obtener de JWT
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo comentario en una entidad.
    
    - **entity_type**: Tipo de entidad ("factura", "pedido", "incidencia", etc.)
    - **entity_id**: ID de la entidad
    - **texto**: Contenido del comentario (máx 5000 caracteres)
    - **tipo**: Tipo de comentario (información, revisión, incidencia, aprobación, rechazo)
    - **parent_id**: ID del comentario padre (para respuestas)
    """
    try:
        servicio = ComentariosService(db)
        return servicio.crear_comentario(
            entity_type=datos.entity_type,
            entity_id=datos.entity_id,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            texto=datos.texto,
            tipo=datos.tipo,
            parent_id=datos.parent_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== OBTENER COMENTARIOS ==========

@router.get("/{entity_type}/{entity_id}", response_model=List[ComentarioResponse])
def obtener_comentarios(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene comentarios principales de una entidad con sus respuestas."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_comentarios_entidad(entity_type, entity_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{entity_type}/{entity_id}/pendientes", response_model=List[ComentarioResponse])
def obtener_pendientes(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene comentarios pendientes de una entidad."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_comentarios_pendientes(entity_type, entity_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{entity_type}/{entity_id}/tipo/{tipo}", response_model=List[ComentarioResponse])
def obtener_por_tipo(
    entity_type: str,
    entity_id: int,
    tipo: str,
    db: Session = Depends(get_db)
):
    """Obtiene comentarios de un tipo específico."""
    tipos_validos = ["informacion", "revision", "incidencia", "aprobacion", "rechazo"]
    if tipo not in tipos_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo inválido. Válidos: {tipos_validos}"
        )
    try:
        servicio = ComentariosService(db)
        comentarios = servicio.repo.obtener_por_tipo(entity_type, entity_id, tipo)
        return [ComentarioResponse.model_validate(c) for c in comentarios]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{comentario_id}/respuestas", response_model=List[ComentarioResponse])
def obtener_respuestas(
    comentario_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene respuestas directas de un comentario."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_respuestas(comentario_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== ACTUALIZAR COMENTARIO ==========

@router.put("/{comentario_id}", response_model=ComentarioResponse)
def actualizar_comentario(
    comentario_id: int,
    datos: ComentarioUpdate,
    usuario_id: str = "usuario_default",
    usuario_nombre: str = "Usuario",
    db: Session = Depends(get_db)
):
    """Actualiza un comentario."""
    try:
        servicio = ComentariosService(db)
        actualizaciones = {k: v for k, v in datos.dict().items() if v is not None}
        return servicio.actualizar_comentario(
            comentario_id=comentario_id,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            **actualizaciones
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== RESOLVER COMENTARIO ==========

@router.post("/{comentario_id}/resolver", response_model=ComentarioResponse)
def resolver_comentario(
    comentario_id: int,
    usuario_id: str = "usuario_default",
    usuario_nombre: str = "Usuario",
    db: Session = Depends(get_db)
):
    """Marca un comentario como resuelto."""
    try:
        servicio = ComentariosService(db)
        return servicio.resolver_comentario(comentario_id, usuario_id, usuario_nombre)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{comentario_id}/reabrirDISCOUNT", response_model=ComentarioResponse)
def reabrircomentario(
    comentario_id: int,
    usuario_id: str = "usuario_default",
    usuario_nombre: str = "Usuario",
    db: Session = Depends(get_db)
):
    """Reabre un comentario resuelto."""
    try:
        servicio = ComentariosService(db)
        return servicio.reabrircomentario(comentario_id, usuario_id, usuario_nombre)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== ESTADÍSTICAS ==========

@router.get("/{entity_type}/{entity_id}/estadisticas", response_model=ComentarioEstadisticas)
def obtener_estadisticas(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas de comentarios."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_estadisticas(entity_type, entity_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{entity_type}/{entity_id}/tiene-pendientes", response_model=dict)
def tiene_comentarios_pendientes(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Verifica si hay comentarios pendientes."""
    try:
        servicio = ComentariosService(db)
        tiene_pendientes = servicio.tiene_pendientes(entity_type, entity_id)
        return {"tiene_pendientes": tiene_pendientes}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sistema/{entity_type}/pendientes", response_model=dict)
def obtener_entidades_con_pendientes(
    entity_type: str,
    db: Session = Depends(get_db)
):
    """Obtiene IDs de todas las entidades con comentarios pendientes."""
    try:
        servicio = ComentariosService(db)
        entidades = servicio.entidades_con_pendientes(entity_type)
        return {"entidades_con_pendientes": entidades}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== AUDITORÍA ==========

@router.get("/{comentario_id}/auditoria", response_model=List[ComentarioAuditoriaResponse])
def obtener_auditoria_comentario(
    comentario_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene historial de auditoría de un comentario."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_auditoria_comentario(comentario_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{entity_type}/{entity_id}/auditoria", response_model=List[ComentarioAuditoriaResponse])
def obtener_auditoria_entidad(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene historial de auditoría de una entidad."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_auditoria_entidad(entity_type, entity_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/usuario/{usuario_id}/auditoria", response_model=List[ComentarioAuditoriaResponse])
def obtener_auditoria_usuario(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """Obtiene historial de acciones de un usuario."""
    try:
        servicio = ComentariosService(db)
        return servicio.obtener_auditoria_usuario(usuario_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== ELIMINAR COMENTARIO ==========

@router.delete("/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_comentario(
    comentario_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un comentario y sus respuestas."""
    try:
        servicio = ComentariosService(db)
        servicio.eliminar_comentario(comentario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
