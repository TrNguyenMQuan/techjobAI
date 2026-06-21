"""
Cover Letter Generator — TechJob AI
Generates personalized cover letters using LLM (Groq) by matching
candidate CV content with job description.

Features:
- PDF CV parsing via pdfplumber
- Anti-hallucination prompt engineering
- Professional Vietnamese/English tone

Usage:
    from ai.cover_letter import parse_cv_pdf, generate_cover_letter
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


# ============================================================
# PDF PARSING
# ============================================================
def parse_cv_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF CV file.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        Extracted text content as a single string.
    """
    import pdfplumber
    import io

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError("Could not extract text from PDF. The file may be image-based or empty.")

    return full_text


# ============================================================
# COVER LETTER GENERATION
# ============================================================

COVER_LETTER_PROMPT_TEMPLATE = """Bạn là một chuyên gia Tuyển dụng (Headhunter) cấp cao và là chuyên gia viết thư ứng tuyển (Cover Letter) chuẩn quốc tế.

## NHIỆM VỤ
Viết một Cover Letter cá nhân hóa, mạnh mẽ, và có tính thuyết phục cao dựa trên CV của ứng viên và Mô tả công việc (JD) bên dưới.

## QUY TẮC BẮT BUỘC (TUYỆT ĐỐI TUÂN THỦ)
1. **SỬ DỤNG TÊN THẬT:** BẮT BUỘC đọc CV để trích xuất tên thật của ứng viên và xưng hô bằng tên thật đó. CHỈ DÙNG `[Tên của bạn]` nếu trong CV tuyệt đối không có bất kỳ tên người nào.
2. **CHỐNG DỮ LIỆU RÁC (ANTI-TEMPLATE):** Lọc bỏ các cụm từ mẫu vô nghĩa như "Forename SURNAME", "123 Street", "Lorem Ipsum" (nếu có).
3. **CẤM LẶP TỪ:** Không sử dụng các mẫu câu nhàm chán như "Tôi tin rằng", "Tôi đã có kinh nghiệm", "Tôi hân hạnh". Sử dụng các động từ chỉ hành động (Action Verbs) mạnh mẽ.
4. **TRUNG THỰC:** CHỈ sử dụng thông tin có trong CV gốc. KHÔNG bịa đặt kỹ năng hoặc số năm kinh nghiệm ảo.
5. **ĐỘ DÀI & NGÔN NGỮ:** Tối đa 350 từ. Viết bằng {language}. Tông giọng chuyên nghiệp, tự tin, định hướng kết quả.

## CẤU TRÚC THƯ (CHUẨN QUỐC TẾ)
1. **Hook (Mở bài thu hút - 1 đoạn):** Vào thẳng vấn đề. Thể hiện sự hào hứng và hiểu biết về {company_name}. Nêu bật ngay giá trị cốt lõi bạn mang lại cho vị trí {job_title}.
2. **Value Proposition (Giá trị mang lại - Bullet points):** BẮT BUỘC sử dụng 2-3 gạch đầu dòng (Bullet points) ngắn gọn để đối chiếu các kỹ năng/thành tựu xuất sắc nhất trong CV khớp hoàn toàn với yêu cầu của JD. Bắt đầu mỗi gạch đầu dòng bằng một Action Verb.
3. **Call to Action (Kết bài - 1 đoạn):** Khẳng định sự phù hợp với văn hóa/mục tiêu của công ty và mở lời cho một cuộc phỏng vấn.

## THÔNG TIN ỨNG VIÊN (từ CV)
```
{cv_text}
```

## MÔ TẢ CÔNG VIỆC (JD)
- **Vị trí:** {job_title}
- **Công ty:** {company_name}
- **Nội dung:**
```
{job_description}
```

## Cover Letter:
"""


def generate_cover_letter(
    cv_text: str,
    job_description: str,
    job_title: str,
    company_name: str,
    language: str = "Tiếng Việt",
) -> dict:
    """
    Generate a personalized cover letter using LLM.

    Args:
        cv_text: Extracted text from candidate's CV.
        job_description: Job description / requirements text.
        job_title: Title of the position.
        company_name: Name of the hiring company.
        language: Output language ("Tiếng Việt" or "English").

    Returns:
        dict with 'cover_letter', 'matched_skills', 'word_count'.
    """
    if not GROQ_API_KEY:
        return {
            "error": "Groq API key not configured. Set GROQ_API_KEY in .env file.",
        }

    from langchain_groq import ChatGroq

    # Truncate inputs to manage token usage
    cv_truncated = cv_text[:3000] if len(cv_text) > 3000 else cv_text
    jd_truncated = job_description[:2000] if len(job_description) > 2000 else job_description

    prompt = COVER_LETTER_PROMPT_TEMPLATE.format(
        cv_text=cv_truncated,
        job_description=jd_truncated,
        job_title=job_title,
        company_name=company_name,
        language=language,
    )

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=1500,
        api_key=GROQ_API_KEY,
    )

    try:
        response = llm.invoke(prompt)
        cover_letter_text = response.content.strip()

        # Extract matched skills (simple keyword matching)
        matched = _extract_matched_skills(cv_text, job_description)

        return {
            "cover_letter": cover_letter_text,
            "matched_skills": matched,
            "word_count": len(cover_letter_text.split()),
            "language": language,
            "job_title": job_title,
            "company_name": company_name,
        }
    except Exception as e:
        return {"error": f"Cover letter generation failed: {str(e)}"}


def _extract_matched_skills(cv_text: str, jd_text: str) -> list:
    """Simple keyword-based skill matching between CV and JD."""
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Git", "CI/CD", "Jenkins", "GitHub Actions",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
        "Apache Spark", "Kafka", "Airflow", "dbt",
        "Agile", "Scrum", "REST API", "GraphQL", "Microservices",
        "Linux", "Nginx", "Power BI", "Tableau",
    ]

    cv_lower = cv_text.lower()
    jd_lower = jd_text.lower()

    matched = []
    for skill in common_skills:
        if skill.lower() in cv_lower and skill.lower() in jd_lower:
            matched.append(skill)

    return matched


def generate_cover_letter_from_job_id(
    cv_bytes: bytes,
    job_id: str,
    language: str = "Tiếng Việt",
) -> dict:
    """
    Convenience function: parse CV + fetch job from DB + generate cover letter.

    Args:
        cv_bytes: Raw PDF bytes.
        job_id: Job ID in the database (source_id).
        language: Output language.

    Returns:
        dict with cover letter result.
    """
    import psycopg2
    import psycopg2.extras

    # Parse CV
    try:
        cv_text = parse_cv_pdf(cv_bytes)
    except Exception as e:
        return {"error": f"File PDF không hợp lệ hoặc bị hỏng: {str(e)}"}

    # Fetch job details
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_USER = os.getenv("POSTGRES_USER", "techjob")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
    DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

    conn = psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT),
        user=DB_USER, password=DB_PASS,
        dbname=DB_NAME,
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT title, company_name, description, requirements
        FROM warehouse_warehouse.fact_job
        WHERE source_id = %s OR job_id::text = %s
        """,
        [job_id, job_id],
    )
    job = cur.fetchone()
    cur.close()
    conn.close()

    if not job:
        return {"error": f"Job ID {job_id} not found in database."}

    jd_text = f"{job['description'] or ''}\n\n{job['requirements'] or ''}"

    return generate_cover_letter(
        cv_text=cv_text,
        job_description=jd_text,
        job_title=job["title"],
        company_name=job["company_name"],
        language=language,
    )
