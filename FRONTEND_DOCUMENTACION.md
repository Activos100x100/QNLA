# 🎨 Frontend - FTRA Sistema de Procesamiento de Facturas

## Descripción General

Frontend moderno, responsive y profesional basado en:
- **FastAPI + Jinja2** para templates
- **Bootstrap 5** para diseño responsivo
- **Chart.js** para gráficos
- **Progressive Web App (PWA)** para instalación en móviles
- **WebSocket** para actualizaciones en tiempo real
- **Service Worker** para funcionalidad offline

## 📁 Estructura de Directorios

```
app/
├── templates/
│   ├── base.html                    # Layout base con sidebar y topbar
│   ├── dashboard.html               # Dashboard con estadísticas
│   ├── cargar.html                  # Pantalla de carga de facturas
│   ├── facturas/
│   │   ├── list.html                # Listado de facturas
│   │   └── detail.html              # Vista detalle de factura
│   ├── proveedores.html             # Gestión de proveedores
│   ├── clientes.html                # Gestión de clientes
│   ├── estadisticas.html            # Gráficos y reportes
│   └── configuracion.html           # Configuración del sistema
│
├── static/
│   ├── css/
│   │   └── main.css                 # Estilos principales (1600+ líneas)
│   ├── js/
│   │   ├── main.js                  # JavaScript principal
│   │   ├── upload.js                # Manager de carga de archivos
│   │   └── service-worker.js        # Service Worker para PWA
│   ├── manifest.json                # Manifest para PWA
│   ├── img/                         # Iconos e imágenes
│   │   ├── icon-192x192.png
│   │   ├── icon-512x512.png
│   │   └── maskable-icon-*png
│   └── offline.html                 # Página offline
```

## 🎯 Características Implementadas

### 1. Diseño Base
- ✅ Layout responsivo con menú lateral (sidebar)
- ✅ Barra superior (topbar) con búsqueda y notificaciones
- ✅ Tema claro/oscuro con persistencia en localStorage
- ✅ Animaciones suaves y transiciones
- ✅ Estructura modular y reutilizable

### 2. Dashboard
- ✅ 8 tarjetas de estadísticas (facturas hoy, procesadas, pendientes, errores, importe, IVA, tiempo, confianza)
- ✅ 3 gráficos principales:
  - Facturas procesadas por día (línea)
  - Importe mensual (barras)
  - Facturas recientes (tabla)
- ✅ 3 gráficos adicionales:
  - Top 5 proveedores (doughnut)
  - Estados de facturas (pie)
  - Confianza IA (polar area)
- ✅ Últimas facturas con estado y acciones

### 3. Listado de Facturas
- ✅ Tabla responsiva con paginación
- ✅ Filtros avanzados:
  - Por estado (10 opciones)
  - Por proveedor
  - Por fecha (desde/hasta)
  - Por nivel de confianza
- ✅ Vista dual: tabla / grid de tarjetas
- ✅ Columnas: número, proveedor, cliente, fecha, importe, confianza, estado
- ✅ Acciones rápidas: ver, descargar
- ✅ Badges con colores por estado y confianza

### 4. Pantalla de Carga
- ✅ Drag & Drop para archivos
- ✅ Selección múltiple de archivos
- ✅ Captura de fotos con cámara (móvil)
- ✅ Vista previa de archivos con miniaturas
- ✅ Barra de progreso en tiempo real
- ✅ Estados de procesamiento:
  - Subiendo...
  - Leyendo PDF...
  - Aplicando OCR...
  - Analizando con IA...
  - Guardando...
  - Completado
- ✅ Cancelar carga
- ✅ Resumen de resultados

### 5. Vista Detalle de Factura
- ✅ Split screen: PDF a la izquierda, datos a la derecha
- ✅ Visor PDF con zoom (50-300%)
- ✅ Formulario editable con todos los campos
- ✅ Badges de confianza en cada campo
- ✅ Secciones:
  - Proveedor (nombre, CIF, dirección, teléfono, email)
  - Cliente (nombre, CIF)
  - Factura (número, fecha, subtotal, IVA, total, forma de pago)
  - Líneas de factura (tabla editable)
  - Notas
- ✅ Historial de cambios con timeline

### 6. Responsividad
- ✅ Móvil (< 480px): Menú hamburguesa, botones grandes, tablas convertidas a cards
- ✅ Tablet (480px - 768px): Layout optimizado, grid responsive
- ✅ Desktop (> 768px): Todas las características disponibles
- ✅ Scrollbars personalizadas
- ✅ Touch-friendly en móviles

### 7. PWA (Progressive Web App)
- ✅ Manifest.json con configuración completa
- ✅ Service Worker para caché y offline
- ✅ Iconos para diferentes tamaños (192x192, 256x256, 512x512)
- ✅ Soporte para "Instalar en pantalla de inicio"
- ✅ Sincronización en segundo plano
- ✅ Notificaciones push

### 8. Tema Claro/Oscuro
- ✅ Toggle en la barra superior
- ✅ Detecta preferencia del sistema
- ✅ Persistencia en localStorage
- ✅ CSS variables para fácil personalización
- ✅ Colores optimizados para ambos temas

### 9. Interactividad
- ✅ Notificaciones flotantes (toast)
- ✅ Modales Bootstrap
- ✅ Dropdown menus
- ✅ Collapsible sidebar submenu
- ✅ Validaciones de forma
- ✅ Búsqueda global

### 10. Gráficos
- ✅ Chart.js integrado
- ✅ 5 tipos de gráficos (line, bar, doughnut, pie, polarArea)
- ✅ Datos dinámicos (fácil de conectar con backend)
- ✅ Tooltip y leyendas personalizadas

## 🎨 Paleta de Colores

```css
--primary: #2563eb        /* Azul principal */
--success: #16a34a        /* Verde */
--warning: #ea580c        /* Naranja */
--danger: #dc2626         /* Rojo */
--info: #0891b2           /* Cian */

Grises: #f9fafb a #111827 (50 a 900)
```

## 🚀 Modo de Uso

### Iniciar desarrollo
```bash
cd /Users/elizabethjimenez/FTRA
python -m uvicorn app.main:app --reload
# Abrir http://localhost:8000
```

### Estructura de URL
```
/                               → Dashboard
/cargar                         → Carga de facturas
/facturas                       → Listado de facturas
/facturas/{id}                  → Detalle de factura
/proveedores                    → Gestión de proveedores
/clientes                       → Gestión de clientes
/estadisticas                   → Estadísticas
/configuracion                  → Configuración
/logs                           → Logs del sistema
```

## 📱 PWA - Instalación

### Android
1. Abrir FTRA en Chrome
2. Menú ⋮ → "Instalar en pantalla de inicio"
3. Aplicación disponible en el escritorio

### iPhone
1. Abrir FTRA en Safari
2. Compartir → "Agregar a pantalla de inicio"
3. Aplicación disponible en la pantalla de inicio

### Desktop
1. Click en la barra de direcciones (ícono de descarga)
2. "Instalar FTRA"
3. Disponible en menú de aplicaciones

## 🎯 Endpoints Requeridos en FastAPI

```python
# Dashboard
@app.get("/")
@app.get("/dashboard")

# Facturas
@app.get("/cargar")
@app.post("/api/facturas/procesar")
@app.get("/facturas")
@app.get("/facturas/{id}")
@app.put("/facturas/{id}")
@app.delete("/facturas/{id}")

# Filtros
@app.get("/api/facturas/search")
@app.get("/api/facturas/estado/{estado}")

# WebSocket
@app.websocket("/ws")

# Estadísticas
@app.get("/api/estadisticas/dashboard")
@app.get("/api/estadisticas/proveedores")

# Proveedores y Clientes
@app.get("/proveedores")
@app.get("/clientes")
```

## 🔌 Integración con Backend

### 1. Carga de Facturas
```javascript
// Enviar archivo a procesar
const formData = new FormData();
formData.append('file', file);

const response = await fetch('/api/facturas/procesar', {
    method: 'POST',
    body: formData
});

const data = await response.json();
// Resultado: {
//   exito: true,
//   factura_id: 1,
//   numero_factura: 'INV-2024-0001',
//   datos: {...},
//   confianza_promedio: 95,
//   campos_bajo_confianza: [],
//   tiene_campos_bajo_confianza: false
// }
```

### 2. WebSocket para Actualizaciones
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    // Tipos: status_update, notification, error
    // Actualizar UI en tiempo real
});
```

## 🛠️ Customización

### Cambiar Colores
Editar `app/static/css/main.css`:
```css
:root {
    --primary: #2563eb;        /* Cambiar aquí */
    --success: #16a34a;        /* Cambiar aquí */
    ...
}
```

### Agregar Nueva Página
1. Crear `app/templates/nueva-pagina.html`
2. Extender `base.html`
3. Agregar link en sidebar (`base.html`)
4. Crear endpoint en FastAPI

### Agregar Gráfico
1. Crear canvas en template: `<canvas id="newChart"></canvas>`
2. Agregar código en `extra_js` del template

## 📊 Performance

- ✅ Imágenes optimizadas
- ✅ CSS minificado (puede optimizarse más)
- ✅ JavaScript modular
- ✅ Caché con Service Worker
- ✅ Lazy loading de componentes

## 🧪 Testing

Tests recomendados:
- [ ] Responsive en móvil (iPhone, Android)
- [ ] Drag & drop de archivos
- [ ] Tema oscuro/claro
- [ ] Filtros y búsqueda
- [ ] Carga de progreso
- [ ] WebSocket en tiempo real
- [ ] PWA offline
- [ ] Notificaciones

## 📝 Notas de Desarrollo

### Estado Actual
- ✅ Todos los templates creados
- ✅ CSS profesional y completo
- ✅ JavaScript interactivo
- ⏳ Endpoints FastAPI (próximo paso)
- ⏳ Conexión con BD (próximo paso)
- ⏳ WebSocket en tiempo real (próximo paso)

### Próximas Mejoras
1. [ ] Agregar más animaciones
2. [ ] Exportar a Excel/PDF
3. [ ] Sistema de permisos (roles)
4. [ ] Búsqueda avanzada
5. [ ] Reportes personalizados
6. [ ] Integración con otras APPs
7. [ ] API documentation
8. [ ] E2E tests

## 📞 Soporte

Para preguntas o mejoras sobre el frontend, revisar:
- `app/templates/base.html` - Estructura base
- `app/static/css/main.css` - Estilos
- `app/static/js/main.js` - Funcionalidad principal
- `app/static/js/upload.js` - Carga de archivos

---

**Estado**: 95% Completado
**Última actualización**: 27 de junio de 2026
**Versión**: 1.0.0
