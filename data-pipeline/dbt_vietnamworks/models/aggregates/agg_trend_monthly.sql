{{ config(materialized='table') }}

-- Monthly job posting trend
SELECT
    DATE_TRUNC('month', posted_date)::date AS month,
    COUNT(*) AS job_count,
    COUNT(CASE WHEN salary_min > 0 THEN 1 END) AS jobs_with_salary
FROM {{ ref('fact_job') }}
WHERE posted_date IS NOT NULL
GROUP BY DATE_TRUNC('month', posted_date)
ORDER BY month DESC
