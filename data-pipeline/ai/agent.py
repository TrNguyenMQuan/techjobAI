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
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

from ai.observability import log_ai_event, timed_ai_event
from ai.llm_provider import create_chat_model, get_provider_chain
from ai.skills import load_skills, render_full_skills, render_skill_index, select_skills

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

LLM_PROVIDER_CHAIN = get_provider_chain()

# ── In-memory chat history (per session) ─────────────────────────────────────
_chat_histories: dict[str, list] = {}
MAX_HISTORY = 6


# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """Bạn là **TechJob AI Assistant** — chuyên gia phân tích thị trường tuyển dụng IT Việt Nam.

## CÔNG CỤ CÓ SẴN
1. **execute_sql_tool**: Trên Data Warehouse PostgreSQL (chỉ SELECT)
2. **execute_rag_culture_tool**: Tìm kiếm văn hóa công ty
3. **semantic_search_tool**: Tìm việc theo ngữ nghĩa
4. **predict_salary_tool**: Dự đoán lương ẩn
5. **generate_chart_tool**: Vẽ biểu đồ trực quan

## DATABASE SCHEMA
Bảng chính:
- `warehouse_warehouse.fact_job_postings`: job_id, company_id, job_title, job_level_id, salary_min, salary_max, is_salary_visible, created_on, working_locations (JSONB), skills (JSONB)
- `warehouse_warehouse.dim_company`: company_id, company_name

WORKING_LOCATIONS và SKILLS là JSONB — dùng `::text ILIKE '%từ khóa%'` khi tìm kiếm.

Market marts:
- `warehouse_marts.mart_skill_demand` (skill_id, skill_name, week_start, job_count)
- `warehouse_marts.mart_location_demand` (city_id, city_name, job_count)
- `warehouse_marts.mart_salary_benchmark` (skill_id, skill_name, job_level_id, level_name_vi, median_salary_min, median_salary_max, sample_size) — toàn quốc, không có city.

## QUY TẮC
1. Trả lời Tiếng Việt (trừ khi user yêu cầu tiếng Anh)
2. Dùng công cụ khi cần dữ liệu, không đoán
3. Lương đơn vị triệu VND/tháng (chia salary_min/max cho 1000000)
4. SQL so sánh: SELECT top 5 kết quả, GROUP BY
5. generate_chart_tool: values phải là list[str] số thực (không được null)
"""


def build_system_prompt() -> str:
    """Build a compact prompt with skill discovery, not every full playbook."""
    skills = load_skills()
    if not skills:
        return SYSTEM_PROMPT

    return (
        SYSTEM_PROMPT
        + "\n\n## PROJECT SKILLS\n"
        + "Danh sách skill khả dụng. Nội dung đầy đủ của skill phù hợp sẽ được "
        + "đính kèm riêng theo từng yêu cầu; không tự giả định skill khác.\n\n"
        + render_skill_index(skills)
    )


def enrich_message_with_skills(message: str) -> str:
    """Attach only playbooks relevant to the current request."""
    selected = select_skills(message, max_skills=2)
    if not selected:
        return message
    return (
        message
        + "\n\n<relevant_project_skills>\n"
        + render_full_skills(selected)
        + "\n</relevant_project_skills>"
    )


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
        Schema:
        - warehouse_warehouse.fact_job_postings: job_id, company_id, job_title, salary_min, salary_max, is_salary_visible, job_level_id, created_on, working_locations, skills
        - warehouse_warehouse.dim_company: company_id, company_name
        - warehouse_marts.mart_skill_demand: skill_id, skill_name, week_start, job_count
        - warehouse_marts.mart_location_demand: city_id, city_name, job_count
        - warehouse_marts.mart_salary_benchmark: skill_id, skill_name, job_level_id, level_name_vi, median_salary_min, median_salary_max, sample_size
        Only SELECT/WITH queries allowed. DELETE/UPDATE/DROP are blocked."""
        result = execute_sql(sql)
        if isinstance(result, dict) and isinstance(result.get("rows"), list):
            rows = result["rows"]
            compact_rows = []
            for row in rows[:10]:
                compact_rows.append({
                    key: value[:300] + "... [TRUNCATED]"
                    if isinstance(value, str) and len(value) > 300
                    else value
                    for key, value in row.items()
                })
            result = {
                "columns": result.get("columns", []),
                "rows": compact_rows,
                "row_count": result.get("row_count", len(rows)),
                "truncated_for_llm": len(rows) > 10 or result.get("truncated", False),
                "notice": (
                    "Agent context is limited to the first 10 rows. "
                    "Use aggregate SQL for summaries."
                ),
            }
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    def execute_rag_culture_tool(company_name: str) -> str:
        """Search for company culture and work environment reviews.
        Returns culture descriptions, employee reviews, and work-life balance info.
        Use when users ask about company culture, work environment, or 'what it's like to work at X'."""
        result = execute_rag_culture(company_name)
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    def semantic_search_tool(query: str, limit: int = 10) -> str:
        """Search for IT jobs using semantic similarity (understands meaning, not just keywords).
        Example: searching 'machine learning' will also find 'AI engineer' or 'data scientist' roles.
        Returns job titles, companies, salaries, and similarity scores."""
        from sentence_transformers import SentenceTransformer
        from be.mcp_server import _get_readonly_conn
        import psycopg2.extras

        limit_val = max(1, min(int(limit), 20))

        # Cache model globally to avoid reloading on every call
        if not hasattr(semantic_search_tool, "_model"):
            semantic_search_tool._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model = semantic_search_tool._model

        query_vec = model.encode(query).tolist()
        vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        conn = _get_readonly_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """SELECT f.job_id, f.job_title, c.company_name, 
                      f.salary_min, f.salary_max,
                      1 - (e.embedding <=> %s::vector) AS similarity
               FROM warehouse_warehouse.fact_job_postings f
               JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
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
        values: list[str],
        ylabel: str = "Giá trị",
    ) -> str:
        """Create a compact chart specification for frontend visualization.
        chart_type: 'bar', 'line', 'pie', or 'horizontal_bar'.
        labels: list of string labels.
        values: list of numeric values as strings (e.g. ["25.5", "32.0", "40"]). MUST be non-null numbers.
        Use this when comparing data visually (e.g., salary comparison, skill popularity)."""
        clean_labels, clean_values = [], []
        for lbl, val in zip(labels, values):
            try:
                fval = float(val) if val is not None else None
                if fval is not None:
                    clean_labels.append(lbl)
                    clean_values.append(fval)
            except (TypeError, ValueError):
                pass

        if not clean_values:
            return json.dumps({"error": "No numeric data to chart"})

        return json.dumps({
            "chart_type": chart_type,
            "title": title,
            "labels": clean_labels[:20],
            "values": clean_values[:20],
            "ylabel": ylabel,
        }, ensure_ascii=False)

    return [execute_sql_tool, execute_rag_culture_tool, semantic_search_tool,
            predict_salary_tool, generate_chart_tool]


# ============================================================
# AGENT CREATION
# ============================================================

_agent_executors = {}


def _get_agent(provider_index: int = 0):
    """Create or return a cached ReAct agent for one provider slot."""
    if provider_index in _agent_executors:
        return _agent_executors[provider_index]

    if provider_index >= len(LLM_PROVIDER_CHAIN):
        raise RuntimeError("No more LLM providers are configured")
    provider, _, api_key = LLM_PROVIDER_CHAIN[provider_index]
    if not api_key:
        raise RuntimeError(f"API key not configured for LLM provider '{provider}'.")

    from langgraph.prebuilt import create_react_agent

    llm = create_chat_model(
        provider_index=provider_index,
        temperature=0.2,
        max_tokens=2048,
    )

    tools = _make_tools()
    system_prompt = build_system_prompt()

    _agent_executors[provider_index] = create_react_agent(
        llm, tools, prompt=system_prompt
    )
    return _agent_executors[provider_index]


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
    with timed_ai_event("chat", session_id=session_id, message_chars=len(message)) as event:
        from ai.market_insight import handle_market_insight
        from ai.salary_analysis import handle_salary_comparison

        deterministic_result = (
            handle_salary_comparison(message)
            or handle_market_insight(message)
        )
        if deterministic_result is not None:
            history = _chat_histories.setdefault(session_id, [])
            history.append({"role": "user", "content": message})
            history.append({
                "role": "assistant",
                "content": deterministic_result["response"],
            })
            if len(history) > MAX_HISTORY * 2:
                _chat_histories[session_id] = history[-MAX_HISTORY * 2:]
            event["route"] = "deterministic_analysis"
            event["tools_used"] = ",".join(deterministic_result["tools_used"])
            event["response_chars"] = len(deterministic_result["response"])
            event["charts"] = len(deterministic_result["charts"])
            return {**deterministic_result, "session_id": session_id}

        # Build messages with history
        if session_id not in _chat_histories:
            _chat_histories[session_id] = []

        history = _chat_histories[session_id]

        messages = []
        for msg in history[-MAX_HISTORY:]:
            messages.append(msg)
        messages.append({"role": "user", "content": enrich_message_with_skills(message)})

        # Try every configured provider in order.
        result = None
        errors = []
        for provider_index, (provider, model, api_key) in enumerate(LLM_PROVIDER_CHAIN):
            if not api_key:
                errors.append(f"{provider}: missing API key")
                continue
            try:
                agent = _get_agent(provider_index)
                request_messages = messages if provider_index == 0 else messages[-3:]
                candidate_result = await agent.ainvoke({"messages": request_messages})
                ai_messages = [
                    item for item in candidate_result.get("messages", [])
                    if getattr(item, "type", "") == "ai"
                ]
                final_ai = ai_messages[-1] if ai_messages else None
                final_text = getattr(final_ai, "content", "") if final_ai else ""
                finish_reason = (
                    getattr(final_ai, "response_metadata", {}).get("finish_reason")
                    if final_ai else None
                )
                if not isinstance(final_text, str) or not final_text.strip():
                    raise RuntimeError(
                        "Provider completed without a final text response"
                    )
                if finish_reason in {"length", "max_tokens"}:
                    raise RuntimeError(
                        "Provider truncated the response at its output-token limit"
                    )
                result = candidate_result
                event["llm_provider"] = provider
                event["llm_model"] = model
                break
            except Exception as provider_error:
                errors.append(f"{provider}: {type(provider_error).__name__}")
                next_provider = (
                    LLM_PROVIDER_CHAIN[provider_index + 1][0]
                    if provider_index + 1 < len(LLM_PROVIDER_CHAIN)
                    else "-"
                )
                log_ai_event(
                    "chat.model_fallback",
                    session_id=session_id,
                    failed_provider=provider,
                    failed_model=model,
                    next_provider=next_provider,
                    error_type=type(provider_error).__name__,
                    error=str(provider_error)[:300],
                )
        if result is None:
            raise RuntimeError("All LLM providers failed: " + "; ".join(errors))

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
                        if isinstance(tool_result, dict) and "chart_type" in tool_result:
                            charts.append(tool_result)
                    except (json.JSONDecodeError, TypeError):
                        pass
                if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tools_used.append(tc["name"])

        if not response_text:
            response_text = "Tôi chưa tạo được câu trả lời từ agent. Vui lòng thử lại với câu hỏi cụ thể hơn."

        # Save to history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response_text})

        if len(history) > MAX_HISTORY * 2:
            _chat_histories[session_id] = history[-MAX_HISTORY * 2:]

        event["tools_used"] = ",".join(sorted(set(tools_used))) if tools_used else "-"
        event["response_chars"] = len(response_text)
        event["charts"] = len(charts)

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
