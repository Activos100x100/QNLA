import requests, json, sys

CSV_PATH = '/Users/elizabethjimenez/Downloads/04 FTRA MES DE ABRIL 2026 - Santander.csv'
CIUDAD_ID = 6  # Santander

with open(CSV_PATH, 'rb') as f:
    csv_bytes = f.read()

resp = requests.post(
    'http://127.0.0.1:8000/api/empleados/asignacion-por-fichero/procesar',
    files={'file': ('santander.csv', csv_bytes, 'text/csv')},
    data={'ciudad_id': CIUDAD_ID}
)

body = resp.json()
print('STATUS:', resp.status_code)
print('OK:', body.get('ok'))
print('SUMMARY:', json.dumps(body.get('summary', {}), ensure_ascii=False, indent=2))

results = body.get('results', [])
print(f'\nPrimeras 10 filas ({len(results)} total):')
for r in results[:10]:
    print(f"  Fila {r.get('row_number')} | RRHH={r.get('rrhh')} | BD={r.get('empleado_nombre')} | CSV={r.get('nombre_csv')} | RiderID={r.get('rider_id')} | Cod={r.get('cod_activo')} | Veh={r.get('vehiculo')} | Jornada={r.get('jornada')} | {r.get('action')}")

cambios = [r for r in results if r.get('action') not in ('Sin cambios',)]
print(f'\nCon cambio real: {len(cambios)}')
for r in cambios[:20]:
    print(f"  [{r.get('action')}] RRHH={r.get('rrhh')} | {r.get('empleado_nombre')} | {r.get('detail')}")

errores = [r for r in results if r.get('action') == 'Error']
print(f'\nErrores: {len(errores)}')
for r in errores[:10]:
    print(f"  Fila {r.get('row_number')} | RRHH={r.get('rrhh')} | {r.get('detail')}")
