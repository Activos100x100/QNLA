"""
Servicio de upload simple para MVP.
- Guarda en Google Drive
- Crea registro en BD
- OCR opcional (no bloquea)
"""

import logging
import tempfile
import os
import re
import mimetypes
import hashlib
from io import BytesIO
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServidorUploadSimple:
    """Upload simple: archivo → Google Drive + BD, OCR opcional."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def procesar_factura(
        self,
        contenido_bytes: bytes,
        nombre_archivo: str,
        usuario_id: str,
        mime_type: str | None = None,
    ) -> Dict[str, Any]:
        """
        Procesa una factura:
        1. Guarda en Google Drive
        2. Crea registro en BD
        3. Intenta OCR (bonus, no bloquea si falla)
        
        Retorna: {"success": bool, "factura_id": int, "ocr_exitoso": bool, "error": str}
        """
        resultado = {
            "success": False,
            "factura_id": None,
            "ocr_exitoso": False,
            "texto_ocr_preview": None,
            "campos_extraidos": None,
            "ocr_error": None,
            "error": None,
            "ruta_drive": None,
            "drive_file_id": None,
            "drive_folder_id": None,
            "storage": None,
        }
        
        try:
            nombre_limpio = self._sanitizar_nombre_archivo(nombre_archivo)
            mime_deducido = self._deducir_mime_type(nombre_limpio, mime_type)

            # Paso 1: Guardar en Google Drive
            storage_info = self._guardar_en_drive(contenido_bytes, nombre_limpio, mime_deducido)
            resultado["ruta_drive"] = storage_info.get("ruta")
            resultado["drive_file_id"] = storage_info.get("file_id")
            resultado["drive_folder_id"] = storage_info.get("folder_id")
            resultado["storage"] = storage_info.get("storage")
            logger.info(f"✅ Archivo guardado en almacenamiento: {storage_info.get('ruta')}")
            
            # Paso 2: Crear registro en BD
            from app.models.factura import Factura
            factura = Factura(
                nombre_archivo=nombre_limpio,
                google_drive_url=storage_info.get("ruta"),
                google_drive_file_id=storage_info.get("file_id"),
                google_drive_folder_id=storage_info.get("folder_id"),
                mime_type=mime_deducido,
                tamano_archivo=len(contenido_bytes),
                hash_sha256=hashlib.sha256(contenido_bytes).hexdigest(),
                fecha_subida=datetime.now(timezone.utc),
                observaciones=f"storage={storage_info.get('storage', 'desconocido')}",
                empresa_id=2,
                created_by=int(usuario_id) if usuario_id.isdigit() else 1,
            )
            self.db.add(factura)
            self.db.commit()
            self.db.refresh(factura)
            
            resultado["factura_id"] = factura.id
            resultado["success"] = True
            logger.info(f"✅ Factura #{factura.id} registrada en BD")
            
            # Paso 3: OCR opcional (no bloquea)
            try:
                texto_ocr = self._extraer_ocr_basico(contenido_bytes)
                if texto_ocr:
                    from app.models.ocr_resultado import OcrResultado
                    ocr = OcrResultado(
                        factura_id=factura.id,
                        texto_extraido=texto_ocr
                    )
                    self.db.add(ocr)
                    self.db.commit()
                    resultado["ocr_exitoso"] = True
                    # Devolver preview para UI (evitar payloads gigantes)
                    resultado["texto_ocr_preview"] = texto_ocr[:4000]
                    campos = self._extraer_campos_clave(texto_ocr)
                    resultado["campos_extraidos"] = campos

                    # Persistir campos útiles sin cambiar estructura BD
                    self._aplicar_campos_extraidos_a_factura(factura, campos)
                    self.db.commit()
                    self.db.refresh(factura)
                    logger.info(f"✅ OCR para factura #{factura.id}")
                else:
                    # Fallback: reutilizar pipeline robusto ya implementado en app/api/facturas.py
                    fallback = self._extraer_campos_con_pipeline_avanzado(contenido_bytes)
                    campos_fb = fallback.get("campos")
                    texto_fb = fallback.get("texto")

                    if texto_fb:
                        resultado["texto_ocr_preview"] = texto_fb[:4000]

                    if campos_fb and any(v is not None for v in campos_fb.values()):
                        resultado["ocr_exitoso"] = True
                        resultado["campos_extraidos"] = campos_fb
                        self._aplicar_campos_extraidos_a_factura(factura, campos_fb)
                        self.db.commit()
                        self.db.refresh(factura)
                        logger.info(f"✅ Extracción fallback para factura #{factura.id}")
                    else:
                        resultado["ocr_error"] = "No se detectó texto legible en el archivo"
            except Exception as e:
                resultado["ocr_error"] = str(e)
                logger.warning(f"⚠️ OCR falló: {e}, pero factura ya guardada")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error procesando factura: {e}")
            resultado["error"] = str(e)
            return resultado
    
    def _guardar_en_drive(self, contenido_bytes: bytes, nombre_archivo: str, mime_type: str) -> Dict[str, Any]:
        """Guarda archivo en Google Drive en estructura FACTURAS/YEAR/MONTH/. Si falla, guarda localmente."""
        try:
            from app.core.integracion.google_drive import SHARED_DRIVE_ID, get_drive_service_for_user, crear_carpeta_por_fecha, subir_archivo_a_drive
            
            # Obtener servicio Drive
            drive = get_drive_service_for_user("sistema@ftra.local")
            
            # Obtener año y mes actual
            ahora = datetime.now()
            year = ahora.strftime("%Y")
            month = ahora.strftime("%m-%B").upper()  # ej: "06-JUNIO"
            
            # Crear carpeta de mes
            month_folder_id = crear_carpeta_por_fecha(drive, SHARED_DRIVE_ID, year, month)
            
            # Subir archivo
            file_result = subir_archivo_a_drive(
                drive=drive,
                contenido_bytes=contenido_bytes,
                nombre_archivo=nombre_archivo,
                parent_folder_id=month_folder_id,
                mime_type=mime_type
            )
            
            # Retornar metadata de Drive
            return {
                "storage": "drive",
                "ruta": file_result.get("webViewLink", f"FACTURAS/{year}/{month}/{nombre_archivo}"),
                "file_id": file_result.get("id"),
                "folder_id": month_folder_id,
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Google Drive falló: {e}, guardando localmente")
            
            # Fallback: guardar localmente
            try:
                ahora = datetime.now()
                year = ahora.strftime("%Y")
                month = ahora.strftime("%m")
                
                # Crear estructura local: uploads/facturas/2026/06/
                local_dir = f"app/uploads/facturas/{year}/{month}"
                os.makedirs(local_dir, exist_ok=True)
                
                file_path = os.path.join(local_dir, nombre_archivo)
                with open(file_path, 'wb') as f:
                    f.write(contenido_bytes)
                
                logger.info(f"✅ Archivo guardado localmente: {file_path}")
                return {
                    "storage": "local",
                    "ruta": file_path,
                    "file_id": None,
                    "folder_id": f"local:{year}/{month}",
                }
                
            except Exception as local_e:
                logger.error(f"❌ Error también guardando localmente: {local_e}")
                raise

    def _sanitizar_nombre_archivo(self, nombre_archivo: str) -> str:
        """Sanitiza nombre de archivo para evitar rutas inválidas o traversal."""
        if not nombre_archivo:
            ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"factura_{ahora}.bin"

        base = os.path.basename(str(nombre_archivo).strip())
        # Reemplazar caracteres conflictivos
        base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
        # Evitar nombre vacío tras sanitizar
        if not base or base in {".", ".."}:
            ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"factura_{ahora}.bin"
        return base

    def _deducir_mime_type(self, nombre_archivo: str, mime_type: str | None) -> str:
        """Determina MIME efectivo a partir del Upload o extensión."""
        if mime_type and mime_type.strip() and mime_type != "application/octet-stream":
            return mime_type.strip().lower()

        guess, _ = mimetypes.guess_type(nombre_archivo)
        return (guess or "application/octet-stream").lower()
    
    def _extraer_ocr_basico(self, contenido_bytes: bytes) -> str | None:
        """Extrae texto de PDF o imagen sin reglas complejas."""
        try:
            # PDF: usar PyMuPDF
            if contenido_bytes[:4] == b"%PDF":
                import fitz
                from PIL import Image

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(contenido_bytes)
                    tmp.flush()

                    doc = fitz.open(tmp.name)
                    texto = ""
                    for page in doc:
                        texto += page.get_text() + "\n"

                    texto = texto.strip()
                    if texto:
                        doc.close()
                        os.unlink(tmp.name)
                        return texto

                    # Fallback OCR para PDFs escaneados (sin texto embebido)
                    texto_ocr_paginas = []
                    for page in doc:
                        pix = page.get_pixmap(dpi=220)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        txt_page = self._ocr_imagen_robusto(img)
                        if txt_page and txt_page.strip():
                            texto_ocr_paginas.append(txt_page.strip())

                    doc.close()
                    os.unlink(tmp.name)
                    texto_ocr = "\n\n".join(texto_ocr_paginas).strip()
                    return texto_ocr if texto_ocr else None

            # Imagen: usar OCR robusto
            from PIL import Image

            imagen = Image.open(BytesIO(contenido_bytes))
            texto = self._ocr_imagen_robusto(imagen)

            return texto.strip() if texto and texto.strip() else None
                
        except Exception as e:
            logger.debug(f"OCR básico falló: {e}")
            return None

    def _extraer_campos_clave(self, texto: str) -> Dict[str, Any]:
        """Extrae campos clave de una factura en formato español a partir del texto OCR."""
        data: Dict[str, Any] = {
            "factura_numero": None,
            "fecha_emision": None,
            "nif_cliente": None,
            "cliente": None,
            "base_imponible": None,
            "iva": None,
            "total": None,
        }

        if not texto:
            return data

        def _first(pattern: str, flags: int = re.IGNORECASE | re.MULTILINE) -> str | None:
            m = re.search(pattern, texto, flags)
            return m.group(1).strip() if m else None

        def _norm_amount(v: str | None) -> float | None:
            if not v:
                return None
            cleaned = re.sub(r"[^\d,.-]", "", v)
            if not cleaned:
                return None
            # Formato ES: 3.470,00 -> 3470.00
            cleaned = cleaned.replace(".", "").replace(",", ".")
            try:
                return float(cleaned)
            except ValueError:
                return None

        data["factura_numero"] = _first(r"Factura\s*N[ºo°]?\s*[:\-]?\s*([A-Z0-9\-/]+)")
        if not data["factura_numero"]:
            data["factura_numero"] = _first(r"\b([A-Z]{1,4}\d{5,12})\b")

        data["fecha_emision"] = _first(r"Fecha\s*emisi[oó]n\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})")
        if not data["fecha_emision"]:
            data["fecha_emision"] = _first(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
        if not data["fecha_emision"]:
            data["fecha_emision"] = _first(
                r"\b(\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\s+de\s+\d{4})\b"
            )

        data["nif_cliente"] = _first(r"N\.?I\.?F\.?\s*Cliente\s*[:\-]?\s*([A-Z0-9\-]{7,12})")
        if not data["nif_cliente"]:
            data["nif_cliente"] = _first(r"CIF\s*[:\-]?\s*([A-Z]\d{8})")

        # Cliente (línea siguiente a NIF si existe en el OCR)
        cliente = _first(r"N\.?I\.?F\.?\s*Cliente\s*[:\-]?.*\n([^\n]{3,80})")
        if cliente and re.search(r"\d", cliente):
            cliente = None
        data["cliente"] = cliente

        base = _first(r"Base\s*Imp\.?\s*[:\-]?\s*([\d\.,]+)")
        iva = _first(r"(?:Importe\s*IVA|I\.?V\.?A\.?\s*[\d,\.%]*)\s*[:\-]?\s*([\d\.,]+)")

        # Total: intentar patrón "Total Factura ... 3.470,00" y variantes
        total = _first(r"Total\s*Factura\s*[:\-]?\s*([\d\.,]+)")
        if not total:
            total = _first(r"TOTAL\s*EUROS\s*[:\-\.]?\s*([\d\.,]+)")

        data["base_imponible"] = _norm_amount(base)
        data["iva"] = _norm_amount(iva)
        data["total"] = _norm_amount(total)

        return data

    def _aplicar_campos_extraidos_a_factura(self, factura, campos: Dict[str, Any]) -> None:
        """Aplica campos extraídos al registro de factura existente (best effort)."""
        if not campos:
            return

        numero = campos.get("factura_numero")
        fecha_txt = campos.get("fecha_emision")
        total = campos.get("total")
        base = campos.get("base_imponible")
        iva = campos.get("iva")
        cliente = campos.get("cliente")
        nif_cliente = campos.get("nif_cliente")

        if numero and not factura.numero_factura:
            factura.numero_factura = str(numero)[:100]

        if fecha_txt and not factura.fecha_factura:
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    factura.fecha_factura = datetime.strptime(fecha_txt, fmt).date()
                    break
                except ValueError:
                    continue

        if total is not None and factura.total is None:
            factura.total = total
        if base is not None and factura.base_imponible is None:
            factura.base_imponible = base
        if iva is not None and factura.iva is None:
            factura.iva = iva

        # Guardar trazabilidad textual sin tocar modelo/BD
        extra_obs = []
        if cliente:
            extra_obs.append(f"Cliente OCR: {cliente}")
        if nif_cliente:
            extra_obs.append(f"NIF OCR: {nif_cliente}")
        if extra_obs:
            prev = factura.observaciones or ""
            merged = (prev + "\n" + " | ".join(extra_obs)).strip()
            factura.observaciones = merged[:5000]

    def _extraer_campos_con_pipeline_avanzado(self, contenido_bytes: bytes) -> Dict[str, Any]:
        """Fallback con extractor robusto existente en app/api/facturas.py."""
        try:
            from app.api.facturas import (
                _texto_desde_pdf,
                _texto_desde_imagen,
                _extraer_datos_fiscales,
                _asegurar_tesseract_disponible,
            )

            is_pdf = contenido_bytes[:4] == b"%PDF"
            if is_pdf:
                t_izq, t_der, t_full = _texto_desde_pdf(contenido_bytes)
            else:
                _asegurar_tesseract_disponible()
                t_izq, t_der, t_full = _texto_desde_imagen(contenido_bytes)

            datos = _extraer_datos_fiscales(t_izq or "", t_der or "", t_full or "")

            campos_regex = self._extraer_campos_clave(t_full or "")

            campos = {
                "factura_numero": datos.get("numero_factura") or campos_regex.get("factura_numero"),
                "fecha_emision": datos.get("fecha") or campos_regex.get("fecha_emision"),
                "nif_cliente": datos.get("receptor_nif") or campos_regex.get("nif_cliente"),
                "cliente": datos.get("receptor_nombre") or campos_regex.get("cliente"),
                "base_imponible": self._normalizar_importe_float(datos.get("base_imponible")) if datos.get("base_imponible") else campos_regex.get("base_imponible"),
                "iva": self._normalizar_importe_float(datos.get("cuota_iva")) if datos.get("cuota_iva") else campos_regex.get("iva"),
                "total": self._normalizar_importe_float(datos.get("total")) if datos.get("total") else campos_regex.get("total"),
            }

            # Sanity check de importes para evitar mostrar valores absurdos
            base = campos.get("base_imponible")
            iva = campos.get("iva")
            total = campos.get("total")
            if base is not None and iva is not None and total is not None:
                if abs((base + iva) - total) > 0.15:
                    campos["base_imponible"] = None
                    campos["iva"] = None

            return {"texto": (t_full or "").strip(), "campos": campos}
        except Exception as e:
            logger.debug(f"Pipeline avanzado falló: {e}")
            return {"texto": None, "campos": None}

    def _normalizar_importe_float(self, valor: Any) -> float | None:
        if valor is None:
            return None
        s = str(valor).strip()
        if not s:
            return None
        s = re.sub(r"[^\d,.-]", "", s)
        if not s:
            return None
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    def _ocr_imagen_robusto(self, imagen) -> str:
        """
        OCR más robusto para facturas escaneadas/fotografiadas.
        Prueba varias configuraciones y preprocesados y devuelve el mejor resultado.
        """
        import pytesseract
        import numpy as np
        import cv2
        from PIL import Image, ImageOps

        # Normalizar a RGB y escalar para mejorar reconocimiento
        imagen = ImageOps.exif_transpose(imagen)
        if imagen.mode not in ("RGB", "L"):
            imagen = imagen.convert("RGB")

        np_img = np.array(imagen)
        if np_img.ndim == 3:
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = np_img

        h, w = gray.shape[:2]
        scale = 2.0 if min(h, w) < 1400 else 1.3
        gray_up = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Variantes de preprocesado
        blur = cv2.GaussianBlur(gray_up, (3, 3), 0)
        _, th_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        th_adapt = cv2.adaptiveThreshold(gray_up, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)

        variantes = [gray_up, th_otsu, th_adapt]
        configs = [
            "--oem 3 --psm 6",
            "--oem 3 --psm 4",
            "--oem 3 --psm 11",
        ]

        mejor_texto = ""
        for variante in variantes:
            img_pil = Image.fromarray(variante)
            for cfg in configs:
                texto = ""
                try:
                    texto = pytesseract.image_to_string(img_pil, lang="spa+eng", config=cfg)
                except Exception:
                    try:
                        texto = pytesseract.image_to_string(img_pil, config=cfg)
                    except Exception:
                        texto = ""

                texto = (texto or "").strip()
                if len(texto) > len(mejor_texto):
                    mejor_texto = texto

        return mejor_texto
