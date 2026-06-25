from ai.cover_letter import _sanitize_cover_letter, _unsupported_claim_warnings


def test_sanitizes_non_sendable_cover_letter_artifacts():
    raw = """```markdown
**Nguyen Huu Khanh Hung**
[Date]
Subject: Application for Software Engineer

Dear Hiring Team,

I am applying for the role.

Best regards,
**Nguyen Huu Khanh Hung**
```"""
    cleaned = _sanitize_cover_letter(raw)

    assert "```" not in cleaned
    assert "**" not in cleaned
    assert "[Date]" not in cleaned
    assert "Subject:" not in cleaned
    assert cleaned.startswith("Dear Hiring Team")
    assert cleaned.endswith("Nguyen Huu Khanh Hung")


def test_flags_jd_claims_not_supported_by_cv():
    cv = "Projects: Built a RAG application using Python and LangGraph."
    letter = (
        "I mastered async protocols, built distributed systems, and have "
        "IoT experience."
    )

    warnings = _unsupported_claim_warnings(letter, cv)

    assert "async protocol" in warnings
    assert "distributed system" in warnings
    assert "iot experience" in warnings
    assert "mastered" in warnings


def test_flags_object_oriented_claim_when_cv_only_lists_languages():
    cv = "Skills: Python, C/C++, SQL."
    letter = "My CV highlights object-oriented programming."

    assert "object-oriented programming" in _unsupported_claim_warnings(letter, cv)


def test_flags_embellished_project_outcomes():
    cv = "Built a Python application using the MNIST dataset."
    letter = (
        "I built an end-to-end, real-time system, demonstrated a proven "
        "ability to collaborate, and quickly mastered new libraries."
    )

    warnings = _unsupported_claim_warnings(letter, cv)

    assert "end-to-end" in warnings
    assert "real-time" in warnings
    assert "collaboration" in warnings
    assert "proven capacity" in warnings
    assert "mastered" in warnings
