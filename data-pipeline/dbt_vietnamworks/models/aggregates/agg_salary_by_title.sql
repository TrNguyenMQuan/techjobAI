{{ config(materialized='table') }}

WITH jobs AS (
    SELECT
        title,
        salary_min_vnd,
        salary_max_vnd,
        salary_currency,
        salary_band
    FROM {{ ref('fact_job') }}
),

categorized AS (
    SELECT
        CASE
            WHEN title ILIKE '%data engineer%' THEN 'Data Engineer'
            WHEN title ILIKE '%backend%' OR title ILIKE '%back-end%' THEN 'Backend Developer'
            WHEN title ILIKE '%frontend%' OR title ILIKE '%front-end%' THEN 'Frontend Developer'
            WHEN title ILIKE '%fullstack%' OR title ILIKE '%full-stack%' OR title ILIKE '%full stack%' THEN 'Fullstack Developer'
            WHEN title ILIKE '%devops%' OR title ILIKE '%dev ops%' THEN 'DevOps Engineer'
            WHEN title ILIKE '%data analyst%' THEN 'Data Analyst'
            WHEN title ILIKE '%data scientist%' THEN 'Data Scientist'
            WHEN title ILIKE '%machine learning%' OR title ILIKE '%ML engineer%' THEN 'ML Engineer'
            WHEN title ILIKE '%software engineer%' OR title ILIKE '%software developer%' THEN 'Software Engineer'
            WHEN title ILIKE '%QA%' OR title ILIKE '%quality%' OR title ILIKE '%test%' THEN 'QA Engineer'
            WHEN title ILIKE '%mobile%' OR title ILIKE '%iOS%' OR title ILIKE '%android%' THEN 'Mobile Developer'
            WHEN title ILIKE '%cloud%' THEN 'Cloud Engineer'
            WHEN title ILIKE '%AI engineer%' OR title ILIKE '%artificial intelligence%' THEN 'AI Engineer'
            WHEN title ILIKE '%product manager%' OR title ILIKE '%product owner%' THEN 'Product Manager'
            WHEN title ILIKE '%business analyst%' THEN 'Business Analyst'
            ELSE 'Other'
        END AS job_category,
        salary_min_vnd,
        salary_max_vnd
    FROM jobs
)

SELECT
    job_category,
    COUNT(*) AS job_count,
    COUNT(salary_min_vnd) AS jobs_with_salary,
    ROUND(AVG(salary_min_vnd)) AS avg_salary_min_vnd,
    ROUND(AVG(salary_max_vnd)) AS avg_salary_max_vnd,
    ROUND(MIN(salary_min_vnd)) AS min_salary_vnd,
    ROUND(MAX(salary_max_vnd)) AS max_salary_vnd,
    -- Salary in triệu VND for readability
    ROUND(AVG(salary_min_vnd) / 1000000, 1) AS avg_min_trieu,
    ROUND(AVG(salary_max_vnd) / 1000000, 1) AS avg_max_trieu
FROM categorized
WHERE job_category != 'Other'
GROUP BY job_category
ORDER BY job_count DESC
