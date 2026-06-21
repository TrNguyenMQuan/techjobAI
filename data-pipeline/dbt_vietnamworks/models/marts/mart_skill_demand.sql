{{
    config(
        materialized='table',
        schema='marts'
    )
}}

SELECT 
    skill_id,
    skill_name,
    DATE_TRUNC('week', created_on)::date AS week_start,
    COUNT(DISTINCT job_id)               AS job_count
from {{ ref('fact_job_skills') }}
GROUP BY skill_id, skill_name, DATE_TRUNC('week', created_on)
ORDER BY week_start DESC, job_count DESC

