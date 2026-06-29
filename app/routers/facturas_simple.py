"""
Router SUPER SIMPLE para MVP.
Solo lo esencial: upload, dashboard, detalle, comentarios, cambiar estado.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.services.upload_simple_service import ServidorUploadSimple

router = APIRouter(prefix="/api/facturas", tags=["facturas"])


# ==================== UPLOAD ====================

@router.post("/upload")
def upload_factura(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_id: str = "usuario_default"
):
    """
    Upload simple para MVP.
    - Recibe: PDF o imagen
    - Guarda: Google Drive + BD
    - Retorna: ID de factura (incluso sin OCR)
    """
    try:
        contenido = file.file.read()
        if not contenido:
            raise HTTPException(status_code=400, detail="El archivo está vacío")
        
        servicio = ServidorUploadSimple(db)
        resultado = servicio.procesar_factura(
            contenido_bytes=contenido,
            nombre_archivo=file.filename,
            usuario_id=usuario_id,
            mime_type=file.content_type,
        )
        
        if resultado["success"]:
            return {
                "status": "ok",
                "factura_id": resultado["factura_id"],
                "mensaje": "Factura subida correctamente",
                "ocr_exitoso": resultado.get("ocr_exitoso", False),
                "texto_ocr_preview": resultado.get("texto_ocr_preview"),
                "campos_extraidos": resultado.get("campos_extraidos"),
                "ocr_error": resultado.get("ocr_error"),
                "ruta_archivo": resultado.get("ruta_drive"),
                "drive_file_id": resultado.get("drive_file_id"),
                "drive_folder_id": resultado.get("drive_folder_id"),
                "storage": resultado.get("storage"),
            }
        else:
            raise HTTPException(status_code=500, detail=resultado["error"])
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== DASHBOARD ====================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Retorna lista de facturas para tabla del dashboard."""
    try:
        from app.models.factura import Factura
        from sqlalchemy import select
        
        facturas = db.scalars(
            select(Factura).order_by(Factura.fecha_subida.desc().nullslast(), Factura.created_at.desc().nullslast())
        ).all()
        
        def _estado_ui(f):
            if f.estado and getattr(f.estado, "nombre", None):
                return str(f.estado.nombre).strip().lower()
            if f.contabilizada:
                return "pagada"
            if f.revisada:
                return "revisada"
            return "pendiente"

        return {
            "total": len(facturas),
            "facturas": [
                {
                    "id": f.id,
                    "numero": f.numero_factura or "—",
                    "fecha": f.fecha_factura.isoformat() if f.fecha_factura else "—",
                    "proveedor": f.proveedor.nombre if f.proveedor else "—",
                    "total": float(f.total) if f.total else 0,
                    "estado": _estado_ui(f),
                    "empleado": f.empleado_id or "—",
                    "fecha_subida": f.fecha_subida.isoformat() if f.fecha_subida else "—",
                    "archivo": f.nombre_archivo or "—",
                    "ruta_drive": f.google_drive_url,
                    "drive_file_id": f.google_drive_file_id,
                    "drive_folder_id": f.google_drive_folder_id,
                    "mime_type": f.mime_type,
                    "tamano_archivo": int(f.tamano_archivo) if f.tamano_archivo is not None else None,
                    "hash_sha256": f.hash_sha256,
                    "storage": "drive" if (f.google_drive_file_id or (f.google_drive_url and "drive.google.com" in f.google_drive_url)) else "local",
                }
                for f in facturas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DETALLE ====================

@router.get("/{factura_id}")
def obtener_factura(factura_id: int, db: Session = Depends(get_db)):
    """Obtiene detalles completos de una factura."""
    try:
        from app.models.factura import Factura
        
        factura = db.get(Factura, factura_id)
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        
        return {
            "id": factura.id,
            "numero_factura": factura.numero_factura,
            "fecha_factura": factura.fecha_factura.isoformat() if factura.fecha_factura else None,
            "proveedor": factura.proveedor.nombre if factura.proveedor else None,
            "proveedor_id": factura.proveedor_id,
            "cliente_id": factura.cliente_id,
            "base_imponible": float(factura.base_imponible) if factura.base_imponible is not None else None,
            "iva": float(factura.iva) if factura.iva is not None else None,
            "total": float(factura.total) if factura.total is not None else None,
            "estado": factura.estado.nombre if factura.estado else None,
            "estado_id": factura.estado_id,
            "empleado_id": factura.empleado_id,
            "ruta_drive": factura.google_drive_url,
            "archivo_nombre": factura.nombre_archivo,
            "drive_file_id": factura.google_drive_file_id,
            "drive_folder_id": factura.google_drive_folder_id,
            "mime_type": factura.mime_type,
            "tamano_archivo": int(factura.tamano_archivo) if factura.tamano_archivo is not None else None,
            "hash_sha256": factura.hash_sha256,
            "storage": "drive" if factura.google_drive_file_id else "local",
            "fecha_subida": factura.fecha_subida.isoformat() if factura.fecha_subida else None,
            "usuario_subida": factura.created_by,
            "observaciones": factura.observaciones
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ACTUALIZAR CAMPOS ====================

@router.put("/{factura_id}")
def actualizar_factura(factura_id: int, datos: dict, db: Session = Depends(get_db)):
    """Actualiza cualquier campo de la factura (edición manual)."""
    try:
        from app.models.factura import Factura
        from datetime import datetime, timezone
        
        factura = db.get(Factura, factura_id)
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        
        # Actualizar solo campos conocidos
        campos_permitidos = {
            "numero_factura",
            "fecha_factura",
            "proveedor_id",
            "cliente_id",
            "base_imponible",
            "iva",
            "total",
            "empleado_id",
            "observaciones",
            "estado_id",
            "revisada",
            "contabilizada",
        }
        
        for campo, valor in datos.items():
            if campo in campos_permitidos:
                setattr(factura, campo, valor)

        # Permitir actualización por nombre de estado para la UI MVP
        if "estado" in datos and datos.get("estado"):
            from app.models.estado import Estado
            estado_nombre = str(datos["estado"]).strip().lower()
            estado_obj = db.scalar(select(Estado).where(func.lower(Estado.nombre) == estado_nombre))
            if estado_obj:
                factura.estado_id = estado_obj.id
            elif estado_nombre == "pagada":
                factura.revisada = True
                factura.contabilizada = True
            elif estado_nombre in ("revisada", "aprobada"):
                factura.revisada = True
        
        factura.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(factura)
        
        return {"status": "ok", "mensaje": "Factura actualizada"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CAMBIAR ESTADO ====================

@router.post("/{factura_id}/estado/{nuevo_estado}")
def cambiar_estado(
    factura_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db)
):
    """Cambia el estado de la factura."""
    estados_validos = ["pendiente", "revisada", "aprobada", "pagada"]
    
    if nuevo_estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado no válido. Válidos: {estados_validos}")
    
    try:
        from app.models.factura import Factura
        from app.models.estado import Estado
        
        factura = db.get(Factura, factura_id)
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        
        estado_obj = db.scalar(select(Estado).where(func.lower(Estado.nombre) == nuevo_estado.lower()))
        if estado_obj:
            factura.estado_id = estado_obj.id
        else:
            # Fallback MVP sin tocar estructura: reflejar en flags
            if nuevo_estado == "pagada":
                factura.revisada = True
                factura.contabilizada = True
            elif nuevo_estado in ("revisada", "aprobada"):
                factura.revisada = True
        db.commit()
        
        return {"status": "ok", "nuevo_estado": nuevo_estado}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ASIGNAR EMPLEADO ====================

@router.post("/{factura_id}/empleado/{empleado_id}")
def asignar_empleado(
    factura_id: int,
    empleado_id: int,
    db: Session = Depends(get_db)
):
    """Asigna un empleado a la factura."""
    try:
        from app.models.factura import Factura
        
        factura = db.get(Factura, factura_id)
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        
        factura.empleado_id = empleado_id
        db.commit()
        
        return {"status": "ok", "empleado_id": empleado_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
