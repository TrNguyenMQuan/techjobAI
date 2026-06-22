"""
Embedding Pipeline (M10 Architecture) — TechJob AI
Encode job descriptions into vectors using Sentence-Transformers
and UPSERT into the dedicated job_embeddings table.

The job_embeddings table is independent from dbt, so embeddings
survive dbt full-refresh cycles.

Usage:
    python ai/embedding.py
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("POSTGRES_USER", "techjob")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32  # Can use larger batches for lighter model
VECTOR_DIM = 384  # all-MiniLM-L6-v2 output dimension


# ============================================================
# LOAD MODEL
# ============================================================
def load_model():
    """Load Sentence-Transformer model."""
    print(f"[INFO] Loading model: {MODEL_NAME}")
    start = time.time()
    model = SentenceTransformer(MODEL_NAME)
    print(f"[INFO] Model loaded in {time.time() - start:.1f}s")
    return model


# ============================================================
# PREPARE TEXT FOR EMBEDDING
# ============================================================
def prepare_text(title: str, description: str, requirements: str, skills: str) -> str:
    """
    Combine job fields into one text for embedding.
    Format: "Title: ... | Skills: ... | Description: ... | Requirements: ..."
    """
    parts = []

    if title:
        parts.append(f"Title: {title}")

    if skills:
        try:
            skill_list = json.loads(skills)
            if skill_list:
                parts.append(f"Skills: {', '.join(skill_list)}")
        except (json.JSONDecodeError, TypeError):
            pass

    if description:
        # Truncate to first 500 chars to keep embedding focused
        parts.append(f"Description: {description[:500]}")

    if requirements:
        parts.append(f"Requirements: {requirements[:300]}")

    return " | ".join(parts) if parts else ""


# ============================================================
# MAIN PIPELINE
# ============================================================
def run():
    print(f"{'=' * 60}")
    print(f"  Embedding Pipeline (M10 Architecture) — {datetime.now().isoformat()}")
    print(f"{'=' * 60}")

    engine = create_engine(DATABASE_URL)

    # 1. Ensure job_embeddings table exists
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse_warehouse;"))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS warehouse_warehouse.job_embeddings (
                job_id      INTEGER PRIMARY KEY,
                embedding   vector({VECTOR_DIM}),
                model_name  TEXT,
                embedded_at TIMESTAMP DEFAULT NOW()
            );
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_job_embeddings_hnsw
            ON warehouse_warehouse.job_embeddings USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """))

    # 2. Fetch jobs WITHOUT embeddings (incremental via LEFT JOIN)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT f.job_id, f.title, f.description, f.requirements, f.source_id
            FROM warehouse_warehouse.fact_job f
            LEFT JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
            WHERE e.job_id IS NULL
            ORDER BY f.job_id
        """))
        jobs = result.fetchall()

    print(f"[INFO] Found {len(jobs)} jobs without embeddings")

    if not jobs:
        print("[INFO] All jobs already have embeddings. Nothing to do.")
        return

    # 3. Also fetch skills for each job from staging
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT f.source_id, s.skills
            FROM warehouse_staging.stg_jobs s
            JOIN warehouse_warehouse.fact_job f ON f.source_id = ('vnw_' || s.job_id::text)
            LEFT JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
            WHERE e.job_id IS NULL
        """))
        skills_map = {}
        for row in result.fetchall():
            source_id, skills_json = row
            try:
                if skills_json:
                    skills_arr = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
                    skill_names = [s.get("skillName", "") for s in skills_arr if isinstance(s, dict) and s.get("skillName")]
                    skills_map[source_id] = json.dumps(skill_names, ensure_ascii=False)
            except Exception:
                skills_map[source_id] = ""

    # 4. Load model
    model = load_model()

    # 5. Process in batches and UPSERT into job_embeddings
    total_processed = 0
    total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        texts = []
        ids = []
        for row in batch:
            job_id, title, description, requirements, source_id = row
            skills_json = skills_map.get(source_id, "")
            text_input = prepare_text(
                title or "",
                description or "",
                requirements or "",
                skills_json or ""
            )
            if text_input:
                texts.append(text_input)
                ids.append(job_id)

        if not texts:
            continue

        # Encode
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=BATCH_SIZE)

        # UPSERT to job_embeddings table
        with engine.begin() as conn:
            for job_id, embedding in zip(ids, embeddings):
                vector_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
                conn.execute(
                    text("""
                        INSERT INTO warehouse_warehouse.job_embeddings (job_id, embedding, model_name, embedded_at)
                        VALUES (:job_id, :embedding, :model_name, NOW())
                        ON CONFLICT (job_id) DO UPDATE
                        SET embedding = EXCLUDED.embedding,
                            model_name = EXCLUDED.model_name,
                            embedded_at = NOW();
                    """),
                    {"job_id": job_id, "embedding": vector_str, "model_name": MODEL_NAME}
                )

        total_processed += len(ids)
        print(f"  Batch {batch_num}/{total_batches}: encoded {len(ids)} jobs (total: {total_processed})")

    # 6. Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) AS total_jobs,
                COUNT(e.job_id) AS jobs_with_embedding
            FROM warehouse_warehouse.fact_job f
            LEFT JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
        """))
        row = result.fetchone()
        print(f"\n{'=' * 60}")
        print(f"  DONE!")
        print(f"  Total jobs          : {row[0]}")
        print(f"  Jobs with embedding : {row[1]}")
        print(f"  Vector dimension    : {VECTOR_DIM}")
        print(f"  Model               : {MODEL_NAME}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    run()
