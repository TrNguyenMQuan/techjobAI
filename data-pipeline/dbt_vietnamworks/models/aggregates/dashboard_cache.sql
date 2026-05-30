{{ config(materialized='table') }}

SELECT
    (SELECT COUNT(*) FROM {{ ref('fact_job') }}) AS total_jobs,
    (SELECT COUNT(DISTINCT company_name) FROM {{ ref('fact_job') }}) AS total_companies,
    (SELECT COUNT(*) FROM {{ ref('dim_skill') }}) AS total_skills,
    -- In feature branch, dim_location is a separate table based on city_id.
    (SELECT COUNT(*) FROM {{ ref('dim_location') }}) AS total_locations,
    (SELECT COUNT(*) FROM {{ ref('fact_job') }} WHERE salary_min_vnd IS NOT NULL) AS jobs_with_salary,
    (SELECT ROUND(AVG(salary_min_vnd) / 1000000, 1) FROM {{ ref('fact_job') }} WHERE salary_min_vnd IS NOT NULL) AS avg_salary_min_trieu,
    (SELECT ROUND(AVG(salary_max_vnd) / 1000000, 1) FROM {{ ref('fact_job') }} WHERE salary_max_vnd IS NOT NULL) AS avg_salary_max_trieu,
    -- Top 5 skills as JSON array
    (SELECT json_agg(row_to_json(t)) FROM (
        SELECT skill_name, job_count FROM {{ ref('agg_top_skills') }} LIMIT 5
    ) t) AS top_5_skills,
    -- Top 5 salary categories
    (SELECT json_agg(row_to_json(t)) FROM (
        SELECT job_category, avg_min_trieu, avg_max_trieu FROM {{ ref('agg_salary_by_title') }} LIMIT 5
    ) t) AS top_5_salary_categories,
    NOW() AS last_updated
