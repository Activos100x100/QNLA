"""
Servicio de autenticación FTRA.

Responsabilidades:
  - Verificar credenciales contra `usuarios_login`
  - Crear y validar tokens de sesión (cookie HTTP-only)

Algoritmo de contraseña detectado en BD:
  hash = base64( PBKDF2-HMAC-SHA256( password, salt_bytes, iterations=100_000 ) )
"""

import base64
import hashlib
import logging
from typing import Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.usuario_login import UsuarioLogin
from app.repositories.usuario_login_repository import UsuarioLoginRepository
from app.repositories.rider_repository import RiderRepository
from app.repositories.cashout_repository import CashOutRepository

logger = logging.getLogger(__name__)

# Tiempo de vida de la sesión: 8 horas
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60
COOKIE_NAME = "ftra_session"

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="ftra-auth")


# ---------------------------------------------------------------------------
# Verificación de contraseña
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 100_000


def _verify_password(password: str, hash_b64: str, salt_b64: str) -> bool:
    """Verifica password contra hash y salt almacenados en Base64.
    Algoritmo: PBKDF2-HMAC-SHA256, 100.000 iteraciones.
    """
    if not hash_b64 or not salt_b64:
        return False
    try:
        salt_bytes = base64.b64decode(salt_b64)
        computed = base64.b64encode(
            hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt_bytes,
                _PBKDF2_ITERATIONS,
            )
        ).decode()
        return computed == hash_b64
    except Exception:
        logger.exception("Error al verificar contraseña")
        return False


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

def autenticar_usuario(
    db: Session, dni_nie: str, password: str
) -> Optional[UsuarioLogin]:
    """
    Valida credenciales.
    Devuelve el usuario si son correctas, None en caso contrario.
    """
    repo = UsuarioLoginRepository(db)
    usuario = repo.obtener_por_dni(dni_nie)

    if usuario is None:
        logger.warning("Intento de login fallido: DNI no encontrado → %s", dni_nie)
        return None

    if not _verify_password(password, usuario.password_hash, usuario.password_salt):
        logger.warning("Intento de login fallido: contraseña incorrecta → %s", dni_nie)
        return None

    logger.info("Login exitoso → usuario_id=%s dni=%s", usuario.usuario_id, dni_nie)
    return usuario


# ---------------------------------------------------------------------------
# Tokens de sesión
# ---------------------------------------------------------------------------

def _obtener_datos_empleado(db: Session, dni_nie: str) -> dict:
    """
    Obtiene nombre del empleado y datos de rider + deuda.
    Retorna dict con: nombre, es_rider, cod_activo, rider_id, deuda_total, deuda_semanas
    """
    try:
        # Obtener nombre
        row = db.execute(
            text(
                "SELECT nombre, apellidos, id FROM empleados "
                "WHERE documento_numero = :dni LIMIT 1"
            ),
            {"dni": dni_nie},
        ).fetchone()
        
        datos = {
            "nombre": "",
            "es_rider": False,
            "cod_activo": "",
            "rider_id": "",
            "deuda_total": 0.0,
            "deuda_semanas": [],
        }
        
        if not row:
            return datos
        
        nombre_partes = [p for p in (row[0], row[1]) if p]
        datos["nombre"] = " ".join(nombre_partes) if nombre_partes else dni_nie
        empleado_id = row[2]
        
        # Obtener info de rider
        repo_rider = RiderRepository(db)
        datos["es_rider"] = repo_rider.es_rider(empleado_id)
        
        if datos["es_rider"]:
            rider = repo_rider.obtener_rider_operativo(empleado_id)
            if rider:
                datos["cod_activo"] = rider.cod_activo or ""
                datos["rider_id"] = rider.rider_id or ""
            
            # Obtener deuda
            repo_cashout = CashOutRepository(db)
            deuda_info = repo_cashout.obtener_deuda_rider_por_semana(empleado_id)
            datos["deuda_total"] = deuda_info.get("total", 0.0)
            datos["deuda_semanas"] = deuda_info.get("semanas", [])
        
        return datos
    except Exception:
        logger.exception("Error al obtener datos de empleado")
        return {
            "nombre": dni_nie,
            "es_rider": False,
            "cod_activo": "",
            "rider_id": "",
            "deuda_total": 0.0,
            "deuda_semanas": [],
        }


def crear_token_sesion(usuario: UsuarioLogin, db: Session) -> str:
    """Genera un token firmado con los datos del usuario + info de rider + deuda."""
    datos = _obtener_datos_empleado(db, usuario.dni_nie)
    payload = {
        "uid": usuario.usuario_id,
        "dni": usuario.dni_nie,
        "nombre": datos["nombre"],
        "es_rider": datos["es_rider"],
        "cod_activo": datos["cod_activo"],
        "rider_id": datos["rider_id"],
        "deuda_total": datos["deuda_total"],
        "deuda_semanas": datos["deuda_semanas"],
    }
    return _serializer.dumps(payload)


def verificar_token_sesion(token: str) -> Optional[dict]:
    """
    Valida el token de sesión.
    Devuelve el payload si es válido y no ha expirado, None en caso contrario.
    """
    try:
        return _serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except SignatureExpired:
        logger.debug("Token de sesión expirado")
        return None
    except BadSignature:
        logger.warning("Token de sesión inválido (posible manipulación)")
        return None
    except Exception:
        logger.exception("Error inesperado al verificar token de sesión")
        return None
