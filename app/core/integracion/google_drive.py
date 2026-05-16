print("[DEBUG] Entrando en app/core/integracion/google_drive.py ...")
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth import default as auth_default
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import logging
import time
import os
import json

SCOPES = ["https://www.googleapis.com/auth/drive"]

# Shared drive id used by the app (keep if you have a specific shared drive)
SHARED_DRIVE_ID = "0APwyMrIG-3zWUk9PVA"

# cache para reducir llamadas a API
FOLDER_CACHE = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_drive_service_for_user(email: str):
    """Return a Drive service.

    Prefer Service Account / Application Default Credentials when available
    (recommended for Cloud Run). If service credentials are not present the
    function falls back to loading per-user stored credentials from
    `app/tokens/{email}.json` to preserve backward compatibility.
    """
    # Try to use service account / ADC for server-side operations (recommended)
    try:
        creds = _get_service_credentials()
        return build("drive", "v3", credentials=creds)
    except Exception:
        # Fallback: try loading user token on disk (legacy flow)
        creds = load_user_credentials(email)
        return build("drive", "v3", credentials=creds)


def execute_request(request, retries=3):
    for i in range(retries):
        try:
            return request.execute()
        except HttpError as e:
            # Log detailed HttpError information to help debugging (status, content)
            try:
                content = getattr(e, 'content', None) or getattr(e, 'resp', None)
            except Exception:
                content = None

            if i == retries - 1:
                logger.exception("Google API HttpError final failure: %s %s", e, content)
                raise

            logger.warning("Retry Google API (attempt %s/%s) due to HttpError: %s %s", i + 1, retries, e, content)
            time.sleep(2 ** i)
        except Exception as e:
            # Non-HTTP errors should also be visible in logs
            if i == retries - 1:
                logger.exception("Google API unexpected error final failure: %s", e)
                raise
            logger.warning("Retry Google API (attempt %s/%s) due to unexpected error: %s", i + 1, retries, e)
            time.sleep(2 ** i)


def crear_carpeta(drive, nombre, parent_id):
    metadata = {
        "name": nombre,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }

    try:
        logger.debug("Creating folder on Drive: name=%s parent=%s", nombre, parent_id)
        folder = drive.files().create(
            body=metadata,
            supportsAllDrives=True,
            fields="id, webViewLink"
        ).execute()
        logger.info("Created folder: %s (parent=%s)", folder.get('id'), parent_id)
        return folder
    except HttpError as e:
        # Provide as much context as possible in the log
        try:
            content = e.content.decode('utf-8') if getattr(e, 'content', None) else None
        except Exception:
            content = str(e)
        logger.exception("Failed to create folder '%s' under parent '%s': %s", nombre, parent_id, content)
        raise
    except Exception as e:
        logger.exception("Unexpected error creating folder '%s' under parent '%s': %s", nombre, parent_id, e)
        raise


def crear_carpeta_empleado(drive, nombre):
    """Crear una carpeta directamente en el Shared Drive configurado usando el drive provisto."""
    return crear_carpeta(drive, nombre, SHARED_DRIVE_ID)


# Note: all callers now use `crear_carpeta(drive, ...)` directly; helper removed.


# Compatibility stubs for code paths that expected OAuth flow. When running
# with Application Default Credentials these are not used, but importing
# them keeps `app.main` from failing.
def get_auth_url(request):
    import tempfile
    import os
    # Si existe la variable de entorno GOOGLE_OAUTH_JSON, úsala
    google_oauth_json = os.environ.get("GOOGLE_OAUTH_JSON")
    if google_oauth_json:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as tmp:
            tmp.write(google_oauth_json)
            tmp.flush()
            flow = Flow.from_client_secrets_file(
                tmp.name,
                scopes=SCOPES,
                redirect_uri="http://localhost:8000/google/callback"
            )
        os.unlink(tmp.name)
    else:
        flow = Flow.from_client_secrets_file(
            "app/google-oauth.json",
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/google/callback"
        )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    # guardar PKCE verifier directamente en sesión (sin silenciar fallos)
    # es importante que la sesión persista entre /google/login y /google/callback
    request.session["pkce_code_verifier"] = flow.code_verifier
    try:
        logger.info("Saved pkce_code_verifier in session: %s", bool(flow.code_verifier))
    except Exception:
        pass

    return auth_url, state


def get_credentials(request, code):
    # recuperar el verifier desde la sesión
    code_verifier = request.session.get("pkce_code_verifier")
    try:
        logger.info("Retrieved pkce_code_verifier from session: %s", bool(code_verifier))
        # optionally log keys present in session for debugging
        logger.debug("Session keys: %s", list(request.session.keys()))
    except Exception:
        pass

    import tempfile
    import os
    google_oauth_json = os.environ.get("GOOGLE_OAUTH_JSON")
    if google_oauth_json:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as tmp:
            tmp.write(google_oauth_json)
            tmp.flush()
            flow = Flow.from_client_secrets_file(
                tmp.name,
                scopes=SCOPES,
                redirect_uri="http://localhost:8000/google/callback"
            )
        os.unlink(tmp.name)
    else:
        flow = Flow.from_client_secrets_file(
            "app/google-oauth.json",
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/google/callback"
        )

    # IMPORTANTE: pasar code_verifier explícitamente a fetch_token
    flow.fetch_token(
        code=code,
        code_verifier=code_verifier
    )

    # cleanup: remove verifier after exchange to avoid reuse
    try:
        if "pkce_code_verifier" in request.session:
            del request.session["pkce_code_verifier"]
    except Exception:
        pass

    return flow.credentials


# ---------------------------
# Service Account helpers
# ---------------------------

SERVICE_ACCOUNT_FILE = os.environ.get('SERVICE_ACCOUNT_FILE', 'app/service-account.json')


def _get_service_credentials():
    """Return credentials from a service account JSON file or Application Default Credentials.

    Raises an Exception if no service credentials are available.
    """
    # Prefer explicit service account JSON if present in the container
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        return service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )

    # Otherwise try Application Default Credentials (e.g., Cloud Run with attached service account)
    creds, project = auth_default(scopes=SCOPES)
    if creds is None:
        raise RuntimeError('No service account credentials available (set SERVICE_ACCOUNT_FILE or enable ADC)')
    return creds


def save_credentials(credentials, path="app/token.json"):
    # Persist credentials JSON to disk. This will be used in the OAuth per-user flow
    # to store tokens under app/tokens/{email}.json (main.google_callback handles the
    # email resolution and writes there). This helper keeps the historical default location.
    data = None
    try:
        data = json.loads(credentials.to_json())
    except Exception:
        # credentials.to_json() may already be JSON string
        try:
            data = json.loads(str(credentials))
        except Exception:
            data = None

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        if data is None:
            # fallback: write raw string
            f.write(credentials.to_json())
        else:
            json.dump(data, f)


def crear_estructura_en_shared_drive(drive, shared_drive_id, city_name, empleado_nombre):
    """Compatibility wrapper that creates the employee folder structure using
    the provided `drive` resource (used by older code paths)."""
    if not empleado_nombre or not empleado_nombre.strip():
        raise ValueError("Nombre empleado inválido")

    emp_name = " ".join(empleado_nombre.split()).upper()

    # per-request cache to avoid cross-user cache leakage
    cache = {}

    # ciudad
    city_id = _find_folder(drive, city_name, shared_drive_id, shared_drive_id, cache=cache)

    if not city_id:
        logger.info("Creando ciudad %s", city_name)
        city = crear_carpeta(drive, city_name, shared_drive_id)
        city_id = city["id"]

    # empleado
    emp_id = _find_folder(drive, emp_name, city_id, shared_drive_id, cache=cache)

    emp_link = None

    if not emp_id:
        logger.info("Creando empleado %s", emp_name)
        emp = crear_carpeta(drive, emp_name, city_id)
        emp_id = emp["id"]
        emp_link = emp.get("webViewLink")
    else:
        meta = execute_request(
            drive.files().get(
                fileId=emp_id,
                fields="webViewLink",
                supportsAllDrives=True
            )
        )
        emp_link = meta.get("webViewLink")

    # estructura interna
    for carpeta, subs in ESTRUCTURA.items():
        carpeta_id = _find_folder(drive, carpeta, emp_id, shared_drive_id, cache=cache)

        if not carpeta_id:
            folder = crear_carpeta(drive, carpeta, emp_id)
            carpeta_id = folder["id"]

        for sub in subs:
            sub_id = _find_folder(drive, sub, carpeta_id, shared_drive_id, cache=cache)
            if not sub_id:
                crear_carpeta(drive, sub, carpeta_id)

    return {"id": emp_id, "link": emp_link}


def crear_estructura_empleado_with_drive(drive, carpeta_nombre):
    """Compatibility overload used by fallback paths in `app.main`.
    Creates a single folder named `carpeta_nombre` under the configured
    `SHARED_DRIVE_ID` using the provided `drive` resource and returns the id."""
    folder = crear_carpeta(drive, carpeta_nombre, SHARED_DRIVE_ID)
    return folder.get("id")


def _find_folder(drive, name, parent_id=None, drive_id=None, cache=None):

    # allow a per-request cache to avoid returning folder ids created by other
    # users in concurrent requests. If no cache is provided, fall back to the
    # global FOLDER_CACHE for compatibility.
    if cache is None:
        cache = FOLDER_CACHE

    # normalize and uppercase to avoid case-variance creating duplicate folders
    cache_key = f"{parent_id}:{(name or '').strip().upper()}"

    if cache_key in cache:
        return cache[cache_key]

    safe_name = (name or "").strip().upper().replace("'", "\\'")

    q = (
        "mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false "
        f"and name = '{safe_name}'"
    )

    if parent_id:
        q += f" and '{parent_id}' in parents"

    params = {
        "q": q,
        "fields": "files(id,name)",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True
    }

    if drive_id:
        params["driveId"] = drive_id
        params["corpora"] = "drive"
    logger.debug("Searching for folder: name=%s parent=%s drive=%s q=%s", safe_name, parent_id, drive_id, q)
    try:
        res = execute_request(drive.files().list(**params))
    except HttpError as e:
        try:
            content = e.content.decode('utf-8') if getattr(e, 'content', None) else str(e)
        except Exception:
            content = str(e)
        logger.error("Drive folder search failed for '%s' under parent '%s': %s", name, parent_id, content)
        raise
    except Exception as e:
        logger.error("Drive folder search unexpected error for '%s' under parent '%s': %s", name, parent_id, e)
        raise

    files = res.get("files", [])

    if files:
        fid = files[0]["id"]
        cache[cache_key] = fid
        logger.debug("Found folder '%s' -> id=%s (parent=%s)", name, fid, parent_id)
        return fid

    return None


# ---------------------------
# ESTRUCTURA EMPLEADO
# ---------------------------

ESTRUCTURA = {
    "Alta": [],
    "Contrato": [],
    "Nóminas": [],
    "Carta vacaciones": [],
    "Carta dotación": [],
    "Carta méritos": [],
    "Amonestación": [],
    "Documentación": [
        "Doc. Identidad",
        "Cert. Seguridad Social",
        "Certificado Bancario",
    ],
    "Incapacidades": [],
}


def crear_estructura_empleado(drive, shared_drive_id, city_name, empleado_nombre):
    if not empleado_nombre or not empleado_nombre.strip():
        raise ValueError("Nombre empleado inválido")

    emp_name = " ".join(empleado_nombre.split()).upper()

    # per-request cache to avoid cross-user cache leakage
    cache = {}

    # ciudad
    logger.debug("crear_estructura_empleado: looking for city '%s' in shared_drive '%s'", city_name, shared_drive_id)
    city_id = _find_folder(drive, city_name, shared_drive_id, shared_drive_id, cache=cache)

    if not city_id:
        logger.info("Creando ciudad %s", city_name)
        try:
            city = crear_carpeta(drive, city_name, shared_drive_id)
            city_id = city["id"]
        except Exception:
            logger.exception("Failed creating city folder '%s' in shared drive '%s'", city_name, shared_drive_id)
            raise

    # empleado
    emp_id = _find_folder(drive, emp_name, city_id, shared_drive_id, cache=cache)

    emp_link = None

    if not emp_id:
        logger.info("Creando empleado %s", emp_name)
        try:
            emp = crear_carpeta(drive, emp_name, city_id)
            emp_id = emp["id"]
            emp_link = emp.get("webViewLink")
        except Exception:
            logger.exception("Failed creating employee folder '%s' under city '%s'", emp_name, city_id)
            # continue without raising so caller can decide; in main we handle best-effort
            emp_id = None
            emp_link = None
    else:
        meta = execute_request(
            drive.files().get(
                fileId=emp_id,
                fields="webViewLink",
                supportsAllDrives=True
            )
        )
        emp_link = meta.get("webViewLink")

    # estructura interna
    for carpeta, subs in ESTRUCTURA.items():
        carpeta_id = _find_folder(drive, carpeta, emp_id, shared_drive_id, cache=cache)

        if not carpeta_id:
            folder = crear_carpeta(drive, carpeta, emp_id)
            carpeta_id = folder["id"]

        for sub in subs:
            sub_id = _find_folder(drive, sub, carpeta_id, shared_drive_id, cache=cache)
            if not sub_id:
                crear_carpeta(drive, sub, carpeta_id)

    return {"id": emp_id, "link": emp_link}


def load_user_credentials(email: str):
    """Load stored user credentials for `email` from `app/tokens/{email}.json`.

    Returns a `google.oauth2.credentials.Credentials` instance.
    """
    token_path = os.path.join('app', 'tokens', f"{email}.json")
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"Token for {email} not found at {token_path}")
    with open(token_path, 'r', encoding='utf-8') as f:
        info = json.load(f)

    # `info` should be the authorized user info dict (the result of Credentials.to_json())
    creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)

    # If the access token is expired and we have a refresh token, refresh it
    # and persist the updated credentials to disk so future requests keep working.
    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
    except Exception:
        # best-effort: if refresh fails, let the caller handle the 401
        try:
            logger.exception('Could not refresh token for %s', email)
        except Exception:
            pass

    return creds