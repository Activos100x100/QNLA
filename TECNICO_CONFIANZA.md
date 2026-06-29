# Resumen Técnico: Sistema de Confianza Integrado

## ✅ Completado

### 1. Backend - Base de Datos
- ✅ Modelo SQLAlchemy: Campos `json_confianza` (TEXT) y `tiene_campos_bajo_confianza` (BOOLEAN)
- ✅ Tabla FTRA_facturas con almacenamiento de estructura de confianza
- ✅ Persistencia completa del análisis de confianza

### 2. Backend - Servicios (app/services/)

#### ai_service.py
- ✅ `extraer_datos_factura()`: Retorna estructura con confianza {"campo": {"valor": X, "confianza": NN}}
- ✅ `_crear_prompt_extraccion()`: Prompt mejorado con calibración de confianza (0-100 escala)
- ✅ `extraer_campos_bajo_confianza(datos, umbral=85)`: Extrae campos con confianza < umbral
- ✅ `calcular_confianza_promedio(datos)`: Promedio de todas las confianzas
- ✅ `extraer_valores_de_confianza(datos)`: Convierte de formato con confianza a valores planos

#### factura_service.py
- ✅ `procesar_archivo()`: Integra análisis de confianza en pipeline
  - Extrae datos con confianza
  - Calcula confianza promedio
  - Identifica campos bajo confianza
  - Retorna en resultado dict: confianza_promedio, campos_bajo_confianza, tiene_campos_bajo_confianza
- ✅ `_guardar_factura()`: Guarda json_confianza y tiene_campos_bajo_confianza en DB
  - Almacena estructura completa de confianza en json_confianza
  - Establece flag booleano para búsquedas rápidas

### 3. Backend - API (app/routers/facturas.py)
- ✅ POST /api/facturas/procesar: Retorna confianza en respuesta
  - confianza_promedio: float
  - campos_bajo_confianza: list[dict]
  - tiene_campos_bajo_confianza: bool

### 4. Frontend - Estilos (app/main.py)
- ✅ CSS para campos bajo confianza
  - .campo-bajo-confianza: Fondo amarillo (#fef08a)
  - .badge-confianza: Indicadores de niveles
  - .confianza-alta/media/baja: Colores por nivel
  - .advertencia-confianza: Panel de alerta
- ✅ Clases para inputs con bajo confianza
  - Background amarillo (#fef3c7)
  - Border amarillo (#fbbf24)
  - Label en negrita (#78350f)

### 5. Frontend - JavaScript (app/main.py)
- ✅ Función `getBadgeConfianza()`: Genera badges de confianza
- ✅ Procesamiento de respuesta con confianza
  - Extrae confianza_promedio y tiene_campos_bajo_confianza
  - Muestra alertas apropiadas (éxito/advertencia)
- ✅ Dashboard mejorado
  - Columna "Confianza" con badges
  - ✅ Verde: Todas confianzas aceptables
  - ⚠️ Amarillo: Revisar campos

### 6. Documentación
- ✅ CONFIANZA_PRECISION.md: Guía completa con ejemplos
  - Niveles de confianza (0-100%)
  - Casos de uso
  - Flujo de trabajo
  - API responses
  - Configuración

## 🔄 Flujo Completo

```
1. Usuario carga PDF/Imagen
    ↓
2. OCR extrae texto (app/services/ocr_service.py)
    ↓
3. IA extrae datos CON confianza (app/services/ai_service.py)
    Retorna: {"campo": {"valor": X, "confianza": NN}}
    ↓
4. Análisis de confianza en factura_service.py
    - Calcula promedio de confianza
    - Identifica campos < 85%
    - Establece flag tiene_campos_bajo_confianza
    ↓
5. Guardado en BD (app/ftra/models.py)
    - json_confianza: Estructura completa
    - tiene_campos_bajo_confianza: Flag booleano
    ↓
6. Respuesta API (app/routers/facturas.py)
    Incluye:
    - confianza_promedio
    - campos_bajo_confianza[]
    - tiene_campos_bajo_confianza
    ↓
7. Frontend renderiza con alertas (app/main.py)
    - Badges de confianza
    - Campos resaltados en amarillo
    - Advertencias si necesario
    ↓
8. Usuario revisa y guarda (o edita campos amarillos)
```

## 📊 Estructura de Datos

### Entrada a IA (texto OCR)
```
[Texto completo del documento OCR]
```

### Salida de IA (con confianza)
```json
{
  "proveedor": {
    "nombre": {"valor": "Repsol", "confianza": 98},
    "cif": {"valor": "A1234567B", "confianza": 95},
    "direccion": {"valor": "Calle Principal 123", "confianza": 75}
  },
  "cliente": {
    "nombre": {"valor": "Mi Empresa", "confianza": 96}
  },
  "factura": {
    "numero": {"valor": "F2026-001", "confianza": 99},
    "fecha": {"valor": "2024-12-15", "confianza": 88},
    "total": {"valor": 1250.50, "confianza": 95}
  },
  "lineas": [...]
}
```

### Base de Datos (FTRA_facturas)
```sql
id INT PRIMARY KEY
numero VARCHAR
...
json_confianza TEXT             -- Estructura completa arriba
tiene_campos_bajo_confianza BOOL -- TRUE si alguno < 85%
json_extraido TEXT              -- Datos sin confianza (valores planos)
```

### Respuesta API
```json
{
  "exito": true,
  "confianza_promedio": 91.3,
  "campos_bajo_confianza": [
    {
      "categoria": "proveedor",
      "campo": "direccion",
      "valor": "Calle Principal 123",
      "confianza": 75
    }
  ],
  "tiene_campos_bajo_confianza": true
}
```

## 🎯 Decisiones de Diseño

### 1. Umbral de 85%
- Balanza entre precisión y usabilidad
- Permite ~15% de margen para OCR y IA
- Datos > 85% son generalmente confiables

### 2. Almacenamiento Dual
- `json_confianza`: Estructura completa para análisis
- `json_extraido`: Valores planos para acceso rápido
- `tiene_campos_bajo_confianza`: Flag para filtros/búsquedas

### 3. Calcular en Backend
- Análisis de confianza en factura_service.py
- No depende de lado del cliente
- Garantiza consistencia

### 4. Visualización en Frontend
- Badges coloreados por nivel
- Resaltado amarillo para campos bajo confianza
- Alertas contextuales según el caso

## 🔐 Validación

### Confianza no reemplaza validación
- Campos bajo confianza se marcan para revisar
- No se rechaza automáticamente
- Usuario siempre tiene la palabra final

### Tipo de validaciones
- IA: "¿Qué confianza tengo en este texto?"
- Negocio: "¿Son válidos estos datos?" (número factura único, etc.)
- Usuario: "¿Se ve correcto?" (revisión manual)

## 📦 Dependencias

### Nuevas
- Ninguna (usa OpenAI + JSON existentes)

### Modificadas
- `app/ftra/models.py`: Dos campos nuevos
- `app/services/ai_service.py`: 3 métodos nuevos
- `app/services/factura_service.py`: Integración de confianza
- `app/routers/facturas.py`: Respuesta ampliada
- `app/main.py`: CSS + JavaScript mejorados

## 🧪 Prueba Manual

```bash
# 1. Cargar PDF con texto de baja calidad
# → Esperado: Campos con confianza < 85% resaltados en amarillo

# 2. Cargar PDF con texto claro
# → Esperado: Todos los campos con confianza > 85%

# 3. Ver respuesta API
curl http://localhost:8080/api/facturas/procesar
# → Incluye confianza_promedio, campos_bajo_confianza, tiene_campos_bajo_confianza

# 4. Consultar en BD
SELECT json_confianza, tiene_campos_bajo_confianza FROM FTRA_facturas WHERE id = 1;
# → Estructura JSON con confianza almacenada
```

## 🚀 Próximos Pasos Opcionales

1. **Dashboard de Confianza**
   - Gráficos de distribución de confianza
   - Filtro por rango de confianza
   - Reportes por proveedor

2. **Retroalimentación del Usuario**
   - Registrar correcciones del usuario
   - Mejorar IA con datos reales
   - A/B testing de prompts

3. **Certificación Automática**
   - Confianza >= 95% → Aprobar automáticamente
   - Confianza 85-94% → Requiere revisión manual
   - Confianza < 85% → Requiere validación completa

4. **Integración con Sistemas Externos**
   - Webhook para alertar sobre baja confianza
   - Exportar confianza a ERP/SAP
   - API para consultar confianza histórica
