"""
Router API para FTRA_FACTURAS.
Endpoints para gestión completa de facturas.
"""

from typing import List, Optional
from datetime import timezone
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.factura import Factura
from app.services.factura_service import FacturaService
from app.repositories.factura_repository import FacturaRepository
from app.schemas.factura_schemas import FacturaCreate, FacturaUpdate
import logging

router = APIRouter(prefix="/api/facturas", tags=["facturas"])
logger = logging.getLogger(__name__)

# Importar utilidades para procesar PDFs
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# Dependencia para obtener el servicio
def get_factura_service(db: Session = Depends(get_db)) -> FacturaService:
    """Obtiene instancia del servicio de facturas."""
    return FacturaService(db)


@router.post("/crear", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_factura(
    datos: FacturaCreate,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Crea una nueva factura desde JSON."""
    try:
        factura = service.crear_factura(datos)
        return {
            "exito": True,
            "mensaje": "Factura creada exitosamente",
            "factura_id": factura.id,
            "numero_factura": factura.numero_factura
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def extraer_texto_imagen(contenido_bytes: bytes) -> str:
    """Extrae texto de una imagen usando OCR (Tesseract)."""
    if not HAS_TESSERACT:
        return "OCR no disponible. Instala pytesseract y tesseract-ocr"
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(contenido_bytes)
            tmp.flush()
            
            imagen = Image.open(tmp.name)
            texto = pytesseract.image_to_string(imagen, lang='spa')
            os.unlink(tmp.name)
            return texto
    except Exception as e:
        logger.warning(f"Error con OCR: {e}")
        return f"Error extrayendo texto de imagen: {str(e)}"


def extraer_texto_pdf(contenido_bytes: bytes) -> str:
    """Extrae texto de un PDF."""
    texto = ""
    
    # Intentar con PyMuPDF primero (mejor formato)
    if HAS_PYMUPDF:
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(contenido_bytes)
                tmp.flush()
                
                doc = fitz.open(tmp.name)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    texto += page.get_text() + "\n"
                doc.close()
                os.unlink(tmp.name)
                return texto
        except Exception as e:
            logger.warning(f"Error con PyMuPDF: {e}")
    
    # Fallback a PyPDF2
    if HAS_PYPDF2:
        try:
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(contenido_bytes))
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                texto += page.extract_text() + "\n"
            return texto
        except Exception as e:
            logger.warning(f"Error con PyPDF2: {e}")
    
    return "No se pudo extraer texto del PDF"


def extraer_datos_factura_con_ia(texto: str) -> dict:
    """Usa IA simple (pattern matching) para extraer datos de factura."""
    import re
    from datetime import datetime
    
    datos = {
        "numero_factura": None,
        "fecha": None,
        "proveedor": None,
        "cliente": None,
        "total": None,
        "base_imponible": None,
        "iva": None,
        "items": [],
        "texto_original": texto[:1000]  # Primeros 1000 caracteres
    }
    
    # Buscar número de factura - múltiples estrategias para PDFs escaneados/OCR
    # 1. Patrón: "Factura n.° FQ0000715" (con caracteres especiales)
    match = re.search(r"[Ff]actura\s+n[.°º\s]*(\d{5,})", texto)
    if not match:
        # 2. Patrón: "Factura nº FQ0000715"
        match = re.search(r"[Ff]actura\s+(?:n[.°º]*|número|nº)\s*([A-Z]*\d+)", texto, re.IGNORECASE)
    if not match:
        # 3. Patrón: Buscar directamente números de factura comunes (FQ, FAC, INV, etc)
        match = re.search(r"^([A-Z]{0,3}\d{5,10})", texto, re.MULTILINE)
    if not match:
        # 4. Último intento: cualquier número de 5+ dígitos precedido por "Factura"
        match = re.search(r"[Ff]actura[:\s]+([A-Z0-9]{5,15})", texto, re.IGNORECASE | re.DOTALL)
    if match:
        numero = match.group(1).strip()
        # Limpiar de caracteres especiales si es necesario
        numero = re.sub(r'[^\w]', '', numero)
        if numero:
            datos["numero_factura"] = numero
    
    # Buscar proveedor - nombres de empresa comunes
    # Busca palabras en mayúsculas con terminaciones como S.L., SL, SA, etc.
    match = re.search(r"^([A-Z\s,\.\-]+?(?:S\.?L\.?|S\.?A\.?|LTDA|UNIPERSONAL|S\.?L\. UNIPERSONAL|LLC|CORP))", texto, re.MULTILINE)
    if match:
        proveedor = match.group(1).strip()
        datos["proveedor"] = proveedor[:150]  # Limitar a 150 caracteres
    
    # Buscar fecha con múltiples formatos
    # Intenta: DD/MM/YYYY, DD-MM-YYYY, DD Mes YYYY, 31 de Enero 2026, etc.
    match = re.search(r"(\d{1,2})\s+de\s+([Ee]nero|[Ff]ebrero|[Mm]arzo|[Aa]bril|[Mm]ayo|[Jj]unio|[Jj]ulio|[Aa]gosto|[Ss]eptiembre|[Oo]ctubre|[Nn]oviembre|[Dd]iciembre)[^0-9]*(\d{4})", texto)
    if match:
        meses = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
                 "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
        mes_nombre = match.group(2).lower()
        mes_num = meses.get(mes_nombre, 1)
        try:
            datos["fecha"] = datetime(int(match.group(3)), mes_num, int(match.group(1))).isoformat()
        except:
            pass
    
    # Intenta sin "de": "31 Enero 2026"
    if not datos["fecha"]:
        match = re.search(r"(\d{1,2})\s+([Ee]nero|[Ff]ebrero|[Mm]arzo|[Aa]bril|[Mm]ayo|[Jj]unio|[Jj]ulio|[Aa]gosto|[Ss]eptiembre|[Oo]ctubre|[Nn]oviembre|[Dd]iciembre)[^0-9]*(\d{4})", texto)
        if match:
            meses = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
                     "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
            mes_nombre = match.group(2).lower()
            mes_num = meses.get(mes_nombre, 1)
            try:
                datos["fecha"] = datetime(int(match.group(3)), mes_num, int(match.group(1))).isoformat()
            except:
                pass
    
    # Si no encuentra formato de mes, intenta DD/MM/YYYY
    if not datos["fecha"]:
        match = re.search(r"(\d{2})[/-](\d{2})[/-](\d{4})", texto)
        if match:
            try:
                datos["fecha"] = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
            except:
                pass
    
    # Buscar TOTAL - patrón muy flexible
    # "TOTAL EUROS.......... 52,24" o "TOTAL: 52.24" o "Total 52,24"
    match = re.search(r"(?:TOTAL\s+EUROS|TOTAL|[Tt]otal)[:\s\.\-]*(\d+[.,]\d{2})", texto, re.IGNORECASE)
    if match:
        cantidad = match.group(1).replace(",", ".")
        try:
            datos["total"] = float(cantidad)
        except:
            pass
    
    # Buscar IVA - suma todos los IVA encontrados
    # Patrón: "I.V.A. XX,XX %....... YY,YY" o "IVA: XX.XX" o "I V A"
    # Primero intentar el patrón con porcentaje y valor separados
    iva_matches = re.findall(r"(?:I\.?V\.?A\.?|IVA)[:\s]*[\d,\.]+\s*%[:\s\.\-]*(\d+[.,]\d{2})", texto, re.IGNORECASE)
    if iva_matches:
        iva_total = 0.0
        for iva_str in iva_matches:
            cantidad = iva_str.replace(",", ".")
            try:
                iva_total += float(cantidad)
            except:
                pass
        if iva_total > 0:
            datos["iva"] = iva_total
    
    # Si no encuentra múltiples IVA, intenta patrón general
    if not datos["iva"]:
        match = re.search(r"(?:I\.?V\.?A\.?)[:\s]*(\d+[.,]\d+)", texto, re.IGNORECASE)
        if match:
            cantidad = match.group(1).replace(",", ".")
            try:
                datos["iva"] = float(cantidad)
            except:
                pass
    
    # Buscar base imponible - suma todas las bases encontradas
    # Patrón: "Base al XX,XX %....... YY,YY" o "Base imponible: YY,YY"
    base_matches = re.findall(r"Base(?:\s+(?:impon\w*|al))?\s*[\d,\.]*\s*%?[:\s\.\-]*(\d+[.,]\d{2})", texto, re.IGNORECASE)
    if base_matches:
        base_total = 0.0
        for base_str in base_matches:
            cantidad = base_str.replace(",", ".")
            try:
                base_total += float(cantidad)
            except:
                pass
        if base_total > 0:
            datos["base_imponible"] = base_total
    
    # Si no encuentra múltiples bases, intenta patrón general
    if not datos["base_imponible"]:
        match = re.search(r"[Bb]ase[:\s]*(\d+[.,]\d+)", texto, re.IGNORECASE)
        if match:
            cantidad = match.group(1).replace(",", ".")
            try:
                datos["base_imponible"] = float(cantidad)
            except:
                pass
    
    return datos


@router.post("/diagnostico", status_code=status.HTTP_201_CREATED)
async def diagnostico_factura_transparente(
    file: UploadFile = File(...)
):
    """
    ENDPOINT TRANSPARENTE - Procesa factura mostrando CADA PASO del proceso.
    
    Retorna:
    - Texto OCR completo
    - Prompt enviado a IA
    - Respuesta de IA
    - Validación
    - Bitácora completa con timestamps
    
    Esto es para DIAGNÓSTICO y DEPURACIÓN. 
    El usuario debe validar y LUEGO guardar con /guardar.
    """
    try:
        from app.services.procesamiento_transparente_service import OrquestadorProcesamiento
        
        logger.info(f"📋 DIAGNOSTICO: {file.filename}, tipo: {file.content_type}")
        
        # Validaciones básicas
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archivo vacío o sin nombre"
            )
        
        filename_lower = file.filename.lower()
        es_pdf = filename_lower.endswith('.pdf') or file.content_type == "application/pdf"
        es_imagen = any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.tiff'])
        
        if not (es_pdf or es_imagen):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no soportado: {file.filename}"
            )
        
        contenido = await file.read()
        tipo_archivo = "pdf" if es_pdf else "imagen"
        
        # Procesar con orquestador transparente
        orquestador = OrquestadorProcesamiento(file.filename, contenido, tipo_archivo)
        resultado = orquestador.procesar()
        
        logger.info(f"✅ DIAGNOSTICO completado: {file.filename}")
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en DIAGNOSTICO: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.post("/procesar", status_code=status.HTTP_201_CREATED)
async def procesar_factura(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Procesa un archivo de factura (PDF o imagen).
    Endpoint multipart/form-data que acepta un archivo y lo procesa.
    """
    try:
        # Log detallado de entrada
        logger.info(f"📤 Procesar factura: {file.filename}, tipo: {file.content_type}, tamaño: {file.size}")
        
        # Validar que file no esté vacío
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archivo vacío o sin nombre"
            )
        
        # Validar tipo de archivo (tolerante con extensiones)
        content_type = file.content_type or ""
        filename_lower = file.filename.lower() if file.filename else ""
        
        tipos_permitidos = ["application/pdf", "image/jpeg", "image/png", "image/tiff", "application/octet-stream"]
        extensiones_permitidas = [".pdf", ".jpg", ".jpeg", ".png", ".tiff"]
        
        es_tipo_permitido = content_type in tipos_permitidos
        es_extension_permitida = any(filename_lower.endswith(ext) for ext in extensiones_permitidas)
        
        if not (es_tipo_permitido or es_extension_permitida):
            error_msg = f"Archivo no soportado: {file.filename} (tipo: {content_type})"
            logger.warning(f"❌ {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Leer contenido del archivo
        contenido = await file.read()
        logger.info(f"📄 Contenido leído: {len(contenido)} bytes")
        
        # Detectar tipo de archivo de forma más robusta
        es_pdf = (filename_lower.endswith('.pdf') or 
                  content_type == "application/pdf")
        es_imagen = (any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.tiff']) or
                     content_type in ["image/jpeg", "image/png", "image/tiff"])
        
        # Extraer texto según tipo de archivo
        if es_pdf:
            logger.info("🔍 Detectado PDF, extrayendo con PyMuPDF/PyPDF2...")
            texto_extraido = extraer_texto_pdf(contenido)
            metodo_extraccion = "PDF_Direct"
        elif es_imagen:
            logger.info("🔍 Detectada imagen, extrayendo con OCR...")
            texto_extraido = extraer_texto_imagen(contenido)
            metodo_extraccion = "OCR_Tesseract"
        else:
            error_msg = f"No se pudo detectar tipo: {file.filename} ({content_type})"
            logger.warning(f"❌ {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Validar que se extrajo texto
        logger.info(f"📝 Texto extraído: {len(texto_extraido)} caracteres")
        if not texto_extraido or "Error" in texto_extraido:
            logger.warning(f"❌ Extracción fallida para {file.filename}: {texto_extraido}")
            return {
                "exito": False,
                "mensaje": f"No se pudo extraer texto: {texto_extraido}",
                "archivo": file.filename,
                "metodo": metodo_extraccion
            }
        
        # Procesar con IA (regex patterns)
        logger.info("🤖 Extrayendo datos de factura...")
        datos_extraidos = extraer_datos_factura_con_ia(texto_extraido)
        
        # Nota: Los datos extraídos contienen información básica de la factura.
        # Para guardar en BD se requerirían proveedor_id y cliente_id,
        # que se completarán manualmente o mediante un paso adicional de validación.
        factura_id = None
        
        # Preparar respuesta
        logger.info(f"✅ Factura procesada exitosamente: {file.filename}")
        return {
            "exito": True,
            "mensaje": f"Factura procesada exitosamente: {file.filename}",
            "archivo": file.filename,
            "metodo_extraccion": metodo_extraccion,
            "factura_id": factura_id,
            "datos_extraidos": datos_extraidos,
            "informacion": {
                "numero_factura": datos_extraidos.get("numero_factura"),
                "fecha": datos_extraidos.get("fecha"),
                "total": datos_extraidos.get("total"),
                "iva": datos_extraidos.get("iva"),
                "base_imponible": datos_extraidos.get("base_imponible")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando factura: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar factura: {str(e)}"
        )


# Schemas para guardar factura con datos extraídos
from pydantic import BaseModel

class FacturaSaveRequest(BaseModel):
    """Schema para guardar factura con datos extraídos."""
    numero_factura: str
    fecha: Optional[str]
    total: Optional[float]
    iva: Optional[float]
    base_imponible: Optional[float]
    empresa_id: Optional[int] = None  # Optional for demo
    proveedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    observaciones: Optional[str] = None


@router.post("/guardar", response_model=dict, status_code=status.HTTP_201_CREATED)
async def guardar_factura_procesada(
    datos: FacturaSaveRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Guarda una factura después de la extracción.
    Almacena los datos extraídos sin requerir referencias de empresa si no existen.
    """
    try:
        from datetime import datetime as dt
        from app.models.factura import Factura as FacturaModel
        from app.repositories.factura_repository import FacturaRepository
        
        # Validar que tenga al menos proveedor o cliente
        if not datos.proveedor_id and not datos.cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere proveedor_id o cliente_id"
            )
        
        # Convertir fecha de string a date
        fecha_factura = None
        if datos.fecha:
            try:
                fecha_obj = dt.fromisoformat(datos.fecha.replace("T00:00:00", ""))
                fecha_factura = fecha_obj.date()
            except:
                pass
        
        # Convertir Decimal
        from decimal import Decimal
        
        # Usar empresa_id si está disponible, sino usar None para permitir inserción demo
        empresa_id = datos.empresa_id
        if not empresa_id:
            # Intentar obtener primera empresa válida
            try:
                from sqlalchemy import text
                result = db.execute(text("SELECT id FROM ftra_empresas LIMIT 1")).scalar()
                empresa_id = result
            except:
                empresa_id = None  # Permitir NULL para demo
        
        # Crear objeto factura directamente en lugar de usar FacturaCreate
        factura_obj = FacturaModel(
            empresa_id=empresa_id,
            numero_factura=datos.numero_factura,
            fecha_factura=fecha_factura,
            total=Decimal(str(datos.total)) if datos.total else None,
            iva=Decimal(str(datos.iva)) if datos.iva else None,
            base_imponible=Decimal(str(datos.base_imponible)) if datos.base_imponible else None,
            proveedor_id=datos.proveedor_id,
            cliente_id=datos.cliente_id,
            observaciones=f"Procesada automáticamente. {datos.observaciones or ''}".strip(),
            estado=None,  # Will use default
            fecha_subida=dt.now(timezone.utc) if hasattr(dt, 'now') else None
        )
        
        # Guardar en BD
        repo = FacturaRepository(db)
        factura_creada = repo.crear(factura_obj)
        
        return {
            "exito": True,
            "mensaje": "Factura guardada correctamente",
            "factura_id": factura_creada.id,
            "numero_factura": factura_creada.numero_factura,
            "fecha": factura_creada.fecha_factura.isoformat() if factura_creada.fecha_factura else None,
            "total": float(factura_creada.total) if factura_creada.total else None
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error guardando factura: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar factura: {str(e)}"
        )


@router.get("/", response_model=dict)
async def listar_facturas_basico():
    """Endpoint básico para evitar 405 Method Not Allowed."""
    return {
        "mensaje": "Usa /api/facturas/empresa/{empresa_id} para obtener facturas",
        "endpointDisponibles": [
            "/api/facturas/empresa/{empresa_id}",
            "/api/facturas/empresa/{empresa_id}/pendientes-revision",
            "/api/facturas/empresa/{empresa_id}/pendientes-contabilizacion",
            "/api/facturas/empresa/{empresa_id}/estadisticas"
        ]
    }


@router.get("/{factura_id}", response_model=dict)
async def obtener_factura(
    factura_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Obtiene una factura por ID."""
    try:
        factura = service.obtener_factura(factura_id)
        return {
            "exito": True,
            "factura_id": factura.id,
            "numero_factura": factura.numero_factura,
            "fecha_factura": factura.fecha_factura.isoformat() if factura.fecha_factura else None,
            "total": float(factura.total) if factura.total else None,
            "estado_id": factura.estado_id,
            "revisada": factura.revisada,
            "contabilizada": factura.contabilizada
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/empresa/{empresa_id}")
async def obtener_facturas_empresa(
    empresa_id: int,
    limite: int = 100,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Obtiene facturas de una empresa."""
    try:
        facturas = service.obtener_facturas_empresa(empresa_id, limite=limite)
        return {
            "exito": True,
            "cantidad": len(facturas),
            "facturas": [
                {
                    "id": f.id,
                    "numero_factura": f.numero_factura,
                    "fecha": f.fecha_factura.isoformat() if f.fecha_factura else None,
                    "total": float(f.total) if f.total else None,
                    "revisada": f.revisada
                }
                for f in facturas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/empresa/{empresa_id}/pendientes-revision")
async def obtener_pendientes_revision(
    empresa_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Obtiene facturas pendientes de revisión."""
    try:
        facturas = service.obtener_pendientes_revision(empresa_id)
        return {
            "exito": True,
            "cantidad": len(facturas),
            "facturas": [
                {
                    "id": f.id,
                    "numero_factura": f.numero_factura,
                    "fecha": f.fecha_factura.isoformat() if f.fecha_factura else None,
                    "total": float(f.total) if f.total else None
                }
                for f in facturas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/empresa/{empresa_id}/pendientes-contabilizacion")
async def obtener_pendientes_contabilizacion(
    empresa_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Obtiene facturas pendientes de contabilizar."""
    try:
        facturas = service.obtener_pendientes_contabilizacion(empresa_id)
        return {
            "exito": True,
            "cantidad": len(facturas),
            "facturas": [
                {
                    "id": f.id,
                    "numero_factura": f.numero_factura,
                    "fecha": f.fecha_factura.isoformat() if f.fecha_factura else None,
                    "total": float(f.total) if f.total else None
                }
                for f in facturas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{factura_id}")
async def actualizar_factura(
    factura_id: int,
    datos: FacturaUpdate,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Actualiza una factura."""
    try:
        factura = service.actualizar_factura(factura_id, datos)
        return {
            "exito": True,
            "mensaje": "Factura actualizada exitosamente",
            "factura_id": factura.id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{factura_id}/marcar-revisada")
async def marcar_revisada(
    factura_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Marca una factura como revisada."""
    try:
        factura = service.marcar_revisada(factura_id)
        return {
            "exito": True,
            "mensaje": "Factura marcada como revisada",
            "factura_id": factura.id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{factura_id}/marcar-contabilizada")
async def marcar_contabilizada(
    factura_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Marca una factura como contabilizada."""
    try:
        factura = service.marcar_contabilizada(factura_id)
        return {
            "exito": True,
            "mensaje": "Factura marcada como contabilizada",
            "factura_id": factura.id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{factura_id}/cambiar-estado")
async def cambiar_estado(
    factura_id: int,
    nuevo_estado_id: int,
    usuario_id: int = None,
    comentario: str = None,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Cambia el estado de una factura."""
    try:
        factura = service.cambiar_estado(factura_id, nuevo_estado_id, usuario_id, comentario)
        return {
            "exito": True,
            "mensaje": "Estado actualizado",
            "factura_id": factura.id,
            "nuevo_estado_id": factura.estado_id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{factura_id}")
async def eliminar_factura(
    factura_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Elimina una factura."""
    try:
        if service.eliminar_factura(factura_id):
            return {
                "exito": True,
                "mensaje": "Factura eliminada exitosamente"
            }
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/empresa/{empresa_id}/estadisticas")
async def obtener_estadisticas(
    empresa_id: int,
    service: FacturaService = Depends(get_factura_service)
) -> dict:
    """Obtiene estadísticas de facturas de una empresa."""
    try:
        stats = service.obtener_estadisticas_empresa(empresa_id)
        return {
            "exito": True,
            "estadisticas": stats
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
