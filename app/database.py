import psycopg2
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Load root .env first
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Optional legacy fallback for this project (disabled by setting ALLOW_LEGACY_APP_ENV=false)
if not os.getenv('DATABASE_URL') and os.getenv('ALLOW_LEGACY_APP_ENV', 'true').strip().lower() == 'true':
    legacy_env_path = os.path.join(os.path.dirname(__file__), 'Archivo .env')
    if os.path.exists(legacy_env_path):
        load_dotenv(legacy_env_path)

DATABASE_URL = os.getenv("DATABASE_URL")


def _build_connection_kwargs():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")
    db_sslmode = os.getenv("DB_SSLMODE", "require")

    if not all([db_host, db_name, db_user, db_password]):
        return None

    kwargs = {
        "host": db_host,
        "dbname": db_name,
        "user": db_user,
        "password": db_password,
        "port": db_port,
    }

    if not str(db_host).startswith("/cloudsql/"):
        kwargs["sslmode"] = db_sslmode

    return kwargs

def get_connection():
    database_url = os.getenv("DATABASE_URL") or DATABASE_URL
    db_sslmode = os.getenv("DB_SSLMODE", "require")
    if database_url:
        return psycopg2.connect(
            database_url,
            sslmode=db_sslmode
        )

    connection_kwargs = _build_connection_kwargs()
    if connection_kwargs:
        return psycopg2.connect(**connection_kwargs)

    raise RuntimeError('DATABASE_URL not set in environment')