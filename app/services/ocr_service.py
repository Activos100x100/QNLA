"""
Servicio de OCR para procesar imágenes y PDFs.
Utiliza PaddleOCR para la extracción de texto de documentos.
"""

import logging
from pathlib import Path
from typing import List, Optional
import cv2
import numpy as np
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from PIL import Image
import io

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    Servicio para procesamiento OCR de documentos.
    Maneja PDFs, imágenes JPEG y PNG.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de OCR con PaddleOCR.
        use_gpu se configura desde variables de entorno.
        """
        self.use_gpu = settings.paddle_use_gpu
        # PaddleOCR inicializado lentamente - comentado por ahora
        # self.ocr = PaddleOCR(
        #     use_angle_cls=True,
        #     lang='es',
        #     use_gpu=self.use_gpu
        # )
        self.ocr = None
        logger.info(f"OCRService inicializado (lazy loading). GPU: {self.use_gpu}")
    
    def procesar_pdf(self, ruta_pdf: str) -> str:
        """
        Convierte un PDF a imágenes y extrae todo el texto.
        
        Args:
            ruta_pdf: Ruta al archivo PDF
            
        Returns:
            Texto completo extraído del PDF
            
        Raises:
            ValueError: Si el archivo no es válido
            Exception: Error durante la conversión o OCR
        """
        try:
            logger.info(f"Procesando PDF: {ruta_pdf}")
            
            # Validar que existe el archivo
            if not Path(ruta_pdf).exists():
                raise ValueError(f"Archivo PDF no encontrado: {ruta_pdf}")
            
            # Convertir PDF a imágenes
            imagenes = convert_from_path(ruta_pdf, dpi=300)
            logger.info(f"PDF convertido a {len(imagenes)} imágenes")
            
            # Procesar cada imagen
            texto_completo = ""
            for idx, imagen in enumerate(imagenes):
                logger.debug(f"Procesando página {idx + 1}/{len(imagenes)}")
                texto = self._procesar_imagen(imagen)
                texto_completo += f"\n--- PÁGINA {idx + 1} ---\n{texto}"
            
            logger.info(f"OCR completado. Palabras extraídas: {len(texto_completo.split())}")
            return texto_completo
            
        except Exception as e:
            logger.error(f"Error al procesar PDF: {str(e)}")
            raise
    
    def procesar_imagen(self, ruta_imagen: str) -> str:
        """
        Extrae texto de una imagen.
        
        Args:
            ruta_imagen: Ruta al archivo de imagen
            
        Returns:
            Texto extraído de la imagen
            
        Raises:
            ValueError: Si el archivo no es válido
            Exception: Error durante OCR
        """
        try:
            logger.info(f"Procesando imagen: {ruta_imagen}")
            
            if not Path(ruta_imagen).exists():
                raise ValueError(f"Archivo de imagen no encontrado: {ruta_imagen}")
            
            # Abrir la imagen
            imagen = Image.open(ruta_imagen)
            
            # Convertir a RGB si es necesario
            if imagen.mode != 'RGB':
                imagen = imagen.convert('RGB')
            
            texto = self._procesar_imagen(imagen)
            logger.info(f"OCR completado. Palabras extraídas: {len(texto.split())}")
            return texto
            
        except Exception as e:
            logger.error(f"Error al procesar imagen: {str(e)}")
            raise
    
    def _procesar_imagen(self, imagen: Image.Image) -> str:
        """
        Realiza OCR en una imagen PIL.
        
        Args:
            imagen: Objeto PIL Image
            
        Returns:
            Texto extraído
        """
        try:
            # Convertir PIL Image a array numpy
            imagen_array = np.array(imagen)
            
            # Si es RGB, convertir a BGR para OpenCV
            if len(imagen_array.shape) == 3 and imagen_array.shape[2] == 3:
                imagen_array = cv2.cvtColor(imagen_array, cv2.COLOR_RGB2BGR)
            
            # Ejecutar OCR
            resultado = self.ocr.ocr(imagen_array, cls=True)
            
            # Extraer texto ordenado
            texto = self._extraer_texto_ordenado(resultado)
            return texto
            
        except Exception as e:
            logger.error(f"Error en OCR de imagen: {str(e)}")
            raise
    
    def _extraer_texto_ordenado(self, resultado: List) -> str:
        """
        Extrae el texto del resultado de PaddleOCR manteniendo el orden.
        
        Args:
            resultado: Resultado del OCR de PaddleOCR
            
        Returns:
            Texto ordenado y formateado
        """
        if not resultado or not resultado[0]:
            return ""
        
        # Ordenar por posición vertical (y) y luego horizontal (x)
        lineas = []
        for linea in resultado[0]:
            bbox, (texto, confianza) = linea
            # bbox contiene las 4 esquinas del rectángulo
            # Usar el punto superior izquierdo para ordenar
            y = bbox[0][1]
            lineas.append((y, texto))
        
        # Ordenar por posición vertical
        lineas.sort(key=lambda x: x[0])
        
        # Extraer solo el texto
        texto_final = "\n".join([linea[1] for linea in lineas])
        return texto_final
    
    def procesar_archivo(self, ruta_archivo: str) -> str:
        """
        Procesa automáticamente el archivo detectando el tipo.
        
        Args:
            ruta_archivo: Ruta al archivo
            
        Returns:
            Texto extraído
            
        Raises:
            ValueError: Si el tipo de archivo no es soportado
        """
        ruta = Path(ruta_archivo)
        extension = ruta.suffix.lower()
        
        if extension == '.pdf':
            return self.procesar_pdf(ruta_archivo)
        elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            return self.procesar_imagen(ruta_archivo)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {extension}")
    
    def optimizar_imagen(self, ruta_imagen: str, output_ruta: Optional[str] = None) -> str:
        """
        Optimiza una imagen para mejorar resultados del OCR.
        Aplica técnicas de preprocesamiento: contraste, brillo, binarización.
        
        Args:
            ruta_imagen: Ruta a la imagen original
            output_ruta: Ruta donde guardar la imagen optimizada
            
        Returns:
            Ruta de la imagen optimizada
        """
        try:
            logger.info(f"Optimizando imagen: {ruta_imagen}")
            
            # Leer la imagen
            img = cv2.imread(ruta_imagen)
            if img is None:
                raise ValueError(f"No se pudo leer la imagen: {ruta_imagen}")
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Aplicar CLAHE para mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Aplicar denoising
            denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10)
            
            # Aplicar binarización adaptativa
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Guardar la imagen optimizada
            if output_ruta is None:
                output_ruta = str(Path(ruta_imagen).parent / f"optimized_{Path(ruta_imagen).name}")
            
            cv2.imwrite(output_ruta, binary)
            logger.info(f"Imagen optimizada guardada en: {output_ruta}")
            
            return output_ruta
            
        except Exception as e:
            logger.error(f"Error al optimizar imagen: {str(e)}")
            raise
