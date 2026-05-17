# QNLA API (.NET 8)

API Minimal para app móvil de QNLA, conectada a la misma base PostgreSQL del backend Python.

## Endpoints

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| POST | `/api/v1/auth/login` | No | Login con `dni_nie` y contraseña |
| POST | `/api/v1/auth/refresh` | No | Refrescar access token |
| GET | `/api/v1/auth/me` | Sí | Usuario autenticado |
| POST | `/api/v1/pronosticos` | Sí | Crea/actualiza pronóstico (UPSERT) |
| PUT | `/api/v1/pronosticos/{id}` | Sí | Edita pronóstico propio |
| GET | `/api/v1/pronosticos/mios?torneo_id={id}` | Sí | Lista pronósticos propios |
| DELETE | `/api/v1/pronosticos/{id}` | Sí | Elimina pronóstico propio (si aún está abierto) |
| GET | `/api/v1/torneos` | Sí | Lista torneos activos |
| GET | `/api/v1/torneos/{id}/ranking?limit=50` | Sí | Ranking desde `qnla_v_ranking` + posición actual |
| GET | `/api/v1/torneos/{id}/partidos?solo_pendientes=true` | Sí | Partidos del torneo |
| POST | `/api/v1/torneos/{id}/calcular-puntos/{partidoId}` | Sí | Llamada interna opcional a `qnla_calcular_puntos_partido` |
| GET | `/health` | No | Health básico |
| GET | `/health/ready` | No | Readiness |
| GET | `/health/version` | No | Versión |

## Variables de entorno

- `PORT` (default `8080`)
- `Jwt__Secret` (obligatorio en producción)
- `Jwt__Issuer` (default `QNLA.Api`)
- `Jwt__Audience` (default `QNLA.Mobile`)
- `Jwt__AccessTokenMinutes` (default `60`)
- `Jwt__RefreshTokenDays` (default `30`)
- Conexión DB:
  - `DATABASE_URL`, **o**
  - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, `DB_SSLMODE`

> Soporta host `/cloudsql/PROJECT:REGION:INSTANCE` sin forzar `sslmode`.

## Ejecutar local

```bash
cd dotnet-api
dotnet restore
dotnet run
```

Swagger: `http://localhost:8080/swagger`

## Deploy Cloud Run

```bash
gcloud builds submit --tag gcr.io/$PROJECT/qnla-api
gcloud run deploy qnla-api --image gcr.io/$PROJECT/qnla-api \
  --region us-central1 --allow-unauthenticated --port 8080 \
  --set-env-vars Jwt__Secret=...,DATABASE_URL=...
```

### Cloud SQL (socket)

Si usas socket en Cloud Run:

- Host DB: `/cloudsql/PROJECT:REGION:INSTANCE`
- Agregar instancia al deploy:

```bash
gcloud run deploy qnla-api \
  --image gcr.io/$PROJECT/qnla-api \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE \
  --set-env-vars Jwt__Secret=...,DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE,DB_NAME=...,DB_USER=...,DB_PASSWORD=...
```
