from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "QNLA funcionando"}
    v = str(v).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            from datetime import datetime as _dt
            return _dt.strptime(v, fmt).date().isoformat()
        except Exception:
            pass
    return None

def _to_int(v):
    try:
        return int(str(v).strip()) if v not in (None, '') else None
    except Exception:
        return None

def _to_bool(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ('1', 'true', 'si', 'sí', 'yes', 't'):
        return True
    if s in ('0', 'false', 'no', 'f', ''):
        return False
    return None
import sys
import traceback
from fastapi.middleware.cors import CORSMiddleware
import csv as _csv
import io as _io
print("[DEBUG] Importing FastAPI and dependencies...")
try:
    from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form  # type: ignore[reportMissingImports]
    print("[DEBUG] FastAPI and dependencies imported OK")
    from fastapi.encoders import jsonable_encoder  # type: ignore[reportMissingImports]
    print("[DEBUG] fastapi.encoders imported OK")
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response  # type: ignore[reportMissingImports]
    print("[DEBUG] fastapi.responses imported OK")
    from fastapi.staticfiles import StaticFiles  # type: ignore[reportMissingImports]
    print("[DEBUG] fastapi.staticfiles imported OK")
    from fastapi.templating import Jinja2Templates  # type: ignore[reportMissingImports]
    print("[DEBUG] fastapi.templating imported OK")
    from app.core.integracion.google_drive import crear_estructura_empleado, crear_estructura_en_shared_drive, get_drive_service_for_user, SHARED_DRIVE_ID
    print("[DEBUG] app.core.integracion.google_drive imported OK")
    from starlette.middleware.sessions import SessionMiddleware  # type: ignore[reportMissingImports]
    print("[DEBUG] starlette.middleware.sessions imported OK")
    from starlette.middleware.trustedhost import TrustedHostMiddleware  # type: ignore[reportMissingImports]
    print("[DEBUG] starlette.middleware.trustedhost imported OK")
    from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware  # type: ignore[reportMissingImports]
    print("[DEBUG] starlette.middleware.httpsredirect imported OK")
    from googleapiclient.discovery import build  # type: ignore[reportMissingImports]
    print("[DEBUG] googleapiclient.discovery imported OK")
    from datetime import datetime
    print("[DEBUG] datetime imported OK")
    import csv
    import io
    import os
    import uuid
    import json
    import traceback
    import logging
    import unicodedata
    import re
    print("[DEBUG] Built-in modules imported OK")
except Exception as e:
    print("\n\nFATAL ERROR DURING IMPORT:\n", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)


app = FastAPI()

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on", "si", "sí"}


def _env_csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [part.strip() for part in str(raw).split(",") if part and part.strip()]


IS_CLOUD_RUN = bool(os.getenv("K_SERVICE"))
FORCE_HTTPS = _env_bool("FORCE_HTTPS", IS_CLOUD_RUN)
ALLOW_ALL_ORIGINS = _env_bool("CORS_ALLOW_ALL", False)

_default_origins = "http://localhost,http://127.0.0.1,http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = ["*"] if ALLOW_ALL_ORIGINS else _env_csv("CORS_ALLOW_ORIGINS", _default_origins)
ALLOWED_HOSTS = _env_csv("ALLOWED_HOSTS", "127.0.0.1,localhost")

SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    if IS_CLOUD_RUN:
        raise RuntimeError("SESSION_SECRET no configurado en entorno de producción")
    SESSION_SECRET = "local-dev-secret-change-me"
    logger.warning("SESSION_SECRET no definido. Se usa secreto de desarrollo local.")

SESSION_HTTPS_ONLY = _env_bool("SESSION_HTTPS_ONLY", FORCE_HTTPS)
SESSION_SAME_SITE = os.getenv("SESSION_SAME_SITE", "lax").strip().lower() or "lax"
if SESSION_SAME_SITE not in {"lax", "strict", "none"}:
    SESSION_SAME_SITE = "lax"


if ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

if FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

# Configuración de CORS para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=not ALLOW_ALL_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# session middleware required to store oauth state between requests
# Use lax same_site and disable https_only for local dev so the OAuth redirect
# from Google does not drop the session on callback.
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site=SESSION_SAME_SITE,
    https_only=SESSION_HTTPS_ONLY
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    if FORCE_HTTPS:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# QNLA (quiniela)
from .qnla.database import Base as QNLABase, engine as qnla_engine
from .qnla import models as qnla_models  # noqa: F401

# include API routers

from .api.ciudades import router as ciudades_router
from .api.usuario_admin import router as usuario_admin_router
from .api.plantillas_whatsapp import router as plantillas_whatsapp_router
from .pages import router as pages_router
from .api.consulta_consentimiento import router as consulta_consentimiento_router
from .api.consentimiento_whatsapp import router as consentimiento_whatsapp_router
from .qnla.routers.pages import router as qnla_pages_router
from .qnla.routers.admin_torneos import router as qnla_admin_torneos_router, public_router as qnla_torneos_public_router
from .qnla.routers.admin_partidos import router as qnla_admin_partidos_router
from .qnla.routers.pronosticos import router as qnla_pronosticos_router
from .qnla.routers.ranking import router as qnla_ranking_router
app.include_router(ciudades_router)
app.include_router(usuario_admin_router)
app.include_router(plantillas_whatsapp_router)
app.include_router(pages_router)
app.include_router(consulta_consentimiento_router)
app.include_router(consentimiento_whatsapp_router)
app.include_router(qnla_pages_router)
app.include_router(qnla_torneos_public_router)
app.include_router(qnla_admin_torneos_router)
app.include_router(qnla_admin_partidos_router)
app.include_router(qnla_pronosticos_router)
app.include_router(qnla_ranking_router)


@app.on_event("startup")
def _qnla_create_tables():
    """Crea tablas QNLA si no existen (bootstrap local)."""
    QNLABase.metadata.create_all(bind=qnla_engine)
    # Compatibilidad con esquemas legacy de qnla_participantes
    # (algunas bases antiguas no incluyen columnas usadas por el modelo ORM actual).
    try:
        with qnla_engine.begin() as conn:
            conn.exec_driver_sql("ALTER TABLE IF EXISTS qnla_participantes ADD COLUMN IF NOT EXISTS nombre VARCHAR(200)")
            conn.exec_driver_sql("ALTER TABLE IF EXISTS qnla_participantes ADD COLUMN IF NOT EXISTS email VARCHAR(254)")
            conn.exec_driver_sql("ALTER TABLE IF EXISTS qnla_participantes ADD COLUMN IF NOT EXISTS password_hash VARCHAR(200)")
            conn.exec_driver_sql("ALTER TABLE IF EXISTS qnla_participantes ADD COLUMN IF NOT EXISTS es_admin BOOLEAN DEFAULT FALSE")
            conn.exec_driver_sql("ALTER TABLE IF EXISTS qnla_participantes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()")

            conn.exec_driver_sql("""
                UPDATE qnla_participantes
                SET nombre = COALESCE(NULLIF(nombre, ''), NULLIF(alias, ''), CONCAT('Participante ', id::text))
            """)
            conn.exec_driver_sql("""
                UPDATE qnla_participantes
                SET email = COALESCE(NULLIF(email, ''),
                                     CASE WHEN NULLIF(alias, '') IS NOT NULL THEN LOWER(alias) || '@qnla.local' ELSE NULL END,
                                     'participante_' || id::text || '@qnla.local')
            """)
            conn.exec_driver_sql("""
                UPDATE qnla_participantes
                SET password_hash = COALESCE(NULLIF(password_hash, ''), 'legacy-no-password')
            """)
            conn.exec_driver_sql("""
                UPDATE qnla_participantes
                SET es_admin = COALESCE(es_admin, FALSE)
            """)
            conn.exec_driver_sql("""
                UPDATE qnla_participantes
                SET created_at = COALESCE(created_at, NOW())
            """)
    except Exception as e:
        logger.warning("QNLA compatibility patch skipped/failed: %s", e)
_EMP_COLS_CACHE = {}


def get_current_user_email(request: Request):
    """Return the current authenticated user's email stored in session.

    Raises HTTPException 401 if no user is stored in session.
    """
    email = None
    try:
        email = request.session.get("user_email")
    except Exception:
        email = None

    if not email:
        raise HTTPException(
            status_code=401,
            detail="User not authenticated. Visit /google/login"
        )

    return email


@app.get('/api/drive/status')
def drive_status(request: Request):
    """Check Drive access for the authenticated user."""
    # Try to detect a caller user stored in session (optional). If none,
    # proceed using the Service Account / ADC credentials.
    user_email = None
    try:
        user_email = get_current_user_email(request)
        user_email = request.session.get("user_email")
    except HTTPException:
        user_email = None

    try:
        drive = get_drive_service_for_user(user_email)
    except FileNotFoundError:
        return JSONResponse({
            "ok": False,
            "error": "no_token",
            "detail": f"No token stored for {user_email} and no service credentials available"
        })
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": "drive_unavailable",
            "detail": str(e)
        })

    try:
        info = drive.drives().get(
            driveId=SHARED_DRIVE_ID,
            fields="id,name"
        ).execute()

        return JSONResponse({
            "ok": True,
            "user": user_email or 'service-account',
            "drive": info
        })

    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": "drive_api_error",
            "detail": str(e)
        })


@app.post('/api/empleados/parse_ita')
async def parse_ita_endpoint(file: UploadFile = File(...)):
    """Recibe un fichero ITA y devuelve JSON con filas parseadas."""
    try:
        raw = await file.read()
        try:
            text = raw.decode('utf-8')
        except Exception:
            text = raw.decode('latin-1', errors='replace')
        rows = _parse_ita_content(text)
        # For each parsed row, check whether the DNI/NIE already exists in empleados
        try:
            from .database import get_connection
            conn = get_connection()
            cur = conn.cursor()
            for r in rows:
                num = (r.get('DNI/NIE') or '').strip()
                if not num:
                    r['exists'] = False
                    r['match'] = None
                    continue
                try:
                    norm = num.upper().replace('-', '').replace(' ', '')
                except Exception:
                    norm = num
                cur.execute("""
                    SELECT id, nombre, apellidos FROM empleados
                    WHERE REPLACE(REPLACE(UPPER(documento_numero), '-', ''), ' ', '') =
                          REPLACE(REPLACE(UPPER(%s), '-', ''), ' ', '')
                    LIMIT 1
                """, (num,))
                row = cur.fetchone()
                if row:
                    r['exists'] = True
                    r['match'] = {'id': row[0], 'nombre': row[1], 'apellidos': row[2]}
                else:
                    r['exists'] = False
                    r['match'] = None
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        except Exception:
            logger.exception('parse_ita: existence checks failed')

        return JSONResponse({'rows': rows})
    except Exception as e:
        logger.exception('parse_ita error')
        return JSONResponse({'rows': []})


@app.post('/api/empleados/import_ita')
async def import_ita_endpoint(request: Request):
    """Recibe JSON {rows: [...] } y simula/importa los registros.
    Actualmente devuelve conteo de filas importadas. Puedes extender para insertar en BD.
    """
    try:
        payload = await request.json()
        rows = payload.get('rows', []) if isinstance(payload, dict) else []
        # Aquí puedes añadir la lógica para insertar en la BD.
        return JSONResponse({'ok': True, 'imported': len(rows)})
    except Exception:
        logger.exception('import_ita error')
        return JSONResponse({'ok': False, 'imported': 0})


@app.post('/api/empleados/vehiculo-asignacion-por-fichero/procesar')
async def vehiculo_asignacion_por_fichero_api(file: UploadFile = File(...)):
    """
    Procesa un CSV con columnas:
        empleado_id, vehiculo_id, fecha_inicio, activo
    y hace upsert en vehiculo_asignacion por empleado_id.
    rider_operativo_id se infiere automáticamente desde rider_operativo del empleado.
    """
    from .database import get_connection
    import csv as _csv
    import io as _io

    def _decode(raw: bytes) -> str:
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                return raw.decode(enc)
            except Exception:
                pass
        return raw.decode('latin-1', errors='replace')

    def _norm_header(v: str) -> str:
        import unicodedata as _ud
        v = _ud.normalize('NFKD', v).encode('ascii', 'ignore').decode('ascii')
        return v.strip().lower().replace(' ', '_').replace('-', '_')

    def _parse_date(v):
        if not v:
            return None
        v = str(v).strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try:
                from datetime import datetime as _dt
                return _dt.strptime(v, fmt).date().isoformat()
            except Exception:
                pass
        return None

    def _to_int(v):
        try:
            return int(str(v).strip()) if v not in (None, '') else None
        except Exception:
            return None

    def _to_bool(v):
        if v is None:
            return None
        s = str(v).strip().lower()
        if s in ('1', 'true', 'si', 'sí', 'yes', 't'):
            return True
        if s in ('0', 'false', 'no', 'f', ''):
            return False
        return None

    def _vals_equal(a, b) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return str(a).strip() == str(b).strip()

    conn = None
    cur = None
    try:
        raw = await file.read()
        text = _decode(raw)

        sample = text[:4096]
        try:
            dialect = _csv.Sniffer().sniff(sample, delimiters=',\t;|')
        except _csv.Error:
            dialect = _csv.excel

        reader = _csv.DictReader(_io.StringIO(text), dialect=dialect)
        if reader.fieldnames is None:
            return JSONResponse({'ok': False, 'detail': 'CSV vacío o sin cabecera.'}, status_code=400)

        header_map = {orig: _norm_header(orig) for orig in reader.fieldnames}
        rows_raw = []
        for i, row in enumerate(reader, start=2):
            normalised = {header_map[k]: v for k, v in row.items() if k in header_map}
            normalised['row_number'] = i
            rows_raw.append(normalised)

        if not rows_raw:
            return JSONResponse({'ok': False, 'detail': 'El fichero CSV no contiene filas de datos.'}, status_code=400)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'vehiculo_asignacion'
            ORDER BY ordinal_position
            """
        )
        va_meta_rows = cur.fetchall()
        va_cols = {r[0] for r in va_meta_rows}
        va_nullable = {r[0]: (r[1] == 'YES') for r in va_meta_rows}
        if not va_cols:
            raise HTTPException(status_code=404, detail='Tabla vehiculo_asignacion no encontrada')

        update_fields = [f for f in ('vehiculo_id', 'rider_operativo_id', 'fecha_inicio', 'activo') if f in va_cols]

        summary = {'total_rows': len(rows_raw), 'created': 0, 'updated': 0, 'errors': 0}
        results = []

        for row in rows_raw:
            sp = f"sp_vehiculo_{int(row['row_number'])}"
            cur.execute(f"SAVEPOINT {sp}")
            try:
                emp_id = _to_int(row.get('empleado_id'))
                if emp_id is None:
                    raise ValueError('empleado_id vacío o no numérico')

                vehiculo_id = _to_int(row.get('vehiculo_id'))
                fecha_inicio = _parse_date(row.get('fecha_inicio'))
                activo_raw = row.get('activo', '')
                activo = _to_bool(activo_raw) if str(activo_raw).strip() != '' else None

                rider_operativo_id = None
                if 'rider_operativo_id' in va_cols:
                    cur.execute(
                        """
                        SELECT id
                        FROM rider_operativo
                        WHERE empleado_id = %s
                        ORDER BY
                            CASE WHEN activo = true THEN 0 ELSE 1 END,
                            fecha_inicio DESC NULLS LAST,
                            id DESC
                        LIMIT 1
                        """,
                        (emp_id,)
                    )
                    ro = cur.fetchone()
                    rider_operativo_id = ro[0] if ro else None
                    if rider_operativo_id is None and not va_nullable.get('rider_operativo_id', True):
                        raise ValueError('No existe rider_operativo para ese empleado y rider_operativo_id es obligatorio')

                cur.execute(
                    """
                    SELECT id, vehiculo_id, rider_operativo_id, fecha_inicio, activo
                    FROM vehiculo_asignacion
                    WHERE empleado_id = %s
                    ORDER BY
                        CASE WHEN COALESCE(activo, false) = true THEN 0 ELSE 1 END,
                        fecha_inicio DESC NULLS LAST,
                        id DESC
                    LIMIT 1
                    """,
                    (emp_id,)
                )
                existing = cur.fetchone()

                new_vals = {
                    'vehiculo_id': vehiculo_id,
                    'rider_operativo_id': rider_operativo_id,
                    'fecha_inicio': fecha_inicio,
                    'activo': activo,
                }

                if existing:
                    row_id = existing[0]
                    old_vals = {
                        'vehiculo_id': existing[1],
                        'rider_operativo_id': existing[2],
                        'fecha_inicio': existing[3],
                        'activo': existing[4],
                    }
                    changed = [
                        k for k in update_fields
                        if new_vals[k] is not None and not _vals_equal(old_vals[k], new_vals[k])
                    ]

                    if not changed:
                        results.append({
                            'row_number': row['row_number'],
                            'empleado_id': emp_id,
                            'vehiculo_id': vehiculo_id if vehiculo_id is not None else '',
                            'action': 'Sin cambios',
                            'detail': 'Sin cambios',
                        })
                    else:
                        set_parts = ', '.join([f"{k} = %s" for k in changed])
                        vals = [new_vals[k] for k in changed] + [row_id]
                        cur.execute(
                            f"UPDATE vehiculo_asignacion SET {set_parts} WHERE id = %s",
                            tuple(vals)
                        )
                        summary['updated'] += 1
                        results.append({
                            'row_number': row['row_number'],
                            'empleado_id': emp_id,
                            'vehiculo_id': vehiculo_id if vehiculo_id is not None else '',
                            'action': 'Actualizado',
                            'updated_fields': changed,
                            'detail': 'Campos actualizados: ' + ', '.join(changed),
                        })
                else:
                    insert_data = {'empleado_id': emp_id}
                    if vehiculo_id is not None and 'vehiculo_id' in va_cols:
                        insert_data['vehiculo_id'] = vehiculo_id
                    if rider_operativo_id is not None and 'rider_operativo_id' in va_cols:
                        insert_data['rider_operativo_id'] = rider_operativo_id
                    if fecha_inicio is not None and 'fecha_inicio' in va_cols:
                        insert_data['fecha_inicio'] = fecha_inicio
                    if activo is not None and 'activo' in va_cols:
                        insert_data['activo'] = activo
                    if 'created_at' in va_cols:
                        insert_data['created_at'] = datetime.utcnow().isoformat()

                    if 'vehiculo_id' in va_cols and vehiculo_id is None and not va_nullable.get('vehiculo_id', True):
                        raise ValueError('vehiculo_id vacío y es obligatorio')

                    cols_sql = ', '.join(insert_data.keys())
                    placeholders = ', '.join(['%s'] * len(insert_data))
                    cur.execute(
                        f"INSERT INTO vehiculo_asignacion ({cols_sql}) VALUES ({placeholders}) RETURNING id",
                        tuple(insert_data.values())
                    )
                    created_fields = list(insert_data.keys())
                    summary['created'] += 1
                    results.append({
                        'row_number': row['row_number'],
                        'empleado_id': emp_id,
                        'vehiculo_id': vehiculo_id if vehiculo_id is not None else '',
                        'action': 'Creado',
                        'created_fields': created_fields,
                        'detail': 'Campos creados: ' + ', '.join(created_fields),
                    })

                cur.execute(f"RELEASE SAVEPOINT {sp}")
            except Exception as row_err:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
                cur.execute(f"RELEASE SAVEPOINT {sp}")
                summary['errors'] += 1
                results.append({
                    'row_number': row['row_number'],
                    'empleado_id': row.get('empleado_id', ''),
                    'vehiculo_id': row.get('vehiculo_id', ''),
                    'action': 'Error',
                    'error': str(row_err),
                    'detail': f"Error: {str(row_err)}",
                })

        conn.commit()
        return JSONResponse({'ok': True, 'summary': summary, 'results': results})

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception('vehiculo_asignacion_por_fichero_api error')
        return JSONResponse({'ok': False, 'detail': str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.get('/api/verificar-documento/{numero}')
def verificar_documento(numero: str):
    """Endpoint auxiliar usado por la validación del frontend.

    Devuelve 400 con JSON {detail: ...} si el documento existe, 200 si está disponible.
    """
    from .database import get_connection
    conn = None
    try:
        logger.info('verificar_documento called numero=%r', numero)
        if not numero:
            return JSONResponse({"status": "disponible"})

        try:
            norm = numero.upper().replace('-', '').replace(' ', '')
        except Exception:
            norm = numero
        logger.info('verificar_documento normalized -> %s', norm)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*)
            FROM empleados
            WHERE REPLACE(REPLACE(UPPER(documento_numero), '-', ''), ' ', '') =
                  REPLACE(REPLACE(UPPER(%s), '-', ''), ' ', '')
        """, (numero,))
        count = cur.fetchone()[0]
        cur.close()
        if count:
            return JSONResponse(status_code=400, content={"detail": "Este número de documento ya está registrado en el sistema"})
        return {"status": "disponible"}
    except Exception as e:
        try:
            logger.exception('verificar_documento error')
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"detail": "error interno"})
    finally:
        if conn:
            conn.close()


@app.get('/api/rider_operativo/check_active')
def check_rider_operativo_active(field: str = None, value: str = None):
    """Check whether a rider_operativo row exists with activo = true for given rider_id or cod_activo.

    Query params:
      - field: 'rider_id' or 'cod_activo'
      - value: value to check

    Returns JSON {"exists": true/false}.
    """
    if not field or not value:
        return JSONResponse({"exists": False})

    allowed = {'rider_id': 'rider_id', 'cod_activo': 'cod_activo'}
    if field not in allowed:
        return JSONResponse({"exists": False})

    col = allowed[field]
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # check active=true
        cur.execute(f"SELECT COUNT(*) FROM rider_operativo WHERE {col} = %s AND activo = true", (value,))
        count = cur.fetchone()[0]
        cur.close()
        return JSONResponse({"exists": bool(count)})
    except Exception as e:
        try:
            print('check_rider_operativo_active error:', e)
        except Exception:
            pass
        return JSONResponse({"exists": False})
    finally:
        if conn:
            conn.close()


@app.post("/api/empleados")
def crear_empleado(request: Request, payload: dict):
    """Crear empleado en la base de datos, crear estructura en Drive y guardar drive_folder_id.

    The function reads the `empleados` table columns and inserts only the provided fields
    to avoid schema mismatch. Then it will attempt to create the Drive folder structure
    using saved credentials (app/token.json) and persist the resulting folder id.
    """
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Get available columns for empleados table (cached to avoid repeated information_schema hits)
        global _EMP_COLS_CACHE
        if 'empleados' not in _EMP_COLS_CACHE:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='empleados'")
            _EMP_COLS_CACHE['empleados'] = [r[0] for r in cur.fetchall()]
        emp_cols = _EMP_COLS_CACHE['empleados']

        # Minimal, explicit cleaning: only empty strings -> None and types for known numeric/boolean fields
        def clean_payload(data):
            cleaned = {}
            for k, v in data.items():
                # treat explicit textual nulls as empty
                if isinstance(v, str) and v.strip() in ('', 'null', 'undefined', 'NaN'):
                    cleaned[k] = None
                else:
                    cleaned[k] = v

            # integer fields commonly used in the form - convert safely
            int_fields = (
                'departamento_id',
                'ciudad_id',
                'vehiculo_id',
                'puesto_nivel_id',
                'puesto_id',
                'puesto',
                'convenio',
                'convenio_tramo_id'
            )
            # include some additional numeric fields present in the schema
            # e.g. grado_discapacidad (integer) and id_rrhh (bigint)
            int_fields = tuple(list(int_fields) + ['grado_discapacidad', 'id_rrhh'])
            for f in int_fields:
                v = cleaned.get(f)
                if v in (None, ''):
                    cleaned[f] = None
                    continue
                # allow textual booleans like 'si'/'no' or 'true'/'false' to map to 1/0
                if isinstance(v, str):
                    low = v.strip().lower()
                    if low in ('si','s','yes','y','true'):
                        cleaned[f] = 1
                        continue
                    if low in ('no','n','false','0'):
                        cleaned[f] = 0
                        continue
                try:
                    cleaned[f] = int(v)
                except Exception:
                    cleaned[f] = None

            # boolean fields commonly used
            bool_fields = ('activo','discapacidad_respuesta')
            for f in bool_fields:
                if f in cleaned and isinstance(cleaned[f], str):
                    low = cleaned[f].lower()
                    if low in ('si','s','yes','y','true','1'):
                        cleaned[f] = True
                    elif low in ('no','n','false','0'):
                        cleaned[f] = False

            return cleaned

        cleaned = clean_payload(payload)

        # DEBUG: log cleaned payload for troubleshooting during development
        try:
            print('crear_empleado cleaned payload ->', cleaned)
        except Exception:
            pass

        # Try to create Drive structure first (so empleado row can reference folder_id)
        root_id = None
        root_link = None
        try:
            # Optional: detect caller email from session for auditing. If absent
            # we proceed using the Service Account credentials.
            try:
                user_email = request.session.get('user_email')
            except Exception:
                user_email = None

            try:
                drive = get_drive_service_for_user(user_email)
            except FileNotFoundError:
                raise HTTPException(status_code=500, detail='No service credentials available and no user token found')
            except HTTPException:
                raise
            except Exception:
                try:
                    traceback.print_exc()
                except Exception:
                    pass
                raise HTTPException(status_code=500, detail='Drive service unavailable')

            # find city name from DB if possible
            city_name = None
            try:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('ciudad', 'ciudades')")
                tables = [r[0] for r in cur.fetchall()]
                if tables and cleaned.get('ciudad_id'):
                    table = tables[0]
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
                    cols_table = [r[0] for r in cur.fetchall()]
                    display_col = None
                    for candidate in ('name','municipio','nombre'):
                        if candidate in cols_table:
                            display_col = candidate
                            break
                    if display_col:
                        cur.execute(f"SELECT {display_col} FROM {table} WHERE id = %s", (cleaned.get('ciudad_id'),))
                        row = cur.fetchone()
                        city_name = row[0] if row else None
            except Exception:
                city_name = None

            try:
                nombre = str(cleaned.get('nombre') or '').strip()
                apellidos = str(cleaned.get('apellidos') or '').strip()
                root_info = crear_estructura_en_shared_drive(drive, SHARED_DRIVE_ID, city_name or 'Sin Ciudad', f"{nombre} {apellidos}")
                if isinstance(root_info, dict):
                    root_id = root_info.get('id')
                    root_link = root_info.get('link')
                else:
                    root_id = root_info
                    root_link = None
            except Exception:
                # best-effort: if drive creation fails, log and continue with DB insert
                try:
                    traceback.print_exc()
                except Exception:
                    pass
                try:
                    logger.exception('Drive folder creation failed; continuing without drive folder')
                except Exception:
                    pass
                root_id = None
                root_link = None

        except HTTPException:
            raise
        except Exception:
            # Unable to initialize Drive service; abort to avoid orphan DB rows
            try:
                traceback.print_exc()
            except Exception:
                pass
            raise HTTPException(status_code=500, detail='Drive service unavailable')

        # attach drive folder id to cleaned payload so it is saved on insert (if column exists)
        if root_id:
            cleaned['drive_folder_id'] = root_id
        # also attach publicly-viewable link (if available) to carpeta_url so the empleados
        # table stores a direct link to the created Drive folder
        if root_link:
            cleaned['carpeta_url'] = root_link

        # DEBUG: log that we're about to insert and whether carpeta_url is present
        try:
            logger.info('Inserting empleado; carpeta_url present: %s', bool(cleaned.get('carpeta_url')))
        except Exception:
            pass

        # Intersection of payload keys and table columns
        keys = [k for k, v in cleaned.items() if k in emp_cols]
        try:
            logger.info('Empleado insert columns: %s', keys)
            # log presence/values of important drive-related fields
            logger.info('Empleado drive fields: drive_folder_id=%s carpeta_url=%s', cleaned.get('drive_folder_id'), cleaned.get('carpeta_url'))
        except Exception:
            pass
        if not keys:
            # fallback minimal insert (nombre, apellidos) if possible
            keys = [k for k in ('nombre','apellidos') if k in emp_cols and k in cleaned]

        if not keys:
            raise HTTPException(status_code=400, detail='No valid fields provided for empleados insert')

        cols_sql = ','.join(keys)
        vals = [cleaned.get(k) for k in keys]
        placeholders = ','.join(['%s'] * len(vals))
        # insert and return id if exists
        sql = f"INSERT INTO empleados ({cols_sql}) VALUES ({placeholders}) RETURNING id"
        cur.execute(sql, vals)
        empleado_id = cur.fetchone()[0]
        conn.commit()

        # If payload contains rider data, try to insert a row into rider_operativo
        inserted = {
            'empleado': None,
            'asignacion': None,
            'compensacion': None,
            'rider_operativo': None,
            'vehiculo_asignacion': None,
            'usuario_login': None
        }

        # Create/update login row in usuarios_login using new empleado_id and documento_numero
        try:
            cur.execute("SELECT to_regclass(%s)", ('public.usuarios_login',))
            reg = cur.fetchone()
            if reg and reg[0]:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='usuarios_login'")
                ul_cols = [r[0] for r in cur.fetchall()]

                dni_nie = cleaned.get('documento_numero') or payload.get('documento_numero') or ''

                login_data = {}
                if 'empleado_id' in ul_cols:
                    login_data['empleado_id'] = empleado_id
                if 'dni_nie' in ul_cols:
                    login_data['dni_nie'] = dni_nie
                if 'password_hash' in ul_cols:
                    login_data['password_hash'] = ''
                if 'password_salt' in ul_cols:
                    login_data['password_salt'] = ''
                if 'activo' in ul_cols:
                    login_data['activo'] = True
                if 'creado_en' in ul_cols:
                    login_data['creado_en'] = datetime.utcnow().isoformat()

                if login_data:
                    existing_id = None
                    if 'empleado_id' in ul_cols:
                        cur.execute("SELECT usuario_id FROM usuarios_login WHERE empleado_id = %s LIMIT 1", (empleado_id,))
                        row = cur.fetchone()
                        existing_id = row[0]

                    if existing_id is None and 'dni_nie' in ul_cols and dni_nie:
                        cur.execute("SELECT usuario_id FROM usuarios_login WHERE dni_nie = %s LIMIT 1", (dni_nie,))
                        row = cur.fetchone()
                        existing_id = row[0]

                    if existing_id is not None:
                        up_keys = [k for k in login_data.keys() if k != 'creado_en']
                        if up_keys:
                            set_sql = ','.join([f"{k} = %s" for k in up_keys])
                            vals = [login_data[k] for k in up_keys] + [existing_id]
                            cur.execute(f"UPDATE usuarios_login SET {set_sql} WHERE usuario_id = %s", vals)
                            conn.commit()
                        inserted['usuario_login'] = existing_id
                    else:
                        ins_keys = [k for k in login_data.keys() if k in ul_cols]
                        cols_sql = ','.join(ins_keys)
                        vals = [login_data[k] for k in ins_keys]
                        placeholders = ','.join(['%s'] * len(vals))
                        cur.execute(f"INSERT INTO usuarios_login ({cols_sql}) VALUES ({placeholders}) RETURNING usuario_id", vals)
                        row = cur.fetchone()
                        conn.commit()
                        inserted['usuario_login'] = row[0] if row else None
        except Exception as e:
            # don't fail the whole request if usuarios_login upsert fails
            print('usuarios_login upsert failed:', e)

        try:
            # check table exists (one fetchonly)
            cur.execute("SELECT to_regclass(%s)", ('public.rider_operativo',))
            row = cur.fetchone()
            if not row or row[0] is None:
                # table doesn't exist; skip rider insert
                pass
        except Exception:
            # ignore and continue
            pass

        try:
            cur.execute("SELECT to_regclass(%s)", ('public.rider_operativo',))
            reg = cur.fetchone()
            if reg and reg[0]:
                # Skip rider_operativo insert when rider_id is not provided.
                # Some schemas enforce rider_id as NOT NULL.
                if payload.get('rider_id') in (None, ''):
                    inserted['rider_operativo_skipped'] = 'missing_rider_id'
                else:
                # prepare rider_operativo payload
                    rider_data = {
                        'empleado_id': empleado_id,
                        'rider_id': payload.get('rider_id')
                    }
                    if 'cod_activo' in payload and payload.get('cod_activo') not in (None, ''):
                        rider_data['cod_activo'] = payload.get('cod_activo')
                    if 'ciudad_id' in payload and payload.get('ciudad_id') not in (None, ''):
                        rider_data['ciudad_id'] = payload.get('ciudad_id')
                    # use provided fecha_inicio if present, otherwise use current UTC
                    if 'fecha_inicio' in payload and payload.get('fecha_inicio') not in (None, ''):
                        rider_data['fecha_inicio'] = payload.get('fecha_inicio')
                    else:
                        rider_data['fecha_inicio'] = datetime.utcnow().isoformat()
                    # default activo true unless explicitly provided
                    rider_data['activo'] = payload.get('activo') if 'activo' in payload else True

                    # detect columns on rider_operativo and insert only available ones
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='rider_operativo'")
                    cols = [r[0] for r in cur.fetchall()]
                    keys = [k for k in rider_data.keys() if k in cols]
                    if keys:
                        cols_sql = ','.join(keys)
                        vals = [rider_data[k] for k in keys]
                        placeholders = ','.join(['%s'] * len(vals))
                        cur.execute(f"INSERT INTO rider_operativo ({cols_sql}) VALUES ({placeholders}) RETURNING id", vals)
                        _rid = cur.fetchone()[0]
                        conn.commit()
                        inserted['rider_operativo'] = _rid
        except Exception as e:
            # don't fail the whole request if rider_operativo insert fails
            print('rider_operativo insert failed:', e)
            try:
                conn.rollback()
            except Exception:
                pass

        # If payload contains vehiculo_id, try to insert a row into vehiculo_asignacion
        try:
            cur.execute("SELECT to_regclass(%s)", ('public.vehiculo_asignacion',))
            reg = cur.fetchone()
            if reg and reg[0] and cleaned.get('vehiculo_id') not in (None, ''):
                va_data = {
                    'vehiculo_id': cleaned.get('vehiculo_id'),
                    'empleado_id': empleado_id,
                    'fecha_inicio': payload.get('fecha_inicio'),
                    'fecha_fin': payload.get('fecha_fin'),
                }
                # link rider_operativo when available
                if inserted.get('rider_operativo') not in (None, ''):
                    va_data['rider_operativo_id'] = inserted.get('rider_operativo')

                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='vehiculo_asignacion'")
                va_cols = [r[0] for r in cur.fetchall()]
                va_keys = [k for k in va_data.keys() if k in va_cols]

                if va_keys:
                    cols_sql = ','.join(va_keys)
                    vals = [va_data[k] for k in va_keys]
                    placeholders = ','.join(['%s'] * len(vals))
                    cur.execute(f"INSERT INTO vehiculo_asignacion ({cols_sql}) VALUES ({placeholders}) RETURNING id", vals)
                    _vaid = cur.fetchone()[0]
                    conn.commit()
                    inserted['vehiculo_asignacion'] = _vaid
                    inserted['vehiculo_asignacion_data'] = va_data
        except Exception as e:
            # don't fail the whole request if vehiculo_asignacion insert fails
            print('vehiculo_asignacion insert failed:', e)
            try:
                conn.rollback()
            except Exception:
                pass

        # Attempt to insert empleado_asignacion and create related puesto/puesto_sueldo or convenio/convenio_tramo
        # prepare container for debugging the assignment insertion
        assign_data = {}
        try:
            # detect if empleado_asignacion table exists by checking information_schema
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='empleado_asignacion'")
            cols_check = cur.fetchall()
            if not cols_check:
                # table does not exist; skip
                pass
            else:
                # build candidate assignment data from payload/cleaned
                assign_data = {'empleado_id': empleado_id}
                # copy common assignment fields from payload if present
                for f in ('departamento_id', 'ciudad_id', 'fecha_inicio', 'fecha_fin', 'puesto_nivel_id', 'puesto_sueldo_id', 'convenio_tramo_id', 'convenio'):
                    if f in cleaned and cleaned.get(f) not in (None, ''):
                        assign_data[f] = cleaned.get(f)

                # ensure fecha_inicio exists
                if 'fecha_inicio' not in assign_data:
                    assign_data['fecha_inicio'] = payload.get('fecha_inicio') or datetime.utcnow().isoformat()

                # handle puesto: either existing id in 'puesto' or create new puesto if string provided
                puesto_id = None
                try:
                    raw_puesto = cleaned.get('puesto') or cleaned.get('puesto_id')
                    if raw_puesto:
                        try:
                            pid = int(raw_puesto)
                        except Exception:
                            pid = None
                        if pid:
                            cur.execute("SELECT id FROM puesto WHERE id = %s", (pid,))
                            if cur.fetchone():
                                puesto_id = pid
                        else:
                            # create puesto if departamento provided
                            if cleaned.get('departamento_id'):
                                cur.execute("INSERT INTO puesto (departamento_id, nombre, tipo_sueldo, activo) VALUES (%s,%s,%s,%s) RETURNING id", (
                                    cleaned.get('departamento_id'), str(raw_puesto)[:255], 'FIJO', True
                                ))
                                row = cur.fetchone()
                                if row:
                                    puesto_id = row[0]
                                    conn.commit()
                except Exception as e:
                    print('puesto create/check failed', e)

                # if we have a puesto_id, handle puesto_sueldo association or creation
                if puesto_id:
                    assign_data['puesto_id'] = puesto_id
                    # detect empleado_asignacion columns
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='empleado_asignacion'")
                    assign_cols = [r[0] for r in cur.fetchall()]

                    # prefer explicit puesto_nivel_id from payload
                    if cleaned.get('puesto_nivel_id'):
                        # some schemas call it puesto_sueldo_id
                        if 'puesto_sueldo_id' in assign_cols:
                            assign_data['puesto_sueldo_id'] = cleaned.get('puesto_nivel_id')
                        elif 'puesto_nivel_id' in assign_cols:
                            assign_data['puesto_nivel_id'] = cleaned.get('puesto_nivel_id')
                    elif cleaned.get('puesto_sueldo') not in (None, ''):
                        # create a puesto_sueldo row
                        try:
                            nivel = 1
                            nombre_nivel = 'Nivel 1'
                            sueldo_val = cleaned.get('puesto_sueldo')
                            cur.execute("INSERT INTO puesto_sueldo (puesto_id, nivel, nombre_nivel, sueldo, activo) VALUES (%s,%s,%s,%s,%s) RETURNING id", (
                                puesto_id, nivel, nombre_nivel, sueldo_val, True
                            ))
                            row = cur.fetchone()
                            if row:
                                psid = row[0]
                                conn.commit()
                                if 'puesto_sueldo_id' in assign_cols:
                                    assign_data['puesto_sueldo_id'] = psid
                                elif 'puesto_nivel_id' in assign_cols:
                                    assign_data['puesto_nivel_id'] = psid
                        except Exception as e:
                            print('puesto_sueldo create failed', e)

                # handle convenio / convenio_tramo
                if cleaned.get('convenio'):
                    # if convenio_tramo_id provided, use it
                    if cleaned.get('convenio_tramo_id'):
                        assign_data['convenio_tramo_id'] = cleaned.get('convenio_tramo_id')
                    elif cleaned.get('convenio_tramo_sueldo') not in (None, ''):
                        # create tramo; use provided horas or default 40
                        try:
                            horas = cleaned.get('convenio_tramo_horas') or 40
                            sueldo_val = cleaned.get('convenio_tramo_sueldo')
                            cur.execute("INSERT INTO convenio_tramo (convenio_id, horas, sueldo) VALUES (%s,%s,%s) RETURNING id", (
                                cleaned.get('convenio'), horas, sueldo_val
                            ))
                            row = cur.fetchone()
                            if row:
                                ct_id = row[0]
                                conn.commit()
                                assign_data['convenio_tramo_id'] = ct_id
                        except Exception as e:
                            print('convenio_tramo create failed', e)

                # final insertion into empleado_asignacion using only existing columns
                try:
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='empleado_asignacion'")
                    cols = [r[0] for r in cur.fetchall()]

                    # build keys that exist in the table, with flexible mapping for common variants
                    keys_ins = [k for k in assign_data.keys() if k in cols]

                    # Support common column name variants: some schemas use `convenio_id` while
                    # others use `convenio`. If the payload provided `convenio` but the
                    # empleado_asignacion table exposes `convenio_id`, map it so the value
                    # is included in the INSERT below.
                    try:
                        if 'convenio' in assign_data and 'convenio_id' in cols and 'convenio_id' not in assign_data:
                            assign_data['convenio_id'] = assign_data['convenio']
                    except Exception:
                        pass

                    # helper: prefer alternative column names if present (e.g. puesto vs puesto_id, puesto_sueldo_id vs puesto_nivel_id)
                    def pick_alternative(preferred, alternatives):
                        for a in alternatives:
                            if a in cols and a not in keys_ins and a in assign_data:
                                keys_ins.append(a)
                                return True
                        # try without _id suffix
                        noid = preferred.replace('_id', '')
                        if noid in cols and preferred not in keys_ins and preferred in assign_data:
                            keys_ins.append(noid)
                            return True
                        return False

                    # attempt some heuristic mappings
                    try:
                        pick_alternative('puesto_id', ['puesto_id', 'puesto'])
                        pick_alternative('puesto_nivel_id', ['puesto_sueldo_id', 'puesto_nivel_id'])
                        pick_alternative('convenio_tramo_id', ['convenio_tramo_id', 'convenio_tramo'])
                    except Exception:
                        pass

                    # ensure uniqueness and order
                    keys_ins = [k for k in dict.fromkeys(keys_ins) if k in assign_data or k in cols]

                    if keys_ins:
                        cols_sql = ','.join(keys_ins)
                        vals = [assign_data.get(k) for k in keys_ins]
                        placeholders = ','.join(['%s'] * len(vals))
                        cur.execute(f"INSERT INTO empleado_asignacion ({cols_sql}) VALUES ({placeholders}) RETURNING id", vals)
                        _asid = cur.fetchone()[0]
                        conn.commit()
                        inserted['asignacion'] = _asid
                        # Map compensación to the assignment insertion: include related sueldo/tramo ids when available
                        try:
                            comp = {}
                            # prefer explicit convenio_tramo_id or puesto_sueldo_id / puesto_nivel_id from assign_data
                            if 'convenio_tramo_id' in assign_data and assign_data.get('convenio_tramo_id') not in (None, ''):
                                comp['convenio_tramo_id'] = assign_data.get('convenio_tramo_id')
                            if 'puesto_sueldo_id' in assign_data and assign_data.get('puesto_sueldo_id') not in (None, ''):
                                comp['puesto_sueldo_id'] = assign_data.get('puesto_sueldo_id')
                            elif 'puesto_nivel_id' in assign_data and assign_data.get('puesto_nivel_id') not in (None, ''):
                                comp['puesto_sueldo_id'] = assign_data.get('puesto_nivel_id')

                            # always include the empleado_asignacion id to indicate where compensación lives
                            comp['asignacion_id'] = _asid

                            inserted['compensacion'] = comp if comp else { 'asignacion_id': _asid }
                        except Exception:
                            # non-fatal: leave compensacion as None if mapping fails
                            pass
                    else:
                        # expose debug info when no matching columns found
                        inserted['asignacion_debug'] = {
                            'assign_data_keys': list(assign_data.keys()),
                            'empleado_asignacion_columns': cols
                        }
                except Exception as e:
                    print('empleado_asignacion final insert failed', e)
                    try:
                        logger.exception('empleado_asignacion insert exception')
                    except Exception:
                        pass
        except Exception as e:
            print('empleado_asignacion block failed', e)
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            # always expose the built assign_data for debugging purposes
            try:
                inserted['assign_data'] = assign_data
            except Exception:
                pass

        inserted['empleado'] = empleado_id

        return JSONResponse({
            "status": "empleado creado",
            "id": empleado_id,
            "drive_folder": root_id,
            "drive_folder_link": root_link,
            "inserts": inserted
        })

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def devtools_probe():
    """Ruta dummy para responder a peticiones de Chrome DevTools probing."""
    return JSONResponse({})


@app.get('/api/departamentos')
def list_departamentos():
    """Devuelve lista de departamentos {id, nombre}."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Try common table name variants and pick the first existing one
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('departamento','departamentos')")
        tables = [r[0] for r in cur.fetchall()]
        if not tables:
            print('list_departamentos: no departamento table found')
            return JSONResponse([])
        table = tables[0]
        # detect columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        cols = [r[0] for r in cur.fetchall()]
        name_col = 'nombre' if 'nombre' in cols else ('name' if 'name' in cols else None)
        if name_col is None:
            # no display name column
            cur.execute(f"SELECT id FROM {table} ORDER BY id")
            rows = cur.fetchall()
            cur.close()
            return JSONResponse([{"id": r[0], "nombre": None} for r in rows])
        # build query
        if name_col:
            cur.execute(f"SELECT id, {name_col} FROM {table} ORDER BY {name_col}")
        rows = cur.fetchall()
        cur.close()
        return JSONResponse([{"id": r[0], "nombre": r[1]} for r in rows])
    except Exception as e:
        # return empty list on error to avoid breaking the client UI during development
        print('list_ciudades error:', e)
        return JSONResponse([])
    finally:
        if conn:
            conn.close()


@app.get('/api/ciudades')
def list_ciudades(q: str = None):
    """Devuelve lista de ciudades {id, name}. Opcionalmente filtra por búsqueda `q`."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Try common table name variants
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('ciudad','ciudades')")
        tables = [r[0] for r in cur.fetchall()]
        if not tables:
            print('list_ciudades: no ciudad table found')
            return JSONResponse([])
        table = tables[0]
        # detect which column holds the city display name
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        cols = [r[0] for r in cur.fetchall()]
        display_col = None
        for candidate in ('name','municipio','nombre'):
            if candidate in cols:
                display_col = candidate
                break

        if not display_col:
            # no suitable name column; return ids only
            cur.execute(f"SELECT id FROM {table} LIMIT 1000")
            rows = cur.fetchall()
            cur.close()
            return JSONResponse([{"id": r[0], "name": None} for r in rows])

        if q:
            like = f"%{q}%"
            sql = f"SELECT id, {display_col} FROM {table} WHERE {display_col} ILIKE %s ORDER BY {display_col} LIMIT 200"
            cur.execute(sql, (like,))
        else:
            sql = f"SELECT id, {display_col} FROM {table} ORDER BY {display_col} LIMIT 1000"
            cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return JSONResponse([{"id": r[0], "name": r[1]} for r in rows])
    except Exception as e:
        print('list_ciudades error:', e)
        return JSONResponse([])
    finally:
        if conn:
            conn.close()


@app.post("/api/empleados/draft")
def save_empleado_draft(payload: dict):
    """Save a temporary draft of empleado form to app/drafts/{uuid}.json.

    If payload contains `draft_id`, it will overwrite that draft.
    Returns: {draft_id: ...}
    """
    drafts_dir = os.path.join('app', 'drafts')
    os.makedirs(drafts_dir, exist_ok=True)
    draft_id = payload.get('draft_id') or str(uuid.uuid4())
    path = os.path.join(drafts_dir, f"{draft_id}.json")
    data = payload.copy()
    # persist with UTC timestamp
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'created_at': datetime.utcnow().isoformat(), 'data': data}, f)
    return JSONResponse({'draft_id': draft_id})


@app.get('/api/departamento_retribucion/{departamento_id}')
def departamento_retribucion(departamento_id: int):
    """Devuelve el tipo de retribución para un departamento (p.ej. 'puesto' o 'convenio')."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT tipo_retribucion FROM departamento_retribucion WHERE departamento_id = %s LIMIT 1", (departamento_id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return JSONResponse({'tipo': None})
        # normalize to lowercase string (DB may store 'PUESTO' / 'CONVENIO')
        try:
            tipo_val = row[0]
            tipo_norm = None if tipo_val is None else str(tipo_val).strip().lower()
        except Exception:
            tipo_norm = None
        return JSONResponse({'tipo': tipo_norm})
    except Exception as e:
        print('departamento_retribucion error:', e)
        return JSONResponse({'tipo': None})
    finally:
        if conn: conn.close()


@app.get('/api/convenios')
def list_convenios(departamento_id: int = None):
    """Devuelve convenios para un departamento: {id, nombre}."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if departamento_id:
            cur.execute("SELECT id, nombre FROM convenio WHERE departamento_id = %s AND (activo IS TRUE OR activo IS NULL) ORDER BY nombre", (departamento_id,))
        else:
            cur.execute("SELECT id, nombre FROM convenio WHERE (activo IS TRUE OR activo IS NULL) ORDER BY nombre")
        rows = cur.fetchall()
        cur.close()
        return JSONResponse([{'id': r[0], 'nombre': r[1]} for r in rows])
    except Exception as e:
        print('list_convenios error:', e)
        return JSONResponse([])
    finally:
        if conn: conn.close()


@app.get('/api/convenio_tramos')
def list_convenio_tramos(convenio_id: int = None):
    """Devuelve tramos/sueldos para un convenio: {id, horas, sueldo}."""
    from .database import get_connection
    conn = None
    if not convenio_id:
        return JSONResponse([])
    try:
        conn = get_connection()
        cur = conn.cursor()
        # The `convenio_tramo` table does not have an `activo` column; return all tramos for the convenio
        cur.execute("SELECT id, horas, sueldo, created_at FROM convenio_tramo WHERE convenio_id = %s ORDER BY horas", (convenio_id,))
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            created_at = r[3] if len(r) > 3 else None
            result.append({
                'id': r[0],
                'horas': r[1],
                'sueldo': float(r[2]) if r[2] is not None else None,
                'created_at': created_at.isoformat() if getattr(created_at, 'isoformat', None) else (str(created_at) if created_at is not None else None)
            })
        return JSONResponse(result)
    except Exception as e:
        print('list_convenio_tramos error:', e)
        return JSONResponse([])
    finally:
        if conn: conn.close()


@app.post('/api/convenios')
def create_convenio(payload: dict):
    """Crear un nuevo convenio. Payload: { departamento_id, nombre, activo }"""
    from .database import get_connection
    conn = None
    try:
        departamento_id = payload.get('departamento_id')
        nombre = (payload.get('nombre') or '').strip()
        if not departamento_id or not nombre:
            raise HTTPException(status_code=400, detail='departamento_id y nombre son requeridos')
        activo = payload.get('activo') if 'activo' in payload else True
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO convenio (departamento_id, nombre, activo) VALUES (%s,%s,%s) RETURNING id, nombre, departamento_id",
                    (departamento_id, nombre, activo))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return JSONResponse({'id': row[0], 'nombre': row[1], 'departamento_id': row[2]})
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@app.post('/api/convenio_tramos')
def create_convenio_tramo(payload: dict):
    """Crear un nuevo tramo de convenio. Payload: { convenio_id, horas, sueldo }"""
    from .database import get_connection
    conn = None
    try:
        convenio_id = payload.get('convenio_id')
        horas = payload.get('horas')
        sueldo = payload.get('sueldo') if 'sueldo' in payload else None
        if not convenio_id or horas is None:
            raise HTTPException(status_code=400, detail='convenio_id y horas son requeridos')
        conn = get_connection()
        cur = conn.cursor()
        # Prevent duplicate (convenio_id, horas) which is constrained by a unique index
        cur.execute("SELECT id FROM convenio_tramo WHERE convenio_id = %s AND horas = %s", (convenio_id, horas))
        if cur.fetchone():
            cur.close()
            raise HTTPException(status_code=409, detail='Tramo para este convenio y horas ya existe')

        cur.execute("INSERT INTO convenio_tramo (convenio_id, horas, sueldo) VALUES (%s,%s,%s) RETURNING id, horas, sueldo, created_at",
                    (convenio_id, horas, sueldo))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        created_at = row[3] if len(row) > 3 else None
        return JSONResponse({
            'id': row[0],
            'horas': row[1],
            'sueldo': float(row[2]) if row[2] is not None else None,
            'created_at': created_at.isoformat() if getattr(created_at, 'isoformat', None) else (str(created_at) if created_at is not None else None)
        })
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@app.get('/api/puestos')
def list_puestos(departamento_id: int = None):
    """Devuelve puestos activos para un departamento: {id, nombre}."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if departamento_id:
            cur.execute("SELECT id, nombre FROM puesto WHERE departamento_id = %s AND (activo IS TRUE OR activo IS NULL) ORDER BY nombre", (departamento_id,))
        else:
            cur.execute("SELECT id, nombre FROM puesto WHERE (activo IS TRUE OR activo IS NULL) ORDER BY nombre")
        rows = cur.fetchall()
        cur.close()
        return JSONResponse([{'id': r[0], 'nombre': r[1]} for r in rows])
    except Exception as e:
        print('list_puestos error:', e)
        return JSONResponse([])
    finally:
        if conn: conn.close()


@app.get('/api/vehiculos')
def list_vehiculos():
    """Devuelve lista de vehículos / riders {id, nombre} para poblar selects."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Try common table name variants and pick the first existing one
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('vehiculo','vehiculos','rider','riders')")
        tables = [r[0] for r in cur.fetchall()]
        if not tables:
            print('list_vehiculos: no vehicle table found')
            return JSONResponse([])
        table = tables[0]
        # detect columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        cols = [r[0] for r in cur.fetchall()]
        # prefer sensible display columns
        name_col = None
        for candidate in ('nombre','name','modelo','matricula'):
            if candidate in cols:
                name_col = candidate
                break
        activo_col = 'activo' if 'activo' in cols else None
        if name_col is None:
            cur.execute(f"SELECT id FROM {table} ORDER BY id")
            rows = cur.fetchall()
            cur.close()
            return JSONResponse([{"id": r[0], "nombre": None} for r in rows])
        # build query
        if activo_col:
            cur.execute(f"SELECT id, {name_col} FROM {table} WHERE {activo_col} IS TRUE OR {activo_col} IS NULL ORDER BY {name_col}")
        else:
            cur.execute(f"SELECT id, {name_col} FROM {table} ORDER BY {name_col}")
        rows = cur.fetchall()
        cur.close()
        return JSONResponse([{"id": r[0], "nombre": r[1]} for r in rows])
    except Exception as e:
        print('list_vehiculos error:', e)
        return JSONResponse([])
    finally:
        if conn: conn.close()


@app.get('/api/vehiculo/{vehiculo_id}')
def get_vehiculo(vehiculo_id: int):
    """Devuelve los datos completos de un vehículo por id."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # get columns for vehiculo
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='vehiculo'")
        cols = [r[0] for r in cur.fetchall()]
        if not cols:
            cur.close()
            return JSONResponse({})
        sql = f"SELECT {', '.join(cols)} FROM vehiculo WHERE id = %s"
        cur.execute(sql, (vehiculo_id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return JSONResponse({})
        out = {}
        for i, c in enumerate(cols):
            v = row[i]
            if hasattr(v, 'isoformat'):
                out[c] = v.isoformat()
            else:
                out[c] = v
        return JSONResponse(out)
    except Exception as e:
        print('get_vehiculo error:', e)
        return JSONResponse({})
    finally:
        if conn: conn.close()


@app.get('/api/vehiculo_asignaciones')
def list_vehiculo_asignaciones(vehiculo_id: int = None):
    """Devuelve asignaciones (vehiculo_asignacion) para un vehículo: lista de registros."""
    from .database import get_connection
    conn = None
    if not vehiculo_id:
        return JSONResponse([])
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, vehiculo_id, rider_operativo_id, empleado_id, fecha_inicio, fecha_fin, activo, created_at FROM vehiculo_asignacion WHERE vehiculo_id = %s ORDER BY fecha_inicio DESC", (vehiculo_id,))
        rows = cur.fetchall()
        cur.close()
        result = []
        for r in rows:
            created_at = r[7] if len(r) > 7 else None
            result.append({
                'id': r[0],
                'vehiculo_id': r[1],
                'rider_operativo_id': r[2],
                'empleado_id': r[3],
                'fecha_inicio': r[4].isoformat() if getattr(r[4], 'isoformat', None) else (str(r[4]) if r[4] is not None else None),
                'fecha_fin': r[5].isoformat() if getattr(r[5], 'isoformat', None) else (str(r[5]) if r[5] is not None else None),
                'activo': r[6],
                'created_at': created_at.isoformat() if getattr(created_at, 'isoformat', None) else (str(created_at) if created_at is not None else None)
            })
        return JSONResponse(result)
    except Exception as e:
        print('list_vehiculo_asignaciones error:', e)
        return JSONResponse([])
    finally:
        if conn: conn.close()


@app.get('/api/puesto_sueldos')
def list_puesto_sueldos(puesto_id: int = None):
    """Devuelve niveles/sueldos para un puesto: {id, nivel, nombre_nivel, sueldo}.
    Si `puesto_id` es None devuelve []
    """
    from .database import get_connection
    conn = None
    if not puesto_id:
        return JSONResponse([])
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nivel, nombre_nivel, sueldo FROM puesto_sueldo WHERE puesto_id = %s AND (activo IS TRUE OR activo IS NULL) ORDER BY nivel", (puesto_id,))
        rows = cur.fetchall()
        cur.close()
        return JSONResponse([{'id': r[0], 'nivel': r[1], 'nombre_nivel': r[2], 'sueldo': float(r[3]) if r[3] is not None else None} for r in rows])
    except Exception as e:
        print('list_puesto_sueldos error:', e)
        return JSONResponse([])
    finally:
        if conn: conn.close()


@app.get('/api/lookups/label')
def lookup_label(kind: str, id: int):
    """Devuelve una etiqueta legible para un id de catálogo usado en formularios."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        kind_norm = str(kind or '').strip().lower()
        label = None

        if kind_norm == 'departamento':
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('departamento','departamentos') ORDER BY table_name LIMIT 1")
            table = (cur.fetchone() or [None])[0]
            if table:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s", (table,))
                cols = [r[0] for r in cur.fetchall()]
                name_col = 'nombre' if 'nombre' in cols else ('name' if 'name' in cols else None)
                if name_col:
                    cur.execute(f"SELECT {name_col} FROM {table} WHERE id = %s", (id,))
                    row = cur.fetchone()
                    label = row[0] if row else None

        elif kind_norm == 'ciudad':
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('ciudad','ciudades') ORDER BY table_name LIMIT 1")
            table = (cur.fetchone() or [None])[0]
            if table:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s", (table,))
                cols = [r[0] for r in cur.fetchall()]
                display_col = None
                for candidate in ('name', 'municipio', 'nombre'):
                    if candidate in cols:
                        display_col = candidate
                        break
                if display_col:
                    cur.execute(f"SELECT {display_col} FROM {table} WHERE id = %s", (id,))
                    row = cur.fetchone()
                    label = row[0] if row else None

        elif kind_norm == 'vehiculo':
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('vehiculo','vehiculos','rider','riders') ORDER BY table_name LIMIT 1")
            table = (cur.fetchone() or [None])[0]
            if table:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s", (table,))
                cols = [r[0] for r in cur.fetchall()]
                name_col = None
                for candidate in ('nombre', 'name', 'modelo', 'matricula'):
                    if candidate in cols:
                        name_col = candidate
                        break
                if name_col:
                    cur.execute(f"SELECT {name_col} FROM {table} WHERE id = %s", (id,))
                    row = cur.fetchone()
                    label = row[0] if row else None

        elif kind_norm == 'convenio_tramo':
            cur.execute("SELECT horas, sueldo FROM convenio_tramo WHERE id = %s", (id,))
            row = cur.fetchone()
            if row:
                horas = row[0]
                sueldo = row[1]
                if horas is not None and sueldo is not None:
                    label = f"{horas} h · {sueldo}"
                elif horas is not None:
                    label = f"{horas} h"
                else:
                    label = f"Tramo {id}"

        elif kind_norm == 'puesto_sueldo':
            cur.execute("SELECT nivel, nombre_nivel, sueldo FROM puesto_sueldo WHERE id = %s", (id,))
            row = cur.fetchone()
            if row:
                nivel = row[0]
                nombre_nivel = row[1]
                sueldo = row[2]
                if nombre_nivel:
                    label = str(nombre_nivel)
                elif nivel is not None:
                    label = f"Nivel {nivel}"
                else:
                    label = f"Puesto sueldo {id}"
                if sueldo is not None:
                    label = f"{label} · {sueldo}"

        if label is None:
            label = str(id)

        cur.close()
        return JSONResponse({'id': id, 'label': label})
    except Exception as e:
        print('lookup_label error:', e)
        return JSONResponse({'id': id, 'label': str(id)})
    finally:
        if conn:
            conn.close()


@app.post('/api/puestos')
def create_puesto(payload: dict):
    """Crear un nuevo puesto.
    Payload esperado: { departamento_id, nombre, tipo_sueldo (opcional), activo (opcional) }
    Devuelve el registro creado como JSON.
    """
    from .database import get_connection
    conn = None
    try:
        dep_id = payload.get('departamento_id')
        nombre = (payload.get('nombre') or '').strip()
        if not dep_id or not nombre:
            raise HTTPException(status_code=400, detail='departamento_id y nombre son requeridos')
        tipo_sueldo = payload.get('tipo_sueldo') or 'FIJO'
        activo = payload.get('activo') if 'activo' in payload else True
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO puesto (departamento_id, nombre, tipo_sueldo, activo) VALUES (%s,%s,%s,%s) RETURNING id, nombre, departamento_id",
                    (dep_id, nombre, tipo_sueldo, activo))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return JSONResponse({'id': row[0], 'nombre': row[1], 'departamento_id': row[2]})
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@app.post('/api/puesto_sueldos')
def create_puesto_sueldo(payload: dict):
    """Crear un nuevo nivel/sueldo para un puesto.
    Payload esperado: { puesto_id, nivel, nombre_nivel (opcional), sueldo (num) }
    Devuelve el registro creado.
    """
    from .database import get_connection
    conn = None
    try:
        puesto_id = payload.get('puesto_id')
        nivel = payload.get('nivel')
        nombre_nivel = (payload.get('nombre_nivel') or f'Nivel {nivel}').strip()
        sueldo = payload.get('sueldo') if 'sueldo' in payload else None
        activo = payload.get('activo') if 'activo' in payload else True
        if not puesto_id or nivel is None:
            raise HTTPException(status_code=400, detail='puesto_id y nivel son requeridos')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO puesto_sueldo (puesto_id, nivel, nombre_nivel, sueldo, activo) VALUES (%s,%s,%s,%s,%s) RETURNING id, nivel, nombre_nivel, sueldo",
                    (puesto_id, nivel, nombre_nivel, sueldo, activo))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return JSONResponse({'id': row[0], 'nivel': row[1], 'nombre_nivel': row[2], 'sueldo': float(row[3]) if row[3] is not None else None})
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@app.get('/api/empleados/draft/{draft_id}')
def load_empleado_draft(draft_id: str):
    path = os.path.join('app', 'drafts', f"{draft_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Draft not found')
    with open(path, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    return JSONResponse(obj)


# OAuth endpoints removed: this app now uses a Service Account for Drive operations.


@app.get('/debug/schema')
def debug_schema():
    """Dev endpoint (dev only) — devuelve tablas/columnas relacionadas con departamentos/ciudades."""
    from .database import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        info = {}
        for tbl in ('departamento','departamentos','ciudad','ciudades','empleados'):
            cur.execute("SELECT to_regclass(%s)", (f'public.{tbl}',))
            exists = cur.fetchone()[0] is not None
            if exists:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (tbl,))
                cols = [r[0] for r in cur.fetchall()]
            else:
                cols = []
            info[tbl] = {'exists': exists, 'columns': cols}
        cur.close()
        return JSONResponse(info)
    except Exception as e:
        return JSONResponse({'error': str(e)})
    finally:
        if conn:
            conn.close()