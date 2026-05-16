from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict
import json
import time
import datetime
import urllib.request

from ..database import get_connection

router = APIRouter(prefix="/api/ciudades")

_SPAIN_MUNICIPIOS_URL = "https://raw.githubusercontent.com/geoinnova/municipiosJson/master/municipios.json"
_GEO_CACHE: Dict[str, Any] = {"loaded_at": 0, "catalog": None}
_GEO_CACHE_TTL_SECONDS = 24 * 60 * 60

_COMMUNITY_BY_PROVINCE_CODE = {
    1: "País Vasco",
    2: "Castilla-La Mancha",
    3: "Comunidad Valenciana",
    4: "Andalucía",
    5: "Castilla y León",
    6: "Extremadura",
    7: "Illes Balears",
    8: "Cataluña",
    9: "Castilla y León",
    10: "Extremadura",
    11: "Andalucía",
    12: "Comunidad Valenciana",
    13: "Castilla-La Mancha",
    14: "Andalucía",
    15: "Galicia",
    16: "Castilla-La Mancha",
    17: "Cataluña",
    18: "Andalucía",
    19: "Castilla-La Mancha",
    20: "País Vasco",
    21: "Andalucía",
    22: "Aragón",
    23: "Andalucía",
    24: "Castilla y León",
    25: "Cataluña",
    26: "La Rioja",
    27: "Galicia",
    28: "Comunidad de Madrid",
    29: "Andalucía",
    30: "Región de Murcia",
    31: "Comunidad Foral de Navarra",
    32: "Galicia",
    33: "Principado de Asturias",
    34: "Castilla y León",
    35: "Canarias",
    36: "Galicia",
    37: "Castilla y León",
    38: "Canarias",
    39: "Cantabria",
    40: "Castilla y León",
    41: "Andalucía",
    42: "Castilla y León",
    43: "Cataluña",
    44: "Aragón",
    45: "Castilla-La Mancha",
    46: "Comunidad Valenciana",
    47: "Castilla y León",
    48: "País Vasco",
    49: "Castilla y León",
    50: "Aragón",
    51: "Ceuta",
    52: "Melilla",
}

_COMMUNITY_ORDER = [
    "Andalucía",
    "Aragón",
    "Principado de Asturias",
    "Illes Balears",
    "Canarias",
    "Cantabria",
    "Castilla-La Mancha",
    "Castilla y León",
    "Cataluña",
    "Ceuta",
    "Comunidad de Madrid",
    "Comunidad Foral de Navarra",
    "Comunidad Valenciana",
    "Extremadura",
    "Galicia",
    "La Rioja",
    "Melilla",
    "País Vasco",
    "Región de Murcia",
]

_PROVINCE_DISPLAY_BY_CODE = {
    1: "Álava",
    2: "Albacete",
    3: "Alicante",
    4: "Almería",
    5: "Ávila",
    6: "Badajoz",
    7: "Illes Balears",
    8: "Barcelona",
    9: "Burgos",
    10: "Cáceres",
    11: "Cádiz",
    12: "Castellón",
    13: "Ciudad Real",
    14: "Córdoba",
    15: "A Coruña",
    16: "Cuenca",
    17: "Girona",
    18: "Granada",
    19: "Guadalajara",
    20: "Gipuzkoa",
    21: "Huelva",
    22: "Huesca",
    23: "Jaén",
    24: "León",
    25: "Lleida",
    26: "La Rioja",
    27: "Lugo",
    28: "Madrid",
    29: "Málaga",
    30: "Murcia",
    31: "Navarra",
    32: "Ourense",
    33: "Asturias",
    34: "Palencia",
    35: "Las Palmas",
    36: "Pontevedra",
    37: "Salamanca",
    38: "Santa Cruz de Tenerife",
    39: "Cantabria",
    40: "Segovia",
    41: "Sevilla",
    42: "Soria",
    43: "Tarragona",
    44: "Teruel",
    45: "Toledo",
    46: "Valencia",
    47: "Valladolid",
    48: "Bizkaia",
    49: "Zamora",
    50: "Zaragoza",
    51: "Ceuta",
    52: "Melilla",
}


def _load_geo_catalog() -> Dict[str, Any]:
    now = time.time()
    if _GEO_CACHE["catalog"] and now - _GEO_CACHE["loaded_at"] < _GEO_CACHE_TTL_SECONDS:
        return _GEO_CACHE["catalog"]

    req = urllib.request.Request(_SPAIN_MUNICIPIOS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw_data = json.load(response)

    provinces_by_community: Dict[str, Dict[int, Dict[str, Any]]] = {}
    municipalities_by_province: Dict[str, list[str]] = {}
    seen_municipalities: Dict[str, set[str]] = {}

    for item in raw_data:
        province_code = int(item.get("COD_PROV"))
        community_name = _COMMUNITY_BY_PROVINCE_CODE.get(province_code)
        if not community_name:
            continue

        province_name = _PROVINCE_DISPLAY_BY_CODE.get(province_code) or str(item.get("PROVINCIA") or "").strip()
        municipality_name = str(item.get("NOMBRE_ACTUAL") or "").strip()
        if not municipality_name:
            continue

        provinces_by_community.setdefault(community_name, {})
        provinces_by_community[community_name].setdefault(
            province_code,
            {"code": province_code, "name": province_name}
        )

        province_key = str(province_code)
        municipalities_by_province.setdefault(province_key, [])
        seen_municipalities.setdefault(province_key, set())
        if municipality_name not in seen_municipalities[province_key]:
            seen_municipalities[province_key].add(municipality_name)
            municipalities_by_province[province_key].append(municipality_name)

    comunidades = []
    for community_name in _COMMUNITY_ORDER:
        if community_name in provinces_by_community:
            comunidades.append({"name": community_name})

    provincias = {
        community_name: sorted(provinces.values(), key=lambda p: p["name"])
        for community_name, provinces in provinces_by_community.items()
    }
    municipios = {
        province_key: sorted(values)
        for province_key, values in municipalities_by_province.items()
    }

    catalog = {
        "comunidades": comunidades,
        "provincias": provincias,
        "municipios": municipios,
    }
    _GEO_CACHE["loaded_at"] = now
    _GEO_CACHE["catalog"] = catalog
    return catalog


def _detect_table(cur) -> str:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('ciudad','ciudades')")
    tables = [r[0] for r in cur.fetchall()]
    return tables[0] if tables else None


def _row_to_dict(cur, row) -> Dict[str, Any]:
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return {cols[i]: row[i] for i in range(len(cols))}



@router.get("/consulta")
def consulta_ciudades(ciudad_id: int = None, mes_id: int = None):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Detectar posible columna de baja en empleados
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='empleados'")
        emp_cols = {r[0] for r in cur.fetchall()}
        baja_col = None
        for candidate in ("fecha_baja_empresa", "fecha_baja", "baja_fecha", "fecha_fin", "fecha_baja_empleado"):
            if candidate in emp_cols:
                baja_col = candidate
                break

        mes_ref_start = None

        baja_select_sql = "NULL::date AS fecha_baja, false AS baja_mes_consulta"
        baja_where_sql = ""
        params_baja = []

        if baja_col:
            if mes_ref_start is not None:
                baja_select_sql = (
                    f"e.{baja_col}::date AS fecha_baja, "
                    f"(e.{baja_col} IS NOT NULL AND DATE_TRUNC('month', e.{baja_col}::date) = DATE_TRUNC('month', %s::date)) AS baja_mes_consulta"
                )
                params_baja.append(mes_ref_start)
                # Excluir bajas anteriores al mes consultado
                baja_where_sql = f" AND (e.{baja_col} IS NULL OR e.{baja_col}::date >= %s::date)"
                params_baja.append(mes_ref_start)
            else:
                baja_select_sql = f"e.{baja_col}::date AS fecha_baja, false AS baja_mes_consulta"

        ea_city_where = ""
        params_ea = []
        if ciudad_id:
            ea_city_where = " AND ea.ciudad_id = %s"
            params_ea.append(ciudad_id)

        query = """
            WITH ea_actual AS (
                SELECT DISTINCT ON (ea.empleado_id)
                    ea.empleado_id,
                    ea.ciudad_id,
                    ea.id,
                    ea.fecha_inicio,
                    ea.fecha_fin
                FROM empleado_asignacion ea
                WHERE (ea.fecha_inicio IS NULL OR ea.fecha_inicio::date <= CURRENT_DATE)
                  AND (ea.fecha_fin IS NULL OR ea.fecha_fin::date >= CURRENT_DATE)
                  {ea_city_where}
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
                JOIN ea_actual ea ON ea.empleado_id = r.empleado_id
                ORDER BY r.empleado_id, COALESCE(r.activo, false) DESC, r.id DESC
            )
            SELECT
                e.id AS empleado_id,
                CONCAT(e.nombre, ' ', e.apellidos) AS nombre_completo,
                e.id_rrhh,
                ro.rider_id AS rider,
                ro.cod_activo,
                e.telefono,
                c.name AS ciudad,
                {baja_select_sql}
            FROM ea_actual ea
            JOIN empleados e ON e.id = ea.empleado_id
            JOIN ciudad c ON c.id = ea.ciudad_id
            LEFT JOIN ro_actual ro ON ro.empleado_id = e.id
            WHERE c.id IS NOT NULL
            {baja_where_sql}
        """.format(
            baja_select_sql=baja_select_sql,
            baja_where_sql=baja_where_sql,
            ea_city_where=ea_city_where,
        )

        query += " ORDER BY nombre_completo LIMIT 2000"

        params = params_ea + params_baja
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        columns = [desc[0] for desc in cur.description]
        data = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return JSONResponse(data)

    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get("/listado")
def listado_ciudades(q: str = None, limit: int = 500):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        ciudad_table = _detect_table(cur)
        if not ciudad_table:
            return JSONResponse([])

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (ciudad_table,))
        cols = [r[0] for r in cur.fetchall()]
        if not cols:
            return JSONResponse([])

        selected_cols = []
        for name in (
            "id",
            "name",
            "municipio",
            "provincia",
            "comunidad_autonoma",
            "pais",
            "time_zone",
            "abreviatura",
            "codigo_postal",
            "prefijo_telefono",
            "id_op",
            "id_rrhh",
        ):
            if name in cols:
                selected_cols.append(name)

        if not selected_cols:
            selected_cols = cols[:8]

        where_clauses = []
        params = []
        if q:
            q_like = f"%{q}%"
            for field in ("name", "municipio", "provincia", "comunidad_autonoma", "pais", "abreviatura"):
                if field in cols:
                    where_clauses.append(f"{field}::text ILIKE %s")
                    params.append(q_like)

        sql = f"SELECT {', '.join(selected_cols)} FROM {ciudad_table}"
        if where_clauses:
            sql += " WHERE (" + " OR ".join(where_clauses) + ")"

        safe_limit = 500
        try:
            safe_limit = max(1, min(int(limit), 2000))
        except Exception:
            safe_limit = 500

        order_field = "id" if "id" in selected_cols else selected_cols[0]
        sql += f" ORDER BY {order_field} DESC LIMIT %s"
        params.append(safe_limit)

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        # Map id_op / id_rrhh to usuario_admin.nombre when possible
        admin_name_by_id = {}
        if rows and ('id_op' in selected_cols or 'id_rrhh' in selected_cols):
            try:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='usuario_admin'")
                if cur.fetchone():
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='usuario_admin'")
                    ua_cols = {r[0] for r in cur.fetchall()}
                    if 'id' in ua_cols and 'nombre' in ua_cols:
                        id_positions = {}
                        if 'id_op' in selected_cols:
                            id_positions['id_op'] = selected_cols.index('id_op')
                        if 'id_rrhh' in selected_cols:
                            id_positions['id_rrhh'] = selected_cols.index('id_rrhh')

                        admin_ids = set()
                        for row in rows:
                            for _, pos in id_positions.items():
                                val = row[pos]
                                if val is not None:
                                    admin_ids.add(val)

                        if admin_ids:
                            placeholders = ','.join(['%s'] * len(admin_ids))
                            cur.execute(f"SELECT id, nombre FROM usuario_admin WHERE id IN ({placeholders})", tuple(admin_ids))
                            admin_name_by_id = {r[0]: r[1] for r in cur.fetchall()}
            except Exception:
                admin_name_by_id = {}

        payload = []
        for row in rows:
            item = {selected_cols[i]: row[i] for i in range(len(selected_cols))}
            if 'id_op' in item and item.get('id_op') in admin_name_by_id:
                item['id_op'] = admin_name_by_id[item.get('id_op')]
            if 'id_rrhh' in item and item.get('id_rrhh') in admin_name_by_id:
                item['id_rrhh'] = admin_name_by_id[item.get('id_rrhh')]
            payload.append(item)

        return JSONResponse(payload)
    except Exception as e:
        print('listado_ciudades error:', e)
        return JSONResponse([])
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/consulta/pestanas")
def consulta_ciudades_pestanas():
    conn = None
    cur = None
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            return JSONResponse([])

        # Buscar columna de nombre
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        cols = {r[0] for r in cur.fetchall()}
        name_col = None
        for candidate in ("name", "municipio", "nombre"):
            if candidate in cols:
                name_col = candidate
                break
        if not name_col:
            return JSONResponse([])

        # Devolver todas las ciudades con id y nombre_ciudad (clave esperada por el frontend)
        cur.execute(f"SELECT id, {name_col} FROM {table} ORDER BY {name_col}")
        rows = cur.fetchall()
        data = [
            {"id": row[0], "nombre_ciudad": row[1]} for row in rows
        ]
        return JSONResponse(data)
    except Exception as e:
        print('consulta_ciudades_pestanas error:', e)
        return JSONResponse([])
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/geo/provincias")
def geo_provincias(comunidad: str):
    try:
        catalog = _load_geo_catalog()
        return JSONResponse(catalog["provincias"].get(comunidad, []))
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "GEO_ERROR", "error": "Error al cargar provincias", "detalle": str(e)})


@router.get("/geo/municipios")
def geo_municipios(provincia_codigo: int):
    try:
        catalog = _load_geo_catalog()
        return JSONResponse(catalog["municipios"].get(str(provincia_codigo), []))
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "GEO_ERROR", "error": "Error al cargar municipios", "detalle": str(e)})


@router.get("/geo/codigo-postal")
def geo_codigo_postal(provincia: str, municipio: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            cur.close()
            conn.close()
            return JSONResponse({"codigo_postal": None})

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        cols = {r[0] for r in cur.fetchall()}

        municipio_col = None
        for candidate in ("municipio", "name", "nombre"):
            if candidate in cols:
                municipio_col = candidate
                break

        provincia_col = "provincia" if "provincia" in cols else None

        codigo_postal_col = None
        for candidate in ("codigo_postal", "cp", "postal_code"):
            if candidate in cols:
                codigo_postal_col = candidate
                break

        if not municipio_col or not provincia_col or not codigo_postal_col:
            cur.close()
            conn.close()
            return JSONResponse({"codigo_postal": None})

        sql = f"""
            SELECT {codigo_postal_col}
            FROM {table}
            WHERE {municipio_col} ILIKE %s
              AND {provincia_col} ILIKE %s
              AND {codigo_postal_col} IS NOT NULL
              AND TRIM(CAST({codigo_postal_col} AS TEXT)) <> ''
            GROUP BY {codigo_postal_col}
            ORDER BY COUNT(*) DESC, {codigo_postal_col}
            LIMIT 1
        """
        cur.execute(sql, (municipio.strip(), provincia.strip()))
        row = cur.fetchone()
        cur.close()
        conn.close()

        return JSONResponse({"codigo_postal": row[0] if row else None})

    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "GEO_ERROR", "error": "Error al buscar código postal", "detalle": str(e)})


@router.get("/usuarios-operaciones")
def usuarios_operaciones(departamento_id: int = 2):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre
            FROM usuario_admin
            WHERE departamento_id = %s
            ORDER BY nombre
            """,
            (departamento_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return JSONResponse([
            {
                "id": row[0],
                "nombre": row[1]
            }
            for row in rows
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al cargar responsables de operaciones", "detalle": str(e)})


@router.get("")
def get_all(q: str = None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            cur.close()
            return JSONResponse([])

        # choose display column if present
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        cols = [r[0] for r in cur.fetchall()]
        display_col = None
        for candidate in ('name', 'municipio', 'nombre'):
            if candidate in cols:
                display_col = candidate
                break

        if display_col:
            if q:
                like = f"%{q}%"
                sql = f"SELECT id, {display_col} FROM {table} WHERE {display_col} ILIKE %s ORDER BY {display_col} LIMIT 200"
                cur.execute(sql, (like,))
            else:
                sql = f"SELECT id, {display_col} FROM {table} ORDER BY {display_col} LIMIT 1000"
                cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            return JSONResponse([{"id": r[0], "name": r[1]} for r in rows])

        # fallback: return full rows
        cur.execute(f"SELECT * FROM {table} LIMIT 1000")
        rows = cur.fetchall()
        result = [_row_to_dict(cur, r) for r in rows]
        cur.close()
        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al obtener ciudades", "detalle": str(e)})


@router.get("/{id}")
def get_by_id(id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            cur.close()
            raise HTTPException(status_code=404, detail={"ok": False, "codigo": "NOT_FOUND", "error": "Ciudad no encontrada", "detalle": f"No existe tabla de ciudades"})

        cur.execute(f"SELECT * FROM {table} WHERE id = %s", (id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            raise HTTPException(status_code=404, detail={"ok": False, "codigo": "NOT_FOUND", "error": "Ciudad no encontrada", "detalle": f"No existe ciudad con ID {id}"})

        result = _row_to_dict(cur, row)
        cur.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al obtener ciudad", "detalle": str(e)})


@router.post("")
def create(payload: Dict[str, Any]):
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            cur.close()
            raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "No existe tabla de ciudades", "detalle": "No se pudo detectar tabla"})

        # only allow provided keys
        keys = [k for k in payload.keys() if payload[k] is not None]
        if not keys:
            cur.close()
            raise HTTPException(status_code=400, detail={"ok": False, "codigo": "BAD_REQUEST", "error": "Payload vacío"})

        cols_sql = ", ".join(keys)
        vals_sql = ", ".join(["%s"] * len(keys))
        sql = f"INSERT INTO {table} ({cols_sql}) VALUES ({vals_sql}) RETURNING *"
        cur.execute(sql, tuple(payload[k] for k in keys))
        row = cur.fetchone()
        conn.commit()
        result = _row_to_dict(cur, row)
        cur.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_UPDATE_ERROR", "error": "Error al guardar la ciudad", "detalle": str(e)})


@router.put("/{id}")
def update(id: int, data: Dict[str, Any]):
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            cur.close()
            raise HTTPException(status_code=404)

        # build SET clause
        keys = [k for k in data.keys()]
        if not keys:
            cur.close()
            raise HTTPException(status_code=400)

        set_sql = ", ".join([f"{k} = %s" for k in keys])
        sql = f"UPDATE {table} SET {set_sql} WHERE id = %s RETURNING *"
        params = tuple(data[k] for k in keys) + (id,)
        cur.execute(sql, params)
        row = cur.fetchone()
        if not row:
            cur.close()
            raise HTTPException(status_code=404)
        conn.commit()
        result = _row_to_dict(cur, row)
        cur.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
def delete(id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        table = _detect_table(cur)
        if not table:
            cur.close()
            raise HTTPException(status_code=404)

        cur.execute(f"DELETE FROM {table} WHERE id = %s RETURNING id", (id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            raise HTTPException(status_code=404)
        conn.commit()
        cur.close()
        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
