from google.auth import default
from googleapiclient.discovery import build
import logging
import time
import argparse

# ---------------------------
# Configuración
# ---------------------------

SCOPES = ["https://www.googleapis.com/auth/drive"]
DEFAULT_SHARED_DRIVE_ID = "0APwyMrIG-3zWUk9PVA"  # tu Shared Drive real
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# ---------------------------
# Funciones de Drive
# ---------------------------

FOLDER_CACHE = {}

def execute_request(request, retries=3):
    for i in range(retries):
        try:
            return request.execute()
        except Exception as e:
            if i == retries - 1:
                raise
            logger.warning("Retry Google API due to error: %s", e)
            time.sleep(2 ** i)

def crear_carpeta(drive, nombre, parent_id):
    metadata = {
        "name": nombre,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = drive.files().create(
        body=metadata,
        supportsAllDrives=True,
        fields="id, webViewLink"
    ).execute()
    return folder

def _find_folder(drive, name, parent_id, cache=None):
    if cache is None:
        cache = FOLDER_CACHE

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

    res = execute_request(drive.files().list(**params))
    files = res.get("files", [])
    if files:
        fid = files[0]["id"]
        cache[cache_key] = fid
        return fid
    return None

def crear_estructura_empleado(drive, shared_drive_id, city_name, empleado_nombre):
    if not empleado_nombre or not empleado_nombre.strip():
        raise ValueError("Nombre empleado inválido")
    emp_name = " ".join(empleado_nombre.split()).upper()
    cache = {}

    # Carpeta ciudad
    city_id = _find_folder(drive, city_name, shared_drive_id, cache=cache)
    if not city_id:
        logger.info("Creando ciudad %s", city_name)
        city = crear_carpeta(drive, city_name, shared_drive_id)
        city_id = city["id"]

    # Carpeta empleado
    emp_id = _find_folder(drive, emp_name, city_id, cache=cache)
    if not emp_id:
        logger.info("Creando empleado %s", emp_name)
        emp = crear_carpeta(drive, emp_name, city_id)
        emp_id = emp["id"]
        emp_link = emp.get("webViewLink")
    else:
        meta = execute_request(drive.files().get(
            fileId=emp_id, fields="webViewLink", supportsAllDrives=True
        ))
        emp_link = meta.get("webViewLink")

    # Crear estructura interna
    for carpeta, subs in ESTRUCTURA.items():
        carpeta_id = _find_folder(drive, carpeta, emp_id, cache=cache)
        if not carpeta_id:
            folder = crear_carpeta(drive, carpeta, emp_id)
            carpeta_id = folder["id"]
        for sub in subs:
            sub_id = _find_folder(drive, sub, carpeta_id, cache=cache)
            if not sub_id:
                crear_carpeta(drive, sub, carpeta_id)

    return {"id": emp_id, "link": emp_link}

# ---------------------------
# MAIN
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Crear estructura de empleado en Shared Drive usando ADC")
    parser.add_argument("--city", "-c", default="MADRID", help="Nombre de la ciudad (carpeta)")
    parser.add_argument("--name", "-n", default="Juan Pérez", help="Nombre del empleado")
    parser.add_argument("--drive", "-d", default=DEFAULT_SHARED_DRIVE_ID, help="ID del Shared Drive")
    parser.add_argument("--dry-run", action="store_true", help="No crear nada; solo mostrar acciones previstas")
    args = parser.parse_args()

    # Credenciales ADC (gcloud auth application-default login)
    creds, _ = default(scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds)

    city_name = args.city
    empleado_nombre = args.name
    shared_drive_id = args.drive

    if args.dry_run:
        logger.info("Dry run: se mostrarán las acciones pero no se crearán carpetas")
        # For dry-run we will only check existing folder ids without creating
        # Attempt to find city and employee and print what would be created
        city_id = _find_folder(drive, city_name, shared_drive_id, cache={})
        if city_id:
            logger.info("Ciudad ya existe: %s", city_id)
        else:
            logger.info("Ciudad NO existe y sería creada: %s", city_name)

        emp_id = None
        if city_id:
            emp_id = _find_folder(drive, " ".join(empleado_nombre.split()).upper(), city_id, cache={})

        if emp_id:
            logger.info("Empleado ya existe: %s", emp_id)
        else:
            logger.info("Empleado NO existe y sería creado: %s", empleado_nombre)

        logger.info("Dry run finalizado")
        return

    result = crear_estructura_empleado(drive, shared_drive_id, city_name, empleado_nombre)
    print("Estructura creada correctamente:")
    print(result)


if __name__ == "__main__":
    main()
