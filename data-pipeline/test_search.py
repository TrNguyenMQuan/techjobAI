import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer
from ai.db_config import psycopg2_kwargs

print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

q = "Backend Engineer"
print(f"Encoding query: {q}")
query_vec = model.encode(q, normalize_embeddings=True).tolist()
vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

print("Connecting to NeonDB...")
conn = psycopg2.connect(**psycopg2_kwargs())
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("Executing search...")
cur.execute(
    """SELECT f.job_id, f.job_title,
              1 - (e.embedding <=> %s::vector) AS similarity
       FROM warehouse_warehouse.fact_job_postings f
       JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
       ORDER BY e.embedding <=> %s::vector
       LIMIT 3;""",
    [vec_str, vec_str],
)
rows = cur.fetchall()

print("Results:")
for r in rows:
    print(r)

cur.close()
conn.close()
print("Done!")
