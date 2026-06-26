# TechJob AI System Proof

This document is a quick checklist to show that TechJob AI is more than an LLM wrapper.

## Runtime capabilities

| Layer | Proof in repo | How to verify |
| --- | --- | --- |
| LLM as orchestrator | `data-pipeline/ai/agent.py` builds a system prompt with SQL/RAG/market tools and project skills. | `GET /api/health/ai` |
| Skills system | `data-pipeline/skills/*/SKILL.md` plus `data-pipeline/ai/skills.py`. | `GET /api/skills` and `GET /api/skills/match?q=cover%20letter` |
| MCP tools | `data-pipeline/be/mcp_server.py` exposes SQL, culture RAG, and table discovery tools. | `python -m be.mcp_server --self-test` |
| External MCP config | `data-pipeline/mcp-client-config.example.json`. | Copy into an MCP-capable client config. |
| AI observability | `data-pipeline/ai/observability.py` logs latency, status, tool usage, and failures. | Check backend logs after `/api/chat`. |
| Offline evals | `data-pipeline/evals/run_evals.py`. | `python data-pipeline/evals/run_evals.py` |
| Data contract | `DATA_CONTRACT.md`. | `GET /api/health/schema` |

## Local demo commands

From repo root:

```bash
docker compose -f data-pipeline/docker-compose.yml up
npm run dev
```

Open:

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- AI health: `http://localhost:8000/api/health/ai`
- Schema health: `http://localhost:8000/api/health/schema`

## Useful smoke tests

```bash
curl http://localhost:8000/api/health/ai
curl http://localhost:8000/api/skills
curl "http://localhost:8000/api/skills/match?q=toi%20muon%20viet%20cover%20letter"
curl "http://localhost:8000/api/search?q=react%20typescript&limit=5"
```

## What should be real by default

Frontend services use `VITE_USE_MOCK=false` by default. Set `VITE_USE_MOCK=true` only for UI-only demos without backend services.

## Remaining production-hardening ideas

- Add CI that runs dbt tests, offline evals, frontend lint/build, and Python import checks.
- Add golden-set eval data for answer accuracy, SQL correctness, search relevance, salary prediction, and cover-letter hallucination.
- Add auth/rate limit boundaries before exposing admin endpoints like embedding rebuild and model retraining.
