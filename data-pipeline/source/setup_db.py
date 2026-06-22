import psycopg
import os 
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

def get_conn(target="dev"):
    if target == "prod":
        return psycopg.connect(
            host=os.getenv("NEON_HOST"),
            port=int(os.getenv("NEON_PORT", 5432)),
            dbname=os.getenv("NEON_DB"),
            user=os.getenv("NEON_USER"),
            password=os.getenv("NEON_PASSWORD"),
            sslmode="require", 
        )
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "techjob_ai"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        sslmode=os.getenv("POSTGRES_SSLMODE", "prefer"), 
    )

def setup():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS silver.jobs (
            job_id            INTEGER PRIMARY KEY,
            job_title         TEXT,
            company_name      TEXT,
            company_id        INTEGER,
            salary_min        INTEGER,
            salary_max        INTEGER,
            is_salary_visible BOOLEAN,
            job_level_id      INTEGER,
            type_working_id   INTEGER,
            created_on        TIMESTAMP,
            expired_on        TIMESTAMP,
            approved_on       TIMESTAMP,
            skills            JSONB,
            working_locations JSONB,
            benefits          JSONB,
            job_functions_v3  JSONB,
            job_description   TEXT,
            job_requirement   TEXT,
            ingested_at       TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Schema silver and table silver.jobs is ready.")

if __name__ == "__main__":
    setup()