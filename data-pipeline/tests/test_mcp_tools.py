import json

from be.mcp_server import get_tool_definitions, handle_tool_call


def test_mcp_tool_definitions_include_standard_tools():
    tool_names = {tool["name"] for tool in get_tool_definitions()}

    assert "execute_sql_tool" in tool_names
    assert "execute_rag_culture_tool" in tool_names
    assert "list_techjob_tables_tool" in tool_names


def test_mcp_table_listing_tool_is_available_without_database():
    result = json.loads(handle_tool_call("list_techjob_tables_tool", {}))

    assert "warehouse_warehouse.fact_job_postings" in result["warehouse"]
    assert "warehouse_marts.mart_salary_benchmark" in result["marts"]


def test_mcp_unknown_tool_returns_error():
    result = json.loads(handle_tool_call("not_a_tool", {}))

    assert "error" in result
