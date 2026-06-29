# Sistema de Confianza y Precisión

## 🎯 Descripción General

El sistema ahora incluye un mecanismo automático de confianza que evalúa la precisión de cada campo extraído. Esto permite a los usuarios identificar fácilmente qué datos necesitan revisión antes de guardar.

## 📊 Niveles de Confianza

### Clasificación de Confianza

- **95-100%**: Confianza muy alta (texto muy claro, datos inequívocos)
- **90-94%**: Confianza alta (texto claro, posibles pequeñas variaciones OCR)
- **85-89%**: Confianza moderada (texto legible, algunos caracteres borrosos)
- **70-84%**: Confianza baja (texto parcialmente legible, requiere revisión)
- **50-69%**: Confianza muy baja (datos borrosos, ambiguos)
- **< 50%**: No confiable (datos ilegibles o ausentes)

### Umbral de Revisión

**Umbral de alerta: 85%**

Los campos con confianza **inferior a 85%** se resaltan en **amarillo** como advertencia de que requieren revisión manual.

## 🔍 Cómo Funciona

### 1. Extracción con Confianza

Cuando el IA procesa el texto OCR, ahora retorna no solo el valor sino también un nivel de confianza:

```json
{
  "numero_factura": {
    "valor": "F2026-001",
    "confianza": 99
  },
  "proveedor": {
    "nombre": {
      "valor": "Repsol",
      "confianza": 98
    },
    "cif": {
      "valor": "A1234567B",
      "confianza": 92
    },
    "direccion": {
      "valor": "Calle Principal 123",
      "confianza": 75
    }
  },
  "factura": {
    "total": {
      "valor": 1250.50,
      "confianza": 95
    },
    "fecha": {
      "valor": "2024-12-15",
      "confianza": 88
    }
  }
}
```

### 2. Análisis Automático

El sistema calcula:
- **Confianza promedio**: Promedio de confianza de todos los campos
- **Campos bajo confianza**: Lista de campos con confianza < 85%
- **Flag de revisión**: Indica si hay campos que necesitan atención

### 3. Presentación al Usuario

#### En la interfaz principal:
```
Archivo procesado exitosamente (Confianza: 91.3%)
⚠️ Revisar campos con baja confianza
```

#### En el dashboard:
- ✅ Verde: Todas confianzas aceptables
- ⚠️ Amarillo: Revisar campos con baja confianza

#### En campos individuales:
```html
<input class="campo-bajo-confianza" />
<span class="badge-confianza confianza-baja">75%</span>
```

## 📱 Interfaz de Usuario

### Indicadores Visuales

1. **Badge de Confianza**
   - Verde: > 90% (muy confiable)
   - Amarillo: 85-89% (moderado)
   - Rojo: < 85% (requiere revisión)

2. **Campos Resaltados**
   - Fondo amarillo claro para campos bajo confianza
   - Border izquierdo amarillo para énfasis
   - Label en negrita indicando el campo

3. **Advertencia General**
   - Alerta en amarillo si hay campos bajo confianza
   - Lista de campos que necesitan revisión

## 🔧 API Endpoints

### Respuesta de procesamiento

```json
{
  "exito": true,
  "mensaje": "Archivo procesado exitosamente",
  "factura_id": 1,
  "confianza_promedio": 91.3,
  "tiene_campos_bajo_confianza": true,
  "campos_bajo_confianza": [
    {
      "categoria": "proveedor",
      "campo": "direccion",
      "valor": "Calle Principal 123",
      "confianza": 75
    },
    {
      "categoria": "factura",
      "campo": "forma_pago",
      "valor": "Transferencia",
      "confianza": 72
    }
  ],
  "datos": {
    "factura_id": 1,
    "numero": "F2026-001",
    "fecha": "2024-12-15",
    "total": 1250.50,
    "proveedor": "Repsol",
    "cliente": "Mi Empresa",
    "lineas_count": 3,
    "confianza_promedio": 91.3,
    "tiene_campos_bajo_confianza": true
  }
}
```

## 📚 Base de Datos

### Nuevos Campos en FTRA_facturas

```sql
-- JSON con estructura de confianza para cada campo
json_confianza TEXT

-- Flag rápido para identificar facturas con baja confianza
tiene_campos_bajo_confianza BOOLEAN DEFAULT FALSE
```

### Estructura de json_confianza

```json
{
  "proveedor": {
    "nombre": {"valor": "...", "confianza": 98},
    "cif": {"valor": "...", "confianza": 95},
    ...
  },
  "cliente": { ... },
  "factura": { ... },
  "lineas": [ ... ]
}
```

## 💡 Casos de Uso

### 1. Factura de Buena Calidad
- Confianza: 95-100%
- Acción: Guardar directamente
- Verificación: Mínima

### 2. Factura con Calidad Media
- Confianza: 85-94%
- Acción: Mostrar algunos campos resaltados
- Verificación: Revisar campos amarillos

### 3. Factura de Baja Calidad
- Confianza: < 85%
- Acción: Todos los campos resaltados
- Verificación: Revisar completamente antes de guardar

## 🎨 Colores y Estilos

### Confianza Alta (≥ 90%)
```css
background-color: #d1fae5;  /* Verde claro */
color: #065f46;              /* Verde oscuro */
```

### Confianza Media (85-89%)
```css
background-color: #fef08a;  /* Amarillo claro */
color: #78350f;              /* Marrón oscuro */
```

### Confianza Baja (< 85%)
```css
background-color: #fee2e2;  /* Rojo claro */
color: #7f1d1d;              /* Rojo oscuro */
```

## 📊 Reporte de Confianza

Consultar confianza de una factura:

```bash
GET /api/facturas/{id}
```

Respuesta incluye:
- `json_confianza`: Estructura completa de confianza
- `tiene_campos_bajo_confianza`: Flag booleano
- En historial: Anotación de confianza promedio al crear

## 🔄 Flujo de Trabajo Recomendado

1. **Subir documento**
   - Sistema procesa OCR + IA
   - Calcula confianza automáticamente

2. **Revisar confianza**
   - Ver alertas de campos bajo confianza
   - Verificar valores en formulario

3. **Editar si necesario**
   - Hacer clic en campos amarillos
   - Corregir valores manualmente
   - Guardar cambios

4. **Confirmar**
   - Sistema registra cambios en historial
   - Marca como "editada" si se cambió

5. **Validar**
   - Cambiar estado a "validada"
   - Registrar en auditoria

## 🛠️ Configuración

### Ajustar umbral de confianza

En `app/services/ai_service.py`:
```python
tiene_bajo_confianza, campos_bajo_confianza = self.ai_service.extraer_campos_bajo_confianza(
    datos_json_con_confianza,
    umbral=85  # Cambiar este valor (0-100)
)
```

### Personalizar mensaje de advertencia

En el frontend, modificar en `app/main.py`:
```javascript
if (resultado.tiene_campos_bajo_confianza) {
    // Personalizar mensaje aquí
}
```

## 📈 Métricas

El sistema guarda:
- Confianza promedio por factura
- Cantidad de campos bajo confianza
- Flag de revisión necesaria
- Historial de cambios post-procesamiento

## 🚀 Próximas Mejoras

- [ ] Exportar reporte de confianza por proveedor
- [ ] Análisis de tendencias de confianza
- [ ] Entrenamiento de IA con retroalimentación
- [ ] Filtro de facturas por rango de confianza
- [ ] Certificación de confianza automática
