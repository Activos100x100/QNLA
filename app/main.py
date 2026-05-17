
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.qnla.routers import pages

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("qnla/admin_torneos.html", {"request": request})

# Incluir el router de páginas de QNLA
app.include_router(pages.router)