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
from ai.db_config import psycopg2_kwargs
from ai.llm_provider import create_chat_model, get_provider_chain

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

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

COVER_LETTER_PROMPT_TEMPLATE = """You are a careful professional cover-letter writer.

## TASK
Write a concise, credible cover letter based only on evidence in the CV.

## STRICT RULES
1. **OUTPUT LANGUAGE:** {language}. This was detected from the CV and is mandatory.
2. **PRESERVE THE NAME:** Copy the candidate's name exactly as written in the CV. Do not reorder, translate, abbreviate, or guess it.
3. **CV EVIDENCE ONLY:** Every claim about the candidate must be directly supported by the CV text.
4. **JD IS NOT CANDIDATE EVIDENCE:** Technologies, protocols, domains, team names, and responsibilities found only in the JD are employer requirements. Never claim the candidate has used or mastered them.
5. **NO INFERENCE BRIDGES:** Do not turn one project into unsupported claims such as "distributed-ready", "scalable", "production-grade", "end-to-end", "real-time", "quickly mastered", collaboration ability, automotive experience, IoT experience, async protocols, GPIO, or Electron-like contexts unless those exact facts appear in the CV.
6. **ACCURATE STRENGTH:** Never use "mastered", "expert", "top-tier", "extensive experience", or a number of years unless explicitly stated in the CV. Prefer precise wording such as "built a project using..." or "developed familiarity with...".
7. **NO PLACEHOLDERS OR DUPLICATE HEADER:** Do not output contact details, postal address, date, subject line, square-bracket placeholders, or Markdown/code fences.
8. **NO UNSUPPORTED COMPANY PRAISE:** Do not invent company culture, mission, products, team details, or business impact. Reference only details explicitly present in the JD.
9. **NATURAL TONE:** Professional, specific, modest, and human. Avoid clichés and exaggerated enthusiasm.
10. **LANGUAGE CONSISTENCY:** Every sentence, greeting, sign-off, and bullet must be in {language}. Technical proper nouns may remain unchanged.
11. **LENGTH:** 180-260 words. Finish with a complete sign-off.

## STRUCTURE
1. Greeting to the hiring team.
2. Opening paragraph: target role and 1-2 strongest verified matches.
3. Evidence paragraph: describe 1-2 relevant CV projects or experiences and what the candidate actually did.
4. Fit paragraph: acknowledge relevant JD requirements without claiming unsupported experience; express readiness to learn where appropriate.
5. Short call to action and sign-off using the exact CV name.

## OUTPUT FORMAT
Plain text only. No Markdown bold, headings, tables, code fences, contact header, date, subject line, or placeholders.

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


RISKY_UNSUPPORTED_TERMS = {
    "distributed system": ("distributed system",),
    "async protocol": ("async protocol", "asynchronous protocol"),
    "object-oriented programming": ("object-oriented programming",),
    "gpio": ("gpio",),
    "electron": ("electron",),
    "end-to-end": ("end-to-end", "end to end"),
    "real-time": ("real-time", "real time"),
    "collaboration": ("collaborat", "teamwork"),
    "proven capacity": ("proven capacity", "proven ability"),
    "automotive experience": (
        "automotive experience",
        "experience in automotive",
        "worked on automotive",
    ),
    "iot experience": (
        "iot experience",
        "experience in iot",
        "worked on iot",
    ),
}


def _sanitize_cover_letter(text: str) -> str:
    """Remove model formatting artifacts and non-sendable placeholders."""
    text = re.sub(r"^\s*```(?:text|markdown)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.replace("**", "").replace("__", "")

    cleaned_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        if re.fullmatch(r"\[[^\]]+\]", line):
            continue
        if re.match(r"^(subject|date|tiêu\s*đề)\s*:", line, flags=re.IGNORECASE):
            continue
        cleaned_lines.append(line)

    greeting_index = next(
        (
            index
            for index, line in enumerate(cleaned_lines)
            if re.match(
                r"^(dear\b|kính gửi\b|thân gửi\b)",
                line,
                flags=re.IGNORECASE,
            )
        ),
        None,
    )
    if greeting_index is not None:
        cleaned_lines = cleaned_lines[greeting_index:]

    return "\n".join(cleaned_lines).strip()


def _unsupported_claim_warnings(cover_letter: str, cv_text: str) -> list[str]:
    """Flag common cases where JD requirements become candidate claims."""
    output_lower = cover_letter.lower()
    cv_lower = cv_text.lower()
    warnings = []
    for label, variants in RISKY_UNSUPPORTED_TERMS.items():
        supported = any(term in cv_lower for term in variants)
        if label == "object-oriented programming":
            supported = supported or bool(re.search(r"\boop\b", cv_lower))
        if any(term in output_lower for term in variants) and not supported:
            warnings.append(label)
    for exaggerated in (
        "mastered",
        "mastering",
        "top-tier",
        "extensive experience",
        "quickly learned",
    ):
        if exaggerated in output_lower and exaggerated not in cv_lower:
            warnings.append(exaggerated)
    return sorted(set(warnings))


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
    provider_chain = get_provider_chain()
    if not any(api_key for _, _, api_key in provider_chain):
        return {
            "error": "No API key is configured for any LLM provider.",
        }

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

    try:
        response = None
        errors = []
        for provider_index, (provider, _, api_key) in enumerate(provider_chain):
            if not api_key:
                continue
            try:
                candidate = create_chat_model(
                    provider_index=provider_index,
                    temperature=0.25,
                    max_tokens=1200,
                ).invoke(prompt)
                finish_reason = getattr(candidate, "response_metadata", {}).get(
                    "finish_reason"
                )
                if finish_reason in {"length", "max_tokens"}:
                    raise RuntimeError("Cover letter was truncated")
                if not isinstance(candidate.content, str) or not candidate.content.strip():
                    raise RuntimeError("Cover letter provider returned empty content")
                response = candidate
                break
            except Exception as provider_error:
                errors.append(f"{provider}: {type(provider_error).__name__}")
        if response is None:
            raise RuntimeError("All LLM providers failed: " + "; ".join(errors))
        cover_letter_text = _sanitize_cover_letter(response.content)
        quality_warnings = _unsupported_claim_warnings(cover_letter_text, cv_text)

        if quality_warnings:
            corrective_prompt = (
                prompt
                + "\n\nQUALITY CHECK FAILED. Rewrite from scratch and remove "
                + ", ".join(quality_warnings)
                + ". These claims are not supported by the CV."
            )
            corrected = None
            for provider_index, (_, _, api_key) in enumerate(provider_chain):
                if not api_key:
                    continue
                try:
                    candidate = create_chat_model(
                        provider_index=provider_index,
                        temperature=0.1,
                        max_tokens=1200,
                    ).invoke(corrective_prompt)
                    candidate_text = _sanitize_cover_letter(candidate.content)
                    if not _unsupported_claim_warnings(candidate_text, cv_text):
                        corrected = candidate_text
                        break
                except Exception:
                    continue
            if corrected:
                cover_letter_text = corrected
                quality_warnings = []
            else:
                return {
                    "error": (
                        "Cover letter quality check failed because unsupported "
                        "claims remained: " + ", ".join(quality_warnings)
                    )
                }

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
            "quality_warnings": quality_warnings,
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
    conn = psycopg2.connect(**psycopg2_kwargs())
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
