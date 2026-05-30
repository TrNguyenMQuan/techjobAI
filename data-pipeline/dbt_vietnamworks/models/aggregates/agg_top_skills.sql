{{ config(materialized='table') }}

-- Top skills by job count
SELECT
    sk.skill_name,
    COUNT(*) AS job_count
FROM {{ ref('job_skill_bridge') }} b
JOIN {{ ref('dim_skill') }} sk ON sk.skill_id = b.skill_id
GROUP BY sk.skill_name
ORDER BY job_count DESC
LIMIT 50
