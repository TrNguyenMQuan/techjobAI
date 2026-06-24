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
from typing import Optional
import re
import unicodedata

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

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

VIETNAMESE_DIACRITICS = set(
    "ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệ"
    "íìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
)

VIETNAMESE_STOPWORDS = {
    "và", "của", "cho", "với", "trong", "tôi", "đã", "là", "các", "kỹ",
    "năng", "kinh", "nghiệm", "học", "vấn", "dự", "án", "làm", "việc",
}

ENGLISH_CV_TERMS = {
    "experience", "education", "skills", "projects", "activities", "summary",
    "objective", "technologies", "programming", "languages", "interests",
    "developed", "built", "participated", "university", "volunteer",
}


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def detect_cv_language(cv_text: str) -> str:
    """Detect whether the CV is primarily Vietnamese or English.

    Product rule: the cover letter must be generated in the same language as
    the CV. This deterministic detector keeps that decision stable and easy to
    test instead of asking the LLM to infer it every time.
    """
    if not cv_text or not cv_text.strip():
        return "English"

    lower = cv_text.lower()
    no_accents = _strip_accents(cv_text)
    words = re.findall(r"[a-zA-ZÀ-ỹ]+", lower)
    word_count = max(len(words), 1)

    diacritic_count = sum(1 for ch in lower if ch in VIETNAMESE_DIACRITICS)
    vietnamese_word_hits = sum(1 for word in words if word in VIETNAMESE_STOPWORDS)
    english_term_hits = sum(1 for term in ENGLISH_CV_TERMS if term in no_accents)

    if diacritic_count >= 8 or vietnamese_word_hits >= 4:
        return "Tiếng Việt"

    if english_term_hits >= 2 and diacritic_count / word_count < 0.03:
        return "English"

    return "Tiếng Việt" if diacritic_count > 0 or vietnamese_word_hits > 0 else "English"


def resolve_cover_letter_language(cv_text: str, requested_language: str = "Auto") -> str:
    """Resolve the final output language. CV language always wins."""
    return detect_cv_language(cv_text)

COVER_LETTER_PROMPT_TEMPLATE = """You are an expert Headhunter and professional Cover Letter writer.

## TASK
Write a highly personalized, compelling Cover Letter based on the candidate's CV and the Job Description (JD).

## STRICT RULES
1. **OUTPUT LANGUAGE:** {language}. This was detected from the CV and is ABSOLUTELY MANDATORY. Do NOT output the wrong language.
2. **USE REAL NAME:** You MUST extract the candidate's real name from the CV.
3. **NO FLUFF:** Remove meaningless template placeholders like "Forename SURNAME" from the CV text.
4. **NO CLICHES:** Avoid overused phrases like "I believe". Use strong Action Verbs.
5. **HONESTY:** ONLY use facts from the CV. DO NOT hallucinate skills or experience.
6. **NATURAL TONE:** If writing in Vietnamese, use natural phrasing (do NOT literally translate English idioms like "a perfect fit"). If writing in English, use professional native phrasing.
7. **LANGUAGE CONSISTENCY:** Every sentence, greeting, sign-off, and bullet must be in {language}. Do not mix Vietnamese and English except for proper nouns, company names, job titles, and technical terms.
8. **LENGTH:** Max 350 words.

## STRUCTURE
1. **Hook (1 paragraph):** Get straight to the point. Show excitement about {company_name} and highlight core value for the {job_title} role.
2. **Value Proposition (Bullet points):** 2-3 bullet points mapping the best skills/achievements in the CV to the JD requirements. Start with Action Verbs.
3. **Call to Action (1 paragraph):** Reiterate culture fit and request an interview.

## CANDIDATE CV
```
{cv_text}
```

## JOB DESCRIPTION
- **Title:** {job_title}
- **Company:** {company_name}
- **Details:**
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
    language = resolve_cover_letter_language(cv_text, language)

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
            "detected_cv_language": language,
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
        SELECT f.job_title AS title,
               COALESCE(c.company_name, 'Company') AS company_name,
               f.job_description AS description,
               f.job_requirement AS requirements
        FROM warehouse_warehouse.fact_job_postings f
        LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
        WHERE f.job_id::text = %s
        """,
        [job_id],
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
