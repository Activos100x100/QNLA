from app.qnla.routers import pages_router, api_torneos_router, api_torneos_public_router, admin_partidos_router
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("qnla/dashboard.html", {"request": request})

app.include_router(pages_router)
app.include_router(api_torneos_router)
app.include_router(api_torneos_public_router)
app.include_router(admin_partidos_router)
