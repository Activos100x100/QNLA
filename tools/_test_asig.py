import sys, os, requests, json

CSV = '/Users/elizabethjimenez/Downloads/04 QNLA MES DE ABRIL 2026 - Santander.csv'
BASE = 'http://127.0.0.1:8000'

# 1. Obtener ciudad_id de Santander
resp = requests.get(f'{BASE}/api/ciudades')
ciudades = resp.json()
print("Ciudades disponibles:")
for c in ciudades:
    print(f"  id={c.get('id')} nombre={c.get('name') or c.get('nombre')}")

santander = next((c for c in ciudades if 'santander' in (c.get('name') or c.get('nombre') or '').lower()), None)
if not santander:
    print("\nERROR: No se encontró ciudad Santander"); sys.exit(1)

ciudad_id = santander['id']
print(f"\nUsando ciudad_id={ciudad_id} ({santander.get('name') or santander.get('nombre')})")

# 2. Subir CSV al endpoint
with open(CSV, 'rb') as f:
    resp2 = requests.post(
        f'{BASE}/api/empleados/asignacion-por-fichero/procesar',
        data={'ciudad_id': str(ciudad_id)},
        files={'file': ('santander.csv', f, 'text/csv')}
    )

print(f"\nHTTP status: {resp2.status_code}")
try:
    data = resp2.json()
except Exception as e:
    print(f"No se pudo parsear JSON: {e}")
    print(resp2.text[:500])
    sys.exit(1)

print(f"ok: {data.get('ok')}")
s = data.get('summary', {})
print(f"Summary: total={s.get('total_rows')} created={s.get('created')} updated={s.get('updated')} sin_cambios={s.get('sin_cambios')} bajas={s.get('bajas')} errors={s.get('errors')}")

results = data.get('results', [])
print(f"\nTotal resultados: {len(results)}")

# Agrupar por acción
from collections import Counter
actions = Counter(r.get('action') for r in results)
print(f"Distribución de acciones: {dict(actions)}")

# Mostrar casos interesantes
print("\n=== Primeros 5 con alguna acción (no Sin cambios) ===")
interesting = [r for r in results if r.get('action') not in ('Sin cambios', None)][:5]
for r in interesting:
    print(f"  fila={r.get('row_number')} rrhh={r.get('rrhh')} nombre={r.get('empleado_nombre')} accion={r.get('action')} detalle={r.get('detail')}")

print("\n=== Primeros 5 con error ===")
errors = [r for r in results if r.get('action') == 'Error'][:5]
for r in errors:
    print(f"  fila={r.get('row_number')} rrhh={r.get('rrhh')} detalle={r.get('detail')}")

print("\n=== Muestra de primeras 5 filas (cualquier acción) ===")
for r in results[:5]:
    print(f"  fila={r.get('row_number')} rrhh={r.get('rrhh')} nombre={r.get('empleado_nombre')} accion={r.get('action')} detalle={r.get('detail')}")
