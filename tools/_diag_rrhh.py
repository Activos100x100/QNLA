import csv, io, unicodedata, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.database import get_connection

def norm(value):
    text = str(value or '').strip().lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.replace(' ', '_').replace('-', '_')

CSV = '/Users/elizabethjimenez/Downloads/04 QNLA MES DE ABRIL 2026 - Santander.csv'
with open(CSV, 'rb') as f:
    raw = f.read()
for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
    try:
        text = raw.decode(enc)
        break
    except Exception:
        pass

rows = list(csv.reader(io.StringIO(text)))
print(f"Total filas CSV: {len(rows)}")
print(f"Fila 0 (primeras 10 celdas): {rows[0][:10]}")
print(f"Fila 1 (primeras 10 celdas): {rows[1][:10]}")
print(f"Fila 2 (datos, primeras 10): {rows[2][:10]}")

headers = [norm(c) for c in rows[1]]
print(f"\nCabeceras normalizadas: {headers[:12]}")

# Buscar índice RRHH
if 'rrhh' not in headers:
    print("ERROR: columna 'rrhh' NO encontrada en headers"); sys.exit(1)

rrhh_idx = headers.index('rrhh')
print(f"Índice de columna RRHH: {rrhh_idx}")

rrhh_vals = []
for i, r in enumerate(rows[2:], start=2):
    if len(r) > rrhh_idx:
        v = r[rrhh_idx].strip()
        if v and v.isdigit():
            rrhh_vals.append(int(v))

print(f"\nTotal RRHH numéricos en CSV: {len(rrhh_vals)}")
print(f"RRHH únicos: {len(set(rrhh_vals))}")
print(f"Muestra (primeros 15): {sorted(set(rrhh_vals))[:15]}")

conn = get_connection()
cur = conn.cursor()

# Cuántos hay en empleados
cur.execute("SELECT COUNT(*) FROM empleados WHERE id_rrhh IS NOT NULL")
total_with_rrhh = cur.fetchone()[0]
print(f"\nEmpleados EN BD con id_rrhh no nulo: {total_with_rrhh}")

cur.execute("SELECT id_rrhh FROM empleados WHERE id_rrhh IS NOT NULL LIMIT 20")
sample_bd = [r[0] for r in cur.fetchall()]
print(f"Muestra id_rrhh en BD: {sorted(sample_bd)[:15]}")

if rrhh_vals:
    unique_vals = list(set(rrhh_vals))
    placeholders = ','.join(['%s'] * len(unique_vals))
    cur.execute(f"SELECT id, id_rrhh, nombre, apellidos FROM empleados WHERE id_rrhh IN ({placeholders})", unique_vals)
    found = cur.fetchall()
    print(f"\nRRHH del CSV encontrados en BD: {len(found)} de {len(unique_vals)}")
    for row in found[:10]:
        print(f"  id={row[0]} id_rrhh={row[1]} nombre={row[2]} {row[3]}")
    not_found = set(unique_vals) - {r[1] for r in found}
    print(f"\nRRHH del CSV NO encontrados: {len(not_found)}")
    print(f"Ejemplos: {sorted(not_found)[:15]}")

cur.close()
conn.close()
