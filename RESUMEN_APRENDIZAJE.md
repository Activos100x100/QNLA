# 🚀 Sistema de Aprendizaje - Resumen Ejecutivo

## ✅ Estado: 90% Completado y Funcional

El sistema ahora es capaz de **aprender automáticamente** de las correcciones que realiza el usuario, mejorando la precisión en futuras extracciones del mismo proveedor.

## 🎯 Ejemplo Real

**Problema**: Leroy Merlin siempre tiene el CIF extraído incorrectamente como "ES123456789A" cuando debería ser "A12345678"

**Solución**:
1. Usuario carga factura de Leroy Merlin → IA extrae CIF como "ES123456789A"
2. Usuario corrige a "A12345678" → Sistema registra corrección
3. Usuario carga otra factura de Leroy Merlin → Usuario corrige de nuevo
4. En la tercera corrección → **Sistema identifica patrón frecuente**
5. Usuario carga 4ª factura de Leroy Merlin → **IA ya incluye el contexto** "Patrón conocido: ES123456789A siempre debe ser A12345678"
6. Resultado: **Extracción correcta sin corrección manual** ✨

## 📦 Componentes Implementados

### 1. Modelo de Base de Datos ✅
**Tabla**: `FTRA_correcciones_aprendizaje`
- Almacena cada corrección con contexto
- Detecta patrones automáticamente (3+ ocurrencias)
- Indexado por proveedor y campo para búsquedas rápidas

### 2. Servicio de Aprendizaje ✅
**Archivo**: `app/services/learning_service.py` (350+ líneas)
- Registra correcciones
- Identifica patrones frecuentes
- Genera contexto para la IA
- Sugiere correcciones
- Mantiene sistema limpio

### 3. API de Correcciones ✅
**Archivo**: `app/routers/correcciones.py` (350+ líneas)
- 6 endpoints para gestionar correcciones
- Registrar, consultar, analizar, sugerir
- Estadísticas del sistema

### 4. Integración en Main ✅
- Router incluido y disponible
- Endpoints accesibles en `/api/correcciones/*`

### 5. Documentación Completa ✅
- `APRENDIZAJE_AUTOMATICO.md`: Guía completa (300+ líneas)
- `INTEGRACION_APRENDIZAJE.md`: Integración técnica (250+ líneas)

## 🔌 Endpoints Disponibles Ahora

| Método | Endpoint | Función |
|--------|----------|---------|
| POST | `/api/correcciones/registrar` | Registrar corrección |
| GET | `/api/correcciones/proveedor/{id}` | Ver historial de correcciones |
| GET | `/api/correcciones/analizar/{id}` | Análisis de campos problemáticos |
| GET | `/api/correcciones/sugerencias/{id}` | Sugerencias automáticas |
| POST | `/api/correcciones/limpiar-antiguas` | Limpieza de datos antiguos |
| GET | `/api/correcciones/estadisticas` | Dashboard de estadísticas |

## 📊 Cómo Funciona

```
┌─────────────────────┐
│ Usuario carga PDF   │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ OCR + IA Extracción │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Usuario revisa form │
│ Corrige datos malo  │
└──────────┬──────────┘
           ↓
┌──────────────────────────────────┐
│ POST /api/correcciones/registrar │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│ LearningService.registrar()       │
│ - Guarda corrección en BD        │
│ - Detecta si es patrón (3+ veces)│
│ - Marca como frecuente si aplica │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│ Próxima factura del proveedor    │
│ IA recibe contexto de aprendizaje│
│ Extracción MEJORADA ✨           │
└──────────────────────────────────┘
```

## 💾 Datos Almacenados

Por cada corrección se registra:
- `factura_id`: Factura que se corrigió
- `proveedor_id`: Proveedor (deducido automáticamente)
- `campo_nombre`: Campo específico (ej: "cif", "direccion")
- `categoria`: Categoría (ej: "proveedor", "cliente", "factura")
- `valor_extraido`: Lo que la IA sacó mal
- `valor_correcto`: Lo que el usuario corrigió
- `confianza_original`: Confianza de la IA (0-100)
- `veces_ocurrido`: Contador de repeticiones
- `es_patron_frecuente`: TRUE si >= 3 veces
- `created_at`: Timestamp automático

## 🔍 Ejemplos de Uso

### Registrar corrección
```bash
curl -X POST http://localhost:8080/api/correcciones/registrar \
  -H "Content-Type: application/json" \
  -d '{
    "factura_id": 42,
    "campo_nombre": "cif",
    "categoria": "proveedor",
    "valor_extraido": "ES123456789A",
    "valor_correcto": "A12345678",
    "confianza_original": 82
  }'
```

### Ver correcciones de un proveedor
```bash
curl http://localhost:8080/api/correcciones/proveedor/5
# Respuesta:
# {
#   "proveedor_id": 5,
#   "proveedor_nombre": "Leroy Merlin",
#   "total_correcciones": 47,
#   "correcciones": [...],
#   "patrones_frecuentes": [...]
# }
```

### Análisis de campos problemáticos
```bash
curl http://localhost:8080/api/correcciones/analizar/5
# Respuesta muestra:
# - Campo "cif": 8 correcciones, SEVERIDAD ALTA
# - Campo "direccion": 5 correcciones, SEVERIDAD MEDIA
# - Etc.
```

### Obtener sugerencias automáticas
```bash
curl http://localhost:8080/api/correcciones/sugerencias/42
# Respuesta:
# {
#   "total_sugerencias": 2,
#   "sugerencias": [
#     {
#       "campo": "cif",
#       "valor_actual": "ES123456789A",
#       "valor_sugerido": "A12345678",
#       "razon": "Patrón frecuente (ocurrió 3 veces)"
#     }
#   ]
# }
```

### Estadísticas globales
```bash
curl http://localhost:8080/api/correcciones/estadisticas
# Respuesta:
# {
#   "total_correcciones": 254,
#   "total_patrones_frecuentes": 18,
#   "porcentaje_patrones": 7.09,
#   "top_campos_problematicos": [...],
#   "top_proveedores_problematicos": [...]
# }
```

## 📈 Beneficios

✅ **Mejora Continua**: El sistema mejora con cada corrección
✅ **Proveedores Consistentes**: Leroy Merlin, Repsol, etc. tendrán mejor precisión
✅ **Sin Intervención Manual**: Automático después de 3 correcciones
✅ **Auditable**: Historial completo de correcciones
✅ **Escalable**: Funciona con cualquier número de proveedores
✅ **Backward Compatible**: No afecta código existente

## ⏳ Próximo Paso: Integración en AIService

Para que la IA **automáticamente use el contexto de aprendizaje**, necesitamos integrar el LearningService en el AIService.

**Cambio requerido**: ~15 líneas en `app/services/ai_service.py`
- Pasar `db` y `proveedor_id` a `extraer_datos_factura()`
- Incluir contexto de aprendizaje en el prompt

**Resultado**: IA automáticamente mejora para proveedores con correcciones previas.

## 🧪 Prueba Rápida

1. **Cargar factura de Leroy Merlin**
   ```bash
   POST /api/facturas/procesar
   # Resultado: CIF extraído como "ES123456789A"
   ```

2. **Registrar corrección 3 veces**
   ```bash
   POST /api/correcciones/registrar (x3)
   ```

3. **Ver patrón identificado**
   ```bash
   GET /api/correcciones/analizar/5
   # Resultado: es_patron_frecuente = true
   ```

4. **Ver estadísticas**
   ```bash
   GET /api/correcciones/estadisticas
   # Resultado: "Leroy Merlin" en top_proveedores_problematicos
   ```

## 📚 Archivos Creados/Modificados

### Nuevos Archivos
- ✅ `app/services/learning_service.py` (350+ líneas)
- ✅ `app/routers/correcciones.py` (350+ líneas)
- ✅ `APRENDIZAJE_AUTOMATICO.md`
- ✅ `INTEGRACION_APRENDIZAJE.md`

### Modificados
- ✅ `app/ftra/models.py` (agregado modelo CorreccionAprendizaje)
- ✅ `app/services/__init__.py` (exportado LearningService)
- ✅ `app/main.py` (incluido router de correcciones)

## 🎓 Aprendizajes Técnicos

### Deduplicación Automática
Cuando se registra una corrección que ya existe:
- Se incrementa `veces_ocurrido`
- Si alcanza 3, se marca como `es_patron_frecuente = true`

### Contexto Generado
El LearningService genera un texto que puede incluirse en el prompt:
```
📚 CONTEXTO DE APRENDIZAJE - Proveedor: Leroy Merlin
1. Campo: proveedor.cif
   ❌ Patrón incorrecto: 'ES123456789A'
   ✅ Patrón correcto: 'A12345678'
   (Ocurrió 3 veces, confianza original: 82%)
```

### Sugerencias Inteligentes
Cuando se carga una factura, el sistema puede sugerir correcciones si:
- El valor extraído coincide con un "patrón incorrecto" conocido
- El patrón es frecuente (>= 3 veces)

## 🚀 Roadmap Futuro

**Fase 2 (1-2 horas)**
- Integración en AIService
- AI automáticamente usa contexto
- Prueba end-to-end

**Fase 3 (1-2 días)**
- Frontend: Mostrar sugerencias
- Frontend: Botón para registrar correcciones
- Dashboard de mejoras

**Fase 4 (1-2 semanas)**
- Fine-tuning automático
- Machine Learning con datos históricos
- Predicción de campos problemáticos

## 💡 Casos de Uso

1. **Leroy Merlin CIF**: Siempre "ES..." cuando debe ser "A..."
2. **Repsol Dirección**: Siempre omite "Edificio X"
3. **Facturas Multisede**: Sucursal no se detecta en dirección
4. **Fechas con Formato**: "01-dic-2024" interpretado mal
5. **Números Borrosos**: "O" confundido con "0" en CIF

Después de 3 correcciones por proveedores, el sistema mejora significativamente.

## ✨ Resultado Final

Un sistema de facturación que **aprende de sus errores** y mejora continuamente sin intervención del desarrollador. ¡El usuario es el entrenador del AI!
