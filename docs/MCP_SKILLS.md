# MCP & Skills Architecture

TechJob AI exposes its agent capabilities in two layers:

1. **MCP server** — standard tool interface for external LLM clients.
2. **Project skills** — markdown playbooks loaded into the LangGraph agent prompt.

## MCP server

Run the MCP server over stdio:

```bash
cd data-pipeline
python -m be.mcp_server
```

Run local safety checks:

```bash
cd data-pipeline
python -m be.mcp_server --self-test
```

The MCP server exposes:

- `execute_sql_tool`
- `execute_rag_culture_tool`
- `list_techjob_tables_tool`

Example MCP client config:

```json
{
  "mcpServers": {
    "techjob-ai": {
      "command": "python",
      "args": ["-m", "be.mcp_server"],
      "cwd": "/path/to/techjobAI/data-pipeline"
    }
  }
}
```

The same underlying functions are still importable by the in-process LangGraph
agent, so existing backend behavior remains compatible.

## Project skills

Skills live under:

```text
data-pipeline/skills/
  salary-analysis/SKILL.md
  job-search/SKILL.md
  market-insight/SKILL.md
  cover-letter/SKILL.md
```

Each skill is a markdown playbook with:

- `Description:`
- `Triggers:`
- `When to use`
- `Workflow`
- `Response format`
- `Guardrails`

The agent loads these through `ai.skills` and injects them into its system
prompt via `build_system_prompt()` in `ai.agent`.

## Skills API

The FastAPI backend exposes:

- `GET /api/skills` — list available skills
- `GET /api/skills/match?q=...` — show which skills match a user query

## Adding a new skill

Create:

```text
data-pipeline/skills/<slug>/SKILL.md
```

Use this template:

```md
# Skill Name

Description: One sentence describing the skill.
Triggers: comma, separated, trigger, phrases

## When to use

Describe when the agent should follow this playbook.

## Workflow

1. First step.
2. Second step.

## Response format

Describe the expected answer structure.

## Guardrails

- Things the agent must not do.
- Accuracy and safety constraints.
```
