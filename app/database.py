"""
Configuración de base de datos PostgreSQL con SQLAlchemy.
Maneja la conexión y sesiones con la base de datos.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Legacy fallback
if not os.getenv('DATABASE_URL') and os.getenv('ALLOW_LEGACY_APP_ENV', 'true').strip().lower() == 'true':
    legacy_env_path = os.path.join(os.path.dirname(__file__), 'Archivo .env')
    if os.path.exists(legacy_env_path):
        load_dotenv(legacy_env_path)

# Obtener URL de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./facturas_dev.db")

# Permitir tanto PostgreSQL como SQLite
if "postgresql" not in DATABASE_URL and "sqlite" not in DATABASE_URL:
    raise ValueError(f"DATABASE_URL debe ser PostgreSQL o SQLite: {DATABASE_URL}")

# Crear engine de SQLAlchemy con parámetros específicos por BD
engine_kwargs = {
    "echo": False,  # Cambiar a True para ver queries SQL
    "pool_pre_ping": True,  # Validar conexiones antes de usarlas
}

if "sqlite" in DATABASE_URL:
    # SQLite no soporta pool_size/max_overflow
    engine = create_engine(DATABASE_URL, **engine_kwargs, connect_args={"check_same_thread": False})
else:
    # PostgreSQL
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20
    })
    engine = create_engine(DATABASE_URL, **engine_kwargs)

# Crear SessionLocal para obtener sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obtener sesión de base de datos.
    Usado en los endpoints de FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Crea todas las tablas en la base de datos.
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Elimina todas las tablas de la base de datos.
    ADVERTENCIA: Destructivo, solo para desarrollo.
    """
    Base.metadata.drop_all(bind=engine)

    connection_kwargs = _build_connection_kwargs()
    if connection_kwargs:
        return psycopg2.connect(**connection_kwargs)

    raise RuntimeError('DATABASE_URL not set in environment')