import os
import requests

def get_whatsapp_message_status(message_id: str, access_token: str = None) -> dict:
    """
    Consulta el estado de un mensaje de WhatsApp usando el message_id y el token de acceso de Meta.
    Devuelve el JSON de estado o un dict con error.
    """
    if not access_token:
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        return {"ok": False, "error": "No se proporcionó access_token"}
    if not message_id:
        return {"ok": False, "error": "No se proporcionó message_id"}

    url = f"https://graph.facebook.com/v18.0/{message_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        else:
            return {"ok": False, "status_code": resp.status_code, "error": resp.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}
