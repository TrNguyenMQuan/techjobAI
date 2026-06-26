import psycopg2
from ai.db_config import psycopg2_kwargs

try:
    conn = psycopg2.connect(**psycopg2_kwargs())
    cur = conn.cursor()

    print("Columns of mart_skill_demand:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'warehouse_marts' 
        AND table_name = 'mart_skill_demand';
    """)
    cols = cur.fetchall()
    for c in cols:
        print(c)

    print("Columns of mart_salary_benchmark:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'warehouse_marts' 
        AND table_name = 'mart_salary_benchmark';
    """)
    cols = cur.fetchall()
    for c in cols:
        print(c)

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
