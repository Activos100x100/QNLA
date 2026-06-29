#!/usr/bin/env python3
"""
Script de inicialización de la aplicación.
Crea la base de datos y las tablas necesarias.

Uso:
    python init_db.py
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Función principal de inicialización."""
    
    logger.info("=" * 60)
    logger.info("Inicializador de Aplicación - Procesador de Facturas")
    logger.info("=" * 60)
    
    try:
        # Importar después de configurar el path
        from app.database import engine, Base, SessionLocal
        from app.config import settings
        
        logger.info("\n1. Verificando configuración...")
        logger.info(f"   - Database URL: {settings.database_url[:50]}...")
        logger.info(f"   - Upload directory: {settings.upload_dir}")
        logger.info(f"   - Max file size: {settings.max_file_size / 1024 / 1024:.1f} MB")
        
        logger.info("\n2. Creando directorio de uploads...")
        settings.upload_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"   ✓ Directorio creado: {settings.upload_path.absolute()}")
        
        logger.info("\n3. Creando tablas de base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("   ✓ Tablas creadas:")
        logger.info("     - FTRA_proveedores")
        logger.info("     - FTRA_clientes")
        logger.info("     - FTRA_facturas")
        logger.info("     - FTRA_lineas_factura")
        logger.info("     - FTRA_historial_facturas")
        logger.info("     - FTRA_errores_procesamiento")
        
        logger.info("\n4. Probando conexión a base de datos...")
        with SessionLocal() as session:
            result = session.execute("SELECT 1")
            logger.info("   ✓ Conexión exitosa")
        
        logger.info("\n5. Verificación de dependencias...")
        try:
            import paddle
            logger.info("   ✓ PaddleOCR disponible")
        except ImportError:
            logger.warning("   ⚠ PaddleOCR no instalado - se instalará con OCR")
        
        try:
            import openai
            logger.info("   ✓ OpenAI disponible")
            
            # Verificar API key
            if settings.openai_api_key == "your_openai_api_key_here":
                logger.warning("   ⚠ OPENAI_API_KEY no está configurada - editar .env")
            else:
                logger.info("   ✓ OPENAI_API_KEY está configurada")
        except ImportError:
            logger.error("   ✗ OpenAI no instalado - instalar con: pip install openai")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Inicialización completada exitosamente")
        logger.info("=" * 60)
        
        logger.info("\n📚 Próximos pasos:")
        logger.info("  1. Verificar la configuración en .env")
        logger.info("  2. Ejecutar: uvicorn app.main:app --reload")
        logger.info("  3. Abrir: http://localhost:8080")
        logger.info("  4. Ver documentación: http://localhost:8080/docs")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Error durante la inicialización: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
