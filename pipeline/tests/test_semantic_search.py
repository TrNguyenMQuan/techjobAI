"""
Test semantic search: tìm job tương tự bằng cosine similarity.

Usage:
    python pipeline/tests/test_semantic_search.py "python data pipeline"
"""

import sys
import os
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("infra/.env")

DB_USER = os.getenv("POSTGRES_USER", "techjob")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def main():
    # Query from user
    query = sys.argv[1] if len(sys.argv) > 1 else "data engineer python ETL pipeline"

    print(f"{'=' * 60}")
    print(f"  Semantic Search Test")
    print(f"  Query: \"{query}\"")
    print(f"{'=' * 60}\n")

    # 1. Encode query
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_vector = model.encode(query)
    vector_str = "[" + ",".join(str(float(x)) for x in query_vector) + "]"

    # 2. Search by cosine similarity

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                title,
                source_id,
                job_level AS experience_level,
                salary_text AS salary_display,
                1 - (embedding <=> cast(:query_vec AS vector)) AS similarity
            FROM warehouse_warehouse.fact_job
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> cast(:query_vec AS vector)
            LIMIT 10
        """), {"query_vec": vector_str})

        rows = result.fetchall()


    print(f"Top 10 kết quả:\n")
    print(f"{'#':<3} {'Similarity':<12} {'Title':<55} {'Salary':<15}")
    print("-" * 85)
    for i, row in enumerate(rows, 1):
        title = row[0][:52] + "..." if len(row[0]) > 55 else row[0]
        print(f"{i:<3} {row[4]:.4f}       {title:<55} {row[3] or 'N/A':<15}")


if __name__ == "__main__":
    main()
