"""Diagnóstico completo: lee el CSV, normaliza cabeceras y prueba pick_value."""
import sys, csv, io, unicodedata
sys.path.insert(0, '/Users/elizabethjimenez/NachitoRRHH')
from app.database import get_connection

CSV_PATH = '/Users/elizabethjimenez/Downloads/04 FTRA MES DE ABRIL 2026 - Santander.csv'

def _normalize_csv_header(value):
    text = str(value or '').strip().lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.replace(' ', '_').replace('-', '_')

HEADER_ALIASES = {
    'rrhh':           ('rrhh', 'id_rrhh', 'codigo_rrhh', 'identificador'),
    'fecha_alta':     ('fecha_alta', 'alta', 'fecha_inicio', 'fecha de alta'),
    'rider_id':       ('rider_id', 'raider_id', 'raider id', 'rider'),
    'cod_activo':     ('cod_activo', 'no_activo', 'n_activo', 'n activo', 'no activo', 'numero_activo', 'activo'),
    'vehiculo':       ('vehiculo', 'tipo_vehiculo'),
    'baja':           ('baja', 'fecha_baja'),
    'nombre_completo':('nombre_completo', 'nombre completo', 'trabajador', 'nombre'),
    'jornada':        ('jornada', 'tipo_jornada', 'contrato'),
}

header_aliases_norm = {
    key: [_normalize_csv_header(v) for v in values]
    for key, values in HEADER_ALIASES.items()
}

def pick_value(row, key_name):
    for alias_norm in header_aliases_norm[key_name]:
        value = row.get(alias_norm)
        if value is not None and str(value).strip() != '':
            return value
    return None

# Leer CSV
with open(CSV_PATH, 'rb') as f:
    raw = f.read()

for enc in ['utf-8-sig', 'latin-1', 'cp1252']:
    try:
        text = raw.decode(enc)
        break
    except Exception:
        continue

try:
    import csv as _csv
    dialect = _csv.Sniffer().sniff(text[:4096], delimiters=',\t;|')
except Exception:
    import csv as _csv
    dialect = _csv.excel

all_rows = list(_csv.reader(io.StringIO(text), dialect=dialect))

# Detectar cabecera
rrhh_aliases_norm = [_normalize_csv_header(v) for v in HEADER_ALIASES['rrhh']]
best_score = -1
header_idx = 0
for idx in range(min(8, len(all_rows))):
    candidate = [_normalize_csv_header(col) for col in all_rows[idx]]
    score = sum(1 for aliases in header_aliases_norm.values() if any(c in aliases for c in candidate))
    has_rrhh = any(c in rrhh_aliases_norm for c in candidate)
    score += 2 if has_rrhh else 0
    if score > best_score:
        best_score = score
        header_idx = idx

headers_orig = all_rows[header_idx]
headers_norm = [_normalize_csv_header(c) for c in headers_orig]
print(f'Cabecera en fila {header_idx}, score={best_score}')
print('Cabeceras normalizadas:', headers_norm[:15])
print()

# Mostrar qué recoge pick_value para las primeras 5 filas con RRHH
count = 0
for row_list in all_rows[header_idx+1:]:
    if len(row_list) < len(headers_norm):
        row_list += [''] * (len(headers_norm) - len(row_list))
    row = {headers_norm[i]: row_list[i] for i in range(len(headers_norm)) if headers_norm[i]}
    rrhh = pick_value(row, 'rrhh')
    if not rrhh or not str(rrhh).strip():
        continue
    print(f'RRHH={rrhh} | rider_id={pick_value(row,"rider_id")} | cod_activo={pick_value(row,"cod_activo")} | vehiculo={pick_value(row,"vehiculo")} | alta={pick_value(row,"fecha_alta")} | baja={pick_value(row,"baja")} | nombre={pick_value(row,"nombre_completo")}')
    count += 1
    if count >= 5:
        break

# Ahora verificar en BD cuántos de esos RRHH existen
print('\n--- Verificando en BD ---')
conn = get_connection()
cur = conn.cursor()
count2 = 0
for row_list in all_rows[header_idx+1:]:
    if len(row_list) < len(headers_norm):
        row_list += [''] * (len(headers_norm) - len(row_list))
    row = {headers_norm[i]: row_list[i] for i in range(len(headers_norm)) if headers_norm[i]}
    rrhh = pick_value(row, 'rrhh')
    if not rrhh or not str(rrhh).strip():
        continue
    try:
        rrhh_int = int(str(rrhh).strip())
    except Exception:
        continue
    cur.execute('SELECT id, nombre, apellidos FROM empleados WHERE id_rrhh=%s LIMIT 1', (rrhh_int,))
    emp = cur.fetchone()
    if emp:
        eid = emp[0]
        cur.execute('SELECT id FROM rider_operativo WHERE empleado_id=%s LIMIT 1', (eid,))
        rider = cur.fetchone()
        print(f'  RRHH={rrhh_int} → eid={eid} ({emp[1]}) | rider_operativo: {"SÍ id="+str(rider[0]) if rider else "vacío"}')
        count2 += 1
        if count2 >= 5:
            break

cur.close()
conn.close()
