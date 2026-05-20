"""
Embedding Service: Encode job descriptions into 768-dim vectors
using Sentence-Transformers (all-MiniLM-L6-v2).

Usage:
    python pipeline/ml/embedding/embedding_service.py
"""

import os
import time
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

load_dotenv(PROJECT_ROOT / "infra/.env")

DB_USER = os.getenv("POSTGRES_USER", "techjob")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64  # Số job encode mỗi batch
VECTOR_DIM = 384  # all-MiniLM-L6-v2 output 384 dimensions (not 768!)


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

    # Parse skills JSON string
    if skills:
        try:
            import json
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
def main():
    print(f"{'=' * 60}")
    print(f"  Embedding Pipeline — {datetime.now().isoformat()}")
    print(f"{'=' * 60}")

    # 1. Connect to DB
    engine = create_engine(DATABASE_URL)

    # 2. Check if embedding column exists, create if not
    with engine.begin() as conn:
        # Ensure pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'warehouse_warehouse'
              AND table_name = 'fact_job'
              AND column_name = 'embedding'
        """))
        if result.fetchone() is None:
            print("[INFO] Adding 'embedding' column to fact_job...")
            conn.execute(text(f"""
                ALTER TABLE warehouse_warehouse.fact_job
                ADD COLUMN embedding vector({VECTOR_DIM});
            """))
            print("[INFO] Column added.")
        else:
            print("[INFO] Column 'embedding' already exists.")

    # 3. Fetch jobs WITHOUT embeddings (incremental)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT job_id, title, description, requirements, source_id
            FROM warehouse_warehouse.fact_job
            WHERE embedding IS NULL
            ORDER BY job_id
        """))
        jobs = result.fetchall()

    print(f"[INFO] Found {len(jobs)} jobs without embeddings")

    if not jobs:
        print("[INFO] All jobs already have embeddings. Nothing to do.")
        return

    # 4. Also fetch skills for each job
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT f.source_id, s.skills_json
            FROM warehouse_staging.stg_jobs s
            JOIN warehouse_warehouse.fact_job f ON f.source_id = s.source_id
            WHERE f.embedding IS NULL
        """))
        skills_map = {row[0]: row[1] for row in result.fetchall()}

    # 5. Load model
    model = load_model()

    # 6. Process in batches
    total_processed = 0
    total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        # Prepare texts
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

        # Save to DB
        with engine.begin() as conn:
            for job_id, embedding in zip(ids, embeddings):
                vector_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
                conn.execute(
                    text("""
                        UPDATE warehouse_warehouse.fact_job
                        SET embedding = :embedding
                        WHERE job_id = :job_id
                    """),
                    {"embedding": vector_str, "job_id": job_id}
                )

        total_processed += len(ids)
        print(f"  Batch {batch_num}/{total_batches}: encoded {len(ids)} jobs (total: {total_processed})")

    # 7. Create HNSW index for fast similarity search
    with engine.begin() as conn:
        # Check if index exists
        result = conn.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'fact_job'
              AND indexname = 'idx_fact_job_embedding_hnsw'
        """))
        if result.fetchone() is None:
            print("[INFO] Creating HNSW index on embedding column...")
            conn.execute(text(f"""
                CREATE INDEX idx_fact_job_embedding_hnsw
                ON warehouse_warehouse.fact_job
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """))
            print("[INFO] HNSW index created.")
        else:
            print("[INFO] HNSW index already exists.")

    # 8. Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) AS total_jobs,
                COUNT(embedding) AS jobs_with_embedding
            FROM warehouse_warehouse.fact_job
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
    main()
