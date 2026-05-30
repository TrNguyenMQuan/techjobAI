"""
FastAPI Backend — TechJob AI
Serves job data, analytics, and semantic search from PostgreSQL + pgvector.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load env from data-pipeline/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "techjob")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

# Model for semantic search
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return model

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT),
        user=DB_USER, password=DB_PASS,
        dbname=DB_NAME
    )

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="TechJob AI API",
    description="IT Job Market Analytics & Semantic Search",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"message": "TechJob AI API is running", "version": "1.0.0"}


@app.get("/api/stats")
def get_stats():
    """Dashboard overview stats."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM warehouse_warehouse.dashboard_cache LIMIT 1;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else {}


@app.get("/api/jobs")
def get_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query("", max_length=100),
    salary_band: str = Query("", max_length=50),
):
    """List jobs with pagination and filters."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    offset = (page - 1) * size
    conditions = []
    params = []

    if keyword:
        conditions.append("(title ILIKE %s OR company_name ILIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if salary_band:
        conditions.append("salary_band = %s")
        params.append(salary_band)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count
    cur.execute(f"SELECT COUNT(*) as total FROM warehouse_warehouse.fact_job {where_clause}", params)
    total = cur.fetchone()["total"]

    # Data
    cur.execute(
        f"""SELECT source_id, title, company_name, primary_city, salary_text,
                   salary_min_vnd, salary_max_vnd, salary_band, job_level_vi,
                   work_mode, source_url, posted_date
            FROM warehouse_warehouse.fact_job {where_clause}
            ORDER BY posted_date DESC NULLS LAST
            LIMIT %s OFFSET %s""",
        params + [size, offset],
    )
    jobs = cur.fetchall()
    cur.close()
    conn.close()

    return {"total": total, "page": page, "size": size, "data": jobs}


@app.get("/api/top-skills")
def get_top_skills(limit: int = Query(20, ge=1, le=50)):
    """Top skills by job count."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT skill_name, job_count FROM warehouse_warehouse.agg_top_skills ORDER BY job_count DESC LIMIT %s;",
        [limit],
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"data": rows}


@app.get("/api/salary-by-title")
def get_salary_by_title():
    """Average salary by job category."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM warehouse_warehouse.agg_salary_by_title ORDER BY job_count DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"data": rows}


@app.get("/api/search")
def semantic_search(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=50),
):
    """Semantic search using pgvector cosine similarity."""
    m = get_model()
    query_vec = m.encode(q).tolist()
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT source_id, title, company_name, primary_city,
                  salary_text, salary_band, source_url,
                  1 - (embedding <=> %s::vector) AS similarity
           FROM warehouse_warehouse.fact_job
           WHERE embedding IS NOT NULL
           ORDER BY embedding <=> %s::vector
           LIMIT %s;""",
        [vec_str, vec_str, limit],
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {"query": q, "results": rows}


@app.get("/api/trends")
def get_trends():
    """Monthly hiring trends."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM warehouse_warehouse.agg_trend_monthly ORDER BY month;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"data": rows}
