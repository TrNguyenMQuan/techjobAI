import psycopg2

try:
    conn = psycopg2.connect(
        host="ep-odd-feather-aok9wn0q.c-2.ap-southeast-1.aws.neon.tech",
        port=5432,
        dbname="neondb",
        user="machine_learning_readonly",
        password="machine_learning",
        sslmode="require"
    )
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
