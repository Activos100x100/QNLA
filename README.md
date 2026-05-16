# QNLA — Deploy en Cloud Run

Este repo contiene una app FastAPI (en `app/`) que interactúa con Google Drive.

Requisitos locales:
- `gcloud` CLI autenticado
- `docker` (opcional)

Configuración local recomendada:
- Copia `.env.example` a `.env` y completa credenciales reales.
- No uses secretos reales en archivos versionados.

Instalar dependencias locales (opcional, recomendado dentro de un venv):
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Build y push (Cloud Build + Container Registry):
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/qnla
```

Desplegar en Cloud Run:
```bash
gcloud run deploy qnla \
  --image gcr.io/PROJECT_ID/qnla \
  --platform managed \
  --region YOUR_REGION \
  --allow-unauthenticated \
  --set-env-vars PORT=8080
```

Credenciales y secretos:
- Nunca incluyas `app/google-oauth.json`, `app/service-account.json` o `app/tokens` en el repositorio.
- Usa Secret Manager y variables de entorno en Cloud Run.
- En producción define siempre: `SESSION_SECRET`, `WHATSAPP_VERIFY_TOKEN` y `WHATSAPP_APP_SECRET`.

Notas:
- Si tu entrypoint no es `app.main:app`, ajusta el `CMD` en `Dockerfile`.
- Recomendado: `gcloud auth application-default login --scopes=https://www.googleapis.com/auth/drive` para usar ADC localmente.
