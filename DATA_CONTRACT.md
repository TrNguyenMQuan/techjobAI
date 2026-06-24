# TechJob AI Data Contract

This file is the source of truth for code, prompts, MCP tools, and evals that query the warehouse.

## Canonical warehouse objects

| Purpose | Object | Notes |
| --- | --- | --- |
| Job postings | `warehouse_warehouse.fact_job_postings` | Canonical 1-row-per-job table. Prefer this over legacy `fact_job`. |
| Companies | `warehouse_warehouse.dim_company` | Join with `fact_job_postings.company_id`. |
| Job levels | `warehouse_warehouse.dim_job_level` | Join with `fact_job_postings.job_level_id`. |
| Working type | `warehouse_warehouse.dim_type_working` | Join with `fact_job_postings.type_working_id`. |
| Embeddings | `warehouse_warehouse.job_embeddings` | `job_id`, `embedding vector(384)`, `model_name`, `embedded_at`. |
| Skill demand | `warehouse_marts.mart_skill_demand` | Weekly demand by skill. |
| Salary benchmark | `warehouse_marts.mart_salary_benchmark` | Salary medians by skill and level. |
| Location demand | `warehouse_marts.mart_location_demand` | Job count by city. |

## `fact_job_postings` columns used by the app

| Field | Meaning |
| --- | --- |
| `job_id` | Primary job identifier. |
| `company_id` | Foreign key to `dim_company`. |
| `job_title` | Display title and search title. |
| `job_level_id` | Foreign key to `dim_job_level`. |
| `type_working_id` | Foreign key to `dim_type_working`. |
| `salary_min`, `salary_max` | Normalized monthly VND salary bounds. Nullable means hidden/negotiable. |
| `created_on`, `expired_on`, `approved_on` | Posting lifecycle dates. |
| `job_description`, `job_requirement` | Cleaned text used by semantic search and cover letter generation. |
| `skills` | JSONB array from source data. |
| `working_locations` | JSONB array; the first city is read with `working_locations->0->>'city'`. |

## Query conventions

Use this pattern for job display queries:

```sql
SELECT
  f.job_id,
  f.job_title,
  c.company_name,
  f.salary_min,
  f.salary_max,
  COALESCE(f.working_locations->0->>'city', 'Unknown') AS primary_city
FROM warehouse_warehouse.fact_job_postings f
LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
ORDER BY f.created_on DESC NULLS LAST
LIMIT 20;
```

Use this pattern for semantic search:

```sql
SELECT
  f.job_id,
  f.job_title,
  c.company_name,
  1 - (e.embedding <=> :query_vector::vector) AS similarity
FROM warehouse_warehouse.fact_job_postings f
JOIN warehouse_warehouse.job_embeddings e ON f.job_id = e.job_id
LEFT JOIN warehouse_warehouse.dim_company c ON f.company_id = c.company_id
ORDER BY e.embedding <=> :query_vector::vector
LIMIT 10;
```

## Deprecated compatibility notes

Older code and logs may mention `warehouse_warehouse.fact_job`. New code, prompts, tools, and docs should use `warehouse_warehouse.fact_job_postings`.

The backend exposes `/api/health/schema` so deployments can verify required objects before enabling AI features.
