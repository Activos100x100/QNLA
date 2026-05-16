from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import os
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])

logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
REQUIRE_SIGNATURE = os.getenv("WHATSAPP_REQUIRE_SIGNATURE", "true").strip().lower() in {"1", "true", "yes", "y", "on"}

@router.get("/whatsapp")
async def verify_webhook(request: Request):
    if not VERIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Webhook verify token is not configured")

    params = dict(request.query_params)
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return params.get("hub.challenge")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp")
async def receive_webhook(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    if REQUIRE_SIGNATURE and not APP_SECRET:
        raise HTTPException(status_code=500, detail="Webhook app secret is not configured")

    if APP_SECRET and not signature and REQUIRE_SIGNATURE:
        raise HTTPException(status_code=403, detail="Missing signature")

    if APP_SECRET and signature:
        expected = "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Aquí puedes procesar y guardar los eventos recibidos
    logger.info("[WEBHOOK EVENT] entries=%s", len(data.get("entry", [])) if isinstance(data, dict) else 0)
    return {"status": "ok"}
