# QLNA.Web

Versión web de QLNA Mobile en Blazor Server.

## Requisitos

- .NET 10 SDK

## Ejecutar local

```bash
cd QLNA.Web && dotnet run
```

Abrir `https://localhost:7116`.

## Variables de entorno

- `Api__BaseUrl` (opcional): sobrescribe la URL base del backend API.

## Docker

```bash
docker build -t qlna-web -f QLNA.Web/Dockerfile .
```

## Deploy en Google Cloud Run

```bash
gcloud run deploy qlna-web \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated
```

Esta app comparte el mismo backend usado por QLNA Mobile.
