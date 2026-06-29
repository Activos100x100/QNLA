
"""
Aplicación principal FastAPI para procesamiento de facturas.
Integra todos los componentes: routers, base de datos, servicios.
"""

import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import Base, engine

# Importar todos los modelos para registrar con Base
# (Necesario para que SQLAlchemy configure las relaciones)
from app.models import (
    Empresa, Estado, TipoGasto, Configuracion,
    Proveedor, Cliente, Etiqueta, DriveCarpeta,
    Factura, FacturaLinea, FacturaEtiqueta, FacturaComentario,
    FacturaAdjunto, FacturaHistorial,
    OcrResultado, IaResultado,
    Auditoria, Notificacion, Log,
    Comentario, ComentarioAuditoria,
    UsuarioLogin,  # noqa: F401 – registra tabla en Base.metadata
    EmpleadoAsignacion,  # noqa: F401
    RiderOperativo,  # noqa: F401
    RtosMesOperativo,  # noqa: F401
    RtosMesSemana,  # noqa: F401
    RtosCashOutDeuda,  # noqa: F401
)

# Importar routers
from app.routers.auth import router as auth_router, set_jinja_env as auth_set_jinja_env
from app.routers.home import router as home_router, set_jinja_env as home_set_jinja_env
from app.routers.comentarios import router as comentarios_router
from app.routers.facturas import router as facturas_router
from app.routers.facturas_simple import router as facturas_simple_router
# TODO: Empresas, Proveedores, Clientes = Features futuras (no MVP)

# Importar servicios de auth para middleware
from app.services.auth_service import COOKIE_NAME, verificar_token_sesion

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear tablas en base de datos
Base.metadata.create_all(bind=engine)
logger.info("Tablas de base de datos creadas")

# Crear aplicación FastAPI
app = FastAPI(
    title="Procesador de Facturas",
    description="Aplicación para escanear, procesar y gestionar facturas españolas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Montar archivos estáticos
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Archivos estáticos montados desde: {static_path}")

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Configurar Jinja2 directamente
templates_path = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_path)),
    autoescape=select_autoescape(['html', 'xml'])
)
logger.info(f"Jinja2 Environment initialized with templates path: {templates_path}")
logger.info(f"Templates path exists: {templates_path.exists()}")

# Inyectar jinja_env en los routers que lo necesitan
auth_set_jinja_env(jinja_env)
home_set_jinja_env(jinja_env)

# Incluir routers
app.include_router(auth_router)          # /login, /logout
app.include_router(home_router)          # /home
app.include_router(facturas_simple_router)  # MVP: Upload simple
app.include_router(facturas_router)
app.include_router(comentarios_router)
# TODO: Habilitar otros routers cuando sean necesarios
logger.info("Routers incluidos en la aplicación")


# ---------------------------------------------------------------------------
# Middleware de autenticación
# ---------------------------------------------------------------------------

# Rutas que no requieren sesión
_AUTH_EXEMPT_PREFIXES = (
    "/login",
    "/logout",
    "/health",
    "/static/",
    "/api/",
    "/docs",
    "/openapi",
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Primera capa de autenticación.
    Protege todas las rutas excepto las exentas.
    """
    path = request.url.path

    # Permitir rutas exentas sin sesión
    if any(path.startswith(prefix) for prefix in _AUTH_EXEMPT_PREFIXES):
        return await call_next(request)

    # Verificar cookie de sesión
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return RedirectResponse(url="/login", status_code=303)

    usuario = verificar_token_sesion(token)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=303)

    # Propagar datos del usuario al request para que los routers los lean
    request.state.usuario = usuario
    return await call_next(request)


@app.get("/", include_in_schema=False)
async def index():
    """
    Redirige a la página de subida MVP.
    Evita mostrar la home legacy que no tiene JS de upload conectado.
    """
    return RedirectResponse(url="/subir-factura", status_code=307)


@app.get("/health")
async def health_check():
    """
    Verificación de salud de la aplicación.
    """
    return {
        "status": "ok",
        "aplicacion": "Procesador de Facturas",
        "version": "1.0.0"
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard con listado de facturas procesadas."""
    try:
        return jinja_env.get_template('dashboard_facturas.html').render()
    except Exception as e:
        return f"<h1>Error: {e}</h1>"


@app.get("/subir-factura", response_class=HTMLResponse)
async def subir_factura_page(request: Request):
    """Página móvil MVP: Un botón para subir factura."""
    try:
        usuario = getattr(request.state, "usuario", {}) or {}
        nombre = usuario.get("nombre", "")
        from datetime import datetime
        hora = datetime.now().hour
        if 6 <= hora < 14:
            saludo = "Buenos días"
        elif 14 <= hora < 21:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        return jinja_env.get_template('subir_factura.html').render(
            nombre=nombre, saludo=saludo
        )
    except Exception as e:
        logger.error(f"Error renderizando página de upload: {e}")
        return f"<h1>Error: {e}</h1>"


@app.get("/facturas", response_class=HTMLResponse)
async def cargar_facturas(request: Request):
    """Redirige a /subir-factura (MVP)."""
    return """
    <script>window.location.href = '/subir-factura';</script>
    """


def get_pagina_principal() -> str:
    """
    Retorna el HTML de la página principal.
    """
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Procesador de Facturas</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary-color: #2563eb;
                --success-color: #10b981;
                --danger-color: #ef4444;
            }
            
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            .navbar {
                background: rgba(255, 255, 255, 0.95);
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .navbar-brand {
                font-weight: 700;
                color: var(--primary-color) !important;
                font-size: 1.3rem;
            }
            
            .container-principal {
                margin-top: 40px;
                margin-bottom: 40px;
            }
            
            .card {
                border: none;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                background: rgba(255, 255, 255, 0.98);
            }
            
            .card-header {
                background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%);
                color: white;
                border-radius: 15px 15px 0 0 !important;
                padding: 20px;
                font-size: 1.2rem;
                font-weight: 600;
            }
            
            .card-body {
                padding: 30px;
            }
            
            .drop-zone {
                border: 3px dashed var(--primary-color);
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #f8fafc;
            }
            
            .drop-zone:hover,
            .drop-zone.dragover {
                background: #eff6ff;
                border-color: #3b82f6;
                box-shadow: 0 5px 15px rgba(37, 99, 235, 0.2);
            }
            
            .drop-zone i {
                font-size: 3rem;
                color: var(--primary-color);
                margin-bottom: 15px;
            }
            
            .drop-zone-text {
                font-size: 1.1rem;
                color: #666;
                margin-bottom: 10px;
            }
            
            .input-file {
                display: none;
            }
            
            .btn-upload {
                background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%);
                border: none;
                color: white;
                padding: 12px 30px;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .btn-upload:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
            }
            
            .progress-container {
                display: none;
                margin-top: 20px;
            }
            
            .progress-bar {
                background: linear-gradient(90deg, var(--primary-color) 0%, #3b82f6 100%);
            }
            
            .alert {
                border-radius: 10px;
                border: none;
            }
            
            .alert-success {
                background: #d1fae5;
                color: #065f46;
            }
            
            .alert-danger {
                background: #fee2e2;
                color: #7f1d1d;
            }
            
            .alert-info {
                background: #dbeafe;
                color: #0c4a6e;
            }
            
            .info-box {
                background: #f0f9ff;
                border-left: 4px solid var(--primary-color);
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            
            .info-box i {
                color: var(--primary-color);
                margin-right: 10px;
            }
            
            .file-list {
                margin-top: 20px;
            }
            
            .file-item {
                background: #f8fafc;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-left: 4px solid var(--primary-color);
            }
            
            .file-item i {
                color: var(--primary-color);
                margin-right: 10px;
            }
            
            .badge-processing {
                background: #fbbf24;
                color: #78350f;
            }
            
            .badge-success {
                background: var(--success-color);
                color: white;
            }
            
            .badge-error {
                background: var(--danger-color);
                color: white;
            }
            
            footer {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                text-align: center;
                color: #666;
                margin-top: 40px;
            }
            
            .stats-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .stat-card .number {
                font-size: 2rem;
                font-weight: 700;
                color: var(--primary-color);
            }
            
            .stat-card .label {
                color: #666;
                font-size: 0.9rem;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <!-- Navbar -->
        <nav class="navbar navbar-expand-lg navbar-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-file-invoice"></i> Procesador de Facturas
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Inicio</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">Dashboard</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <!-- Contenido Principal -->
        <div class="container container-principal">
            <div class="row">
                <div class="col-lg-8 offset-lg-2">
                    <!-- Estadísticas -->
                    <div class="stats-container" id="stats">
                        <div class="stat-card">
                            <div class="number" id="stat-total">0</div>
                            <div class="label">Facturas Procesadas</div>
                        </div>
                        <div class="stat-card">
                            <div class="number" id="stat-hoy">0</div>
                            <div class="label">Hoy</div>
                        </div>
                    </div>

                    <!-- Card Principal -->
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-upload"></i> Subir Facturas
                        </div>
                        <div class="card-body">
                            <!-- Información -->
                            <div class="info-box">
                                <i class="fas fa-info-circle"></i>
                                Carga uno o varios archivos PDF o fotografías. El sistema extraerá automáticamente toda la información.
                            </div>

                            <!-- Drag & Drop -->
                            <div class="drop-zone" id="dropZone">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <div class="drop-zone-text">Arrastra archivos aquí</div>
                                <small class="text-muted">o haz clic para seleccionar</small>
                            </div>

                            <!-- Input File Oculto -->
                            <input type="file" id="inputFile" class="input-file" multiple accept=".pdf,.jpg,.jpeg,.png,.bmp">

                            <!-- Botón de Subida -->
                            <div style="text-align: center; margin-top: 20px;">
                                <button class="btn-upload" id="btnUpload">
                                    <i class="fas fa-upload"></i> Seleccionar Archivos
                                </button>
                            </div>

                            <!-- Barra de Progreso -->
                            <div class="progress-container" id="progressContainer">
                                <label>Procesando archivos...</label>
                                <div class="progress" style="height: 25px;">
                                    <div class="progress-bar" id="progressBar" role="progressbar" style="width: 0%">
                                        <span id="progressText">0%</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Alertas -->
                            <div id="alertContainer"></div>

                            <!-- Lista de Archivos -->
                            <div class="file-list" id="fileList"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer>
            <p>&copy; 2024 Procesador de Facturas. Todos los derechos reservados.</p>
        </footer>

        <!-- Scripts -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


def get_pagina_dashboard() -> str:
    """
    Retorna el HTML del dashboard.
    """
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - Procesador de Facturas</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary-color: #2563eb;
            }
            
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            
            .navbar {
                background: rgba(255, 255, 255, 0.95);
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .navbar-brand {
                font-weight: 700;
                color: var(--primary-color) !important;
            }
            
            .container-dashboard {
                margin-top: 40px;
                margin-bottom: 40px;
            }
            
            .card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                background: white;
            }
            
            table {
                background: white;
            }
            
            thead {
                background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%);
                color: white;
            }
            
            tbody tr:hover {
                background: #f8fafc;
            }
            
            .badge {
                padding: 6px 12px;
                border-radius: 20px;
            }
            
            /* Estilos para confianza */
            .campo-bajo-confianza {
                background-color: #fef08a !important;
                border-left: 4px solid #facc15;
                padding: 12px;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            
            .badge-confianza {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.85rem;
                margin-left: 10px;
            }
            
            .confianza-alta {
                background-color: #d1fae5;
                color: #065f46;
            }
            
            .confianza-media {
                background-color: #fef08a;
                color: #78350f;
            }
            
            .confianza-baja {
                background-color: #fee2e2;
                color: #7f1d1d;
            }
            
            .input-field {
                margin-bottom: 15px;
            }
            
            .input-field.bajo-confianza {
                background-color: #fef08a;
                border-color: #facc15;
            }
            
            .input-field.bajo-confianza input,
            .input-field.bajo-confianza textarea {
                background-color: #fef3c7;
                border-color: #fbbf24;
            }
            
            .input-field.bajo-confianza label {
                color: #78350f;
                font-weight: 600;
            }
            
            .advertencia-confianza {
                background: #fef08a;
                border: 2px solid #facc15;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                display: none;
            }
            
            .advertencia-confianza.mostrar {
                display: block;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-file-invoice"></i> Procesador de Facturas
                </a>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Inicio</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/dashboard">Dashboard</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container container-dashboard">
            <h1 class="text-white mb-4"><i class="fas fa-chart-bar"></i> Dashboard</h1>
            
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Facturas Procesadas</h5>
                    <div id="tableContainer">
                        <p class="text-center text-muted">Cargando...</p>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            async function cargarFacturas() {
                try {
                    const response = await fetch('/api/facturas/');
                    const facturas = await response.json();
                    
                    if (facturas.length === 0) {
                        document.getElementById('tableContainer').innerHTML = '<p class="text-center text-muted">No hay facturas procesadas</p>';
                        return;
                    }
                    
                    let html = `
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Número</th>
                                    <th>Fecha</th>
                                    <th>Total</th>
                                    <th>Confianza</th>
                                    <th>Estado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    facturas.forEach(f => {
                        const fecha = f.fecha ? new Date(f.fecha).toLocaleDateString('es-ES') : '-';
                        const total = f.total ? parseFloat(f.total).toFixed(2) : '0.00';
                        const estadoBadge = f.estado === 'procesada' ? 'success' : 'warning';
                        
                        // Mostrar indicador de confianza
                        let confianzaBadge = '';
                        if (f.tiene_campos_bajo_confianza) {
                            confianzaBadge = '<span class="badge bg-warning text-dark"><i class="fas fa-exclamation-triangle"></i> Revisar</span>';
                        } else {
                            confianzaBadge = '<span class="badge bg-success"><i class="fas fa-check"></i> Confiable</span>';
                        }
                        
                        html += `
                            <tr>
                                <td>#${f.id}</td>
                                <td>${f.numero}</td>
                                <td>${fecha}</td>
                                <td>€${total}</td>
                                <td>${confianzaBadge}</td>
                                <td><span class="badge bg-${estadoBadge}">${f.estado}</span></td>
                                <td>
                                    <a href="#" class="btn btn-sm btn-primary">Ver</a>
                                </td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('tableContainer').innerHTML = html;
                } catch (e) {
                    console.error('Error:', e);
                    document.getElementById('tableContainer').innerHTML = '<p class="alert alert-danger">Error cargando facturas</p>';
                }
            }
            
            cargarFacturas();
        </script>
    </body>
    </html>
    """


# ============ TEMPLATE ROUTES (FASE 5) ============

@app.get("/empresas", response_class=HTMLResponse)
async def empresas_page(request: Request):
    """Página de gestión de empresas."""
    try:
        logger.info(f"Rendering empresas template")
        template = jinja_env.get_template("empresas.html")
        html = template.render(request=request, url_for=request.url_for)
        return html
    except Exception as e:
        logger.error(f"Error rendering empresas template: {str(e)}", exc_info=True)
        raise


@app.get("/proveedores", response_class=HTMLResponse)
async def proveedores_page(request: Request):
    """Página de gestión de proveedores."""
    try:
        template = jinja_env.get_template("proveedores.html")
        html = template.render(request=request, url_for=request.url_for)
        return html
    except Exception as e:
        logger.error(f"Error rendering proveedores template: {str(e)}", exc_info=True)
        raise


@app.get("/clientes", response_class=HTMLResponse)
async def clientes_page(request: Request):
    """Página de gestión de clientes."""
    try:
        template = jinja_env.get_template("clientes.html")
        html = template.render(request=request, url_for=request.url_for)
        return html
    except Exception as e:
        logger.error(f"Error rendering clientes template: {str(e)}", exc_info=True)
        raise


@app.get("/facturas", response_class=HTMLResponse)
async def facturas_page(request: Request):
    """Página de gestión de facturas."""
    try:
        template = jinja_env.get_template("facturas/list.html")
        html = template.render(request=request, url_for=request.url_for)
        return html
    except Exception as e:
        logger.error(f"Error rendering facturas template: {str(e)}", exc_info=True)
        raise


@app.get("/facturas/{factura_id}", response_class=HTMLResponse)
async def factura_detail_page(factura_id: int, request: Request):
    """Página de detalle de factura."""
    try:
        template = jinja_env.get_template("facturas/detail.html")
        html = template.render(request=request, url_for=request.url_for, factura_id=factura_id)
        return html
    except Exception as e:
        logger.error(f"Error rendering factura detail template: {str(e)}", exc_info=True)
        raise


@app.get("/facturas/upload", response_class=HTMLResponse)
async def factura_upload_page(request: Request):
    """Página de carga de facturas."""
    try:
        template = jinja_env.get_template("cargar.html")
        html = template.render(request=request, url_for=request.url_for)
        return html
    except Exception as e:
        logger.error(f"Error rendering cargar template: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )