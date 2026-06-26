"""
FastAPI Backend — TechJob AI
Serves job data, analytics, semantic search, AI agent chat,
salary prediction, and cover letter generation from PostgreSQL + pgvector.
"""

from fastapi import FastAPI, Query, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import psycopg2
import psycopg2.extras
import json
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from ai.db_config import psycopg2_kwargs, public_config
from ai.observability import log_ai_event, timed_ai_event

# Load env from data-pipeline/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

# Model for semantic search (cached globally)
_search_model = None
_search_model_lock = threading.Lock()

def get_model():
    global _search_model
    if _search_model is None:
        with _search_model_lock:
            if _search_model is None:
                from sentence_transformers import SentenceTransformer
                _search_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _search_model

def get_conn():
    return psycopg2.connect(
        **psycopg2_kwargs(
            connect_timeout=8,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=3,
        ),
    )

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="TechJob AI API",
    description="IT Job Market Analytics, Semantic Search, AI Agent Chat, Salary Prediction & Cover Letter Generation",
    version="2.0.0",
)
from psycopg2 import pool
from fastapi import Depends
db_pool = None

@app.on_event("startup")
def startup():
    global db_pool
    db_pool = pool.ThreadedConnectionPool(
        1,
        10,
        **psycopg2_kwargs(
            connect_timeout=8,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=3,
        ),
    )

@app.on_event("shutdown")
def shutdown():
    if db_pool: db_pool.closeall()

def get_db():
    conn = db_pool.getconn()
    discard = False
    try:
        # Neon may close an idle SSL connection while it is still present in
        # the local pool. Validate before handing it to an endpoint.
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            conn.rollback()
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            db_pool.putconn(conn, close=True)
            conn = db_pool.getconn()
        yield conn
    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        discard = True
        raise
    finally:
        if not conn.closed:
            try:
                conn.rollback()
            except psycopg2.Error:
                discard = True
        db_pool.putconn(conn, close=discard or bool(conn.closed))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
STATIC_DIR = Path(__file__).resolve().parent.parent / "fe"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root(conn = Depends(get_db)):
    """Redirect to frontend UI."""
    return RedirectResponse(url="/static/index.html")


@app.get("/api/health/ai")
def ai_health(conn = Depends(get_db)):
    """Lightweight AI system health without calling the LLM or database."""
    from ai.llm_provider import get_provider_chain
    from ai.skills import load_skills
    from be.mcp_server import get_tool_definitions

    provider_chain = get_provider_chain()
    providers = [
        {
            "priority": index + 1,
            "provider": provider,
            "model": model,
            "configured": bool(api_key),
        }
        for index, (provider, model, api_key) in enumerate(provider_chain)
    ]
    primary = providers[0] if providers else {}
    return {
        "status": "ok",
        "llm_configured": any(item["configured"] for item in providers),
        "provider": primary.get("provider"),
        "model": primary.get("model"),
        "provider_chain": providers,
        "embedding_model": "all-MiniLM-L6-v2",
        "skills_count": len(load_skills()),
        "mcp_tools": [tool["name"] for tool in get_tool_definitions()],
    }


@app.get("/api/health/db")
def db_health(conn = Depends(get_db)):
    """Confirm the backend, not the browser/user, owns the DB connection."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT current_database() AS database,
               current_user AS current_user,
               version() AS server_version
        """
    )
    row = cur.fetchone()
    cur.close()
    return {
        "status": "ok",
        "connection": public_config(),
        "database": row,
    }


@app.get("/api/health/schema")
def schema_health(conn = Depends(get_db)):
    """Check whether key warehouse objects are reachable."""
    required_tables = [
        "warehouse_warehouse.fact_job_postings",
        "warehouse_warehouse.dim_company",
        "warehouse_warehouse.job_embeddings",
        "warehouse_marts.mart_skill_demand",
        "warehouse_marts.mart_salary_benchmark",
    ]

    cur = conn.cursor()
    results = {}
    for table in required_tables:
        schema_name, table_name = table.split(".", 1)
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            )
            """,
            [schema_name, table_name],
        )
        results[table] = bool(cur.fetchone()[0])
    cur.close()
    return {
        "status": "ok" if all(results.values()) else "degraded",
        "tables": results,
    }


@app.get("/api/stats")
def get_stats(conn = Depends(get_db)):
    """Dashboard overview stats."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM warehouse_warehouse.fact_job_postings) as total_jobs,
            (SELECT COUNT(city_id) FROM warehouse_marts.mart_location_demand) as total_cities
    """)
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


@app.get("/api/jobs")
def get_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=2000),
    keyword: str = Query("", max_length=100),
    salary_band: str = Query("", max_length=50),
    ai_estimate: str = Query("true", max_length=10),
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
    if salary_band:
        conditions.append(
            """CASE
                WHEN f.salary_min IS NULL AND f.salary_max IS NULL THEN 'Negotiable'
                WHEN COALESCE(f.salary_max, f.salary_min) < 20000000 THEN 'Under 20M'
                WHEN COALESCE(f.salary_max, f.salary_min) < 40000000 THEN '20M-40M'
                WHEN COALESCE(f.salary_max, f.salary_min) < 70000000 THEN '40M-70M'
                ELSE '70M+'
            END = %s"""
        )
        params.append(salary_band)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count
    cur.execute(
        f"""SELECT COUNT(*) as total
            FROM warehouse_warehouse.fact_job_postings f
            LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
            {where_clause}""",
        params,
    )
    total = cur.fetchone()["total"]

    # Data
    cur.execute(
        f"""SELECT f.job_id::text AS source_id,
                   f.job_title AS title,
                   COALESCE(c.company_name, 'Unknown') AS company_name,
                   COALESCE(
                       f.working_locations->0->>'cityNameVI',
                       f.working_locations->0->>'cityName',
                       'Unknown'
                   ) AS primary_city,
                   CONCAT(COALESCE(f.salary_min::text, 'Negotiable'), ' - ', COALESCE(f.salary_max::text, 'Negotiable')) AS salary_text,
                   f.salary_min AS salary_min_vnd,
                   f.salary_max AS salary_max_vnd,
                   CASE
                       WHEN f.salary_min IS NULL AND f.salary_max IS NULL THEN 'Negotiable'
                       WHEN COALESCE(f.salary_max, f.salary_min) < 20000000 THEN 'Under 20M'
                       WHEN COALESCE(f.salary_max, f.salary_min) < 40000000 THEN '20M-40M'
                       WHEN COALESCE(f.salary_max, f.salary_min) < 70000000 THEN '40M-70M'
                       ELSE '70M+'
                   END AS salary_band,
                   COALESCE(l.level_name_vi, 'Unknown') AS job_level_vi,
                   CASE 
                       WHEN f.type_working_id = 1 THEN 'Toàn thời gian'
                       WHEN f.type_working_id = 2 THEN 'Bán thời gian'
                       WHEN f.type_working_id = 3 THEN 'Hợp đồng'
                       WHEN f.type_working_id = 4 THEN 'Tự do'
                       WHEN f.type_working_id = 5 THEN 'Thực tập'
                       ELSE 'Khác'
                   END AS work_mode,
                   '' AS source_url,
                   f.created_on AS posted_date
            FROM warehouse_warehouse.fact_job_postings f
            LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
            LEFT JOIN warehouse_warehouse.dim_job_level l ON f.job_level_id = l.job_level_id
            {where_clause}
            ORDER BY f.created_on DESC NULLS LAST
            LIMIT %s OFFSET %s""",
        params + [size, offset],
    )
    jobs = cur.fetchall()
    cur.close()

    results = []
    if ai_estimate.lower() == 'true':
        from ai.salary_predictor import predict_hidden_salary
        for job in jobs:
            d = dict(job)
            if d.get("salary_min_vnd") is None and d.get("salary_max_vnd") is None:
                pred = predict_hidden_salary(
                    title=d.get("title", ""),
                    city=d.get("primary_city", ""),
                    level=d.get("job_level_vi", ""),
                    work_mode=d.get("work_mode", ""),
                    skills=d.get("skills", "") or ""
                )
                if pred:
                    d["aiEstimatedSalary"] = pred.get("predicted_max_vnd")
            results.append(d)
    else:
        results = [dict(job) for job in jobs]

    return {"total": total, "page": page, "size": size, "data": results}


@app.get("/api/jobs/{job_id}")
def get_job_by_id(job_id: int, conn = Depends(get_db)):
    """Get detailed information for a single job posting."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        SELECT f.job_id AS source_id, f.job_title AS title, c.company_name, 
               (f.working_locations->0->>'cityNameVI') AS primary_city, 
               f.working_locations,
               f.salary_min AS salary_min_vnd, f.salary_max AS salary_max_vnd, 
               jl.level_name_vi AS job_level_vi,
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
        query = """
            SELECT f.job_id AS source_id, f.job_title AS title, c.company_name, 
                   (f.working_locations->0->>'cityNameVI') AS primary_city, 
                   f.salary_min AS salary_min_vnd, f.salary_max AS salary_max_vnd, jl.level_name_vi AS job_level_vi,
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
        SELECT f.job_id AS source_id, f.job_title AS title, c.company_name, 
               (f.working_locations->0->>'cityNameVI') AS primary_city, 
               f.salary_min AS salary_min_vnd, f.salary_max AS salary_max_vnd, jl.level_name_vi AS job_level_vi,
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
def get_top_skills(limit: int = Query(20, ge=1, le=200), conn = Depends(get_db)):
    """Top skills by job count."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT skill_name, SUM(job_count) AS total_jobs FROM warehouse_marts.mart_skill_demand GROUP BY skill_name ORDER BY total_jobs DESC LIMIT %s;",
        [limit],
    )
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/salary-by-title")
def get_salary_by_title(conn = Depends(get_db)):
    """Average salary by job category."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT skill_name, level_name_vi, median_salary_min, median_salary_max, sample_size FROM warehouse_marts.mart_salary_benchmark ORDER BY sample_size DESC LIMIT 50;")
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/search")
def semantic_search(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(50, ge=1, le=2000),
    ai_estimate: str = Query("true", max_length=10),
    conn = Depends(get_db)
):
    """Semantic search using pgvector cosine similarity via job_embeddings table (M10)."""
    m = get_model()
    # Normalize embeddings is REQUIRED for valid cosine distance search using <=> in pgvector
    query_vec = m.encode(q, normalize_embeddings=True).tolist()
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT f.job_id AS source_id, f.job_title AS title, c.company_name,
                  COALESCE(
                      f.working_locations->0->>'cityNameVI',
                      f.working_locations->0->>'cityName',
                      'Unknown'
                  ) AS primary_city,
                  f.salary_min AS salary_min_vnd,
                  f.salary_max AS salary_max_vnd,
                  CONCAT(f.salary_min, ' - ', f.salary_max) AS salary_text,
                  COALESCE(l.level_name_vi, 'Unknown') AS job_level_vi,
                  CASE 
                      WHEN f.type_working_id = 1 THEN 'Toàn thời gian'
                      WHEN f.type_working_id = 2 THEN 'Bán thời gian'
                      WHEN f.type_working_id = 3 THEN 'Hợp đồng'
                      WHEN f.type_working_id = 4 THEN 'Tự do'
                      WHEN f.type_working_id = 5 THEN 'Thực tập'
                      ELSE 'Khác'
                  END AS work_mode,
                  f.skills,
                  f.created_on AS posted_date,
                  '' AS salary_band, '' AS source_url,
                  1 - (e.embedding <=> %s::vector) AS similarity
           FROM warehouse_warehouse.fact_job_postings f
           LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
           LEFT JOIN warehouse_warehouse.dim_job_level l ON f.job_level_id = l.job_level_id
           JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
           ORDER BY (e.embedding <=> %s::vector) - (CASE WHEN f.job_title ILIKE %s OR c.company_name ILIKE %s THEN 0.2 ELSE 0 END) ASC
           LIMIT %s;""",
        [vec_str, vec_str, f"%{q}%", f"%{q}%", limit],
    )
    rows = cur.fetchall()
    cur.close()

    results = []
    if ai_estimate.lower() == 'true':
        from ai.salary_predictor import predict_hidden_salary
        for row in rows:
            d = dict(row)
            if d.get("salary_min_vnd") is None and d.get("salary_max_vnd") is None:
                pred = predict_hidden_salary(
                    title=d.get("title", ""),
                    city=d.get("primary_city", ""),
                    level=d.get("job_level_vi", ""),
                    work_mode=d.get("work_mode", ""),
                    skills=d.get("skills", "") or ""
                )
                if pred:
                    d["aiEstimatedSalary"] = pred.get("predicted_max_vnd")
            results.append(d)
    else:
        results = [dict(row) for row in rows]

    return {"query": q, "results": results}


@app.get("/api/jobs-by-level")
def get_jobs_by_level(conn = Depends(get_db)):
    """Job count by seniority level."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT lvl.level_name_vi, lvl.seniority_order, COUNT(*) AS job_count
        FROM warehouse_warehouse.fact_job_postings AS f
        LEFT JOIN warehouse_warehouse.dim_job_level AS lvl USING (job_level_id)
        GROUP BY lvl.level_name_vi, lvl.seniority_order
        ORDER BY lvl.seniority_order;
    """)
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/locations")
def get_locations(conn = Depends(get_db)):
    """Job count distribution by city for Pie Chart."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT l.city_name_vi, m.job_count
        FROM warehouse_marts.mart_location_demand m
        JOIN warehouse_warehouse.dim_location l ON m.city_id = l.city_id
        ORDER BY m.job_count DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


@app.get("/api/skill-trends")
def get_skill_trends(conn = Depends(get_db)):
    """Monthly trend for top 5 hottest skills."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
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
    """)
    rows = cur.fetchall()
    cur.close()
    return {"data": rows}


# ============================================================
# AI ENDPOINTS
# ============================================================

@app.post("/api/chat")
async def agent_chat(
    message: str = Query(..., min_length=1, max_length=1000),
    session_id: str = Query("default", max_length=100),
    conn = Depends(get_db)
):
    """Chat with TechJob AI Agent (ReAct Agent powered by Groq LLaMA)."""
    with timed_ai_event("api.chat", session_id=session_id, message_chars=len(message)):
        try:
            from ai.agent import chat as agent_chat_fn
            result = await agent_chat_fn(message, session_id)
            return {"ok": True, **result}
        except Exception as exc:
            log_ai_event(
                "api.chat.failed",
                session_id=session_id,
                error_type=type(exc).__name__,
                error=str(exc)[:300],
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "ok": False,
                    "error": "AI_CHAT_UNAVAILABLE",
                    "message": "AI chat is temporarily unavailable. Please try again later.",
                },
            ) from exc


@app.get("/api/chat/history/{session_id}")
def get_chat_history(session_id: str, conn = Depends(get_db)):
    """Get chat history for a session."""
    from ai.agent import get_chat_history
    history = get_chat_history(session_id)
    return {"session_id": session_id, "messages": history}


@app.get("/api/skills")
def list_agent_skills(conn = Depends(get_db)):
    """List project skill playbooks loaded by the AI agent."""
    from ai.skills import load_skills
    return {
        "data": [
            {
                "slug": skill.slug,
                "name": skill.name,
                "description": skill.description,
                "triggers": list(skill.triggers),
            }
            for skill in load_skills()
        ]
    }


@app.get("/api/skills/match")
def match_agent_skills(q: str = Query(..., min_length=1, max_length=500), conn = Depends(get_db)):
    """Return skill playbooks that match a user query."""
    from ai.skills import select_skills
    return {
        "query": q,
        "data": [
            {
                "slug": skill.slug,
                "name": skill.name,
                "description": skill.description,
                "triggers": list(skill.triggers),
            }
            for skill in select_skills(q)
        ],
    }


@app.post("/api/predict-salary")
def predict_salary(
    title: str = Query(..., min_length=2, max_length=200),
    city: str = Query("unknown", max_length=100),
    level: str = Query("unknown", max_length=50),
    work_mode: str = Query("unknown", max_length=20),
    skills: str = Query("", max_length=500),
    conn = Depends(get_db)
):
    """Predict salary range for a job with hidden/negotiable salary.
    Uses RandomForestRegressor trained on real job data. Label: 'AI Predicted'."""
    from ai.salary_predictor import predict_hidden_salary
    return predict_hidden_salary(title, city, level, work_mode, skills)


@app.post("/api/cover-letter")
async def generate_cover_letter_endpoint(
    cv_file: UploadFile = File(..., description="PDF file of candidate CV"),
    job_id: str = Form(None, description="Job ID to generate cover letter for"),
    job_title: str = Form("Software Engineer", description="Job Title"),
    company_name: str = Form("Company", description="Company Name"),
    job_description: str = Form("", description="Job Description text"),
    language: str = Form("Tiếng Việt", description="Output language"),
    conn = Depends(get_db)
):
    """Generate a personalized cover letter from CV (PDF) + Job Description."""
    from ai.cover_letter import generate_cover_letter, parse_cv_pdf, detect_cv_language
    cv_bytes = await cv_file.read()
    
    # Handle the mock UI CV gracefully
    if cv_file.filename == "dummy.pdf":
        cv_text = "Nguyễn Văn A\nSenior Frontend Developer\nKỹ năng: ReactJS, Node.js, TypeScript, UI/UX\nKinh nghiệm: 5 năm kinh nghiệm phát triển Web. Từng làm leader team Frontend tại TechCorp."
    else:
        try:
            cv_text = parse_cv_pdf(cv_bytes)
        except Exception as e:
            return {"error": f"Lỗi đọc file PDF: {str(e)}"}
            
    detected_language = detect_cv_language(cv_text)
    log_ai_event(
        "api.cover_letter.cv_parsed",
        detected_language=detected_language,
        cv_chars=len(cv_text),
        job_id=job_id,
        filename=cv_file.filename,
    )

    if job_description and len(job_description.strip()) > 10:
        return generate_cover_letter(cv_text, job_description, job_title, company_name, language)

    if not job_id:
        return {"error": "Missing job_id or job_description"}
        
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT f.job_title AS title,
                  COALESCE(c.company_name, %s) AS company_name,
                  f.job_description AS description,
                  f.job_requirement AS requirements
           FROM warehouse_warehouse.fact_job_postings f
           LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
           WHERE f.job_id::text = %s""",
        [company_name, job_id],
    )
    job = cur.fetchone()
    cur.close()
    if not job:
        return {"error": f"Job ID {job_id} not found in database."}

    jd_text = f"{job['description'] or ''}\n\n{job['requirements'] or ''}"
    return generate_cover_letter(cv_text, jd_text, job["title"], job["company_name"], language)


def _legacy_build_embeddings_disabled(batch_size: int = Query(8, ge=1, le=64)):
    """Build embeddings for jobs missing from job_embeddings table.
    Reuses the model already loaded in memory — no extra RAM needed."""
    model = get_model()

    cur = conn.cursor()

    # Ensure table exists
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_warehouse.job_embeddings (
            job_id      INTEGER PRIMARY KEY,
            embedding   vector(384),
            model_name  TEXT,
            embedded_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_embeddings_hnsw
        ON warehouse_warehouse.job_embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    conn.commit()

    # Fetch jobs without embeddings
    cur.execute("""
        SELECT f.job_id, f.job_title, f.job_description, f.job_requirement
        FROM warehouse_warehouse.fact_job_postings f
        LEFT JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
        WHERE e.job_id IS NULL
        ORDER BY f.job_id
    """)
    jobs = cur.fetchall()

    if not jobs:
        cur.close()
        return {"status": "ok", "message": "All jobs already have embeddings", "processed": 0}

    total = 0
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        texts = []
        ids = []
        for job_id, title, desc, req in batch:
            parts = []
            if title:
                parts.append(f"Title: {title}")
            if desc:
                parts.append(f"Description: {desc[:500]}")
            if req:
                parts.append(f"Requirements: {req[:300]}")
            text = " | ".join(parts) if parts else ""
            if text:
                texts.append(text)
                ids.append(job_id)

        if not texts:
            continue

        embeddings = model.encode(texts, show_progress_bar=False, batch_size=batch_size)

        for job_id, emb in zip(ids, embeddings):
            vec_str = "[" + ",".join(str(float(x)) for x in emb) + "]"
            cur.execute(
                """INSERT INTO warehouse_warehouse.job_embeddings (job_id, embedding, model_name, embedded_at)
                   VALUES (%s, %s::vector, %s, NOW())
                   ON CONFLICT (job_id) DO UPDATE
                   SET embedding = EXCLUDED.embedding, model_name = EXCLUDED.model_name, embedded_at = NOW();""",
                [job_id, vec_str, "all-MiniLM-L6-v2"]
            )
        conn.commit()
        total += len(ids)

    cur.close()
    return {"status": "ok", "processed": total, "total_jobs": len(jobs)}
@app.post("/api/train-salary-model")
def train_salary_model(conn = Depends(get_db)):
    """Retrain the salary prediction model with latest data (admin endpoint)."""
    from ai.salary_predictor import train
    result = train()
    if result is None:
        return {"status": "skipped", "message": "Not enough training data"}
    return {
        "status": "success",
        "training_samples": result["training_samples"],
        "r2_min": result["r2_min"],
        "r2_max": result["r2_max"],
        "trained_at": result["trained_at"],
    }


@app.post("/api/build-embeddings")
def build_embeddings(batch_size: int = Query(8, ge=1, le=64), conn = Depends(get_db)):
    """Build embeddings for jobs missing from job_embeddings table.
    Reuses the model already loaded in memory — no extra RAM needed."""
    model = get_model()

    cur = conn.cursor()

    # Ensure table exists
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_warehouse.job_embeddings (
            job_id      INTEGER PRIMARY KEY,
            embedding   vector(384),
            model_name  TEXT,
            embedded_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_embeddings_hnsw
        ON warehouse_warehouse.job_embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    conn.commit()

    # Fetch jobs without embeddings
    cur.execute("""
        SELECT f.job_id, f.job_title, f.job_description, f.job_requirement
        FROM warehouse_warehouse.fact_job_postings f
        LEFT JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
        WHERE e.job_id IS NULL
        ORDER BY f.job_id
    """)
    jobs = cur.fetchall()

    if not jobs:
        cur.close()
        return {"status": "ok", "message": "All jobs already have embeddings", "processed": 0}

    total = 0
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        texts = []
        ids = []
        for job_id, title, desc, req in batch:
            parts = []
            if title:
                parts.append(f"Title: {title}")
            if desc:
                parts.append(f"Description: {desc[:500]}")
            if req:
                parts.append(f"Requirements: {req[:300]}")
            text = " | ".join(parts) if parts else ""
            if text:
                texts.append(text)
                ids.append(job_id)

        if not texts:
            continue

        embeddings = model.encode(texts, show_progress_bar=False, batch_size=batch_size)

        for job_id, emb in zip(ids, embeddings):
            vec_str = "[" + ",".join(str(float(x)) for x in emb) + "]"
            cur.execute(
                """INSERT INTO warehouse_warehouse.job_embeddings (job_id, embedding, model_name, embedded_at)
                   VALUES (%s, %s::vector, %s, NOW())
                   ON CONFLICT (job_id) DO UPDATE
                   SET embedding = EXCLUDED.embedding, model_name = EXCLUDED.model_name, embedded_at = NOW();""",
                [job_id, vec_str, "all-MiniLM-L6-v2"]
            )
        conn.commit()
        total += len(ids)

    cur.close()
    return {"status": "ok", "processed": total, "total_jobs": len(jobs)}
