from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import get_connection

router = APIRouter()

@router.get("/api/consulta_consentimiento/listado")
def consulta_consentimiento_listado():
    conn = None
    cur = None
    try:
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
        # Obtener todas las ciudades
        # Usar la misma lógica que empleado_por_ciudad para obtener todas las ciudades
        cur.execute('SELECT id, name FROM ciudad ORDER BY name')
        ciudades = cur.fetchall()
        if not ciudades:
            return JSONResponse({"ok": False, "error": "No hay ciudades en la base de datos"})
        ciudad_map = {c[0]: c[1] for c in ciudades}
        data = {nombre: [] for nombre in ciudad_map.values()}

        # Obtener todos los empleados con su ciudad y teléfono
        cur.execute('''
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
                SELECT DISTINCT ON (r.empleado_id)
                    r.empleado_id,
                    r.rider_id,
                    r.cod_activo,
                    r.id
                FROM rider_operativo r
                ORDER BY
                    r.empleado_id,
                    COALESCE(r.activo, false) DESC,
                    r.id DESC
            )
            SELECT 
                c.id AS ciudad_id,
                c.name AS ciudad,
                r.rider_id,
                r.cod_activo,
                CONCAT(e.nombre, ' ', e.apellidos) AS nombre_completo,
                e.telefono,
                e.id AS empleado_id
            FROM empleados e
            LEFT JOIN ea_actual ea ON e.id = ea.empleado_id
            LEFT JOIN ciudad c ON ea.ciudad_id = c.id
            LEFT JOIN ro_actual r ON e.id = r.empleado_id
            WHERE c.id IS NOT NULL
            {baja_where_sql}
            GROUP BY c.id, c.name, r.rider_id, r.cod_activo, e.nombre, e.apellidos, e.telefono, e.id
            ORDER BY c.name, nombre_completo
            LIMIT 2000;
        '''.format(baja_where_sql=baja_where_sql))
        empleados = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Buscar consentimiento por teléfono
        telefonos = [row[columns.index('telefono')] for row in empleados if row[columns.index('telefono')]]
        consentimiento_map = {}
        if telefonos:
            format_strings = ','.join(['%s'] * len(telefonos))
            cur.execute(f'''
                SELECT telefono, consentimiento
                FROM rtos_consentimiento_whatsapp
                WHERE telefono IN ({format_strings})
                AND id IN (
                    SELECT MAX(id) FROM rtos_consentimiento_whatsapp WHERE telefono IN ({format_strings}) GROUP BY telefono
                )
            ''', telefonos + telefonos)
            for tel, consentimiento in cur.fetchall():
                consentimiento_map[tel] = consentimiento

        for row in empleados:
            item = dict(zip(columns, row))
            tel = item.get('telefono')
            item['consentimiento'] = consentimiento_map.get(tel, False)
            ciudad = item.pop("ciudad")
            if ciudad in data:
                data[ciudad].append(item)

        cur.close()
        conn.close()
        return JSONResponse({"ok": True, "data": data})
    except Exception as e:
        data = {"Sin datos": []}
        return JSONResponse({"ok": True, "data": data, "error": str(e)})
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
