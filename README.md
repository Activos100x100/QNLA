# FTRA — Deploy en Cloud Run

Este repo contiene una app FastAPI (en `app/`) para gestionar facturas y comentarios.

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
gcloud builds submit --tag gcr.io/PROJECT_ID/ftra
```

Desplegar en Cloud Run:
```bash
gcloud run deploy ftra \
  --image gcr.io/PROJECT_ID/ftra \
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

## Lector de facturas (OCR + validación fiscal ES)

La app incluye un lector de facturas en `app/api/facturas.py` con dos modos:

- Web (HTML): `POST /facturas/analizar`
- API (JSON): `POST /facturas/analizar-json`

### Qué devuelve

Además de los datos extraídos (emisor, receptor, NIF, número, fecha, base, IVA, total), ahora devuelve:

- `validacion.estado`: `valida` o `incompleta`
- `validacion.tipo_factura`: `completa`, `simplificada`, `rectificativa` o `desconocida`
- `validacion.puntuacion`: score 0..100
- `validacion.bloqueantes`: lista de errores que impiden validar formalmente
- `validacion.advertencias`: incidencias a revisar manualmente

### Requisitos OCR locales

Este módulo usa `pytesseract` y requiere tener Tesseract OCR instalado en el sistema.
En macOS puedes instalarlo con Homebrew:

- `brew install tesseract`
- Opcional español: `brew install tesseract-lang`

Si no está instalado, la extracción OCR desde imágenes o PDFs escaneados no funcionará correctamente.

### Cobertura de pruebas (fase 2)

Se añadió una batería ampliada en `test_facturas_reader.py` para cubrir:

- Validación fiscal completa e incompleta.
- Casos rectificativos (incluyendo ausencia de referencia a factura original).
- Coherencia matemática de importes (base + IVA vs total).
- Robustez de extracción ante ruido OCR (p.ej. CIF con `€` detectado en lugar de `E`).
- Endpoints API con errores controlados (`415` por MIME no soportado, `413` por tamaño, `503` por dependencia OCR no disponible).

Ejecución local de la suite:

- `python -m unittest -v test_facturas_reader.py`
