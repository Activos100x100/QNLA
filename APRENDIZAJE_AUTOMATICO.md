# Sistema de Aprendizaje Automático

## 🎯 Descripción General

El sistema ahora es capaz de **aprender de las correcciones** que realiza el usuario. Cuando un usuario corrige un dato extraído incorrectamente, el sistema registra esa corrección y la usa para mejorar futuras extracciones del mismo proveedor.

**Ejemplo Real:**
- Leroy Merlin siempre tiene CIF mal extraído como "ES123456789A" pero el correcto es "A12345678"
- Tras la segunda corrección, el sistema identifica un patrón
- En la tercera factura de Leroy Merlin, el sistema ya incluye esta información en el prompt de la IA
- La IA mejora su precisión para este proveedor específico

## 🏗️ Arquitectura

### 1. Modelo de Base de Datos: CorreccionAprendizaje
```python
FTRA_correcciones_aprendizaje
├── id (PK)
├── factura_id (FK) ──→ FTRA_facturas
├── proveedor_id (FK) ──→ FTRA_proveedores
├── campo_nombre (INDEX) # "cif", "direccion", "total", etc.
├── categoria (INDEX)    # "proveedor", "cliente", "factura"
├── valor_extraido       # Lo que la IA sacó mal
├── valor_correcto       # Lo que el usuario corrigió
├── confianza_original   # 0-100, confianza de la IA
├── es_patron_frecuente  # TRUE si ocurrió 3+ veces
├── veces_ocurrido       # Counter de cuántas veces pasó
└── created_at
```

### 2. Servicio de Aprendizaje: LearningService
Ubicación: `app/services/learning_service.py`

Métodos principales:
- `registrar_correccion()`: Captura correcciones del usuario
- `obtener_correcciones_proveedor()`: Historial completo de correcciones
- `obtener_correcciones_frecuentes()`: Solo los patrones que se repiten
- `generar_contexto_aprendizaje()`: Crea un texto para incluir en el prompt de IA
- `analizar_mejora()`: Identifica qué campos necesitan más trabajo
- `sugerir_correcciones()`: Propone correcciones basadas en aprendizaje previo
- `limpiar_correcciones_antiguas()`: Mantiene el sistema limpio

### 3. Router de Correcciones: app/routers/correcciones.py
Endpoints disponibles:
- `POST /api/correcciones/registrar`: Registrar una corrección
- `GET /api/correcciones/proveedor/{id}`: Ver correcciones de un proveedor
- `GET /api/correcciones/analizar/{id}`: Análisis de campos problemáticos
- `GET /api/correcciones/sugerencias/{id}`: Sugerencias de corrección
- `POST /api/correcciones/limpiar-antiguas`: Limpieza de datos antiguos
- `GET /api/correcciones/estadisticas`: Dashboard de estadísticas

## 📊 Flujo de Aprendizaje

### Flujo Actual (v1)
```
Usuario sube factura
    ↓
Procesamiento normal (OCR + IA + confianza)
    ↓
Usuario ve formulario con datos
    ↓
Usuario corrige campo erróneo (ej: CIF)
    ↓
POST /api/correcciones/registrar
    ↓
LearningService.registrar_correccion()
    ↓
Datos guardados en FTRA_correcciones_aprendizaje
    ↓
Si veces_ocurrido >= 3:
    es_patron_frecuente = TRUE
```

### Flujo Futuro (v2)
```
Usuario sube factura de Leroy Merlin
    ↓
AIService.extraer_datos_factura()
    ↓
LearningService.generar_contexto_aprendizaje()
    ↓
Contexto incluido en prompt:
    "📚 CONTEXTO DE APRENDIZAJE - Proveedor: Leroy Merlin
     1. Campo: proveedor.cif
        ❌ Patrón incorrecto: 'ES123456789A'
        ✅ Patrón correcto: 'A12345678'
        (Ocurrió 3 veces, confianza original: 82%)"
    ↓
IA extrae con contexto
    ↓
Resultado más preciso
```

## 🔄 Casos de Uso

### Caso 1: Registrar Corrección
```bash
POST /api/correcciones/registrar
{
    "factura_id": 1,
    "campo_nombre": "cif",
    "categoria": "proveedor",
    "valor_extraido": "ES123456789A",
    "valor_correcto": "A12345678",
    "confianza_original": 82
}

Response:
{
    "exito": true,
    "mensaje": "Corrección registrada exitosamente",
    "correccion_id": 1,
    "es_patron_frecuente": false,
    "veces_ocurrido": 1
}
```

### Caso 2: Analizar Campos Problemáticos
```bash
GET /api/correcciones/analizar/5

Response:
{
    "proveedor_id": 5,
    "proveedor_nombre": "Leroy Merlin",
    "total_correcciones": 47,
    "campos_problematicos": [
        {
            "campo": "cif",
            "categoria": "proveedor",
            "total_correcciones": 8,
            "confianza_promedio": 75,
            "severidad": "ALTA",
            "ejemplos": [
                {
                    "incorrecto": "ES123456789A",
                    "correcto": "A12345678",
                    "veces": 3
                }
            ]
        }
    ]
}
```

### Caso 3: Obtener Sugerencias
```bash
GET /api/correcciones/sugerencias/42

Response:
{
    "factura_id": 42,
    "total_sugerencias": 2,
    "sugerencias": [
        {
            "categoria": "proveedor",
            "campo": "cif",
            "valor_actual": "ES123456789A",
            "valor_sugerido": "A12345678",
            "razon": "Patrón frecuente (ocurrió 3 veces)",
            "confianza_sugerencia": 95
        }
    ]
}
```

## 📈 Estadísticas del Sistema

```bash
GET /api/correcciones/estadisticas

Response:
{
    "total_correcciones": 254,
    "total_patrones_frecuentes": 18,
    "porcentaje_patrones": 7.09,
    "top_campos_problematicos": [
        {
            "campo": "cif",
            "correcciones": 47
        },
        {
            "campo": "direccion",
            "correcciones": 32
        }
    ],
    "top_proveedores_problematicos": [
        {
            "proveedor": "Leroy Merlin",
            "correcciones": 47
        }
    ]
}
```

## 🔐 Seguridad

- Las correcciones solo se registran si la factura existe
- Se registra el proveedor automáticamente (desde la factura)
- Auditoría completa (created_at timestamp)
- No se elimina historial, solo se marca como antiguo
- Acceso a través de routers autenticados (opcional)

## 🔧 Configuración

### Umbral para Patrón Frecuente
En `app/services/learning_service.py`:
```python
if correccion_existente.veces_ocurrido >= 3:  # Cambiar a 2, 5, etc.
    correccion_existente.es_patron_frecuente = True
```

### Días de Antigüedad
En `app/services/learning_service.py`:
```python
def limpiar_correcciones_antiguas(self, db, dias_antiguedad: int = 180):
    # Cambiar 180 a otro valor según política
```

### Límite de Correcciones
En `app/services/learning_service.py`:
```python
def obtener_correcciones_proveedor(self, db, proveedor_id, limite: int = 100):
    # Cambiar 100 a otro valor según necesidad
```

## 📚 Integración Futura

### Fase 2: Aprendizaje Automático
- Incluir contexto de correcciones en el prompt de IA
- Mejorar prompts basado en patrones observados
- Ajustar confianza dinámicamente

### Fase 3: Machine Learning
- Fine-tuning de modelo con datos históricos
- Entrenar modelo específico por proveedor
- Predicción de campos problemáticos

### Fase 4: Feedback Loop
- Usuario valida sugerencias (thumbs up/down)
- Sistema aprende de validaciones
- Mejora continua sin intervención manual

## 🛠️ Ejemplo de Integración en Frontend

```javascript
// Cuando usuario corrige un campo
function corregirCampo(factura_id, campo, valor_incorrecto, valor_correcto) {
    fetch('/api/correcciones/registrar', {
        method: 'POST',
        body: JSON.stringify({
            factura_id: factura_id,
            campo_nombre: campo.split('.')[1],  // "cif"
            categoria: campo.split('.')[0],     // "proveedor"
            valor_extraido: valor_incorrecto,
            valor_correcto: valor_correcto,
            confianza_original: obtenerConfianza(campo)
        })
    }).then(r => r.json())
      .then(data => {
          console.log(`Corrección registrada: ${data.correccion_id}`);
          if (data.es_patron_frecuente) {
              alert('⚠️ Este error se repite. El sistema aprenderá.');
          }
      });
}

// Obtener sugerencias al cargar factura
function cargarSugerencias(factura_id) {
    fetch(`/api/correcciones/sugerencias/${factura_id}`)
        .then(r => r.json())
        .then(data => {
            data.sugerencias.forEach(sug => {
                mostrarSugerencia(sug);
            });
        });
}

// Mostrar sugerencia en formulario
function mostrarSugerencia(sugerencia) {
    const campo = document.querySelector(`[data-field="${sugerencia.categoria}.${sugerencia.campo}"]`);
    if (campo) {
        const badge = document.createElement('span');
        badge.className = 'badge bg-success ms-2';
        badge.innerHTML = `💡 Valor anterior: ${sugerencia.valor_sugerido}`;
        campo.appendChild(badge);
    }
}
```

## 📊 Métricas Importantes

- **Total de Correcciones**: Acumulado de todas
- **Patrones Frecuentes**: Correcciones que se repiten (>= 3 veces)
- **Severidad**: ALTA (>= 5), MEDIA (>= 3), BAJA (< 3)
- **Confianza Promedio**: Promedio de confianza original de un campo
- **Tasa de Mejora**: (Patrones identificados / Correcciones totales) * 100

## 🚀 Próximos Pasos

1. ✅ Modelo de base de datos
2. ✅ Servicio de aprendizaje
3. ✅ Router de correcciones
4. ⏳ Integración en AIService (incluir contexto en prompt)
5. ⏳ Frontend (mostrar sugerencias)
6. ⏳ Métricas y reportes
7. ⏳ Fine-tuning automático de IA

## 📞 Soporte

Para dudas sobre el sistema de aprendizaje, consultar:
- `app/services/learning_service.py`: Lógica completa
- `app/routers/correcciones.py`: Endpoints
- `app/ftra/models.py`: Modelo CorreccionAprendizaje
- Tabla: `FTRA_correcciones_aprendizaje` en PostgreSQL
