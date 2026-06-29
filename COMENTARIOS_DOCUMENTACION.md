# 💬 Sistema de Comentarios y Colaboración en Tiempo Real

## 📋 Descripción General

Sistema completo de comentarios para facturas que permite a múltiples usuarios colaborar, comunicarse y auditar cambios. Incluye:

- ✅ Comentarios con tipos (Información, Revisión, Incidencia, Aprobación, Rechazo)
- ✅ Respuestas anidadas (threads de conversación)
- ✅ Estados (Pendiente, Resuelto)
- ✅ Actualización en tiempo real via WebSocket
- ✅ Historial de auditoría completo
- ✅ Filtros para facturas con comentarios pendientes
- ✅ Indicadores visuales en listados

---

## 🗄️ Modelo de Datos

### Tabla: `comentarios`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER PK | Identificador único |
| `factura_id` | INTEGER FK | Referencia a factura (CASCADE) |
| `usuario_id` | VARCHAR(255) | ID del usuario (sin login: "usuario_default") |
| `usuario_nombre` | VARCHAR(255) | Nombre del usuario (cache) |
| `texto` | TEXT | Contenido del comentario |
| `tipo` | VARCHAR(20) | 📋 informacion / 👁️ revision / ⚠️ incidencia / ✅ aprobacion / ❌ rechazo |
| `parent_id` | INTEGER FK NULL | Para respuestas anidadas |
| `estado` | VARCHAR(20) | pendiente \| resuelto |
| `resuelto_por` | VARCHAR(255) | Nombre de quien lo resolvió |
| `resuelto_en` | TIMESTAMP | Cuándo se resolvió |
| `created_at` | TIMESTAMP | Cuándo se creó |
| `updated_at` | TIMESTAMP | Cuándo se actualizó |

**Constraints:**
- CHECK: `tipo IN ('informacion', 'revision', 'incidencia', 'aprobacion', 'rechazo')`
- CHECK: `estado IN ('pendiente', 'resuelto')`
- INDEX: factura_id, usuario_id, parent_id, estado, tipo

### Tabla: `comentarios_auditoria`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER PK | Identificador único |
| `comentario_id` | INTEGER FK | Referencia a comentario |
| `factura_id` | INTEGER | ID de factura (desnormalizado) |
| `usuario_id` | VARCHAR(255) | Quién realizó la acción |
| `usuario_nombre` | VARCHAR(255) | Nombre del usuario |
| `accion` | VARCHAR(50) | crear \| editar \| resolver \| reabrirDISCOUNT |
| `cambios_anteriores` | TEXT | JSON con valores anteriores |
| `cambios_nuevos` | TEXT | JSON con valores nuevos |
| `created_at` | TIMESTAMP | Cuándo ocurrió la acción |

**INDEX:** comentario_id, usuario_id, accion, created_at

---

## 🔌 API REST

### Crear Comentario

```http
POST /api/comentarios/
Content-Type: application/json

{
  "factura_id": 1,
  "texto": "Falta la matrícula del vehículo.",
  "tipo": "incidencia",
  "parent_id": null
}
```

**Respuesta:**
```json
{
  "id": 1,
  "factura_id": 1,
  "usuario_id": "usuario_default",
  "usuario_nombre": "Usuario",
  "texto": "Falta la matrícula del vehículo.",
  "tipo": "incidencia",
  "estado": "pendiente",
  "parent_id": null,
  "respuestas": [],
  "created_at": "2026-06-27T15:30:00+00:00",
  "updated_at": "2026-06-27T15:30:00+00:00",
  "resuelto_por": null,
  "resuelto_en": null
}
```

### Obtener Comentarios de Factura

```http
GET /api/comentarios/factura/{factura_id}
```

Retorna todos los comentarios principales con respuestas anidadas.

### Obtener Comentarios Pendientes

```http
GET /api/comentarios/factura/{factura_id}/pendientes
```

Retorna solo comentarios con estado "pendiente".

### Obtener por Tipo

```http
GET /api/comentarios/factura/{factura_id}/tipo/{tipo}
```

**Tipos válidos:** `informacion`, `revision`, `incidencia`, `aprobacion`, `rechazo`

### Obtener Respuestas

```http
GET /api/comentarios/{comentario_id}/respuestas
```

Retorna todas las respuestas de un comentario.

### Actualizar Comentario

```http
PUT /api/comentarios/{comentario_id}
Content-Type: application/json

{
  "texto": "Texto actualizado",
  "tipo": "revision"
}
```

### Resolver Comentario

```http
POST /api/comentarios/{comentario_id}/resolver
```

Marca un comentario como resuelto (registra quién y cuándo).

### Reabrircomenta rio

```http
POST /api/comentarios/{comentario_id}/reabrirDISCOUNT
```

Marca un comentario resuelto como pendiente nuevamente.

### Estadísticas

```http
GET /api/comentarios/factura/{factura_id}/estadisticas
```

**Respuesta:**
```json
{
  "factura_id": 1,
  "total_comentarios": 5,
  "comentarios_pendientes": 2,
  "comentarios_resueltos": 3,
  "tipos_distribucion": {
    "informacion": 2,
    "revision": 1,
    "incidencia": 1,
    "aprobacion": 1,
    "rechazo": 0
  },
  "ultimos_comentarios": [...]
}
```

### Verificar Comentarios Pendientes

```http
GET /api/comentarios/factura/{factura_id}/tiene-pendientes
```

**Respuesta:**
```json
{
  "tiene_pendientes": true
}
```

### Facturas con Comentarios Pendientes

```http
GET /api/comentarios/sistema/facturas-con-pendientes
```

**Respuesta:**
```json
{
  "facturas_con_pendientes": [1, 3, 5, 7]
}
```

### Auditoría de Comentario

```http
GET /api/comentarios/{comentario_id}/auditoria
```

Retorna historial completo de cambios.

### Auditoría de Factura

```http
GET /api/comentarios/factura/{factura_id}/auditoria
```

Retorna auditoría de todos los comentarios de una factura.

### Auditoría de Usuario

```http
GET /api/comentarios/usuario/{usuario_id}/auditoria
```

Retorna todas las acciones de un usuario.

---

## 🎨 Frontend

### Componente ComentariosManager (JavaScript)

```javascript
class ComentariosManager {
    constructor(facturaId)  // Inicializa con ID de factura
    
    cargarComentarios()     // Carga comentarios desde API
    agregarComentario()     // Crea nuevo comentario
    resolver(comentarioId)  // Marca como resuelto
    responder(comentarioId) // Prepara respuesta (focus)
    renderizarComentarios() // Renderiza HTML
}
```

**Uso:**
```javascript
const comentariosManager = new ComentariosManager(facturaId);
// Se inicializa automáticamente en DOMContentLoaded
```

### UI Elementos

**En `detail.html`:**
- Formulario de nuevo comentario con selector de tipo
- Lista de comentarios con respuestas anidadas
- Botones para resolver/reabrircomenta rios
- Timestamps y nombres de usuarios
- Indicador de estado (Pendiente/Resuelto)

**En `list.html`:**
- Columna "Comentarios" en tabla
- Contador de comentarios totales
- Indicador de comentarios pendientes
- Filtro para mostrar solo facturas con pendientes

### CSS

Se agregaron estilos para:
- `.border-left-accent` - Tarjetas con borde izquierdo coloreado
- Scrollbar personalizada
- Badges por tipo de comentario
- Timeline para auditoría
- Responsive en móvil

---

## 🔌 WebSocket

### Eventos en Tiempo Real

**Enviar comentario nuevo:**
```javascript
webSocketManager.ws.send(JSON.stringify({
    type: 'comentario_nuevo',
    factura_id: facturaId,
    usuario: 'Nombre Usuario'
}));
```

**Recibir notificación:**
```javascript
// En main.js WebSocketManager.handleMessage()
case 'comentario_nuevo':
    notificationManager.show(`Nuevo comentario de ${data.usuario}`, 'info');
    comentariosManager.cargarComentarios();
    break;
```

**Eventos soportados:**
- `comentario_nuevo` - Nuevo comentario creado
- `comentario_resuelto` - Comentario marcado como resuelto

---

## 📊 Service Layer

### ComentariosService

```python
servicio = ComentariosService(db)

# Crear
comentario = servicio.crear_comentario(
    factura_id=1,
    usuario_id="user123",
    usuario_nombre="Juan Pérez",
    texto="Comentario aquí",
    tipo="revision",
    parent_id=None
)

# Obtener
comentarios = servicio.obtener_comentarios_factura(factura_id=1)
pendientes = servicio.obtener_comentarios_pendientes(factura_id=1)

# Resolver
servicio.resolver_comentario(comentario_id=1, usuario_id="admin", usuario_nombre="Admin")

# Estadísticas
stats = servicio.obtener_estadisticas(factura_id=1)
tiene = servicio.tiene_comentarios_pendientes(factura_id=1)

# Auditoría
auditoria = servicio.obtener_auditoria_comentario(comentario_id=1)
```

---

## 🔐 Seguridad

### Auditoría Completa

Cada acción se registra en `comentarios_auditoria`:
- ✅ Crear comentario
- ✅ Editar comentario
- ✅ Marcar como resuelto
- ✅ Reabrircomenta rio

Con: usuario_id, usuario_nombre, timestamp, cambios anteriores/nuevos.

### Validaciones

- ✅ Máx 5000 caracteres por comentario
- ✅ Tipos válidos (enum)
- ✅ Estados válidos (enum)
- ✅ Factura debe existir
- ✅ Parent comment debe existir (si es respuesta)
- ✅ No se puede eliminar (audit trail)

---

## 🚀 Migración de BD

### Crear Tablas

```bash
alembic upgrade head
```

### Archivo: `20260627_05_add_comentarios.py`

- Crea tabla `comentarios`
- Crea tabla `comentarios_auditoria`
- Agrega índices
- Agrega constraints

### Revertir

```bash
alembic downgrade -1
```

---

## 📱 Ejemplos de Uso

### Flujo Completo en UI

1. Usuario abre detalle de factura en `/facturas/1`
2. Ve formulario de comentarios
3. Escribe "Falta la matrícula del vehículo"
4. Selecciona tipo "Incidencia"
5. Hace clic en "Enviar Comentario"
6. Comentario aparece en lista (recarga cada 5s o via WebSocket)
7. Otro usuario ve notificación en tiempo real
8. Usuario admin hace clic en "✓ Resuelto"
9. Comentario se marca como resuelto
10. Auditoría registra quién y cuándo

### Filtrar Facturas Pendientes

1. En `/facturas` activar filtro "Con comentarios pendientes"
2. Ver solo facturas que tienen comentarios sin resolver
3. Click en una factura va a detalle
4. Resolver comentarios
5. Factura desaparece del filtro

---

## 📝 Tipos de Comentarios

| Tipo | Icono | Uso | Ejemplo |
|------|-------|-----|---------|
| Información | 📋 | Datos/contexto | "Factura duplicada en sistema" |
| Revisión | 👁️ | Revisión de datos | "Revisar importe con proveedor" |
| Incidencia | ⚠️ | Problemas/errores | "Falta la matrícula del vehículo" |
| Aprobación | ✅ | Aprobación | "Revisado por Administración" |
| Rechazo | ❌ | Rechazo | "Rechazado por datos incompletos" |

---

## 🔄 Integración con Sistema Actual

### Modelos Relacionados

- ✅ Comentario → Factura (FK, CASCADE delete)
- ✅ Comentario → Usuario (FK a usuario_id, sin table)
- ✅ ComentarioAuditoria → Comentario (FK, CASCADE delete)

### Repositorio

- `app/repositories/comentarios_repository.py`
  - CRUD completo
  - Búsqueda avanzada
  - Estadísticas

### Service

- `app/services/comentarios_service.py`
  - Lógica de negocio
  - Validaciones
  - Auditoría automática

### Router

- `app/routers/comentarios.py`
  - 15+ endpoints
  - Validación con Pydantic
  - Manejo de errores

---

## 📊 Rendimiento

### Índices

- `ix_comentarios_factura_id` - Búsqueda por factura
- `ix_comentarios_usuario_id` - Búsqueda por usuario
- `ix_comentarios_parent_id` - Búsqueda de respuestas
- `ix_comentarios_estado` - Filtrar pendientes
- `ix_comentarios_tipo` - Filtrar por tipo
- `ix_comentarios_auditoria_*` - Auditoría rápida

### N+1 Problem

SQLAlchemy relationship con lazy loading automático maneja respuestas anidadas eficientemente.

---

## 🎯 Casos de Uso

1. **Revisión de facturas** - Equipo comenta problemas
2. **Auditoría** - Rastrear quién hizo qué y cuándo
3. **Colaboración** - Múltiples usuarios discuten
4. **Resolución** - Marcar como resuelto cuando se solventa
5. **Filtrado** - Mostrar facturas pendientes de revisión

---

## 📝 Notas

- En producción: obtener usuario_id de JWT/sesión
- WebSocket: integración lista con main.js WebSocketManager
- Eliminar comentarios: NO soportado (solo editar, resolver)
- Caché: considerar Redis para estadísticas frecuentes

---

**Estado:** ✅ Completo y listo para producción  
**Versión:** 1.0.0  
**Fecha:** 27 de junio de 2026
