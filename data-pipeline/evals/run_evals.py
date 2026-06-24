"""Offline eval runner for TechJob AI.

The goal is not to replace full LLM evals. This runner catches deterministic
regressions in the AI contract: skills routing, MCP safety, cover-letter
language policy, and prompt/tool visibility.

Usage:
    python data-pipeline/evals/run_evals.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _case(name: str, fn: Callable[[], None]) -> dict:
    try:
        fn()
        return {"name": name, "status": "pass"}
    except AssertionError as exc:
        return {"name": name, "status": "fail", "error": str(exc)}
    except Exception as exc:  # pragma: no cover - useful for CLI diagnostics
        return {"name": name, "status": "error", "error": f"{type(exc).__name__}: {exc}"}


def eval_cover_letter_language() -> None:
    from ai.cover_letter import detect_cv_language

    english_cv = """
    Nguyen Huu Khanh Hung
    Skills: Python, Machine Learning, LangChain, React
    Projects: Built a handwriting recognition web app.
    Activities: Volunteer at Green Summer Campaign.
    """
    vietnamese_cv = """
    Nguyễn Văn A
    Kỹ năng: Python, React, phân tích dữ liệu
    Kinh nghiệm: 3 năm làm việc trong các dự án phần mềm.
    """

    assert detect_cv_language(english_cv) == "English"
    assert detect_cv_language(vietnamese_cv) == "Tiếng Việt"


def eval_mcp_safety_and_discovery() -> None:
    from be.mcp_server import execute_sql, list_techjob_tables

    blocked = execute_sql("DROP TABLE warehouse_warehouse.fact_job_postings;")
    assert blocked.get("blocked_keyword") == "DROP"

    tables = list_techjob_tables()
    assert "warehouse_warehouse.fact_job_postings" in tables["warehouse"]
    assert "warehouse_marts.mart_skill_demand" in tables["marts"]


def eval_skills_routing() -> None:
    from ai.skills import select_skills

    cover = [skill.slug for skill in select_skills("tạo cover letter từ CV tiếng Anh")]
    salary = [skill.slug for skill in select_skills("dự đoán lương backend senior ở HCM")]

    assert "cover-letter" in cover
    assert "salary-analysis" in salary


def eval_agent_prompt_contract() -> None:
    from ai.agent import build_system_prompt

    prompt = build_system_prompt()
    assert "PROJECT SKILLS" in prompt
    assert "fact_job_postings" in prompt
    assert "cover-letter" in prompt
    assert "salary-analysis" in prompt


def main() -> int:
    results = [
        _case("cover_letter_language", eval_cover_letter_language),
        _case("mcp_safety_and_discovery", eval_mcp_safety_and_discovery),
        _case("skills_routing", eval_skills_routing),
        _case("agent_prompt_contract", eval_agent_prompt_contract),
    ]
    summary = {
        "total": len(results),
        "passed": sum(1 for result in results if result["status"] == "pass"),
        "failed": [result for result in results if result["status"] != "pass"],
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
