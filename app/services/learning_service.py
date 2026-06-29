"""
Servicio de aprendizaje automático para mejora continua de extracción.
Registra correcciones y las usa para mejorar futuras extracciones.
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

# Importaciones FTRA - comentadas temporalmente
# from app.ftra.models import CorreccionAprendizaje, Proveedor, Factura
from app.config import settings

logger = logging.getLogger(__name__)


class LearningService:
    """
    Servicio para gestionar el aprendizaje del sistema basado en retroalimentación del usuario.
    
    Funciones principales:
    - Registrar correcciones realizadas por usuarios
    - Analizar patrones frecuentes de errores
    - Proporcionar contexto histórico para mejorar extracciones futuras
    - Actualizar confianza basada en aciertos/errores
    """
    
    def registrar_correccion(
        self,
        db: Session,
        factura_id: int,
        proveedor_id: int,
        campo_nombre: str,
        categoria: str,
        valor_extraido: str,
        valor_correcto: str,
        confianza_original: int = 0
    ) -> CorreccionAprendizaje:
        """
        Registra una corrección realizada por el usuario.
        
        Args:
            db: Sesión de base de datos
            factura_id: ID de la factura corregida
            proveedor_id: ID del proveedor
            campo_nombre: Nombre del campo que se corrigió (ej: "cif", "direccion")
            categoria: Categoría del campo (ej: "proveedor", "cliente", "factura")
            valor_extraido: Valor que la IA extrajo
            valor_correcto: Valor correcto según el usuario
            confianza_original: Confianza que tenía la IA en ese valor
            
        Returns:
            Objeto CorreccionAprendizaje creado
        """
        try:
            # Verificar si ya existe una corrección similar para este proveedor/campo
            correccion_existente = db.query(CorreccionAprendizaje).filter(
                and_(
                    CorreccionAprendizaje.proveedor_id == proveedor_id,
                    CorreccionAprendizaje.campo_nombre == campo_nombre,
                    CorreccionAprendizaje.valor_extraido == valor_extraido
                )
            ).first()
            
            if correccion_existente:
                # Incrementar contador
                correccion_existente.veces_ocurrido += 1
                if correccion_existente.veces_ocurrido >= 3:
                    correccion_existente.es_patron_frecuente = True
                db.commit()
                logger.info(
                    f"Corrección actualizada: {proveedor_id}/{campo_nombre} "
                    f"(ocurrencias: {correccion_existente.veces_ocurrido})"
                )
                return correccion_existente
            
            # Crear nueva corrección
            correccion = CorreccionAprendizaje(
                factura_id=factura_id,
                proveedor_id=proveedor_id,
                campo_nombre=campo_nombre,
                categoria=categoria,
                valor_extraido=valor_extraido,
                valor_correcto=valor_correcto,
                confianza_original=confianza_original,
                veces_ocurrido=1,
                es_patron_frecuente=False  # Se marca en True cuando ocurra 3+ veces
            )
            db.add(correccion)
            db.commit()
            
            logger.info(
                f"Corrección registrada: {proveedor_id}/{campo_nombre} "
                f"'{valor_extraido}' → '{valor_correcto}'"
            )
            return correccion
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error registrando corrección: {str(e)}")
            raise
    
    def obtener_correcciones_proveedor(
        self,
        db: Session,
        proveedor_id: int,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las correcciones registradas para un proveedor.
        Útil para mejorar extracciones futuras del mismo proveedor.
        
        Args:
            db: Sesión de base de datos
            proveedor_id: ID del proveedor
            limite: Máximo número de correcciones a retornar
            
        Returns:
            Lista de correcciones con formato dict
        """
        try:
            correcciones = db.query(CorreccionAprendizaje).filter(
                CorreccionAprendizaje.proveedor_id == proveedor_id
            ).order_by(
                CorreccionAprendizaje.veces_ocurrido.desc(),
                CorreccionAprendizaje.created_at.desc()
            ).limit(limite).all()
            
            resultado = []
            for c in correcciones:
                resultado.append({
                    "campo": c.campo_nombre,
                    "categoria": c.categoria,
                    "valor_incorrecto": c.valor_extraido,
                    "valor_correcto": c.valor_correcto,
                    "confianza_original": c.confianza_original,
                    "veces_ocurrido": c.veces_ocurrido,
                    "es_patron": c.es_patron_frecuente
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo correcciones: {str(e)}")
            return []
    
    def obtener_correcciones_frecuentes(
        self,
        db: Session,
        proveedor_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene solo las correcciones que se repiten frecuentemente.
        Estas son los patrones que definitivamente deberían considerarse.
        
        Args:
            db: Sesión de base de datos
            proveedor_id: ID del proveedor
            
        Returns:
            Lista de correcciones frecuentes
        """
        try:
            correcciones = db.query(CorreccionAprendizaje).filter(
                and_(
                    CorreccionAprendizaje.proveedor_id == proveedor_id,
                    CorreccionAprendizaje.es_patron_frecuente == True
                )
            ).order_by(
                CorreccionAprendizaje.veces_ocurrido.desc()
            ).all()
            
            resultado = []
            for c in correcciones:
                resultado.append({
                    "campo": c.campo_nombre,
                    "categoria": c.categoria,
                    "patron_incorrecto": c.valor_extraido,
                    "patron_correcto": c.valor_correcto,
                    "confianza_original": c.confianza_original,
                    "veces_ocurrido": c.veces_ocurrido
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo correcciones frecuentes: {str(e)}")
            return []
    
    def generar_contexto_aprendizaje(
        self,
        db: Session,
        proveedor_id: int
    ) -> str:
        """
        Genera un contexto de texto para incluir en el prompt de la IA.
        Incluye correcciones frecuentes y patrones aprendidos.
        
        Args:
            db: Sesión de base de datos
            proveedor_id: ID del proveedor
            
        Returns:
            Texto con contexto para el prompt (cadena vacía si no hay aprendizaje)
        """
        try:
            # Obtener proveedor
            proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
            if not proveedor:
                return ""
            
            # Obtener correcciones frecuentes
            correcciones_frecuentes = self.obtener_correcciones_frecuentes(db, proveedor_id)
            if not correcciones_frecuentes:
                return ""
            
            # Generar contexto
            contexto = f"\n\n📚 CONTEXTO DE APRENDIZAJE - Proveedor: {proveedor.nombre}\n"
            contexto += "Errores frecuentes corregidos previamente (usa estos patrones correctos):\n"
            
            for i, corr in enumerate(correcciones_frecuentes, 1):
                contexto += f"\n{i}. Campo: {corr['categoria']}.{corr['campo']}\n"
                contexto += f"   ❌ Patrón incorrecto: '{corr['patron_incorrecto']}'\n"
                contexto += f"   ✅ Patrón correcto: '{corr['patron_correcto']}'\n"
                contexto += f"   (Ocurrió {corr['veces_ocurrido']} veces, confianza original: {corr['confianza_original']}%)\n"
            
            return contexto
            
        except Exception as e:
            logger.error(f"Error generando contexto de aprendizaje: {str(e)}")
            return ""
    
    def generar_contexto_simple(
        self,
        db: Session,
        proveedor_id: int
    ) -> Dict[str, Any]:
        """
        Genera contexto estructurado (JSON) para aprendizaje.
        
        Args:
            db: Sesión de base de datos
            proveedor_id: ID del proveedor
            
        Returns:
            Dict con correcciones organizadas por categoría
        """
        try:
            correcciones = self.obtener_correcciones_proveedor(db, proveedor_id)
            if not correcciones:
                return {}
            
            # Organizar por categoría
            contexto = {}
            for c in correcciones:
                categoria = c["categoria"]
                if categoria not in contexto:
                    contexto[categoria] = []
                
                contexto[categoria].append({
                    "campo": c["campo"],
                    "valor_incorrecto": c["valor_incorrecto"],
                    "valor_correcto": c["valor_correcto"],
                    "confianza": c["confianza_original"],
                    "frecuencia": c["veces_ocurrido"],
                    "es_patron": c["es_patron"]
                })
            
            return contexto
            
        except Exception as e:
            logger.error(f"Error generando contexto simple: {str(e)}")
            return {}
    
    def analizar_mejora(
        self,
        db: Session,
        proveedor_id: int
    ) -> Dict[str, Any]:
        """
        Analiza qué campos necesitan más mejora basado en correcciones.
        
        Args:
            db: Sesión de base de datos
            proveedor_id: ID del proveedor
            
        Returns:
            Dict con análisis de campos problemáticos
        """
        try:
            correcciones = db.query(CorreccionAprendizaje).filter(
                CorreccionAprendizaje.proveedor_id == proveedor_id
            ).all()
            
            if not correcciones:
                return {"campos_problematicos": []}
            
            # Contar correcciones por campo
            campos_problema = {}
            for c in correcciones:
                clave = f"{c.categoria}.{c.campo_nombre}"
                if clave not in campos_problema:
                    campos_problema[clave] = {
                        "campo": c.campo_nombre,
                        "categoria": c.categoria,
                        "total_correcciones": 0,
                        "confianza_promedio": 0,
                        "ejemplos": []
                    }
                
                campos_problema[clave]["total_correcciones"] += c.veces_ocurrido
                campos_problema[clave]["confianza_promedio"] += (c.confianza_original or 0)
                campos_problema[clave]["ejemplos"].append({
                    "incorrecto": c.valor_extraido,
                    "correcto": c.valor_correcto,
                    "veces": c.veces_ocurrido
                })
            
            # Calcular promedios y ordenar
            resultado = []
            for clave, datos in campos_problema.items():
                datos["confianza_promedio"] = datos["confianza_promedio"] / max(1, len(datos["ejemplos"]))
                datos["severidad"] = "ALTA" if datos["total_correcciones"] >= 5 else "MEDIA" if datos["total_correcciones"] >= 3 else "BAJA"
                resultado.append(datos)
            
            # Ordenar por total de correcciones
            resultado.sort(key=lambda x: x["total_correcciones"], reverse=True)
            
            return {
                "proveedor_id": proveedor_id,
                "total_correcciones": len(correcciones),
                "campos_problematicos": resultado[:10]  # Top 10 campos
            }
            
        except Exception as e:
            logger.error(f"Error analizando mejora: {str(e)}")
            return {"campos_problematicos": []}
    
    def sugerir_correcciones(
        self,
        db: Session,
        proveedor_id: int,
        datos_extraidos: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Sugiere correcciones basadas en aprendizaje previo.
        Útil para pre-llenar campos que sabemos que suelen estar mal.
        
        Args:
            db: Sesión de base de datos
            proveedor_id: ID del proveedor
            datos_extraidos: Datos que la IA extrajo
            
        Returns:
            Lista de sugerencias de corrección
        """
        try:
            correcciones_frecuentes = self.obtener_correcciones_frecuentes(db, proveedor_id)
            sugerencias = []
            
            for corr in correcciones_frecuentes:
                # Verificar si el valor incorrecto aparece en los datos extraídos
                categoria = corr["categoria"]
                campo = corr["campo"]
                valor_incorrecto = corr["patron_incorrecto"]
                valor_correcto = corr["patron_correcto"]
                
                # Buscar en datos extraídos (estructura anidada)
                valor_actual = None
                if categoria in datos_extraidos and isinstance(datos_extraidos[categoria], dict):
                    if campo in datos_extraidos[categoria]:
                        item = datos_extraidos[categoria][campo]
                        # Puede ser {"valor": X, "confianza": Y} o solo X
                        valor_actual = item.get("valor") if isinstance(item, dict) else item
                
                # Si encontramos el valor incorrecto, sugerir corrección
                if valor_actual and str(valor_actual) == valor_incorrecto:
                    sugerencias.append({
                        "categoria": categoria,
                        "campo": campo,
                        "valor_actual": valor_actual,
                        "valor_sugerido": valor_correcto,
                        "razon": f"Patrón frecuente (ocurrió {corr['veces_ocurrido']} veces)",
                        "confianza_sugerencia": 95
                    })
            
            return sugerencias
            
        except Exception as e:
            logger.error(f"Error sugiriendo correcciones: {str(e)}")
            return []
    
    def limpiar_correcciones_antiguas(
        self,
        db: Session,
        dias_antiguedad: int = 180
    ) -> int:
        """
        Elimina correcciones muy antiguas o con baja ocurrencia.
        Mantiene solo patrones relevantes y actuales.
        
        Args:
            db: Sesión de base de datos
            dias_antiguedad: Días para considerar una corrección como antigua
            
        Returns:
            Número de registros eliminados
        """
        try:
            from datetime import datetime, timedelta
            
            fecha_limite = datetime.utcnow() - timedelta(days=dias_antiguedad)
            
            # Eliminar correcciones antiguas con baja ocurrencia
            eliminadas = db.query(CorreccionAprendizaje).filter(
                and_(
                    CorreccionAprendizaje.created_at < fecha_limite,
                    CorreccionAprendizaje.veces_ocurrido < 2
                )
            ).delete()
            
            db.commit()
            logger.info(f"Limpiadas {eliminadas} correcciones antiguas")
            return eliminadas
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error limpiando correcciones: {str(e)}")
            return 0
