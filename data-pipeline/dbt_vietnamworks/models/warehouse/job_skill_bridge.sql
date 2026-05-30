{{ config(materialized='table') }}

WITH jobs AS (
    SELECT
        job_id,
        skills
    FROM {{ ref('stg_jobs') }}
    WHERE skills IS NOT NULL AND jsonb_array_length(skills) > 0
),

exploded AS (
    SELECT
        j.job_id,
        (s.skill ->> 'skillId')::integer AS skill_id,
        COALESCE((s.skill ->> 'skillWeight')::integer, 0) AS skill_weight
    FROM jobs j,
    LATERAL jsonb_array_elements(j.skills) AS s(skill)
)

SELECT
    job_id,
    skill_id,
    skill_weight
FROM exploded
