import psycopg
import sys 
import os 
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))

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

def setup(target="dev"):
    conn = get_conn(target)
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
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
            pretty_salary     TEXT,
            salary_currency   TEXT,
            company_logo      TEXT,
            job_url           TEXT,
            job_level         TEXT,
            job_level_vi      TEXT,
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

def setup_embeddings(target="dev"):
    conn = get_conn(target)
    cur = conn.cursor()
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Make sure warehouse schema exists
    cur.execute("CREATE SCHEMA IF NOT EXISTS warehouse_warehouse;")

    # Embeddings table — dimension is configurable via EMBEDDING_DIM env var
    # Local dev: 384 (all-MiniLM-L6-v2), Prod: 1024 (BAAI/bge-m3)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS warehouse_warehouse.job_embeddings (
            job_id          INTEGER PRIMARY KEY,
            embedding       vector({EMBEDDING_DIM}),
            model_name      TEXT NOT NULL,
            embedded_at     TIMESTAMP DEFAULT NOW()
        );
    """)

    # HNSW index for fast similarity search
    cur.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_job_embeddings_hnsw
        ON warehouse_warehouse.job_embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print(f"pgvector ON + warehouse_warehouse.job_embeddings ready (dim={EMBEDDING_DIM})")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "dev"
    setup(target)
    setup_embeddings(target)