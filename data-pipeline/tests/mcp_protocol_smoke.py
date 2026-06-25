"""End-to-end MCP stdio smoke test for TechJob AI.

This starts the MCP server exactly like an external client would, performs the
protocol handshake, discovers tools, and calls one read-only SQL tool.
"""

import json
import os

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command="python",
        args=["-m", "be.mcp_server"],
        # MCP SDKs intentionally inherit only a small allow-list by default.
        # Pass the configured database environment to the spawned server.
        env=dict(os.environ),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            tools_response = await session.list_tools()
            tool_names = [tool.name for tool in tools_response.tools]

            result = await session.call_tool(
                "execute_sql_tool",
                {
                    "sql": (
                        "SELECT COUNT(*) AS total_jobs "
                        "FROM warehouse_warehouse.fact_job_postings"
                    )
                },
            )
            schema_result = await session.call_tool(
                "execute_sql_tool",
                {
                    "sql": (
                        "SELECT "
                        "to_regclass('warehouse_warehouse.fact_job_postings') "
                        "AS fact_jobs, "
                        "to_regclass('warehouse_warehouse.job_embeddings') "
                        "AS job_embeddings, "
                        "to_regclass('warehouse_warehouse.company_culture') "
                        "AS company_culture"
                    )
                },
            )

            print(json.dumps({
                "server": initialized.serverInfo.name,
                "version": initialized.serverInfo.version,
                "tools": tool_names,
                "sql_result": result.content[0].text,
                "schema_result": schema_result.content[0].text,
            }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    anyio.run(main)
