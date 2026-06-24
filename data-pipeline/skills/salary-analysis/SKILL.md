# Salary Analysis

Description: Analyze salary ranges, compensation benchmarks, and hidden/negotiable salary estimates for Vietnam IT jobs.
Triggers: salary, lương, compensation, benchmark, thu nhập, offer, deal lương, hidden salary, predict salary, dự đoán lương

## When to use

Use this skill when the user asks about salary ranges, salary comparison, whether an offer is fair, or salary prediction for a hidden-salary job.

## Workflow

1. Identify the role/title, city, level, work mode, and key skills from the user message.
2. Prefer real market data before prediction:
   - Use `warehouse_marts.mart_salary_benchmark` for skill/level salary medians.
   - Use `warehouse_warehouse.fact_job_postings` for role/city samples.
3. If salary is missing or the user asks about a hypothetical role, call `predict_salary_tool`.
4. Always express salary as triệu VND/tháng.
5. Include sample size when data comes from SQL.
6. Include confidence when data comes from the ML predictor.
7. If comparing three or more roles/skills/cities, use `generate_chart_tool`.

## Response format

- Start with the short conclusion.
- Then show the range, median/average if available, sample size, and confidence if available.
- End with a practical note for negotiation or next action.

## Guardrails

- Do not invent salary numbers. If data is sparse, say so and use prediction as an estimate.
- Separate observed market data from AI-predicted salary.
- Do not present hidden salary predictions as guaranteed compensation.
