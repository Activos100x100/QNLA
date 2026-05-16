from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict

from ..database import get_connection

router = APIRouter(prefix="/api/usuario-admin")


def _usuario_admin_table_exists(cur) -> bool:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'usuario_admin'")
    return bool(cur.fetchone())


def _get_usuario_admin_columns(cur) -> list[str]:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='usuario_admin'")
    cols = [r[0] for r in cur.fetchall()]
    return cols


@router.get("")
def list_usuario_admin(q: str = None):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if not _usuario_admin_table_exists(cur):
            return JSONResponse([])

        cols = _get_usuario_admin_columns(cur)
        select_cols = [
            c for c in [
                "id", "nombre", "apellidos", "dni", "email_corporativo", "email_personal",
                "telefono_corporativo", "telefono_personal", "direccion", "activo",
                "created_at", "departamento_id", "fecha_baja"
            ]
            if c in cols
        ]

        if not select_cols:
            return JSONResponse([])

        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('departamento','departamentos')")
        departamento_tables = [r[0] for r in cur.fetchall()]
        departamento_table = departamento_tables[0] if departamento_tables else None

        select_exprs = [f"ua.{c}" for c in select_cols]
        response_cols = list(select_cols)
        from_sql = "FROM usuario_admin ua"

        if departamento_table and "departamento_id" in select_cols:
            from_sql += f" LEFT JOIN {departamento_table} d ON ua.departamento_id = d.id"
            select_exprs.append("d.nombre AS departamento_nombre")
            response_cols.append("departamento_nombre")

        cols_sql = ", ".join(select_exprs)
        if q:
            query = f"""
                SELECT {cols_sql}
                {from_sql}
                WHERE COALESCE(ua.nombre, '') ILIKE %s
                   OR COALESCE(ua.apellidos, '') ILIKE %s
                   OR COALESCE(ua.dni, '') ILIKE %s
                ORDER BY ua.id DESC
                LIMIT 200
            """
            like = f"%{q.strip()}%"
            cur.execute(query, (like, like, like))
        else:
            query = f"SELECT {cols_sql} {from_sql} ORDER BY ua.id DESC LIMIT 500"
            cur.execute(query)

        rows = cur.fetchall()
        result = []
        for row in rows:
            item = {}
            for idx, col in enumerate(response_cols):
                item[col] = row[idx]
            result.append(item)

        return JSONResponse(jsonable_encoder(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al consultar usuarios admin", "detalle": str(e)})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/{id}")
def get_usuario_admin(id: int):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if not _usuario_admin_table_exists(cur):
            raise HTTPException(status_code=404, detail={"ok": False, "codigo": "NOT_FOUND", "error": "No existe tabla usuario_admin"})

        cols = _get_usuario_admin_columns(cur)
        if not cols:
            raise HTTPException(status_code=404, detail={"ok": False, "codigo": "NOT_FOUND", "error": "No hay columnas en usuario_admin"})

        cols_sql = ", ".join(cols)
        cur.execute(f"SELECT {cols_sql} FROM usuario_admin WHERE id = %s", (id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"ok": False, "codigo": "NOT_FOUND", "error": f"No existe usuario admin con id {id}"})

        result = {}
        for idx, col in enumerate(cols):
            result[col] = row[idx]

        return JSONResponse(jsonable_encoder(result))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al obtener usuario admin", "detalle": str(e)})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.post("")
def create_usuario_admin(payload: Dict[str, Any]):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if not _usuario_admin_table_exists(cur):
            raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "No existe tabla usuario_admin"})

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='usuario_admin'")
        cols = {r[0] for r in cur.fetchall()}

        keys = [k for k, v in payload.items() if k in cols and k != 'id' and v is not None]
        if not keys:
            raise HTTPException(status_code=400, detail={"ok": False, "codigo": "BAD_REQUEST", "error": "Payload vacío"})

        if "activo" in cols and "activo" not in keys:
            payload["activo"] = True
            keys.append("activo")

        required = ["nombre", "apellidos", "dni", "departamento_id"]
        missing_required = [field for field in required if field in cols and (field not in keys or str(payload.get(field, "")).strip() == "")]
        if missing_required:
            raise HTTPException(status_code=400, detail={"ok": False, "codigo": "BAD_REQUEST", "error": f"Faltan campos requeridos: {', '.join(missing_required)}"})

        cols_sql = ", ".join(keys)
        vals_sql = ", ".join(["%s"] * len(keys))
        sql = f"INSERT INTO usuario_admin ({cols_sql}) VALUES ({vals_sql}) RETURNING id, nombre"
        cur.execute(sql, tuple(payload[k] for k in keys))
        row = cur.fetchone()
        conn.commit()

        return JSONResponse({"ok": True, "id": row[0], "nombre": row[1]})

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al crear usuario admin", "detalle": str(e)})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.put("/{id}")
def update_usuario_admin(id: int, payload: Dict[str, Any]):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if not _usuario_admin_table_exists(cur):
            raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "No existe tabla usuario_admin"})

        cols = set(_get_usuario_admin_columns(cur))
        keys = [k for k, v in payload.items() if k in cols and k != 'id' and v is not None]
        if not keys:
            raise HTTPException(status_code=400, detail={"ok": False, "codigo": "BAD_REQUEST", "error": "Payload vacío"})

        set_sql = ", ".join([f"{k} = %s" for k in keys])
        sql = f"UPDATE usuario_admin SET {set_sql} WHERE id = %s RETURNING id, nombre"
        params = tuple(payload[k] for k in keys) + (id,)
        cur.execute(sql, params)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"ok": False, "codigo": "NOT_FOUND", "error": f"No existe usuario admin con id {id}"})

        conn.commit()
        return JSONResponse({"ok": True, "id": row[0], "nombre": row[1]})
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail={"ok": False, "codigo": "DB_ERROR", "error": "Error al actualizar usuario admin", "detalle": str(e)})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
