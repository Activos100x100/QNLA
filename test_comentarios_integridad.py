#!/usr/bin/env python
"""
Script de verificación para el sistema de comentarios
Comprueba que todos los archivos están en su lugar y son válidos
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def check_file_exists(filepath):
    """Verifica que un archivo existe"""
    if Path(filepath).exists():
        print(f"✅ {filepath}")
        return True
    else:
        print(f"❌ {filepath} - NO ENCONTRADO")
        return False

def check_python_syntax(filepath):
    """Verifica la sintaxis de Python"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        print(f"✅ Sintaxis válida: {filepath}")
        return True
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en {filepath}: {e}")
        return False

def test_imports():
    """Testa las importaciones principales"""
    try:
        print("\n🔍 Probando importaciones...")
        
        # Models
        from app.models.comentario import Comentario, ComentarioAuditoria
        print("✅ app.models.comentario")
        
        # Schemas
        from app.schemas.factura_schemas import (
            ComentarioCreate, ComentarioUpdate, ComentarioResponse,
            ComentarioEstadisticas, ComentarioAuditoriaResponse
        )
        print("✅ app.schemas.factura_schemas")
        
        # Repository
        from app.repositories.comentarios_repository import (
            ComentariosRepository, ComentariosAuditoriaRepository
        )
        print("✅ app.repositories.comentarios_repository")
        
        # Service
        from app.services.comentarios_service import ComentariosService
        print("✅ app.services.comentarios_service")
        
        # Router
        from app.routers.comentarios import router
        print("✅ app.routers.comentarios")
        
        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 Sistema de Comentarios - Verificación de Integridad")
    print("=" * 60)
    
    all_good = True
    base_path = Path(__file__).parent
    
    # 1. Verificar archivos
    print("\n📁 Verificando archivos...")
    files_to_check = [
        "app/models/comentario.py",
        "app/repositories/comentarios_repository.py",
        "app/services/comentarios_service.py",
        "app/routers/comentarios.py",
        "alembic/versions/20260627_05_add_comentarios.py",
    ]
    
    for filepath in files_to_check:
        full_path = base_path / filepath
        if not check_file_exists(full_path):
            all_good = False
    
    # 2. Verificar sintaxis
    print("\n🐍 Verificando sintaxis Python...")
    python_files = [
        "app/models/comentario.py",
        "app/repositories/comentarios_repository.py",
        "app/services/comentarios_service.py",
        "app/routers/comentarios.py",
    ]
    
    for filepath in python_files:
        full_path = base_path / filepath
        if not check_python_syntax(full_path):
            all_good = False
    
    # 3. Probar importaciones
    if not test_imports():
        all_good = False
    
    # 4. Resumen
    print("\n" + "=" * 60)
    if all_good:
        print("✅ ¡Todas las verificaciones pasaron!")
        print("\n📝 Próximos pasos:")
        print("1. Ejecutar: alembic upgrade head")
        print("2. Reiniciar el servidor FastAPI")
        print("3. Probar endpoints en: http://localhost:8000/docs")
    else:
        print("❌ Hay problemas que necesitan ser resueltos")
        sys.exit(1)

if __name__ == "__main__":
    main()
