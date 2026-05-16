
from fastapi import APIRouter, Request, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return RedirectResponse("/qnla/admin/torneos")


@router.get("/empleados/alta", response_class=HTMLResponse)
@router.get("/empleados/alta-empleado", response_class=HTMLResponse)
def alta_empleado(request: Request):
    return templates.TemplateResponse("empleados_alta.html", {"request": request})


@router.get("/empleados/alta-por-fichero", response_class=HTMLResponse)
def alta_por_fichero(request: Request):
    """Vista para subir ficheros ITA y visualizar tabla temporal."""
    return templates.TemplateResponse("alta_por_fichero.html", {"request": request})


@router.get('/empleados/rider-operativo-por-fichero', response_class=HTMLResponse)
def rider_operativo_por_fichero_view(request: Request):
    """Vista para cargar registros rider_operativo desde un CSV."""
    return templates.TemplateResponse("rider_operativo_por_fichero.html", {"request": request})


@router.get('/empleados/vehiculo-asignacion-por-fichero', response_class=HTMLResponse)
def vehiculo_asignacion_por_fichero_view(request: Request):
    """Vista para cargar registros vehiculo_asignacion desde un CSV."""
    return templates.TemplateResponse("vehiculo_asignacion_por_fichero.html", {"request": request})


@router.get('/empleados/alta-usuario-admin', response_class=HTMLResponse)
def alta_usuario_admin(request: Request):
    """Vista para dar de alta usuarios administradores."""
    return templates.TemplateResponse("usuario_admin_alta.html", {"request": request})


@router.get('/empleados/consulta-usuario-admin', response_class=HTMLResponse)
def consulta_usuario_admin(request: Request):
    """Vista para consultar usuarios administradores."""
    return templates.TemplateResponse("usuario_admin_consulta.html", {"request": request})


@router.get('/empleados/modificacion-usuario-admin', response_class=HTMLResponse)
def modificacion_usuario_admin(request: Request):
    """Vista para modificar usuarios administradores."""
    return templates.TemplateResponse("usuario_admin_modificacion.html", {"request": request})


@router.get('/ciudades/alta', response_class=HTMLResponse)
def alta_ciudad(request: Request):
    """Vista simple para dar de alta una ciudad."""
    return templates.TemplateResponse("ciudad_alta.html", {"request": request})


@router.get('/ciudades/listado', response_class=HTMLResponse)
def listado_ciudad_view(request: Request):
    """Vista para listar registros de ciudad."""
    return templates.TemplateResponse("ciudad_listado.html", {"request": request})


@router.get('/ciudades/modificacion', response_class=HTMLResponse)
def modificacion_ciudad(request: Request):
    """Vista para modificar una ciudad existente."""
    return templates.TemplateResponse("ciudad_modificacion.html", {"request": request})


@router.get('/empleados', response_class=HTMLResponse)
def lista_empleados_redirect(request: Request):
    """Ruta de lista de empleados — actualmente redirige al dashboard si no existe vista específica."""
    return RedirectResponse('/')





@router.get("/.well-known/appspecific/com.chrome.devtools.json")
def devtools_probe():
    """Ruta dummy para responder a peticiones de Chrome DevTools probing."""
    return JSONResponse({})

@router.get('/consentimiento', response_class=HTMLResponse)
def consentimiento_ciudad_view(request: Request):
    return templates.TemplateResponse("consulta_consentimiento.html", {"request": request})



# Ruta clara y única para consentimiento WhatsApp
@router.get("/herramientas/consentimiento-whatsapp", response_class=HTMLResponse)
def consentimiento_whatsapp(request: Request):
    return templates.TemplateResponse("consentimiento_whatsapp.html", {"request": request})

app = FastAPI()
@app.get("/health")
def health():
    return {"status": "running"}