"""
Autonomous ReAct Agent — TechJob AI
LangGraph-based AI agent that interacts with the IT job market data
through natural language using Reason-Act-Observe loop.

LLM: Groq (llama-3.3-70b-versatile) — free, ultra-fast inference

Tools:
  - execute_sql_tool: Query database via MCP Server sandbox
  - execute_rag_culture_tool: Retrieve company culture via RAG
  - semantic_search_tool: Search jobs by meaning (pgvector)
  - predict_salary_tool: Predict hidden salaries (ML model)
  - generate_chart_tool: Create inline visualizations
"""

import os
import json
import base64
import io
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── In-memory chat history (per session) ─────────────────────────────────────
_chat_histories: dict[str, list] = {}
MAX_HISTORY = 20


# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """Bạn là **TechJob AI Assistant** — một chuyên gia phân tích thị trường tuyển dụng IT tại Việt Nam.

## NĂNG LỰC CỦA BẠN
Bạn có quyền truy cập vào cơ sở dữ liệu tuyển dụng IT thực tế từ VietnamWorks, bao gồm:
- Hàng nghìn tin tuyển dụng IT với thông tin chi tiết (vị trí, lương, kỹ năng, địa điểm)
- Dữ liệu thống kê về xu hướng tuyển dụng, mức lương trung bình
- Đánh giá văn hóa công ty từ nhân viên
- Mô hình AI dự đoán lương cho các vị trí ẩn lương

## CÔNG CỤ SẴN CÓ
1. **execute_sql_tool**: Truy vấn SQL trực tiếp vào data warehouse (chỉ SELECT)
2. **execute_rag_culture_tool**: Tra cứu đánh giá văn hóa, môi trường làm việc của công ty
3. **semantic_search_tool**: Tìm kiếm việc làm theo ngữ nghĩa (hiểu ý nghĩa, không chỉ từ khóa)
4. **predict_salary_tool**: Dự đoán mức lương cho vị trí ẩn lương
5. **generate_chart_tool**: Tạo biểu đồ trực quan hóa dữ liệu

## CƠ SỞ DỮ LIỆU
Bảng chính: `warehouse_warehouse.fact_job`
- Cột quan trọng: source_id, title, company_name, primary_city, salary_min_vnd, salary_max_vnd, salary_band, job_level_vi, work_mode, description, requirements, skills_json, posted_date

Bảng thống kê:
- `warehouse_warehouse.agg_top_skills` (skill_name, job_count)
- `warehouse_warehouse.agg_salary_by_title` (job_category, avg_min_trieu, avg_max_trieu, job_count)
- `warehouse_warehouse.agg_trend_monthly` (month, job_count)
- `warehouse_warehouse.dashboard_cache` (tổng quan)

## QUY TẮC
1. Luôn trả lời bằng tiếng Việt (trừ khi user yêu cầu tiếng Anh)
2. Khi cần dữ liệu, hãy sử dụng công cụ thay vì đoán
3. Trình bày kết quả rõ ràng, có cấu trúc (bullet points, bảng)
4. Khi so sánh số liệu, hãy tạo biểu đồ để trực quan hóa
5. Đơn vị lương: triệu VND/tháng (chia salary_min_vnd hoặc salary_max_vnd cho 1000000)
6. Hãy chủ động phân tích và đưa ra nhận xét chuyên sâu, không chỉ liệt kê số liệu
"""


# ============================================================
# TOOL DEFINITIONS
# ============================================================

def _make_tools():
    """Create LangChain tool objects for the agent."""
    from langchain_core.tools import tool
    from be.mcp_server import execute_sql, execute_rag_culture

    @tool
    def execute_sql_tool(sql: str) -> str:
        """Execute a read-only SQL SELECT query against the TechJob AI data warehouse.
        The database contains job postings, salary data, skills, and company info.
        Tables: warehouse_warehouse.fact_job, agg_top_skills, agg_salary_by_title,
        agg_trend_monthly, dashboard_cache, dim_skill, dim_company, dim_location.
        Key columns in fact_job: title, company_name, primary_city, salary_min_vnd,
        salary_max_vnd, salary_band, job_level_vi, work_mode, skills_json, posted_date.
        Only SELECT/WITH queries allowed. DELETE/UPDATE/DROP are blocked."""
        result = execute_sql(sql)
        if isinstance(result, list) and len(result) > 15:
            truncated_data = {
                "notice": f"Kết quả quá lớn ({len(result)} dòng). Chỉ hiển thị 15 dòng đầu để tiết kiệm tokens.",
                "data": result[:15]
            }
            return json.dumps(truncated_data, ensure_ascii=False, default=str)
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    def execute_rag_culture_tool(company_name: str) -> str:
        """Search for company culture and work environment reviews.
        Returns culture descriptions, employee reviews, and work-life balance info.
        Use when users ask about company culture, work environment, or 'what it's like to work at X'."""
        result = execute_rag_culture(company_name)
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    def semantic_search_tool(query: str, limit: str = "10") -> str:
        """Search for IT jobs using semantic similarity (understands meaning, not just keywords).
        Example: searching 'machine learning' will also find 'AI engineer' or 'data scientist' roles.
        Returns job titles, companies, salaries, and similarity scores."""
        from sentence_transformers import SentenceTransformer
        from be.mcp_server import _get_readonly_conn
        import psycopg2.extras

        try:
            limit_val = int(limit)
        except ValueError:
            limit_val = 10

        # Cache model globally to avoid reloading on every call
        if not hasattr(semantic_search_tool, "_model"):
            semantic_search_tool._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model = semantic_search_tool._model

        query_vec = model.encode(query).tolist()
        vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        conn = _get_readonly_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """SELECT f.source_id, f.title, f.company_name, f.primary_city,
                      f.salary_text, f.salary_band, f.source_url,
                      1 - (e.embedding <=> %s::vector) AS similarity
               FROM warehouse_warehouse.fact_job f
               JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
               ORDER BY e.embedding <=> %s::vector
               LIMIT %s;""",
            [vec_str, vec_str, limit_val],
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r["similarity"] = round(float(r["similarity"]), 4) if r.get("similarity") else None
            results.append(r)

        return json.dumps({"query": query, "results": results}, ensure_ascii=False, default=str)

    @tool
    def predict_salary_tool(
        title: str,
        city: str = "unknown",
        level: str = "unknown",
        work_mode: str = "unknown",
        skills: str = "",
    ) -> str:
        """Predict the salary range for a job with hidden/negotiable salary.
        Input the job title, city, experience level, work mode, and key skills.
        Returns predicted min/max salary in VND and confidence score."""
        from ai.salary_predictor import predict_hidden_salary
        result = predict_hidden_salary(title, city, level, work_mode, skills)
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    def generate_chart_tool(
        chart_type: str,
        title: str,
        labels: list[str],
        values: list[float],
        ylabel: str = "Giá trị",
    ) -> str:
        """Generate an inline chart image for data visualization in the chat.
        chart_type: 'bar', 'line', 'pie', or 'horizontal_bar'.
        Returns a base64-encoded PNG image string.
        Use this when comparing data visually (e.g., salary comparison, skill popularity)."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#16213e")

        colors = ["#e94560", "#0f3460", "#533483", "#00b4d8", "#06d6a0",
                   "#90e0ef", "#ffc300", "#ef476f", "#118ab2", "#073b4c"]

        if chart_type == "bar":
            bars = ax.bar(labels, values, color=colors[:len(labels)], edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.1f", color="white", fontsize=10)
        elif chart_type == "horizontal_bar":
            bars = ax.barh(labels, values, color=colors[:len(labels)], edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.1f", color="white", fontsize=10)
        elif chart_type == "line":
            ax.plot(labels, values, color="#e94560", marker="o", linewidth=2, markersize=8)
            ax.fill_between(range(len(labels)), values, alpha=0.15, color="#e94560")
        elif chart_type == "pie":
            ax.pie(values, labels=labels, colors=colors[:len(labels)],
                   autopct="%1.1f%%", textprops={"color": "white", "fontsize": 10})

        ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=15)
        if chart_type != "pie":
            ax.set_ylabel(ylabel, color="white", fontsize=11)
            ax.tick_params(colors="white", labelsize=9)
            ax.spines["bottom"].set_color("#333")
            ax.spines["left"].set_color("#333")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", alpha=0.15, color="white")
            plt.xticks(rotation=30, ha="right")

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        return json.dumps({
            "chart_type": chart_type,
            "title": title,
            "image_base64": img_b64,
        })

    return [execute_sql_tool, execute_rag_culture_tool, semantic_search_tool,
            predict_salary_tool, generate_chart_tool]


# ============================================================
# AGENT CREATION
# ============================================================

_agent_executor = None


def _get_agent():
    """Create or return cached LangGraph ReAct agent using Groq."""
    global _agent_executor

    if _agent_executor is not None:
        return _agent_executor

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not configured. Set it in .env file to use the AI Agent."
        )

    from langchain_groq import ChatGroq
    from langgraph.prebuilt import create_react_agent

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0.3,
        api_key=GROQ_API_KEY,
    )

    tools = _make_tools()

    _agent_executor = create_react_agent(
        llm,
        tools,
        prompt=SYSTEM_PROMPT,
    )

    return _agent_executor


# ============================================================
# CHAT INTERFACE
# ============================================================

async def chat(message: str, session_id: str = "default") -> dict:
    """
    Send a message to the AI Agent and get a response.

    Args:
        message: User's natural language message.
        session_id: Session ID for conversation history.

    Returns:
        dict with 'response' (text), 'charts' (list of base64 images),
        'tools_used' (list of tool names called).
    """
    agent = _get_agent()

    # Build messages with history
    if session_id not in _chat_histories:
        _chat_histories[session_id] = []

    history = _chat_histories[session_id]

    messages = []
    for msg in history[-MAX_HISTORY:]:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    # Invoke agent
    result = await agent.ainvoke({"messages": messages})

    # Extract response
    response_text = ""
    charts = []
    tools_used = []

    for msg in result["messages"]:
        if hasattr(msg, "type"):
            if msg.type == "ai" and hasattr(msg, "content") and msg.content:
                response_text = msg.content
            elif msg.type == "tool" and hasattr(msg, "content"):
                try:
                    tool_result = json.loads(msg.content)
                    if isinstance(tool_result, dict) and "image_base64" in tool_result:
                        charts.append(tool_result)
                except (json.JSONDecodeError, TypeError):
                    pass
            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tools_used.append(tc["name"])

    # Save to history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response_text})

    if len(history) > MAX_HISTORY * 2:
        _chat_histories[session_id] = history[-MAX_HISTORY * 2:]

    return {
        "response": response_text,
        "charts": charts,
        "tools_used": tools_used,
        "session_id": session_id,
    }


def get_chat_history(session_id: str) -> list:
    """Get chat history for a session."""
    return _chat_histories.get(session_id, [])


def clear_chat_history(session_id: str) -> None:
    """Clear chat history for a session."""
    _chat_histories.pop(session_id, None)
