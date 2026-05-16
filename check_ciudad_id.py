#!/usr/bin/env python3
import os
from app.database import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    
    # Check if empleados table has ciudad_id column
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='empleados'")
    cols = [r[0] for r in cur.fetchall()]
    
    if 'ciudad_id' in cols:
        print("✓ ciudad_id column exists in empleados table")
        print("  Sample query: SELECT COUNT(*) FROM empleados WHERE ciudad_id = 1")
        cur.execute("SELECT COUNT(*) FROM empleados WHERE ciudad_id = %s", (1,))
        count = cur.fetchone()[0]
        print(f"  Result: {count} empleados in ciudad_id=1")
    else:
        print("✗ ciudad_id column NOT found in empleados table")
        print(f"  Available columns: {', '.join(sorted(cols))}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
