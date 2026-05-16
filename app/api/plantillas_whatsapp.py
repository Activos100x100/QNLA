from fastapi import APIRouter, Body
from app.core.whatsapp import templates as whatsapp_templates

router = APIRouter(prefix="/plantillas/whatsapp", tags=["whatsapp"])

@router.post("/enviar")
def enviar_plantilla_whatsapp(
    body: dict = Body(...)
):
    """
    Enviar cualquier plantilla de WhatsApp.
    body = {
        "telefono": "34666666666",
        "template_name": "notificacion_pago_empleado",
        "language_code": "es",
        "parametros": [ ... ]
    }
    """
    telefono = body.get("telefono")
    template_name = body.get("template_name")
    language_code = body.get("language_code", "es")
    parametros = body.get("parametros", [])
    if not telefono or not template_name:
        return {"ok": False, "error": "Faltan campos obligatorios"}
    try:
        resp = whatsapp_templates.enviar_template(
            telefono,
            template_name=template_name,
            language_code=language_code,
            parametros=parametros
        )
        return {
            "ok": resp.status_code in (200, 201),
            "status_code": resp.status_code,
            "response": resp.text
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
