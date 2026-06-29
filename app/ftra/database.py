"""SQLAlchemy engine and session for the quiniela module."""
from __future__ import annotations

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from urllib.parse import urlparse, parse_qs

# Reutiliza las mismas variables de entorno que el resto de la app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
if not os.getenv("DATABASE_URL"):
    legacy = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Archivo .env")
    if os.path.exists(legacy):
        load_dotenv(legacy)

_raw_url: str = os.getenv("DATABASE_URL", "")

if not _raw_url:
    _host = os.getenv("DB_HOST", "")
    _name = os.getenv("DB_NAME", "")
    _user = os.getenv("DB_USER", "")
    _pass = os.getenv("DB_PASSWORD", "")
    _port = os.getenv("DB_PORT", "5432")
    _raw_url = f"postgresql://{_user}:{_pass}@{_host}:{_port}/{_name}"

# SQLAlchemy espera postgresql:// no postgres://
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

# Configurar connect_args según tipo de BD
_connect_args: dict = {}

if "sqlite" in DATABASE_URL:
    _connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    _sslmode = os.getenv("DB_SSLMODE", "require")
    _parsed = urlparse(DATABASE_URL)
    _query = parse_qs(_parsed.query)
    _query_host = (_query.get("host") or [""])[0]
    _looks_like_cloudsql_socket = (
        "/cloudsql/" in DATABASE_URL
        or str(_parsed.hostname or "").startswith("/cloudsql/")
        or str(_query_host or "").startswith("/cloudsql/")
    )
    if not _looks_like_cloudsql_socket:
        _connect_args = {"sslmode": _sslmode}

# Pool settings específicas por BD
_pool_kwargs = {}
if "postgresql" in DATABASE_URL:
    _pool_kwargs = {"pool_size": 5, "max_overflow": 10}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency que provee una sesión SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
