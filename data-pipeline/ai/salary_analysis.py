"""Reliable salary comparison for common multi-skill questions."""

from __future__ import annotations

import re


SKILL_ALIASES = {
    "ReactJS": ("react", "reactjs", "react.js"),
    "Python": ("python",),
    "Go": ("golang", "go language"),
    "Java": ("java",),
    "JavaScript": ("javascript",),
    "TypeScript": ("typescript",),
    "Node.js": ("node.js", "nodejs"),
}


def _requested_skills(message: str) -> list[str]:
    lower = message.lower()
    found = []
    for skill, aliases in SKILL_ALIASES.items():
        matched = (
            bool(re.search(r"\b(?:go|golang)\b", lower))
            if skill == "Go"
            else any(alias in lower for alias in aliases)
        )
        if matched:
            found.append(skill)
    return found


def _is_comparison_request(message: str, skills: list[str]) -> bool:
    lower = message.lower()
    asks_salary = "lương" in lower or "salary" in lower or "compensation" in lower
    asks_comparison = "so sánh" in lower or "compare" in lower or " vs " in f" {lower} "
    return asks_salary and asks_comparison and len(skills) >= 2


def _query_salary(skill: str, *, exact_scope: bool) -> dict:
    from be.mcp_server import _get_readonly_conn
    import psycopg2.extras

    aliases = SKILL_ALIASES[skill]
    alias_sql = " OR ".join(
        ["LOWER(item->>'skillName') LIKE %s"] * len(aliases)
    )
    params = [f"%{alias.lower()}%" for alias in aliases]
    scope_sql = ""
    if exact_scope:
        scope_sql = """
          AND f.working_locations::text ILIKE %s
          AND (f.job_title ILIKE %s OR f.job_title ILIKE %s)
        """
        params.extend(["%Ho Chi Minh%", "%Senior%", "%Sr.%"])

    sql = f"""
        WITH matched AS (
            SELECT
                CASE WHEN f.salary_min BETWEEN 1 AND 100000
                    THEN f.salary_min * 26300 ELSE f.salary_min END AS salary_min_vnd,
                CASE WHEN f.salary_max BETWEEN 1 AND 100000
                    THEN f.salary_max * 26300 ELSE f.salary_max END AS salary_max_vnd
            FROM warehouse_warehouse.fact_job_postings f
            WHERE EXISTS (
                SELECT 1
                FROM jsonb_array_elements(COALESCE(f.skills, '[]'::jsonb)) item
                WHERE {alias_sql}
            )
              AND f.salary_min IS NOT NULL
              AND f.salary_max IS NOT NULL
              {scope_sql}
        )
        SELECT
            COUNT(*) AS sample_size,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
                (ORDER BY salary_min_vnd)::numeric) AS median_min,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
                (ORDER BY salary_max_vnd)::numeric) AS median_max
        FROM matched
        WHERE salary_min_vnd BETWEEN 3000000 AND 200000000
          AND salary_max_vnd BETWEEN 3000000 AND 200000000
    """

    conn = _get_readonly_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return dict(cur.fetchone() or {})
    finally:
        conn.close()


def handle_salary_comparison(message: str) -> dict | None:
    """Return a grounded comparison, or None for unrelated messages."""
    skills = _requested_skills(message)
    if not _is_comparison_request(message, skills):
        return None

    results = []
    for skill in skills:
        exact = _query_salary(skill, exact_scope=True)
        if exact.get("sample_size"):
            results.append({**exact, "skill": skill, "scope": "Senior tại TP.HCM"})
            continue

        broad = _query_salary(skill, exact_scope=False)
        if broad.get("sample_size"):
            results.append({
                **broad,
                "skill": skill,
                "scope": "tham chiếu toàn thị trường",
            })
        else:
            results.append({
                "skill": skill,
                "scope": "không có mẫu lương công khai",
                "sample_size": 0,
                "median_min": None,
                "median_max": None,
            })

    lines = [
        (
            "**Kết luận:** Dữ liệu lương công khai cho Senior tại TP.HCM "
            "hiện còn thưa, nên chưa thể xếp hạng các kỹ năng một cách đáng tin cậy."
        ),
        "",
    ]
    chart_labels, chart_values = [], []
    for item in results:
        if item["sample_size"]:
            min_m = float(item["median_min"]) / 1_000_000
            max_m = float(item["median_max"]) / 1_000_000
            lines.append(
                f"- **{item['skill']}**: {min_m:.1f}–{max_m:.1f} triệu VND/tháng "
                f"(trung vị, {item['sample_size']} mẫu; {item['scope']})."
            )
            chart_labels.append(item["skill"])
            chart_values.append(round((min_m + max_m) / 2, 1))
        else:
            lines.append(
                f"- **{item['skill']}**: chưa có mẫu lương công khai phù hợp "
                "trong dữ liệu hiện tại."
            )

    lines.extend([
        "",
        (
            "Các mức “tham chiếu toàn thị trường” không phải riêng Senior/TP.HCM. "
            "Không nên kết luận kỹ năng thiếu dữ liệu có mức lương thấp hơn."
        ),
        "Bạn có thể mở rộng sang toàn quốc hoặc mọi cấp bậc để có mẫu lớn hơn.",
    ])

    charts = []
    if chart_values:
        charts.append({
            "chart_type": "bar",
            "title": "Trung điểm khoảng lương quan sát",
            "labels": chart_labels,
            "values": chart_values,
            "ylabel": "Triệu VND/tháng",
        })

    return {
        "response": "\n".join(lines),
        "charts": charts,
        "tools_used": ["salary_comparison_tool"],
    }
