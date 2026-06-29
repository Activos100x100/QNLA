"""
Servicio de Inteligencia Artificial para procesamiento de facturas.
Utiliza OpenAI API para convertir texto extraído en datos estructurados.
Incluye mejora continua usando correcciones del usuario.
"""

import json
import logging
from typing import Optional, Dict, Any
import re
from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.factura_schemas import DatosExtraidos

logger = logging.getLogger(__name__)


class AIService:
    """
    Servicio de IA para procesar texto OCR y convertirlo en datos estructurados.
    Utiliza GPT para entender y extraer información de facturas españolas.
    Mejora continuamente usando retroalimentación del usuario.
    """
    
    def __init__(self, learning_service=None):
        """
        Inicializa el cliente de OpenAI.
        
        Args:
            learning_service: Instancia del LearningService (opcional)
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.modelo = "gpt-4-turbo-preview"  # Usar modelo más potente si está disponible
        self.learning_service = learning_service
        logger.info("AIService inicializado")
    
    def extraer_datos_factura(
        self,
        texto_ocr: str,
        db: Session = None,
        proveedor_id: int = None
    ) -> Dict[str, Any]:
        """
        Extrae datos estructurados de un texto OCR de factura.
        Usa aprendizaje previo si está disponible.
        
        Args:
            texto_ocr: Texto completo extraído por OCR de la factura
            db: Sesión de base de datos (opcional, para acceder a aprendizaje)
            proveedor_id: ID del proveedor (opcional, para obtener contexto de aprendizaje)
            
        Returns:
            Diccionario con datos estructurados de la factura
            
        Raises:
            ValueError: Si la respuesta de OpenAI no es un JSON válido
            Exception: Error en la comunicación con OpenAI
        """
        try:
            logger.info("Iniciando extracción de datos de factura con IA")
            
            # Crear el prompt (con contexto de aprendizaje si está disponible)
            prompt = self._crear_prompt_extraccion(
                texto_ocr,
                db=db,
                proveedor_id=proveedor_id
            )
            
            # Llamar a OpenAI
            logger.debug("Enviando solicitud a OpenAI")
            respuesta = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en procesamiento de facturas españolas. "
                                 "Debes extraer la información y retornar SOLO un JSON válido, "
                                 "sin texto adicional, explicaciones o markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Baja temperatura para respuestas más consistentes
                max_tokens=2000
            )
            
            # Extraer el contenido
            contenido = respuesta.choices[0].message.content.strip()
            logger.debug(f"Respuesta recibida de OpenAI (primeros 500 caracteres): {contenido[:500]}")
            
            # Limpiar la respuesta (por si contiene markdown)
            contenido_limpio = self._limpiar_respuesta_json(contenido)
            
            # Parsear JSON
            datos = json.loads(contenido_limpio)
            logger.info("Datos extraídos exitosamente")
            
            return datos
            
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON de OpenAI: {str(e)}")
            logger.error(f"Contenido recibido: {contenido}")
            raise ValueError(f"Respuesta de OpenAI no es JSON válido: {str(e)}")
        except Exception as e:
            logger.error(f"Error en extracción de datos con IA: {str(e)}")
            raise
    
    def _construir_prompt_extraccion(self, texto_ocr: str) -> str:
        """Construye el prompt para extracción de datos."""
        prompt = f"""
Analiza el siguiente texto OCR de una factura española y extrae TODOS los datos en formato JSON válido.
Para CADA CAMPO, proporciona el valor y un nivel de confianza (0-100).

TEXTO OCR DE LA FACTURA:
{texto_ocr}

Retorna EXCLUSIVAMENTE un JSON válido (sin markdown, sin explicaciones) con esta estructura exacta:
{{
    "proveedor": {{
        "nombre": {{"valor": "nombre del proveedor", "confianza": 95}},
        "cif": {{"valor": "CIF del proveedor", "confianza": 90}},
        "direccion": {{"valor": "dirección completa", "confianza": 85}},
        "telefono": {{"valor": "teléfono", "confianza": 70}},
        "email": {{"valor": "email", "confianza": 80}}
    }},
    "cliente": {{
        "nombre": {{"valor": "nombre del cliente", "confianza": 98}},
        "cif": {{"valor": "CIF del cliente", "confianza": 95}}
    }},
    "factura": {{
        "numero": {{"valor": "número de factura", "confianza": 99}},
        "serie": {{"valor": "serie si existe", "confianza": 85}},
        "fecha": {{"valor": "YYYY-MM-DD", "confianza": 95}},
        "fecha_vencimiento": {{"valor": "YYYY-MM-DD", "confianza": 80}},
        "base_imponible": {{"valor": número decimal, "confianza": 90}},
        "iva": {{"valor": número decimal, "confianza": 92}},
        "tipo_iva": {{"valor": "porcentaje como string (ej: 21%)", "confianza": 98}},
        "irpf": {{"valor": número decimal, "confianza": 70}},
        "total": {{"valor": número decimal, "confianza": 95}},
        "forma_pago": {{"valor": "método de pago", "confianza": 75}},
        "iban": {{"valor": "IBAN", "confianza": 85}},
        "observaciones": {{"valor": "notas o conceptos especiales", "confianza": 60}}
    }},
    "lineas": [
        {{
            "descripcion": {{"valor": "descripción del concepto", "confianza": 92}},
            "cantidad": {{"valor": número decimal, "confianza": 95}},
            "precio_unitario": {{"valor": número decimal, "confianza": 90}},
            "tipo_iva": {{"valor": "porcentaje", "confianza": 88}},
            "total": {{"valor": número decimal, "confianza": 92}}
        }}
    ]
}}

INSTRUCCIONES CRÍTICAS SOBRE CONFIANZA:
1. La confianza debe ser un número entero de 0 a 100
2. 100 = Completamente seguro (datos muy claros)
3. 85-99 = Muy confiable (datos claros, posibles pequeños errores OCR)
4. 70-84 = Moderadamente confiable (datos parcialmente legibles)
5. 50-69 = Baja confianza (datos muy borrosos o ambiguos)
6. < 50 = Si el valor es null, confianza 0; si existe pero muy incierto, usa valor nulo
7. Si un campo no existe en el documento, usa null como valor y 0 como confianza

INSTRUCCIONES SOBRE VALORES:
1. Si un campo no existe, usa null
2. Los números decimales usan punto (.) como separador
3. Las fechas en formato ISO 8601 (YYYY-MM-DD)
4. El IVA como número decimal (ej: 21.00 para 21%)
5. Mantén los porcentajes como string con el símbolo % (ej: "21%")
6. Retorna SOLAMENTE JSON válido, sin explicaciones
7. Si es factura múltiple, lista todas las líneas
8. Extrae cualquier información que puedas

EVALUACIÓN DE CONFIANZA:
- Texto OCR claro = confianza alta (85-100)
- Números borrosos = confianza moderada (70-84)
- Texto ilegible = baja confianza o null (< 70)
- Campos ausentes = null con confianza 0
"""
        return prompt
    
    def _limpiar_respuesta_json(self, respuesta: str) -> str:
        """
        Limpia la respuesta de OpenAI eliminando markdown u otros caracteres.
        
        Args:
            respuesta: Respuesta original de OpenAI
            
        Returns:
            Respuesta limpiada lista para parsear
        """
        # Eliminar bloques de código markdown
        if respuesta.startswith("```"):
            # Eliminar ``` al inicio
            respuesta = respuesta.lstrip("`")
            # Eliminar json o json.
            respuesta = re.sub(r'^json\s*', '', respuesta, flags=re.IGNORECASE)
        
        if respuesta.endswith("```"):
            respuesta = respuesta.rstrip("`")
        
        # Eliminar espacios en blanco al inicio y final
        respuesta = respuesta.strip()
        
        return respuesta
    
    def validar_datos_extraidos(self, datos: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Valida los datos extraídos según reglas de negocio.
        
        Args:
            datos: Diccionario con datos extraídos
            
        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errores = []
        
        try:
            # Validar estructura básica
            if not datos.get("proveedor"):
                errores.append("Falta información del proveedor")
            
            if not datos.get("cliente"):
                errores.append("Falta información del cliente")
            
            if not datos.get("factura"):
                errores.append("Falta información de la factura")
            
            # Validar factura
            factura = datos.get("factura", {})
            if not factura.get("numero"):
                errores.append("Falta número de factura")
            
            if not factura.get("fecha"):
                errores.append("Falta fecha de factura")
            
            if factura.get("total") is None or factura.get("total") == 0:
                errores.append("Total de factura inválido o cero")
            
            # Validar líneas
            lineas = datos.get("lineas", [])
            if not lineas:
                errores.append("No se encontraron líneas de factura")
            
            for idx, linea in enumerate(lineas):
                if not linea.get("descripcion"):
                    errores.append(f"Línea {idx + 1}: descripción vacía")
                if linea.get("cantidad") is None or linea.get("cantidad") <= 0:
                    errores.append(f"Línea {idx + 1}: cantidad inválida")
                if linea.get("precio_unitario") is None or linea.get("precio_unitario") < 0:
                    errores.append(f"Línea {idx + 1}: precio unitario inválido")
            
            return len(errores) == 0, errores
            
        except Exception as e:
            logger.error(f"Error en validación de datos: {str(e)}")
            return False, [f"Error en validación: {str(e)}"]
    
    def extraer_campos_bajo_confianza(self, datos_con_confianza: Dict[str, Any], umbral: int = 85) -> tuple[bool, List[dict]]:
        """
        Analiza los datos extraídos y retorna campos con confianza baja.
        
        Args:
            datos_con_confianza: Diccionario con estructura de confianza
            umbral: Umbral mínimo de confianza (default 85%)
            
        Returns:
            Tupla (tiene_bajo_confianza, lista_de_campos_bajo_confianza)
        """
        campos_bajo_confianza = []
        
        try:
            # Procesar proveedor
            proveedor = datos_con_confianza.get("proveedor", {})
            for campo, dato in proveedor.items():
                if isinstance(dato, dict) and "confianza" in dato:
                    confianza = dato["confianza"]
                    if confianza < umbral and dato.get("valor") is not None:
                        campos_bajo_confianza.append({
                            "categoria": "proveedor",
                            "campo": campo,
                            "valor": dato.get("valor"),
                            "confianza": confianza
                        })
            
            # Procesar cliente
            cliente = datos_con_confianza.get("cliente", {})
            for campo, dato in cliente.items():
                if isinstance(dato, dict) and "confianza" in dato:
                    confianza = dato["confianza"]
                    if confianza < umbral and dato.get("valor") is not None:
                        campos_bajo_confianza.append({
                            "categoria": "cliente",
                            "campo": campo,
                            "valor": dato.get("valor"),
                            "confianza": confianza
                        })
            
            # Procesar factura
            factura = datos_con_confianza.get("factura", {})
            for campo, dato in factura.items():
                if isinstance(dato, dict) and "confianza" in dato:
                    confianza = dato["confianza"]
                    if confianza < umbral and dato.get("valor") is not None:
                        campos_bajo_confianza.append({
                            "categoria": "factura",
                            "campo": campo,
                            "valor": dato.get("valor"),
                            "confianza": confianza
                        })
            
            # Procesar líneas
            lineas = datos_con_confianza.get("lineas", [])
            for idx, linea in enumerate(lineas):
                for campo, dato in linea.items():
                    if isinstance(dato, dict) and "confianza" in dato:
                        confianza = dato["confianza"]
                        if confianza < umbral and dato.get("valor") is not None:
                            campos_bajo_confianza.append({
                                "categoria": f"linea_{idx + 1}",
                                "campo": campo,
                                "valor": dato.get("valor"),
                                "confianza": confianza
                            })
            
            tiene_bajo_confianza = len(campos_bajo_confianza) > 0
            logger.info(f"Campos bajo confianza encontrados: {len(campos_bajo_confianza)}")
            
            return tiene_bajo_confianza, campos_bajo_confianza
            
        except Exception as e:
            logger.error(f"Error analizando confianza: {str(e)}")
            return False, []
    
    def calcular_confianza_promedio(self, datos_con_confianza: Dict[str, Any]) -> float:
        """
        Calcula el nivel promedio de confianza de todos los campos.
        
        Args:
            datos_con_confianza: Diccionario con estructura de confianza
            
        Returns:
            Porcentaje promedio de confianza (0-100)
        """
        try:
            valores_confianza = []
            
            # Extraer todas las confianzas
            def extraer_confianzas(obj):
                if isinstance(obj, dict):
                    for valor in obj.values():
                        if isinstance(valor, dict) and "confianza" in valor:
                            valores_confianza.append(valor["confianza"])
                        elif isinstance(valor, (list, dict)):
                            extraer_confianzas(valor)
                elif isinstance(obj, list):
                    for item in obj:
                        extraer_confianzas(item)
            
            extraer_confianzas(datos_con_confianza)
            
            if not valores_confianza:
                return 100.0
            
            promedio = sum(valores_confianza) / len(valores_confianza)
            logger.info(f"Confianza promedio: {promedio:.2f}%")
            
            return round(promedio, 2)
            
        except Exception as e:
            logger.error(f"Error calculando confianza promedio: {str(e)}")
            return 100.0
    
    def extraer_valores_de_confianza(self, datos_con_confianza: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae solo los valores (sin confianza) de la respuesta de IA.
        Convierte de formato con confianza a formato sin confianza.
        
        Args:
            datos_con_confianza: Diccionario con estructura de confianza
            
        Returns:
            Diccionario con solo valores
        """
        def extraer_valores(obj):
            if isinstance(obj, dict):
                resultado = {}
                for clave, valor in obj.items():
                    if isinstance(valor, dict):
                        if "valor" in valor and "confianza" in valor:
                            # Es un campo con confianza
                            resultado[clave] = valor["valor"]
                        else:
                            # Es un objeto anidado
                            resultado[clave] = extraer_valores(valor)
                    elif isinstance(valor, list):
                        resultado[clave] = [extraer_valores(item) if isinstance(item, dict) else item for item in valor]
                    else:
                        resultado[clave] = valor
                return resultado
            elif isinstance(obj, list):
                return [extraer_valores(item) if isinstance(item, dict) else item for item in obj]
            else:
                return obj
        
        return extraer_valores(datos_con_confianza)
    
    def mejorar_datos(self, datos, contexto=None):
        """
        Mejora o corrige datos extraídos usando IA.
        Útil para casos donde falta información o hay inconsistencias.
        
        Args:
            datos: Datos extraídos originales
            contexto: Información adicional de contexto
            
        Returns:
            Datos mejorados
        """
        try:
            logger.info("Mejorando datos de factura con IA")
            
            prompt = f"""
Analiza los siguientes datos extraídos de una factura y mejóralos:

DATOS ACTUALES:
{json.dumps(datos, ensure_ascii=False, indent=2)}

{('CONTEXTO ADICIONAL: ' + contexto) if contexto else ''}

Retorna los mismos datos mejorados en JSON. Intenta:
1. Completar campos null con información relacionada
2. Corregir formatos (fechas, números)
3. Limpiar espacios en blanco extra
4. Validar coherencia entre campos (ej: total debe ser suma de líneas)

Retorna SOLAMENTE JSON válido.
"""
            
            respuesta = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de facturas. Mejora los datos manteniendo la estructura JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            contenido = respuesta.choices[0].message.content.strip()
            contenido_limpio = self._limpiar_respuesta_json(contenido)
            datos_mejorados = json.loads(contenido_limpio)
            
            logger.info("Datos mejorados exitosamente")
            return datos_mejorados
            
        except Exception as e:
            logger.error(f"Error mejorando datos: {str(e)}")
            # Si hay error, retornar los datos originales
            return datos
