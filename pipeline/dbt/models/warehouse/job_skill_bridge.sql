{{ config(materialized='table') }}

WITH fact AS (
    SELECT
        source_id,
        skills_json
    FROM {{ ref('fact_job') }}
    WHERE skills_json IS NOT NULL AND skills_json != '[]'
),

exploded AS (
    SELECT
        f.source_id,
        sk.skill_name
    FROM fact f,
    LATERAL jsonb_array_elements_text(f.skills_json::jsonb) AS sk(skill_name)
),

with_dim AS (
    SELECT
        e.source_id,
        d.id AS skill_id,
        e.skill_name
    FROM exploded e
    INNER JOIN {{ ref('dim_skill') }} d
        ON LOWER(TRIM(e.skill_name)) = LOWER(TRIM(d.skill_name))
)

SELECT * FROM with_dim
