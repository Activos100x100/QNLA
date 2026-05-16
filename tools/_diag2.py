import sys
sys.path.insert(0, '/Users/elizabethjimenez/NachitoRRHH')
from app.database import get_connection
conn = get_connection()
cur = conn.cursor()

print('=== empleado_asignacion nullable ===')
cur.execute("""
    SELECT column_name, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='empleado_asignacion'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(r)

print('\n=== Tablas vehiculo ===')
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%vehiculo%'")
print(cur.fetchall())

print('\n=== Cols vehiculos ===')
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='vehiculos' ORDER BY ordinal_position")
print([r[0] for r in cur.fetchall()])

print('\n=== Vehiculos data ===')
cur.execute('SELECT id, name FROM vehiculos LIMIT 10')
print(cur.fetchall())

cur.close()
conn.close()
