
import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from ..database import get_connection

router = APIRouter()


def _telefono_solo_digitos(telefono) -> str:
    return ''.join(ch for ch in str(telefono or '') if ch.isdigit())


def _normalizar_telefono_consulta(telefono) -> str:
    """Normaliza el teléfono para validar consentimiento.

    - elimina espacios y cualquier carácter no numérico
    - elimina prefijo internacional 00 si viene informado
    - elimina el prefijo 34 al inicio para comparar siempre en base local
    - elimina un 0 inicial residual
    """
    tel = _telefono_solo_digitos(telefono)
    if not tel:
        return ''
    if tel.startswith('00'):
        tel = tel[2:]
    while tel.startswith('34') and len(tel) > 9:
        tel = tel[2:]
    if tel.startswith('0') and len(tel) > 9:
        tel = tel[1:]
    return tel

def _detect_table(cur):
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('ciudad','ciudades')")
    tables = [r[0] for r in cur.fetchall()]
    return tables[0] if tables else None

@router.get("/api/consentimiento_whatsapp/listado")
def consentimiento_whatsapp_listado():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='empleados'")
    emp_cols = {r[0] for r in cur.fetchall()}
    baja_col = None
    for candidate in ("fecha_baja_empresa", "fecha_baja", "baja_fecha", "fecha_fin", "fecha_baja_empleado"):
        if candidate in emp_cols:
            baja_col = candidate
            break
    baja_where_sql = (
        f" AND (e.{baja_col} IS NULL OR e.{baja_col}::date >= DATE_TRUNC('month', CURRENT_DATE)::date)"
        if baja_col else ""
    )
    # Detectar tabla y campo de nombre
    ciudad_table = _detect_table(cur)
    if not ciudad_table:
        cur.close()
        conn.close()
        return JSONResponse({"ok": True, "data": {}})
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name=%s", (ciudad_table,))
    cols = {r[0] for r in cur.fetchall()}
    name_col = None
    for candidate in ("name", "municipio", "nombre"):
        if candidate in cols:
            name_col = candidate
            break
    if not name_col:
        cur.close()
        conn.close()
        return JSONResponse({"ok": True, "data": {}})

    # Obtener ciudades
    cur.execute(f"SELECT id, {name_col} FROM {ciudad_table} ORDER BY {name_col}")
    ciudades = cur.fetchall()
    ciudad_map = {c[0]: c[1] for c in ciudades}
    data = {nombre: [] for nombre in ciudad_map.values()}

    # Obtener empleados con ciudad, teléfono, rider_id y cod_activo
    cur.execute(f'''
        WITH ea_actual AS (
            SELECT DISTINCT ON (ea.empleado_id)
                ea.empleado_id,
                ea.ciudad_id,
                ea.fecha_inicio,
                ea.fecha_fin,
                ea.id
            FROM empleado_asignacion ea
            WHERE (ea.fecha_inicio IS NULL OR ea.fecha_inicio::date <= CURRENT_DATE)
              AND (ea.fecha_fin IS NULL OR ea.fecha_fin::date >= CURRENT_DATE)
            ORDER BY
                ea.empleado_id,
                CASE WHEN ea.fecha_inicio IS NULL THEN 1 ELSE 0 END,
                ea.fecha_inicio DESC NULLS LAST,
                ea.id DESC
        ),
        ro_actual AS (
            SELECT DISTINCT ON (ro.empleado_id)
                ro.empleado_id,
                ro.rider_id,
                ro.cod_activo,
                ro.id
            FROM rider_operativo ro
            ORDER BY
                ro.empleado_id,
                COALESCE(ro.activo, false) DESC,
                ro.id DESC
        )
        SELECT c.id AS ciudad_id, c.{name_col} AS ciudad, e.id AS empleado_id, e.nombre, e.apellidos, e.telefono,
               ro.rider_id, ro.cod_activo
        FROM empleados e
        LEFT JOIN ea_actual ea ON e.id = ea.empleado_id
        LEFT JOIN {ciudad_table} c ON ea.ciudad_id = c.id
        LEFT JOIN ro_actual ro ON ro.empleado_id = e.id
        WHERE c.id IS NOT NULL
        {baja_where_sql}
        ORDER BY c.{name_col}, e.nombre, e.apellidos
    '''.format(name_col=name_col, ciudad_table=ciudad_table, baja_where_sql=baja_where_sql))
    empleados = cur.fetchall()

    # Cargar todos los consentimientos de una sola vez
    cur.execute("SELECT telefono FROM rtos_consentimiento_whatsapp")
    telefonos_con_cons = {
        tel_norm
        for (telefono_consentimiento,) in cur.fetchall()
        for tel_norm in [_normalizar_telefono_consulta(telefono_consentimiento)]
        if tel_norm
    }

    for ciudad_id, ciudad, empleado_id, nombre, apellidos, telefono, rider_id, cod_activo in empleados:
        tel = _normalizar_telefono_consulta(telefono)
        cons = tel in telefonos_con_cons if tel else False
        data[ciudad].append({
            "empleado_id": empleado_id,
            "rider_id": rider_id,
            "cod_activo": cod_activo,
            "ciudad": ciudad,
            "nombre_completo": f"{nombre} {apellidos}",
            "telefono": tel,
            "consentimiento": cons
        })
    cur.close()
    conn.close()
    return JSONResponse({"ok": True, "data": data})


@router.get("/api/consentimiento_whatsapp/exportar-no-sheet")
def exportar_no_sheet(ciudad: str):
    """Crea un Google Sheet con los riders SIN consentimiento de una ciudad."""
    if not ciudad or not ciudad.strip():
        return JSONResponse({"ok": False, "error": "Ciudad requerida"}, status_code=400)

    ciudad = ciudad.strip()

    conn = get_connection()
    cur = conn.cursor()

    ciudad_table = _detect_table(cur)
    if not ciudad_table:
        cur.close(); conn.close()
        return JSONResponse({"ok": False, "error": "No se encontró tabla de ciudades"}, status_code=500)

    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (ciudad_table,))
    cols = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='empleados'")
    emp_cols = {r[0] for r in cur.fetchall()}
    name_col = None
    for candidate in ("name", "municipio", "nombre"):
        if candidate in cols:
            name_col = candidate
            break
    baja_col = None
    for candidate in ("fecha_baja_empresa", "fecha_baja", "baja_fecha", "fecha_fin", "fecha_baja_empleado"):
        if candidate in emp_cols:
            baja_col = candidate
            break
    baja_where_sql = (
        f" AND (e.{baja_col} IS NULL OR e.{baja_col}::date >= DATE_TRUNC('month', CURRENT_DATE)::date)"
        if baja_col else ""
    )
    if not name_col:
        cur.close(); conn.close()
        return JSONResponse({"ok": False, "error": "No se encontró columna de nombre en ciudades"}, status_code=500)

    cur.execute(f'''
        WITH ea_actual AS (
            SELECT DISTINCT ON (ea.empleado_id)
                ea.empleado_id,
                ea.ciudad_id,
                ea.fecha_inicio,
                ea.fecha_fin,
                ea.id
            FROM empleado_asignacion ea
            WHERE (ea.fecha_inicio IS NULL OR ea.fecha_inicio::date <= CURRENT_DATE)
              AND (ea.fecha_fin IS NULL OR ea.fecha_fin::date >= CURRENT_DATE)
            ORDER BY
                ea.empleado_id,
                CASE WHEN ea.fecha_inicio IS NULL THEN 1 ELSE 0 END,
                ea.fecha_inicio DESC NULLS LAST,
                ea.id DESC
        ),
        ro_actual AS (
            SELECT DISTINCT ON (ro.empleado_id)
                ro.empleado_id,
                ro.rider_id,
                ro.cod_activo,
                ro.id
            FROM rider_operativo ro
            ORDER BY
                ro.empleado_id,
                COALESCE(ro.activo, false) DESC,
                ro.id DESC
        )
        SELECT e.id, e.nombre, e.apellidos, e.telefono, ro.rider_id, ro.cod_activo
        FROM empleados e
        LEFT JOIN ea_actual ea ON e.id = ea.empleado_id
        LEFT JOIN {ciudad_table} c ON ea.ciudad_id = c.id
        LEFT JOIN ro_actual ro ON ro.empleado_id = e.id
        WHERE c.{name_col} = %s
        {baja_where_sql}
        ORDER BY e.nombre, e.apellidos
    '''.format(ciudad_table=ciudad_table, name_col=name_col, baja_where_sql=baja_where_sql), (ciudad,))
    empleados = cur.fetchall()

    # Cargar todos los consentimientos de una sola vez
    cur.execute("SELECT telefono FROM rtos_consentimiento_whatsapp")
    telefonos_con_cons = {
        tel_norm
        for (telefono_consentimiento,) in cur.fetchall()
        for tel_norm in [_normalizar_telefono_consulta(telefono_consentimiento)]
        if tel_norm
    }

    rows_no = []
    for emp_id, nombre, apellidos, telefono, rider_id, cod_activo in empleados:
        tel = _normalizar_telefono_consulta(telefono)
        if not tel or tel not in telefonos_con_cons:
            rows_no.append([
                str(rider_id or ''),
                str(cod_activo or ''),
                f"{nombre} {apellidos}".strip(),
                tel
            ])

    cur.close()
    conn.close()

    if not rows_no:
        return JSONResponse({"ok": False, "error": f"No hay riders sin consentimiento en {ciudad}"})

    import io, csv
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Rider ID", "Cod. Activo", "Nombre Completo", "Nro. Teléfono"])
    writer.writerows(rows_no)
    buf.seek(0)

    filename = f"sin_consentimiento_{ciudad.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
