"""
FastAPI Backend — TechJob AI
Serves job data, analytics, and semantic search from PostgreSQL + pgvector.
"""

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2 import pool
import psycopg2.extras
import os
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load env from data-pipeline/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

# Dùng biến môi trường NEON nếu có, không thì mặc định
DB_HOST = os.getenv("NEON_HOST", os.getenv("POSTGRES_HOST", "localhost"))
DB_PORT = os.getenv("NEON_PORT", os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("NEON_USER", os.getenv("POSTGRES_USER", "techjob"))
DB_PASS = os.getenv("NEON_PASSWORD", os.getenv("POSTGRES_PASSWORD", "techjob123"))
DB_NAME = os.getenv("NEON_DB", os.getenv("POSTGRES_DB", "techjob_ai"))

# Model for semantic search
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("BAAI/bge-m3")
    return model

# Connection Pool
db_pool = None

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="TechJob AI API",
    description="IT Job Market Analytics & Semantic Search (Powered by NeonDB & dbt Marts)",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    global db_pool
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,
        host=DB_HOST, port=int(DB_PORT),
        user=DB_USER, password=DB_PASS,
        dbname=DB_NAME,
        sslmode="require" # Bắt buộc cho NeonDB
    )

@app.on_event("shutdown")
def shutdown():
    if db_pool:
        db_pool.closeall()

def get_db():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"message": "TechJob AI API is running on NeonDB Marts", "version": "1.2.0"}


@app.get("/api/stats")
def get_stats(conn = Depends(get_db)):
    """Dashboard overview stats."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("SELECT SUM(job_count) as total_jobs, COUNT(city_id) as total_cities FROM warehouse_marts.mart_location_demand;")
    row1 = cur.fetchone()
    
    cur.execute("SELECT COUNT(*) as total_skills FROM warehouse_warehouse.dim_skill;")
    row2 = cur.fetchone()
    
    cur.execute("SELECT COUNT(*) as total_companies FROM warehouse_warehouse.dim_company;")
    row3 = cur.fetchone()
    
    cur.close()
    
    result = dict(row1) if row1 else {}
    if row2: result.update(row2)
    if row3: result.update(row3)
    
    return result

@app.get("/api/jobs-by-level")
def get_jobs_by_level(conn = Depends(get_db)):
    """Job count by seniority level."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT lvl.level_name_vi, lvl.seniority_order, COUNT(*) AS job_count
        FROM warehouse_warehouse.fact_job_postings AS f
        LEFT JOIN warehouse_warehouse.dim_job_level AS lvl USING (job_level_id)
        GROUP BY lvl.level_name_vi, lvl.seniority_order
        ORDER BY lvl.seniority_order;
        """
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/jobs")
def get_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query("", max_length=100),
    conn = Depends(get_db)
):
    """List jobs with pagination and filters."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    offset = (page - 1) * size
    conditions = []
    params = []

    if keyword:
        conditions.append("(f.job_title ILIKE %s OR c.company_name ILIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count
    count_sql = f"""
        SELECT COUNT(*) as total 
        FROM warehouse_warehouse.fact_job_postings f
        LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
        {where_clause}
    """
    cur.execute(count_sql, params)
    total = cur.fetchone()["total"]

    # Data
    data_sql = f"""
        SELECT f.job_id, f.job_title AS title, c.company_name, 
               (f.working_locations->0->>'cityNameVI') AS primary_city, 
               f.salary_min, f.salary_max, 
               jl.level_name_vi,
               f.created_on AS posted_date,
               CONCAT('https://www.vietnamworks.com/-', f.job_id, '-jv') AS source_url
        FROM warehouse_warehouse.fact_job_postings f
        LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
        LEFT JOIN warehouse_warehouse.dim_job_level jl ON f.job_level_id = jl.job_level_id
        {where_clause}
        ORDER BY f.created_on DESC NULLS LAST
        LIMIT %s OFFSET %s
    """
    cur.execute(data_sql, params + [size, offset])
    jobs = cur.fetchall()
    cur.close()

    return {"total": total, "page": page, "size": size, "data": jobs}


@app.get("/api/jobs/{job_id}")
def get_job_by_id(job_id: int, conn = Depends(get_db)):
    """Get detailed information for a single job posting."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = """
        SELECT f.job_id, f.job_title AS title, c.company_name, 
               (f.working_locations->0->>'cityNameVI') AS primary_city, 
               f.working_locations,
               f.salary_min, f.salary_max, 
               jl.level_name_vi,
               f.job_description,
               f.job_requirement,
               f.benefits,
               f.skills,
               f.created_on AS posted_date,
               CONCAT('https://www.vietnamworks.com/-', f.job_id, '-jv') AS source_url
        FROM warehouse_warehouse.fact_job_postings f
        LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
        LEFT JOIN warehouse_warehouse.dim_job_level jl ON f.job_level_id = jl.job_level_id
        WHERE f.job_id = %s
    """
    cur.execute(query, [job_id])
    job = cur.fetchone()
    cur.close()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return job


@app.get("/api/jobs/{job_id}/related")
def get_related_jobs(job_id: int, limit: int = Query(3, ge=1, le=10), conn = Depends(get_db)):
    """Get related jobs using pgvector semantic similarity."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("SELECT embedding FROM warehouse_warehouse.job_embeddings WHERE job_id = %s", [job_id])
    row = cur.fetchone()
    
    if not row or row["embedding"] is None:
        # Fallback if no embedding exists
        query = """
            SELECT f.job_id, f.job_title AS title, c.company_name, 
                   (f.working_locations->0->>'cityNameVI') AS primary_city, 
                   f.salary_min, f.salary_max, jl.level_name_vi,
                   CONCAT('https://www.vietnamworks.com/-', f.job_id, '-jv') AS source_url
            FROM warehouse_warehouse.fact_job_postings f
            LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
            LEFT JOIN warehouse_warehouse.dim_job_level jl ON f.job_level_id = jl.job_level_id
            WHERE f.job_id != %s 
              AND f.job_level_id = (SELECT job_level_id FROM warehouse_warehouse.fact_job_postings WHERE job_id = %s)
            LIMIT %s
        """
        cur.execute(query, [job_id, job_id, limit])
        jobs = cur.fetchall()
        cur.close()
        return {"data": jobs, "method": "fallback_level"}

    vec_str = row["embedding"]
    query = """
        SELECT f.job_id, f.job_title AS title, c.company_name, 
               (f.working_locations->0->>'cityNameVI') AS primary_city, 
               f.salary_min, f.salary_max, jl.level_name_vi,
               CONCAT('https://www.vietnamworks.com/-', f.job_id, '-jv') AS source_url,
               1 - (e.embedding <=> %s::vector) AS similarity
        FROM warehouse_warehouse.fact_job_postings f
        JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
        LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
        LEFT JOIN warehouse_warehouse.dim_job_level jl ON f.job_level_id = jl.job_level_id
        WHERE f.job_id != %s AND e.embedding IS NOT NULL
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
    """
    cur.execute(query, [vec_str, job_id, vec_str, limit])
    jobs = cur.fetchall()
    cur.close()
    
    return {"data": jobs, "method": "semantic"}

@app.get("/api/top-skills")
def get_top_skills(limit: int = Query(20, ge=1, le=50), conn = Depends(get_db)):
    """Top skills by job count."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute(
        """
        SELECT s.skill_name, SUM(m.job_count) AS total_jobs 
        FROM warehouse_marts.mart_skill_demand m
        JOIN warehouse_warehouse.dim_skill s ON m.skill_id = s.skill_id
        GROUP BY s.skill_name 
        ORDER BY total_jobs DESC 
        LIMIT %s;
        """,
        [limit],
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/salary-by-title")
def get_salary_by_title(conn = Depends(get_db)):
    """Median salary by skill and job level."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT skill_name, level_name_vi, median_salary_min, median_salary_max, sample_size
        FROM warehouse_marts.mart_salary_benchmark
        ORDER BY median_salary_max DESC NULLS LAST;
        """
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/search")
def semantic_search(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    conn = Depends(get_db)
):
    """Semantic search using pgvector cosine similarity."""
    m = get_model()
    query_vec = m.encode(q).tolist()
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT f.job_id, f.job_title AS title, c.company_name, 
                  (f.working_locations->0->>'cityNameVI') AS primary_city,
                  f.salary_min, f.salary_max, 
                  CONCAT('https://www.vietnamworks.com/-', f.job_id, '-jv') AS source_url,
                  1 - (e.embedding <=> %s::vector) AS similarity
           FROM warehouse_warehouse.fact_job_postings f
           JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
           LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
           WHERE e.embedding IS NOT NULL
           ORDER BY e.embedding <=> %s::vector
           LIMIT %s;""",
        [vec_str, vec_str, limit],
    )
    rows = cur.fetchall()
    cur.close()

    return {"query": q, "results": rows}


@app.get("/api/trends")
def get_trends(conn = Depends(get_db)):
    """Monthly hiring trends without double counting skills."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT DATE_TRUNC('month', created_on)::DATE AS month, COUNT(*) AS job_count
        FROM warehouse_warehouse.fact_job_postings
        WHERE created_on IS NOT NULL
        GROUP BY 1
        ORDER BY 1;
        """
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/locations")
def get_locations(conn = Depends(get_db)):
    """Job count distribution by city for Pie Chart."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT l.city_name_vi, m.job_count
        FROM warehouse_marts.mart_location_demand m
        JOIN warehouse_warehouse.dim_location l ON m.city_id = l.city_id
        ORDER BY m.job_count DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/skill-trends")
def get_skill_trends(conn = Depends(get_db)):
    """Monthly trend for top 5 hottest skills."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        WITH top_skills AS (
            SELECT skill_id FROM warehouse_marts.mart_skill_demand
            GROUP BY skill_id ORDER BY SUM(job_count) DESC LIMIT 5
        )
        SELECT s.skill_name, DATE_TRUNC('month', m.week_start)::DATE AS month, SUM(m.job_count) AS job_count
        FROM warehouse_marts.mart_skill_demand m
        JOIN warehouse_warehouse.dim_skill s ON m.skill_id = s.skill_id
        WHERE m.skill_id IN (SELECT skill_id FROM top_skills)
        GROUP BY s.skill_name, month
        ORDER BY month, s.skill_name;
        """
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}
