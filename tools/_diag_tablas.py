"""Diagnóstico de tablas empleado_asignacion, rider_operativo, vehiculo_asignacion."""
import sys
sys.path.insert(0, '/Users/elizabethjimenez/NachitoRRHH')
from app.database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute('SELECT id, nombre, apellidos, id_rrhh FROM empleados WHERE id_rrhh IS NOT NULL ORDER BY id LIMIT 5')
emps = cur.fetchall()
for emp in emps:
    eid, nombre, apellidos, rrhh = emp
    print(f'\n--- RRHH={rrhh} eid={eid} ({nombre} {apellidos}) ---')
    cur.execute('SELECT id, departamento_id, ciudad_id, fecha_inicio FROM empleado_asignacion WHERE empleado_id=%s ORDER BY id DESC LIMIT 2', (eid,))
    print(f'  asignacion : {cur.fetchall()}')
    cur.execute('SELECT id, rider_id, cod_activo, ciudad_id, activo FROM rider_operativo WHERE empleado_id=%s ORDER BY id DESC LIMIT 2', (eid,))
    print(f'  rider_op   : {cur.fetchall()}')
    cur.execute('SELECT id, vehiculo_id, rider_operativo_id, empleado_id FROM vehiculo_asignacion WHERE empleado_id=%s ORDER BY id DESC LIMIT 2', (eid,))
    print(f'  vehiculo   : {cur.fetchall()}')

cur.close()
conn.close()
