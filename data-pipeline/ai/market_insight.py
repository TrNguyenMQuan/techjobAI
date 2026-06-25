"""Grounded market-insight reports backed by warehouse aggregates."""

from __future__ import annotations

import calendar
import re
from datetime import date


MARKET_TERMS = (
    "xu hướng", "thị trường", "market", "trend", "kỹ năng hot",
    "hot skill", "nhu cầu tuyển dụng",
)


def _requested_month(message: str) -> tuple[int, int] | None:
    patterns = (
        r"tháng\s*(\d{1,2})\s*[/\-]\s*(\d{4})",
        r"(\d{1,2})\s*[/\-]\s*(\d{4})",
    )
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            month, year = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12:
                return year, month
    return None


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _query_rows(sql: str, params=()) -> list[dict]:
    from be.mcp_server import _get_readonly_conn
    import psycopg2.extras

    conn = _get_readonly_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def handle_market_insight(message: str) -> dict | None:
    """Build a concise report for market/trend questions."""
    lower = message.lower()
    if not any(term in lower for term in MARKET_TERMS):
        return None

    available = _query_rows("""
        SELECT MIN(week_start) AS min_date, MAX(week_start) AS max_date
        FROM warehouse_marts.mart_skill_demand
    """)[0]
    requested = _requested_month(message)
    max_date = available["max_date"]
    min_date = available["min_date"]

    if requested:
        year, month = requested
    else:
        year, month = max_date.year, max_date.month
    start, end = _month_bounds(year, month)

    skills = _query_rows("""
        SELECT skill_name, SUM(job_count)::integer AS job_count
        FROM warehouse_marts.mart_skill_demand
        WHERE week_start >= %s AND week_start < %s
        GROUP BY skill_name
        ORDER BY job_count DESC, skill_name
        LIMIT 6
    """, (start, end))

    used_fallback_period = False
    if not skills:
        used_fallback_period = True
        year, month = max_date.year, max_date.month
        start, end = _month_bounds(year, month)
        skills = _query_rows("""
            SELECT skill_name, SUM(job_count)::integer AS job_count
            FROM warehouse_marts.mart_skill_demand
            WHERE week_start >= %s AND week_start < %s
            GROUP BY skill_name
            ORDER BY job_count DESC, skill_name
            LIMIT 6
        """, (start, end))

    locations = _query_rows("""
        SELECT city_name_vi, job_count::integer
        FROM warehouse_marts.mart_location_demand
        ORDER BY job_count DESC, city_name_vi
        LIMIT 5
    """)
    total_locations = sum(
        row["job_count"] for row in _query_rows("""
            SELECT job_count::integer
            FROM warehouse_marts.mart_location_demand
        """)
    )

    lines = []
    if used_fallback_period and requested:
        requested_year, requested_month = requested
        lines.extend([
            f"### Không có dữ liệu cho tháng {requested_month}/{requested_year}",
            "",
            (
                f"Kho dữ liệu hiện chỉ bao phủ từ **{min_date:%d/%m/%Y}** đến "
                f"**{max_date:%d/%m/%Y}**. Vì vậy, hệ thống không gán số liệu hiện tại "
                f"cho tháng {requested_month}/{requested_year}."
            ),
            "",
            f"Dưới đây là kỳ gần nhất có dữ liệu: **tháng {month}/{year}**.",
            "",
        ])

    lines.extend([
        f"### Xu hướng tuyển dụng IT tháng {month}/{year}",
        "",
        "#### Kỹ năng có nhu cầu cao",
        "",
        "| Kỹ năng | Số lượt nhu cầu |",
        "|---|---:|",
    ])
    lines.extend(
        f"| {row['skill_name']} | {row['job_count']} |" for row in skills
    )

    lines.extend([
        "",
        "#### Địa điểm tuyển dụng nổi bật",
        "",
        "| Thành phố | Số vị trí | Tỷ trọng |",
        "|---|---:|---:|",
    ])
    for row in locations:
        share = (
            row["job_count"] / total_locations * 100 if total_locations else 0
        )
        lines.append(
            f"| {row['city_name_vi']} | {row['job_count']} | {share:.1f}% |"
        )

    if skills:
        top_names = ", ".join(row["skill_name"] for row in skills[:3])
        lines.extend([
            "",
            "#### Nhận xét ngắn",
            "",
            f"- Nhóm dẫn đầu trong kỳ là **{top_names}**.",
            (
                f"- **{locations[0]['city_name_vi']}** và "
                f"**{locations[1]['city_name_vi']}** tiếp tục là hai thị trường "
                "tuyển dụng lớn nhất."
            ) if len(locations) >= 2 else "",
            "- Các con số là nhu cầu quan sát trong kho dữ liệu, không phải dự báo.",
        ])

    charts = [{
        "chart_type": "bar",
        "title": f"Top kỹ năng IT tháng {month}/{year}",
        "labels": [row["skill_name"] for row in skills],
        "values": [row["job_count"] for row in skills],
        "ylabel": "Số lượt nhu cầu",
    }] if skills else []

    return {
        "response": "\n".join(line for line in lines if line is not None),
        "charts": charts,
        "tools_used": ["market_insight_tool"],
    }
