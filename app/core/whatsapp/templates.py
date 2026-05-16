import os

import requests


PHONE_NUMBER_ID = "1118738041314274"
DEFAULT_TEMPLATE_NAME = "bienvenido_ia"

def enviar_template(numero, template_name=DEFAULT_TEMPLATE_NAME, language_code="es", parametros=None):
    """
    Envía una plantilla de WhatsApp con parámetros personalizados.
    parametros: lista de strings, en el orden de la plantilla.
    """
    token = os.getenv("WHATSAPP_TOKEN")
    if not token:
        raise RuntimeError("WHATSAPP_TOKEN no esta definido en el entorno")
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    template_data = {
        "name": template_name,
        "language": {"code": language_code},
    }
    if parametros:
        # Filtrar parámetros vacíos o None
        parametros_filtrados = [p for p in parametros if p is not None and str(p).strip() != ""]
        if len(parametros_filtrados) != len(parametros):
            raise ValueError("Todos los parámetros de la plantilla deben tener un valor no vacío.")
        template_data["components"] = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(p)} for p in parametros_filtrados
                ]
            }
        ]
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": template_data,
    }
    print(f"[enviar_template] Enviando a {numero} con payload: {payload}")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"[enviar_template] Respuesta: {response.status_code} {response.text}")
    try:
        data = response.json()
        message_id = None
        if 'messages' in data and data['messages'] and 'id' in data['messages'][0]:
            message_id = data['messages'][0]['id']
        print(f"[enviar_template] JSON: {data}")
        print(f"[enviar_template] message_id extraído: {message_id}")
    except Exception as e:
        print(f"[enviar_template] Error parseando JSON de respuesta: {e}")
    return response