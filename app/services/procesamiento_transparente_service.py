"""
Servicio de procesamiento transparente de facturas.
Registra CADA paso del proceso con timestamps, tokens, errores, etc.
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from decimal import Decimal
from io import BytesIO
import re

# Logging
logger = logging.getLogger(__name__)


class ProcesoBitacora:
    """Bitácora detallada de cada etapa del procesamiento."""
    
    def __init__(self, archivo_nombre: str):
        self.archivo_nombre = archivo_nombre
        self.inicio = datetime.now(timezone.utc)
        self.etapas = []
        self.errores = []
        
    def registrar_etapa(self, nombre: str, duracion_ms: float, datos: Dict = None, error: str = None):
        """Registra una etapa completada."""
        etapa = {
            "nombre": nombre,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duracion_ms": duracion_ms,
            "datos": datos or {},
            "error": error,
            "exitosa": error is None
        }
        self.etapas.append(etapa)
        
        if error:
            self.errores.append({
                "etapa": nombre,
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logger.error(f"❌ Etapa {nombre} falló: {error}")
        else:
            logger.info(f"✅ Etapa {nombre} completada en {duracion_ms:.1f}ms")
    
    def resumen(self) -> Dict[str, Any]:
        """Retorna resumen completo del proceso."""
        duracion_total_ms = (datetime.now(timezone.utc) - self.inicio).total_seconds() * 1000
        return {
            "archivo": self.archivo_nombre,
            "inicio": self.inicio.isoformat(),
            "duracion_total_ms": duracion_total_ms,
            "cantidad_etapas": len(self.etapas),
            "etapas_exitosas": sum(1 for e in self.etapas if e["exitosa"]),
            "cantidad_errores": len(self.errores),
            "etapas": self.etapas,
            "errores": self.errores
        }


class ExtractorTextoOCR:
    """Extrae texto de PDF/imagen con logging detallado."""
    
    def __init__(self, bitacora: ProcesoBitacora):
        self.bitacora = bitacora
    
    def extraer_pdf(self, contenido_bytes: bytes) -> Dict[str, Any]:
        """Extrae texto de PDF con PyMuPDF/PyPDF2."""
        inicio = time.time()
        try:
            import tempfile
            import os
            
            # Intentar con PyMuPDF primero
            try:
                import fitz
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(contenido_bytes)
                    tmp.flush()
                    
                    doc = fitz.open(tmp.name)
                    texto = ""
                    paginas_info = []
                    
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        pagina_texto = page.get_text()
                        texto += pagina_texto + "\n"
                        paginas_info.append({
                            "numero": page_num + 1,
                            "caracteres": len(pagina_texto),
                            "bloques": len(page.get_text("blocks"))
                        })
                    
                    doc.close()
                    os.unlink(tmp.name)
                    
                    duracion_ms = (time.time() - inicio) * 1000
                    self.bitacora.registrar_etapa(
                        "OCR_PDF_PyMuPDF",
                        duracion_ms,
                        {
                            "total_caracteres": len(texto),
                            "total_paginas": len(paginas_info),
                            "paginas": paginas_info,
                            "bytes_entrada": len(contenido_bytes),
                            "metodo": "PyMuPDF"
                        }
                    )
                    
                    return {
                        "success": True,
                        "texto": texto,
                        "metodo": "PyMuPDF",
                        "paginas": len(paginas_info),
                        "caracteres": len(texto)
                    }
            except ImportError:
                logger.warning("PyMuPDF no disponible, usando PyPDF2")
            
            # Fallback: PyPDF2
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(BytesIO(contenido_bytes))
                texto = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    texto += page.extract_text() + "\n"
                
                duracion_ms = (time.time() - inicio) * 1000
                self.bitacora.registrar_etapa(
                    "OCR_PDF_PyPDF2",
                    duracion_ms,
                    {
                        "total_caracteres": len(texto),
                        "total_paginas": len(pdf_reader.pages),
                        "metodo": "PyPDF2"
                    }
                )
                
                return {
                    "success": True,
                    "texto": texto,
                    "metodo": "PyPDF2",
                    "paginas": len(pdf_reader.pages),
                    "caracteres": len(texto)
                }
            except ImportError:
                raise Exception("Ni PyMuPDF ni PyPDF2 disponibles")
            
        except Exception as e:
            duracion_ms = (time.time() - inicio) * 1000
            self.bitacora.registrar_etapa(
                "OCR_PDF",
                duracion_ms,
                error=f"{str(e)}\n{type(e).__name__}"
            )
            return {
                "success": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }
    
    def extraer_imagen(self, contenido_bytes: bytes) -> Dict[str, Any]:
        """Extrae texto de imagen con Tesseract OCR."""
        inicio = time.time()
        try:
            import tempfile
            import os
            import pytesseract
            from PIL import Image
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(contenido_bytes)
                tmp.flush()
                
                imagen = Image.open(tmp.name)
                tamaño_imagen = imagen.size
                
                # Extraer texto
                texto = pytesseract.image_to_string(imagen, lang='spa')
                
                # Obtener información de confianza
                datos_detallados = pytesseract.image_to_data(imagen, lang='spa', output_type=pytesseract.Output.DICT)
                confianza_promedio = sum([int(c) for c in datos_detallados['conf'] if int(c) > 0]) / len([c for c in datos_detallados['conf'] if int(c) > 0])
                
                os.unlink(tmp.name)
                
                duracion_ms = (time.time() - inicio) * 1000
                self.bitacora.registrar_etapa(
                    "OCR_Imagen_Tesseract",
                    duracion_ms,
                    {
                        "total_caracteres": len(texto),
                        "tamaño_imagen": tamaño_imagen,
                        "confianza_promedio": round(confianza_promedio, 2),
                        "metodo": "Tesseract_OCR"
                    }
                )
                
                return {
                    "success": True,
                    "texto": texto,
                    "metodo": "Tesseract_OCR",
                    "confianza": round(confianza_promedio, 2),
                    "caracteres": len(texto)
                }
        except Exception as e:
            duracion_ms = (time.time() - inicio) * 1000
            self.bitacora.registrar_etapa(
                "OCR_Imagen",
                duracion_ms,
                error=f"{str(e)}\n{type(e).__name__}"
            )
            return {
                "success": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }


class ProcesadorIASimple:
    """Procesa texto con IA (inicialmente regex, luego será llamada real)."""
    
    def __init__(self, bitacora: ProcesoBitacora):
        self.bitacora = bitacora
        self.prompt_enviado = None
        self.respuesta_ia = None
    
    def procesar_texto(self, texto: str) -> Dict[str, Any]:
        """Procesa texto para extraer datos de factura."""
        inicio = time.time()
        
        # Construir prompt explícito
        prompt = self._construir_prompt(texto)
        self.prompt_enviado = prompt
        
        logger.info(f"📨 Prompt enviado a IA:\n{prompt[:500]}...")
        
        try:
            # Por ahora usar regex simple (luego será reemplazado por llamada real a IA)
            resultado_json = self._extraer_json_con_regex(texto)
            
            duracion_ms = (time.time() - inicio) * 1000
            self.bitacora.registrar_etapa(
                "Procesamiento_IA",
                duracion_ms,
                {
                    "prompt_caracteres": len(prompt),
                    "respuesta_caracteres": len(json.dumps(resultado_json)),
                    "modelo": "regex_simple",
                    "tokens_aproximados": len(prompt.split()) + len(json.dumps(resultado_json).split())
                }
            )
            
            self.respuesta_ia = resultado_json
            return {
                "success": True,
                "datos": resultado_json,
                "prompt": prompt,
                "modelo": "regex_simple",
                "duracion_ms": duracion_ms
            }
        except Exception as e:
            duracion_ms = (time.time() - inicio) * 1000
            self.bitacora.registrar_etapa(
                "Procesamiento_IA",
                duracion_ms,
                error=f"{str(e)}\n{type(e).__name__}"
            )
            return {
                "success": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }
    
    def _construir_prompt(self, texto: str) -> str:
        """Construye el prompt enviado a IA."""
        prompt = f"""Analiza el siguiente texto OCR de una factura y extrae los datos en formato JSON.

INSTRUCCIONES:
- Extrae ÚNICAMENTE del texto proporcionado
- NO inventes datos
- Si un dato no está disponible, usa null
- Devuelve SOLO el JSON, sin explicaciones adicionales

TEXTO OCR:
{texto}

FORMATO JSON ESPERADO:
{{
  "numero_factura": "string",
  "fecha": "YYYY-MM-DD",
  "proveedor": "string",
  "cif": "string",
  "base_imponible": number,
  "iva": number,
  "total": number,
  "lineas": []
}}

Responde con el JSON completo."""
        return prompt
    
    def _extraer_json_con_regex(self, texto: str) -> Dict[str, Any]:
        """Extrae datos con patrones regex (versión actual)."""
        datos = {
            "numero_factura": None,
            "fecha": None,
            "proveedor": None,
            "cif": None,
            "base_imponible": None,
            "iva": None,
            "total": None,
            "lineas": []
        }
        
        # Número de factura - ORDEN IMPORTANTE: de más específico a más genérico
        patterns = [
            # Patrón 1: "Factura n.° XYZ" o "Factura n.º XYZ" (MÁS ESPECÍFICO)
            (r"[Ff]actura\s+n[.°º]+\s*([A-Z]{0,3}\d{5,10})", "específico con símbolo"),
            # Patrón 2: "Factura n. XYZ" o "Factura n XYZ"  
            (r"[Ff]actura\s+n\.?\s+([A-Z]{0,3}\d{5,10})", "específico con punto"),
            # Patrón 3: Fallback a "Factura número" o "Factura nº"
            (r"[Ff]actura\s+(?:número|nº)\s*([A-Z]*\d{5,10})", "con palabra número"),
            # Patrón 4: Último recurso genérico
            (r"[Ff]actura[:\s]+([A-Z0-9]{5,15})", "genérico")
        ]
        
        for pattern, estrategia in patterns:
            match = re.search(pattern, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                numero = match.group(1).strip()
                numero = re.sub(r'[^\w]', '', numero)
                if numero and len(numero) >= 5:
                    datos["numero_factura"] = numero
                    logger.debug(f"📋 Número de factura capturado ({estrategia}): {numero}")
                    break
        
        # Proveedor
        match = re.search(
            r"^([A-Z\s,\.\-]+?(?:S\.?L\.?|S\.?A\.?|LTDA|UNIPERSONAL|LLC|CORP))",
            texto, re.MULTILINE
        )
        if match:
            datos["proveedor"] = match.group(1).strip()[:150]
        
        # Fecha - múltiples formatos
        match = re.search(
            r"(\d{1,2})\s+de\s+([Ee]nero|[Ff]ebrero|[Mm]arzo|[Aa]bril|[Mm]ayo|[Jj]unio|[Jj]ulio|[Aa]gosto|[Ss]eptiembre|[Oo]ctubre|[Nn]oviembre|[Dd]iciembre)[^0-9]*(\d{4})",
            texto
        )
        if match:
            meses = {
                "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
                "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
            }
            mes_nombre = match.group(2).lower()
            mes_num = meses.get(mes_nombre, 1)
            try:
                from datetime import date
                datos["fecha"] = date(int(match.group(3)), mes_num, int(match.group(1))).isoformat()
            except:
                pass
        
        # Total
        match = re.search(
            r"(?:TOTAL\s+EUROS|TOTAL|[Tt]otal)[:\s\.\-]*(\d+[.,]\d{2})",
            texto, re.IGNORECASE
        )
        if match:
            cantidad = match.group(1).replace(",", ".")
            try:
                datos["total"] = float(cantidad)
            except:
                pass
        
        # IVA - suma todos
        iva_matches = re.findall(
            r"(?:I\.?V\.?A\.?|IVA)[:\s]*[\d,\.]+\s*%[:\s\.\-]*(\d+[.,]\d{2})",
            texto, re.IGNORECASE
        )
        if iva_matches:
            iva_total = 0.0
            for iva_str in iva_matches:
                try:
                    iva_total += float(iva_str.replace(",", "."))
                except:
                    pass
            if iva_total > 0:
                datos["iva"] = iva_total
        
        # Base imponible - suma todos
        base_matches = re.findall(
            r"Base(?:\s+(?:impon\w*|al))?\s*[\d,\.]*\s*%?[:\s\.\-]*(\d+[.,]\d{2})",
            texto, re.IGNORECASE
        )
        if base_matches:
            base_total = 0.0
            for base_str in base_matches:
                try:
                    base_total += float(base_str.replace(",", "."))
                except:
                    pass
            if base_total > 0:
                datos["base_imponible"] = base_total
        
        return datos


class ValidadorDatos:
    """Valida los datos extraídos."""
    
    def __init__(self, bitacora: ProcesoBitacora):
        self.bitacora = bitacora
    
    def validar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Valida completitud y consistencia de datos."""
        inicio = time.time()
        
        validacion = {
            "campos_completos": {},
            "errores": [],
            "advertencias": [],
            "puntuacion_confianza": 0
        }
        
        campos_requeridos = ["numero_factura", "fecha", "proveedor", "total"]
        campos_opcionales = ["cif", "base_imponible", "iva"]
        
        # Validar campos requeridos
        for campo in campos_requeridos:
            valor = datos.get(campo)
            completado = valor is not None and valor != ""
            validacion["campos_completos"][campo] = completado
            
            if not completado:
                validacion["errores"].append(f"Campo requerido '{campo}' falta")
        
        # Validar campos opcionales
        for campo in campos_opcionales:
            valor = datos.get(campo)
            validacion["campos_completos"][campo] = valor is not None and valor != ""
        
        # Validaciones lógicas
        if datos.get("base_imponible") and datos.get("iva") and datos.get("total"):
            total_calculado = float(datos["base_imponible"]) + float(datos["iva"])
            total_real = float(datos["total"])
            if abs(total_calculado - total_real) > 0.01:
                validacion["advertencias"].append(
                    f"Total inconsistente: Base({datos['base_imponible']}) + IVA({datos['iva']}) = {total_calculado}, pero Total = {total_real}"
                )
        
        # Calcular puntuación de confianza
        campos_completos = sum(1 for v in validacion["campos_completos"].values() if v)
        puntuacion = (campos_completos / (len(campos_requeridos) + len(campos_opcionales))) * 100
        validacion["puntuacion_confianza"] = round(puntuacion, 1)
        
        duracion_ms = (time.time() - inicio) * 1000
        self.bitacora.registrar_etapa(
            "Validacion_Datos",
            duracion_ms,
            {
                "campos_completos": campos_completos,
                "campos_totales": len(campos_requeridos) + len(campos_opcionales),
                "confianza": validacion["puntuacion_confianza"],
                "errores": len(validacion["errores"]),
                "advertencias": len(validacion["advertencias"])
            }
        )
        
        return validacion


class OrquestadorProcesamiento:
    """Orquesta todo el flujo de procesamiento transparente."""
    
    def __init__(self, archivo_nombre: str, contenido_bytes: bytes, tipo_archivo: str):
        self.archivo_nombre = archivo_nombre
        self.contenido_bytes = contenido_bytes
        self.tipo_archivo = tipo_archivo
        self.bitacora = ProcesoBitacora(archivo_nombre)
    
    def procesar(self) -> Dict[str, Any]:
        """Ejecuta el flujo completo de procesamiento."""
        logger.info(f"🚀 Iniciando procesamiento transparente de {self.archivo_nombre}")
        
        # 1. Extraer texto
        extractor = ExtractorTextoOCR(self.bitacora)
        if self.tipo_archivo == "pdf":
            resultado_ocr = extractor.extraer_pdf(self.contenido_bytes)
        else:
            resultado_ocr = extractor.extraer_imagen(self.contenido_bytes)
        
        if not resultado_ocr.get("success"):
            return {
                "success": False,
                "error": resultado_ocr.get("error"),
                "bitacora": self.bitacora.resumen()
            }
        
        texto_extraido = resultado_ocr["texto"]
        
        # 2. Procesar con IA
        procesador_ia = ProcesadorIASimple(self.bitacora)
        resultado_ia = procesador_ia.procesar_texto(texto_extraido)
        
        if not resultado_ia.get("success"):
            return {
                "success": False,
                "error": resultado_ia.get("error"),
                "bitacora": self.bitacora.resumen()
            }
        
        datos_extraidos = resultado_ia["datos"]
        
        # 3. Validar
        validador = ValidadorDatos(self.bitacora)
        validacion = validador.validar(datos_extraidos)
        
        # Respuesta final completa
        return {
            "success": True,
            "archivo": self.archivo_nombre,
            "ocr": {
                "metodo": resultado_ocr["metodo"],
                "texto": texto_extraido,
                "caracteres": resultado_ocr["caracteres"],
                "paginas": resultado_ocr.get("paginas"),
                "duracion_ms": resultado_ocr.get("duracion_ms", 0)
            },
            "ia": {
                "modelo": resultado_ia["modelo"],
                "prompt": resultado_ia["prompt"],
                "datos_extraidos": datos_extraidos,
                "duracion_ms": resultado_ia["duracion_ms"]
            },
            "validacion": validacion,
            "bitacora": self.bitacora.resumen()
        }
