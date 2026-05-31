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

## Cambiar el logo

El proyecto usa por defecto `wwwroot/img/logo.svg` — un SVG vectorial de corona dorada con 5 puntas y 5 piedras, creado como placeholder fiel al diseño corporativo de Activos 100x100. Es totalmente funcional pero puede sustituirse por el PNG corporativo oficial:

1. Añadid `wwwroot/img/logo.png`.
2. Cambiad `src="/img/logo.svg"` por `src="/img/logo.png"` en `Components/Pages/Login.razor`.
3. Cambiad `src="/img/logo.svg"` por `src="/img/logo.png"` en `Components/Layout/MainLayout.razor` (clase `brand-logo`, `height: 38px`).
