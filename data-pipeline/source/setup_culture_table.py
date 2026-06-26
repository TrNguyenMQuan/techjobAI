"""
Setup Company Culture Table — TechJob AI
Creates warehouse_warehouse.company_culture table with pgvector embedding
and seeds sample data for RAG Culture tool.

Usage:
    python source/setup_culture_table.py
"""

import json
from pathlib import Path
from dotenv import load_dotenv
import psycopg
from ai.db_config import psycopg3_kwargs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_conn():
    return psycopg.connect(**psycopg3_kwargs())


# ── Seed data: sample culture reviews for major VN IT companies ──────────────
SEED_DATA = [
    {
        "company_name": "FPT Software",
        "culture_text": (
            "FPT Software có văn hóa làm việc năng động, khuyến khích sáng tạo và đổi mới. "
            "Công ty tổ chức nhiều hoạt động team building, hackathon nội bộ và chương trình đào tạo. "
            "Môi trường làm việc quốc tế với nhiều dự án outsourcing cho khách hàng Nhật, Mỹ, EU. "
            "Chế độ phúc lợi tốt bao gồm bảo hiểm sức khỏe, thưởng dự án và cơ hội onsite nước ngoài."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "VNG Corporation",
        "culture_text": (
            "VNG nổi tiếng với văn hóa startup trong một tập đoàn lớn. Nhân viên được khuyến khích "
            "tự do sáng tạo, thử nghiệm công nghệ mới. Văn phòng hiện đại tại Quận 7, TP.HCM với "
            "không gian mở. Chế độ lương thưởng cạnh tranh, ESOP cho nhân viên lâu năm. "
            "Tuy nhiên, deadline dự án game có thể áp lực cao vào mùa cao điểm."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "Tiki",
        "culture_text": (
            "Tiki có môi trường làm việc trẻ trung, tốc độ nhanh đặc trưng của e-commerce. "
            "Văn hóa data-driven, các quyết định đều dựa trên dữ liệu. Đội ngũ kỹ thuật mạnh "
            "với nhiều thử thách về scalability và high traffic. Work-life balance có thể bị ảnh hưởng "
            "vào các đợt sale lớn như 11/11, 12/12."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "Momo",
        "culture_text": (
            "Momo (M_Service) có văn hóa fintech năng động, tập trung vào đổi mới thanh toán số. "
            "Đội ngũ tech được đầu tư mạnh với nhiều dự án AI/ML trong lĩnh vực tài chính. "
            "Chế độ đãi ngộ tốt, văn phòng hiện đại. Môi trường làm việc chuyên nghiệp, "
            "yêu cầu cao về bảo mật và compliance trong lĩnh vực tài chính."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "Shopee Vietnam",
        "culture_text": (
            "Shopee có văn hóa làm việc cường độ cao nhưng học hỏi rất nhiều. Quy trình quản lý "
            "theo chuẩn Singapore, làm việc với các team đa quốc gia. Lương và thưởng thuộc top "
            "thị trường. Tuy nhiên, văn hóa OT (overtime) khá phổ biến, đặc biệt vào mùa sale."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "Grab Vietnam",
        "culture_text": (
            "Grab Việt Nam có văn hóa làm việc theo kiểu startup unicorn - nhanh, linh hoạt nhưng "
            "chuyên nghiệp. Chính sách remote/hybrid linh hoạt. Đội ngũ kỹ thuật làm việc trên "
            "các bài toán real-time lớn (maps, payments, logistics). Phúc lợi tốt bao gồm "
            "cổ phiếu, bảo hiểm cao cấp và các chương trình wellness."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "KMS Technology",
        "culture_text": (
            "KMS Technology nổi tiếng với văn hóa 'People First'. Công ty đầu tư mạnh vào đào tạo "
            "nhân viên với KMS Academy. Chế độ phúc lợi toàn diện, work-life balance tốt. "
            "Các dự án chủ yếu cho thị trường Mỹ, sử dụng công nghệ hiện đại. Quản lý theo "
            "phương pháp Agile/Scrum chuẩn."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "NashTech Vietnam",
        "culture_text": (
            "NashTech có văn hóa làm việc kiểu Anh (UK-based), chuyên nghiệp và quy trình rõ ràng. "
            "Đội ngũ quản lý có nhiều kinh nghiệm quốc tế. Công ty có chương trình NashTech University "
            "đào tạo nội bộ. Dự án đa dạng từ .NET, Java đến Cloud & Data. "
            "Môi trường phù hợp cho người thích sự ổn định và phát triển bài bản."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "TMA Solutions",
        "culture_text": (
            "TMA Solutions là một trong những công ty outsourcing lâu đời nhất Việt Nam. "
            "Văn hóa gia đình, gắn bó lâu dài. Nhiều nhân viên làm việc trên 10 năm. "
            "Dự án đa dạng với khách hàng từ Nhật, Mỹ, Châu Âu. Chế độ đào tạo tốt cho fresher. "
            "Tuy nhiên, mức lương có thể thấp hơn so với startup và big tech."
        ),
        "source": "employee_review",
    },
    {
        "company_name": "Zalo (VNG)",
        "culture_text": (
            "Zalo, sản phẩm chủ lực của VNG, có đội ngũ kỹ thuật hàng đầu Việt Nam. "
            "Làm việc trên các bài toán AI/ML phức tạp (NLP, Computer Vision, Recommendation). "
            "Văn hóa kỹ thuật mạnh, khuyến khích nghiên cứu và publish paper. "
            "Lương cạnh tranh, nhưng áp lực về performance và KPI khá cao."
        ),
        "source": "employee_review",
    },
]


def setup():
    conn = get_conn()
    cur = conn.cursor()

    # Ensure schema exists
    cur.execute("CREATE SCHEMA IF NOT EXISTS warehouse_warehouse;")

    # Create company_culture table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_warehouse.company_culture (
            id              SERIAL PRIMARY KEY,
            company_name    TEXT NOT NULL,
            culture_text    TEXT NOT NULL,
            embedding       vector(384),
            source          TEXT DEFAULT 'employee_review',
            created_at      TIMESTAMP DEFAULT NOW()
        );
    """)

    # Check if data already exists
    cur.execute("SELECT COUNT(*) FROM warehouse_warehouse.company_culture;")
    count = cur.fetchone()[0]

    if count == 0:
        print("[INFO] Seeding company culture data...")
        for item in SEED_DATA:
            cur.execute(
                """
                INSERT INTO warehouse_warehouse.company_culture (company_name, culture_text, source)
                VALUES (%s, %s, %s)
                """,
                (item["company_name"], item["culture_text"], item["source"]),
            )
        print(f"[INFO] Seeded {len(SEED_DATA)} culture records.")
    else:
        print(f"[INFO] Culture table already has {count} records. Skipping seed.")

    conn.commit()
    cur.close()
    conn.close()
    print("Table warehouse_warehouse.company_culture is ready.")


def embed_culture():
    """Generate embeddings for culture records that don't have one yet."""
    from sentence_transformers import SentenceTransformer

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, culture_text FROM warehouse_warehouse.company_culture
        WHERE embedding IS NULL
    """)
    rows = cur.fetchall()

    if not rows:
        print("[INFO] All culture records already have embeddings.")
        conn.close()
        return

    print(f"[INFO] Embedding {len(rows)} culture records...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    texts = [r[1] for r in rows]
    ids = [r[0] for r in rows]
    embeddings = model.encode(texts, show_progress_bar=True)

    for record_id, emb in zip(ids, embeddings):
        vec_str = "[" + ",".join(str(float(x)) for x in emb) + "]"
        cur.execute(
            "UPDATE warehouse_warehouse.company_culture SET embedding = %s WHERE id = %s",
            (vec_str, record_id),
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"[INFO] Embedded {len(rows)} culture records.")


if __name__ == "__main__":
    setup()
    embed_culture()
