# 📚 Documentación del Modelo de Datos QNLA

Documentación completa del modelo de datos de la **Quiniela de Torneos** (Mundial 2026 y posteriores).

---

## 🎯 Visión general

Sistema de quinielas de fútbol con las siguientes características:

| Característica | Decisión |
|---|---|
| **Motor de BD** | PostgreSQL |
| **Esquema** | `public` |
| **Prefijo de tablas** | `qnla_` |
| **Multi-torneo** | Sí, soporta varias ediciones simultáneas |
| **Tipo de pronóstico** | Marcador exacto (goles local/visitante) |
| **Sistema de puntos** | 3 / 1 / 0 (configurable por torneo) |
| **Eliminatorias** | Solo cuentan los 90 minutos (sin prórroga ni penales) |
| **Identidad de usuario** | FK a `public.empleados.id` |
| **Login** | Vía `public.usuarios_login.dni_nie` |

---

## 🗺️ Diagrama de relaciones

```
┌─────────────────┐
│  empleados      │  (preexistente)
│  (público)      │
└────────┬────────┘
         │
         │ login vía
         ▼
┌─────────────────┐
│ usuarios_login  │  (preexistente)
│  (público)      │
└────────┬────────┘
         │ empleado_id (FK)
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│                       MODELO QNLA                            │
│                                                              │
│   ┌──────────────────┐                                       │
│   │  qnla_torneos    │◄──── raíz: una fila por torneo        │
│   └────────┬─────────┘                                       │
│            │ 1:N (CASCADE)                                   │
│            ├──────► qnla_reglas_puntaje  (1:1)               │
│            ├──────► qnla_fases           (7 por torneo)      │
│            ├──────► qnla_grupos          (12 por torneo)     │
│            ├──────► qnla_sedes           (16 por torneo)     │
│            ├──────► qnla_selecciones     (48 por torneo)─┐   │
│            ├──────► qnla_participantes   (N empleados)   │   │
│            └──────► qnla_partidos ◄──────────────────────┤   │
│                          │                               │   │
│                          │ FK local/visitante ───────────┘   │
│                          │                                   │
│                          │ 1:N                               │
│                          ▼                                   │
│                    qnla_pronosticos                          │
│                          ▲                                   │
│                          │ FK participante                   │
│                    qnla_participantes                        │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ qnla_v_ranking │  (vista de tabla de posiciones)
                  └────────────────┘
```

---

## 📋 Catálogo de tablas

### 1. `qnla_torneos` — Raíz del sistema

Cada fila es un torneo (Mundial 2026, Eurocopa 2028, etc.).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | Identificador único |
| `nombre` | `VARCHAR(100)` | Nombre del torneo (único de facto) |
| `descripcion` | `TEXT` | Descripción libre |
| `anio` | `INTEGER` | Año del torneo |
| `fecha_inicio` | `DATE` | Fecha del primer partido |
| `fecha_fin` | `DATE` | Fecha de la final |
| `activo` | `BOOLEAN` | Si está visible para usuarios |
| `cierre_inscripcion` | `TIMESTAMP` | Fecha límite para inscribirse |
| `created_at` | `TIMESTAMP` | Fecha de creación del registro |

**Constraints:** `fecha_fin >= fecha_inicio`.

---

### 2. `qnla_reglas_puntaje` — Configuración de puntos por torneo

Relación 1:1 con torneo (UNIQUE en `torneo_id`).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK UNIQUE` | → `qnla_torneos.id` (CASCADE) |
| `puntos_exacto` | `SMALLINT` | Puntos por acertar el marcador exacto (default `3`) |
| `puntos_ganador` | `SMALLINT` | Puntos por acertar solo el ganador/empate (default `1`) |
| `puntos_fallo` | `SMALLINT` | Puntos cuando se falla (default `0`) |
| `created_at` | `TIMESTAMP` | |

**Por qué existe:** permite cambiar el sistema de puntos entre torneos sin tocar código.

---

### 3. `qnla_fases` — Etapas del torneo

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK` | → `qnla_torneos.id` (CASCADE) |
| `nombre` | `VARCHAR(50)` | "Fase de Grupos", "Octavos", "Final"... |
| `orden` | `SMALLINT` | 1, 2, 3... para ordenar cronológicamente |
| `es_eliminatoria` | `BOOLEAN` | TRUE para todo lo que no sea fase de grupos |

**Constraint:** `UNIQUE (torneo_id, nombre)`.

**Mundial 2026 → 7 fases:** Fase de Grupos · 32avos · Octavos · Cuartos · Semis · 3er Puesto · Final.

---

### 4. `qnla_grupos` — Grupos de la fase inicial

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK` | → `qnla_torneos.id` (CASCADE) |
| `nombre` | `VARCHAR(5)` | "A", "B", ..., "L" |

**Constraint:** `UNIQUE (torneo_id, nombre)`.

**Mundial 2026 → 12 grupos** (A a L).

---

### 5. `qnla_selecciones` — Equipos participantes

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK` | → `qnla_torneos.id` (CASCADE) |
| `nombre` | `VARCHAR(100)` | "España", "Brasil"... |
| `codigo_fifa` | `VARCHAR(3)` | Código ISO/FIFA: "ESP", "BRA"... |
| `bandera_url` | `TEXT` | URL del icono de la bandera (opcional) |
| `grupo_id` | `INTEGER FK NULL` | → `qnla_grupos.id` (SET NULL si se borra el grupo) |

**Constraint:** `UNIQUE (torneo_id, nombre)`.

**Mundial 2026 → 48 selecciones** ya cargadas con su grupo asignado.

---

### 6. `qnla_sedes` — Estadios

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK` | → `qnla_torneos.id` (CASCADE) |
| `nombre` | `VARCHAR(150)` | "Estadio Azteca", "MetLife Stadium"... |
| `ciudad` | `VARCHAR(100)` | |
| `pais` | `VARCHAR(100)` | "México", "USA", "Canadá" |
| `capacidad` | `INTEGER` | Aforo |

**Mundial 2026 → 16 sedes** (3 México + 2 Canadá + 11 USA).

---

### 7. `qnla_partidos` — Fixture y resultados

Tabla central. Contiene tanto el **calendario** como el **resultado real** (cuando se juega).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK` | → `qnla_torneos.id` |
| `fase_id` | `INTEGER FK` | → `qnla_fases.id` |
| `grupo_id` | `INTEGER FK NULL` | → `qnla_grupos.id` (NULL en eliminatorias) |
| `sede_id` | `INTEGER FK` | → `qnla_sedes.id` |
| `seleccion_local_id` | `INTEGER FK` | → `qnla_selecciones.id` |
| `seleccion_visitante_id` | `INTEGER FK` | → `qnla_selecciones.id` |
| `fecha_partido` | `TIMESTAMP` | Kickoff |
| `cierre_pronostico` | `TIMESTAMP` | Hasta cuándo se admiten pronósticos |
| `goles_local` | `SMALLINT NULL` | **Resultado real** (NULL hasta que se juegue) |
| `goles_visitante` | `SMALLINT NULL` | **Resultado real** (NULL hasta que se juegue) |
| `finalizado` | `BOOLEAN` | TRUE cuando el resultado es definitivo |
| `created_at` / `updated_at` | `TIMESTAMP` | |

**Constraints:**
- Los dos equipos deben ser distintos
- `goles_local` y `goles_visitante` deben ser ambos NULL o ambos ≥ 0
- Índice en `(torneo_id, fecha_partido)` para consultas cronológicas

**Mundial 2026 → 72 partidos** de fase de grupos cargados (32 eliminatorios pendientes).

---

### 8. `qnla_participantes` — Empleados inscritos en cada torneo

Tabla puente entre `empleados` y un torneo concreto. Un empleado puede participar en varios torneos.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `torneo_id` | `INTEGER FK` | → `qnla_torneos.id` (CASCADE) |
| `empleado_id` | `INTEGER FK` | → `public.empleados.id` (**RESTRICT**) |
| `alias` | `VARCHAR(50)` | Nick opcional para mostrar en ranking |
| `fecha_inscripcion` | `TIMESTAMP` | |
| `activo` | `BOOLEAN` | Permite "desactivar" sin borrar histórico |

**Constraint:** `UNIQUE (torneo_id, empleado_id)` → un empleado solo se inscribe una vez por torneo.

**Importante:** el `ON DELETE RESTRICT` sobre `empleado_id` impide borrar un empleado que tenga historial de quinielas.

---

### 9. `qnla_pronosticos` — Las apuestas de los usuarios

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `SERIAL PK` | |
| `participante_id` | `INTEGER FK` | → `qnla_participantes.id` (CASCADE) |
| `partido_id` | `INTEGER FK` | → `qnla_partidos.id` (CASCADE) |
| `goles_local` | `SMALLINT` | Pronóstico del usuario |
| `goles_visitante` | `SMALLINT` | Pronóstico del usuario |
| `puntos_obtenidos` | `SMALLINT NULL` | Calculados tras finalizar el partido |
| `calculado_en` | `TIMESTAMP NULL` | Cuándo se calcularon los puntos |
| `created_at` / `updated_at` | `TIMESTAMP` | |

**Constraints:**
- `UNIQUE (participante_id, partido_id)` → un solo pronóstico por partido y usuario
- `goles_local >= 0 AND goles_visitante >= 0`
- Índice en `partido_id` para acelerar el cálculo masivo

**Flujo:** el usuario crea/actualiza el pronóstico **hasta `cierre_pronostico`**. Después, cuando se ingresa el resultado real, se ejecuta la función de cálculo y se rellena `puntos_obtenidos`.

---

## ⚙️ Función `qnla_calcular_puntos_partido`

```sql
SELECT public.qnla_calcular_puntos_partido(123);
```

**Qué hace** (en orden):

1. Lee el partido `123`.
2. Valida que esté `finalizado = TRUE` y tenga goles. Si no → `RAISE EXCEPTION`.
3. Lee las reglas de puntaje del torneo (`puntos_exacto`, `puntos_ganador`, `puntos_fallo`).
4. Por cada pronóstico de ese partido:
   - Si `goles_local` y `goles_visitante` coinciden con el resultado real → asigna **`puntos_exacto`** (3 pts)
   - Si solo coincide el signo de `(local - visitante)` → asigna **`puntos_ganador`** (1 pt)
   - En cualquier otro caso → asigna **`puntos_fallo`** (0 pts)
5. Marca `calculado_en = NOW()`.
6. Devuelve el número de pronósticos actualizados.

**Truco matemático:** `SIGN(goles_local - goles_visitante)` da `+1` (gana local), `0` (empate) o `-1` (gana visitante). Si el signo del pronóstico coincide con el del resultado → acertó al ganador/empate.

---

## 📊 Vista `qnla_v_ranking` — Tabla de posiciones

Tabla derivada (no almacena datos) que calcula la clasificación al vuelo:

| Columna | Descripción |
|---|---|
| `torneo_id` | Torneo |
| `participante_id` | |
| `empleado_id` | |
| `nombre_completo` | `nombre + apellidos` del empleado |
| `alias` | Si tiene; si no, el nombre |
| `pronosticos_realizados` | Total de pronósticos hechos |
| `aciertos_exactos` | Cuántos marcadores exactos clavó |
| `aciertos_ganador` | Cuántas veces acertó solo el ganador/empate |
| `puntos_totales` | Suma total de puntos |

Ordenada por `puntos_totales DESC, aciertos_exactos DESC`.

**Uso típico:**
```sql
SELECT * FROM qnla_v_ranking WHERE torneo_id = 1 LIMIT 20;
```

---

## 🔄 Flujo de uso completo (extremo a extremo)

```
1. ADMIN crea torneo
   └─► INSERT en qnla_torneos, qnla_reglas_puntaje, qnla_fases, qnla_grupos,
       qnla_sedes, qnla_selecciones, qnla_partidos

2. EMPLEADO se loguea (vía usuarios_login.dni_nie)
   └─► Obtiene su empleado_id

3. EMPLEADO se inscribe al torneo
   └─► INSERT en qnla_participantes (torneo_id, empleado_id)

4. EMPLEADO pronostica partidos
   └─► INSERT/UPDATE en qnla_pronosticos (mientras NOW() < cierre_pronostico)

5. Se juega el partido → ADMIN ingresa resultado
   └─► UPDATE qnla_partidos SET goles_local, goles_visitante, finalizado=TRUE
   └─► SELECT qnla_calcular_puntos_partido(partido_id)
       → Actualiza puntos_obtenidos en todos los pronósticos

6. EMPLEADOS consultan ranking
   └─► SELECT * FROM qnla_v_ranking WHERE torneo_id = X
```

---

## 📦 Estado actual del Mundial 2026

| Tabla | Filas cargadas |
|---|---|
| `qnla_torneos` | 1 (Mundial FIFA 2026) |
| `qnla_reglas_puntaje` | 1 (3/1/0) |
| `qnla_fases` | 7 |
| `qnla_grupos` | 12 (A–L) |
| `qnla_sedes` | 16 |
| `qnla_selecciones` | 48 (con grupo asignado) |
| `qnla_partidos` | 72 (solo fase de grupos) |
| `qnla_participantes` | 0 (se llena con la app) |
| `qnla_pronosticos` | 0 (se llena con la app) |

**Pendiente:** 32 partidos de fase eliminatoria (dependen de los resultados de la fase de grupos o de placeholders tipo "1º Grupo A vs 2º Grupo F").

---

## 🛡️ Decisiones de diseño clave (y por qué)

| Decisión | Razón |
|---|---|
| Multi-torneo desde el inicio | El repo se llama "torneos" (plural). Evita refactor futuro. |
| Reglas de puntaje por torneo (no globales) | Permite cambiar el sistema sin migración de código. |
| Resultado dentro de `qnla_partidos` (no tabla aparte) | Es 1:1; separarlo sería sobreingeniería. |
| `puntos_obtenidos` pre-calculado en `qnla_pronosticos` | Ranking ultra-rápido sin recalcular cada vez. |
| `qnla_participantes` como tabla puente | Desacopla "empleado" de "jugador de quiniela" → historial limpio. |
| `cierre_pronostico` en cada partido | Validación de negocio en BD (defensa en profundidad). |
| `ON DELETE CASCADE` desde torneos | Borrar un torneo limpia todo su contexto automáticamente. |
| `ON DELETE RESTRICT` en `empleado_id` | Protege la integridad del historial frente a borrados accidentales. |
| Solo 90 min en eliminatorias | Decisión funcional: simplifica el cálculo, no hay columnas extra. |

---

## 🚧 Pendientes / mejoras futuras

- **Partidos de eliminatoria** (32 partidos) — requieren decidir si se usan placeholders o se cargan post-fase-de-grupos.
- **Trigger automático** que invoque `qnla_calcular_puntos_partido()` cuando `finalizado` cambie a `TRUE`.
- **Auditoría** de cambios en pronósticos (tabla `qnla_pronosticos_historico`) — útil ante disputas.
- **Pronósticos "extra"** (campeón, máximo goleador, jugador del torneo) — requeriría nueva tabla.
- **Tabla de roles/permisos** para distinguir admin de usuario regular.
