import psycopg2

import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

try:
    conn = psycopg2.connect(
        host=os.getenv("NEON_HOST", os.getenv("POSTGRES_HOST", "localhost")),
        port=int(os.getenv("NEON_PORT", os.getenv("POSTGRES_PORT", "5432"))),
        user=os.getenv("NEON_USER", os.getenv("POSTGRES_USER", "techjob")),
        password=os.getenv("NEON_PASSWORD", os.getenv("POSTGRES_PASSWORD", "techjob123")),
        dbname=os.getenv("NEON_DB", os.getenv("POSTGRES_DB", "techjob_ai")),
        sslmode="require" if os.getenv("NEON_HOST") else os.getenv("PGSSLMODE", "prefer")
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
