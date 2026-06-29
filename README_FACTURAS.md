# Procesador de Facturas - Aplicación FastAPI

Aplicación web completa para escanear, procesar y gestionar facturas españolas usando OCR e Inteligencia Artificial.

## 🎯 Características

- **OCR Automático**: Extrae texto de PDFs e imágenes usando PaddleOCR
- **IA Inteligente**: Procesa texto con OpenAI para obtener datos estructurados
- **Interfaz Web**: Dashboard moderno con Bootstrap 5
- **Base de Datos**: PostgreSQL con SQLAlchemy
- **API REST**: Endpoints completos para todas las operaciones
- **Búsqueda y Filtros**: Por número, proveedor, CIF, fecha, importe
- **Validación**: Datos automáticos y manuales

## 📋 Requisitos

- Python 3.11+
- PostgreSQL 12+
- Clave API de OpenAI

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd FTRA
```

### 2. Crear entorno virtual

```bash
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Editar el archivo `.env`:

```env
# Base de datos PostgreSQL
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/facturas_db

# OpenAI API
OPENAI_API_KEY=tu_clave_api_openai_aqui

# Configuración
DEBUG=True
SECRET_KEY=tu_clave_secreta_aqui

# PaddleOCR
PADDLE_USE_GPU=False  # True si tienes CUDA disponible

# Archivos
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=uploads

# Servidor
HOST=127.0.0.1
PORT=8080
```

### 5. Crear base de datos PostgreSQL

```bash
createdb facturas_db
```

### 6. Ejecutar la aplicación

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

O usar la tarea configurada:

```bash
# En VS Code: Ctrl+Shift+B
# Seleccionar "Run FastAPI local"
```

## 📊 Estructura del Proyecto

```
FTRA/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación FastAPI principal
│   ├── config.py              # Configuración centralizada
│   ├── database.py            # Configuración de BD
│   ├── models.py              # Modelos SQLAlchemy
│   ├── schemas/               # Esquemas Pydantic
│   ├── services/              # Servicios de negocio
│   │   ├── ocr_service.py     # OCR con PaddleOCR
│   │   ├── ai_service.py      # IA con OpenAI
│   │   └── factura_service.py # Orquestación
│   ├── routers/               # Endpoints de API
│   │   └── facturas.py        # Rutas de facturas
│   ├── static/                # CSS, JS, imágenes
│   └── templates/             # Plantillas HTML
├── uploads/                   # Archivos subidos
├── .env                       # Variables de entorno
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## 🔧 Uso de la API

### Subir y procesar factura

```bash
curl -X POST "http://localhost:8080/api/facturas/procesar" \
  -F "archivo=@factura.pdf"
```

Respuesta:
```json
{
  "exito": true,
  "mensaje": "Archivo procesado exitosamente",
  "factura_id": 1,
  "datos": {
    "factura_id": 1,
    "numero": "2024001",
    "fecha": "2024-01-15",
    "total": 1250.50,
    "proveedor": "Empresa XYZ",
    "cliente": "Mi Empresa",
    "lineas_count": 3
  }
}
```

### Listar facturas

```bash
GET http://localhost:8080/api/facturas/
GET http://localhost:8080/api/facturas/?skip=0&limit=10
GET http://localhost:8080/api/facturas/?estado=procesada
GET http://localhost:8080/api/facturas/?proveedor_id=1
```

### Obtener factura específica

```bash
GET http://localhost:8080/api/facturas/1
```

### Actualizar factura

```bash
PUT http://localhost:8080/api/facturas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "numero": "2024001-CORREGIDO",
    "total": 1350.50,
    "estado": "validada"
  }'
```

### Buscar facturas

```bash
# Por número
GET http://localhost:8080/api/facturas/buscar/por-numero?numero=2024001

# Por proveedor
GET http://localhost:8080/api/facturas/buscar/por-proveedor?nombre=Empresa

# Por CIF
GET http://localhost:8080/api/facturas/buscar/por-cif?cif=A12345678

# Por fecha
GET http://localhost:8080/api/facturas/filtrar/por-fecha?fecha_desde=2024-01-01&fecha_hasta=2024-12-31

# Por importe
GET http://localhost:8080/api/facturas/filtrar/por-importe?importe_minimo=100&importe_maximo=5000
```

## 🎨 Interfaz de Usuario

### Página principal
- **URL**: http://localhost:8080/
- Drag & Drop de archivos
- Barra de progreso
- Estadísticas de procesamiento

### Dashboard
- **URL**: http://localhost:8080/dashboard
- Tabla de facturas procesadas
- Filtros y búsqueda
- Acciones por factura

## 📝 Modelos de Base de Datos

### FTRA_proveedores
```sql
- id (PK)
- nombre
- cif
- direccion
- telefono
- email
- created_at
- updated_at
```

### FTRA_clientes
```sql
- id (PK)
- nombre
- cif
- created_at
- updated_at
```

### FTRA_facturas
```sql
- id (PK)
- numero
- serie
- fecha
- fecha_vencimiento
- proveedor_id (FK)
- cliente_id (FK)
- base_imponible
- iva
- tipo_iva
- irpf
- total
- forma_pago
- iban
- observaciones
- archivo_original
- estado
- texto_ocr (completo)
- json_extraido (bruto)
- created_at
- updated_at
- procesada_en
```

### FTRA_lineas_factura
```sql
- id (PK)
- factura_id (FK)
- numero_linea
- descripcion
- cantidad
- precio_unitario
- tipo_iva
- total
- created_at
- updated_at
```

### FTRA_historial_facturas
```sql
- id (PK)
- factura_id (FK)
- accion
- campo_modificado
- valor_anterior
- valor_nuevo
- descripcion
- created_at
```

### FTRA_errores_procesamiento
```sql
- id (PK)
- nombre_archivo
- ruta_archivo
- tipo_error
- mensaje_error
- stack_trace
- resuelto
- nota_resolucion
- created_at
- resuelto_en
```

## 🤖 Flujo de Procesamiento

1. **Subida de archivo**
   - Validación de tipo y tamaño
   - Guardado temporal

2. **OCR**
   - Conversión PDF → Imágenes
   - Extracción de texto con PaddleOCR
   - Preprocesamiento opcional

3. **Inteligencia Artificial**
   - Envío de texto a OpenAI
   - Extracción de datos estructurados
   - Validación de respuesta JSON

4. **Validación**
   - Verificación de campos requeridos
   - Coherencia de datos
   - Intento de mejora automática

5. **Guardado**
   - Creación/actualización de proveedores y clientes
   - Almacenamiento de factura
   - Registro de líneas
   - Entrada en historial

6. **Presentación**
   - Formulario editable
   - Vista previa
   - Opción de guardar

## 🔐 Seguridad

- ✅ Validación de entrada
- ✅ Sanitización de datos
- ✅ CORS habilitado
- ✅ Variables de entorno sensibles
- ✅ Preparación para HTTPS

## 📚 Documentación de API

La documentación interactiva está disponible en:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🧪 Testing

```bash
# Crear archivo de prueba
python -m pytest

# Con cobertura
pytest --cov=app
```

## 🐛 Troubleshooting

### Error: "Archivo PDF no encontrado"
- Verificar ruta del archivo
- Asegurar permisos de lectura

### Error: "OCR no extrajo ningún texto"
- La imagen/PDF puede estar corrupta
- Intentar optimizar imagen primero

### Error: "OpenAI API key no válida"
- Verificar `OPENAI_API_KEY` en `.env`
- Asegurar acceso a la API

### Error: "Conexión a PostgreSQL fallida"
- Verificar PostgreSQL está corriendo
- Validar `DATABASE_URL`
- Crear database si no existe

## 📧 Contacto

Para reportar problemas o sugerencias, contactar al equipo de desarrollo.

## 📄 Licencia

Todos los derechos reservados © 2024
