"""
FastAPI Backend — TechJob AI
Serves job data, analytics, semantic search, AI agent chat,
salary prediction, and cover letter generation from PostgreSQL + pgvector.
"""

from fastapi import FastAPI, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
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

# Model for semantic search (cached globally)
_search_model = None

def get_model():
    global _search_model
    if _search_model is None:
        _search_model = SentenceTransformer("BAAI/bge-m3")
    return _search_model

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
    description="IT Job Market Analytics, Semantic Search, AI Agent Chat, Salary Prediction & Cover Letter Generation",
    version="2.0.0",
)

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
def root():
    """Redirect to frontend UI."""
    return RedirectResponse(url="/static/index.html")


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
    """Semantic search using pgvector cosine similarity via job_embeddings table (M10)."""
    m = get_model()
    query_vec = m.encode(q).tolist()
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT f.source_id, f.title, f.company_name, f.primary_city,
                  f.salary_text, f.salary_band, f.source_url,
                  1 - (e.embedding <=> %s::vector) AS similarity
           FROM warehouse_warehouse.fact_job f
           JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
           ORDER BY e.embedding <=> %s::vector
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


# ============================================================
# AI ENDPOINTS
# ============================================================

@app.post("/api/chat")
async def agent_chat(
    message: str = Query(..., min_length=1, max_length=1000),
    session_id: str = Query("default", max_length=100),
):
    """Chat with TechJob AI Agent (ReAct Agent powered by Groq LLaMA)."""
    from ai.agent import chat as agent_chat_fn
    result = await agent_chat_fn(message, session_id)
    return result


@app.get("/api/chat/history/{session_id}")
def get_chat_history(session_id: str):
    """Get chat history for a session."""
    from ai.agent import get_chat_history
    history = get_chat_history(session_id)
    return {"session_id": session_id, "messages": history}


@app.post("/api/predict-salary")
def predict_salary(
    title: str = Query(..., min_length=2, max_length=200),
    city: str = Query("unknown", max_length=100),
    level: str = Query("unknown", max_length=50),
    work_mode: str = Query("unknown", max_length=20),
    skills: str = Query("", max_length=500),
):
    """Predict salary range for a job with hidden/negotiable salary.
    Uses RandomForestRegressor trained on real job data. Label: 'AI Predicted'."""
    from ai.salary_predictor import predict_hidden_salary
    return predict_hidden_salary(title, city, level, work_mode, skills)


@app.post("/api/cover-letter")
async def generate_cover_letter_endpoint(
    cv_file: UploadFile = File(..., description="PDF file of candidate CV"),
    job_id: str = Form(..., description="Job ID to generate cover letter for"),
    language: str = Form("Tiếng Việt", description="Output language"),
):
    """Generate a personalized cover letter from CV (PDF) + Job Description.
    Uses LLM with anti-hallucination prompting."""
    from ai.cover_letter import generate_cover_letter_from_job_id
    cv_bytes = await cv_file.read()
    result = generate_cover_letter_from_job_id(cv_bytes, job_id, language)
    return result


@app.post("/api/train-salary-model")
def train_salary_model():
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
