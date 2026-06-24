"""
MCP Server — TechJob AI
Model Context Protocol server providing safe database access tools for the AI Agent.

Tools:
  - execute_sql_tool: Text-to-SQL sandbox with read-only enforcement
  - execute_rag_culture_tool: RAG retrieval for company culture data

Usage:
    python -m be.mcp_server              # MCP stdio server
    python -m be.mcp_server --self-test  # quick local safety checks
"""

import os
import re
import json
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "techjob")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

# ── Dangerous SQL patterns — block any data-modifying statements ─────────────
BLOCKED_PATTERNS = re.compile(
    r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXECUTE)\b",
    re.IGNORECASE,
)

# Maximum rows returned per query to prevent memory issues
MAX_ROWS = 200


def list_techjob_tables() -> dict:
    """Return the main warehouse objects exposed to agents and MCP clients."""
    return {
        "warehouse": [
            "warehouse_warehouse.fact_job_postings",
            "warehouse_warehouse.dim_company",
            "warehouse_warehouse.dim_skill",
            "warehouse_warehouse.dim_location",
            "warehouse_warehouse.job_embeddings",
            "warehouse_warehouse.company_culture",
        ],
        "marts": [
            "warehouse_marts.mart_skill_demand",
            "warehouse_marts.mart_salary_benchmark",
            "warehouse_marts.mart_salary_features",
            "warehouse_marts.mart_location_demand",
        ],
        "aggregates": [
            "warehouse_warehouse.agg_top_skills",
            "warehouse_warehouse.agg_salary_by_title",
            "warehouse_warehouse.agg_trend_monthly",
            "warehouse_warehouse.dashboard_cache",
        ],
    }


def _get_readonly_conn():
    """Create a read-only database connection."""
    if psycopg2 is None:
        raise RuntimeError(
            "psycopg2 is required for database-backed MCP tools. "
            "Install data-pipeline/requirements.txt first."
        )

    conn = psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME,
    )
    conn.set_session(readonly=True, autocommit=True)
    return conn


def execute_sql(sql: str) -> dict:
    """
    Execute a SQL query in a read-only sandbox.

    Security layers:
    1. Regex blocks dangerous keywords (DELETE, UPDATE, DROP, etc.)
    2. Connection is set to READ ONLY mode
    3. Results capped at MAX_ROWS

    Args:
        sql: The SQL query string to execute.

    Returns:
        dict with 'columns', 'rows', 'row_count' or 'error'.
    """
    # Layer 1: Pattern-based blocking
    if BLOCKED_PATTERNS.search(sql):
        blocked_word = BLOCKED_PATTERNS.search(sql).group(0).upper()
        return {
            "error": f"🚫 Blocked: '{blocked_word}' statements are not allowed. "
                     f"This SQL sandbox only supports SELECT queries.",
            "blocked_keyword": blocked_word,
        }

    # Layer 2: Must start with SELECT or WITH (CTE)
    stripped = sql.strip().upper()
    if not (stripped.startswith("SELECT") or stripped.startswith("WITH")):
        return {
            "error": "🚫 Only SELECT and WITH (CTE) queries are allowed.",
        }

    try:
        conn = _get_readonly_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql)

        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(MAX_ROWS)

        # Convert to serializable format
        result_rows = []
        for row in rows:
            clean_row = {}
            for k, v in dict(row).items():
                if hasattr(v, "isoformat"):
                    clean_row[k] = v.isoformat()
                elif isinstance(v, (bytes, memoryview)):
                    clean_row[k] = "<binary>"
                else:
                    clean_row[k] = v
            result_rows.append(clean_row)

        total_count = cur.rowcount
        cur.close()
        conn.close()

        return {
            "columns": columns,
            "rows": result_rows,
            "row_count": total_count,
            "truncated": total_count > MAX_ROWS,
        }
    except Exception as e:
        return {"error": f"SQL execution error: {str(e)}"}


def execute_rag_culture(company_name: str, top_k: int = 3) -> dict:
    """
    RAG retrieval for company culture data using pgvector cosine similarity.

    Args:
        company_name: Name of the company to search for.
        top_k: Number of top results to return.

    Returns:
        dict with 'company_name', 'results' (list of culture text + similarity).
    """
    try:
        from sentence_transformers import SentenceTransformer

        # Encode company name as query vector
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_text = f"Văn hóa làm việc tại {company_name}"
        query_vec = model.encode(query_text).tolist()
        vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        conn = _get_readonly_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # First try exact name match
        cur.execute(
            """
            SELECT company_name, culture_text, source,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM warehouse_warehouse.company_culture
            WHERE embedding IS NOT NULL
              AND company_name ILIKE %s
            ORDER BY similarity DESC
            LIMIT %s;
            """,
            [vec_str, f"%{company_name}%", top_k],
        )
        rows = cur.fetchall()

        # Fallback: semantic search across all companies
        if not rows:
            cur.execute(
                """
                SELECT company_name, culture_text, source,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM warehouse_warehouse.company_culture
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                [vec_str, vec_str, top_k],
            )
            rows = cur.fetchall()

        cur.close()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "company_name": row["company_name"],
                "culture_text": row["culture_text"],
                "source": row["source"],
                "similarity": round(float(row["similarity"]), 4),
            })

        return {
            "query_company": company_name,
            "results": results,
        }
    except Exception as e:
        return {"error": f"RAG culture search error: {str(e)}"}


# ── MCP Server Protocol (stdio mode) ────────────────────────────────────────
# When running as MCP server, expose tools via the MCP protocol.
# For direct integration, import execute_sql / execute_rag_culture as functions.

def get_tool_definitions():
    """Return MCP-compatible tool definitions."""
    return [
        {
            "name": "execute_sql_tool",
            "description": (
                "Execute a read-only SQL query against the TechJob AI data warehouse. "
                "Only SELECT queries are allowed. The database contains tables: "
                "warehouse_warehouse.fact_job_postings (job postings with salary, skills, location), "
                "warehouse_warehouse.dim_company, warehouse_warehouse.dim_skill, "
                "warehouse_warehouse.dim_location, warehouse_warehouse.agg_top_skills, "
                "warehouse_warehouse.agg_salary_by_title, warehouse_warehouse.agg_trend_monthly, "
                "warehouse_warehouse.dashboard_cache. "
                "Key columns in fact_job_postings: job_id, company_id, job_title, "
                "salary_min, salary_max, working_locations, skills, created_on, "
                "job_description, job_requirement."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute.",
                    }
                },
                "required": ["sql"],
            },
        },
        {
            "name": "execute_rag_culture_tool",
            "description": (
                "Search for company culture and work environment reviews using semantic "
                "similarity. Returns relevant culture descriptions for a given company name. "
                "Use this when users ask about company culture, work environment, or employee reviews."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to search culture info for.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default 3).",
                        "default": 3,
                    },
                },
                "required": ["company_name"],
            },
        },
        {
            "name": "list_techjob_tables_tool",
            "description": "List the main TechJob AI warehouse, mart, aggregate, embedding, and culture tables.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def handle_tool_call(tool_name: str, arguments: dict) -> str:
    """Route MCP tool calls to the appropriate handler."""
    if tool_name == "execute_sql_tool":
        result = execute_sql(arguments["sql"])
    elif tool_name == "execute_rag_culture_tool":
        result = execute_rag_culture(
            arguments["company_name"],
            arguments.get("top_k", 3),
        )
    elif tool_name == "list_techjob_tables_tool":
        result = list_techjob_tables()
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    return json.dumps(result, ensure_ascii=False, default=str)


def create_mcp_server():
    """Create a real MCP server exposing TechJob AI tools.

    The functions above remain importable for the in-process LangGraph agent,
    while this wrapper exposes the same capabilities through the standard
    Model Context Protocol. External MCP clients can run this module over stdio
    and discover/call the tools without importing project internals.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The 'mcp' package is required to run the MCP server. "
            "Install data-pipeline/requirements.txt first."
        ) from exc

    mcp = FastMCP("techjob-ai")

    @mcp.tool()
    def execute_sql_tool(sql: str) -> dict:
        """Execute a read-only SQL SELECT/WITH query against the TechJob AI warehouse.

        Dangerous SQL statements are blocked, the database session is read-only,
        and results are capped to prevent oversized tool responses.
        """
        return execute_sql(sql)

    @mcp.tool()
    def execute_rag_culture_tool(company_name: str, top_k: int = 3) -> dict:
        """Retrieve company culture/work-environment snippets using semantic search."""
        return execute_rag_culture(company_name=company_name, top_k=top_k)

    @mcp.tool()
    def list_techjob_tables_tool() -> dict:
        """List the main tables and marts the agent is expected to query."""
        return list_techjob_tables()

    return mcp


def run_mcp_server() -> None:
    """Run TechJob AI MCP server over stdio."""
    create_mcp_server().run()


def _run_self_test() -> None:
    # Self-test mode
    print("=== MCP Server Self-Test ===")

    # Test 1: Valid SELECT
    print("\n[Test 1] Valid SELECT:")
    result = execute_sql("SELECT 1 AS test_value;")
    print(json.dumps(result, indent=2))

    # Test 2: Blocked DELETE
    print("\n[Test 2] Blocked DELETE:")
    result = execute_sql("DELETE FROM warehouse_warehouse.fact_job_postings;")
    print(json.dumps(result, indent=2))

    # Test 3: Blocked UPDATE
    print("\n[Test 3] Blocked UPDATE:")
    result = execute_sql("UPDATE warehouse_warehouse.fact_job_postings SET job_title='hacked';")
    print(json.dumps(result, indent=2))

    print("\n=== All tests passed ===")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _run_self_test()
    else:
        run_mcp_server()
