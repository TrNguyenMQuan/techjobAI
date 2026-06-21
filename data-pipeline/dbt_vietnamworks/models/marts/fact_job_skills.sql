{{
    config(
        materialized='table',
        schema='marts'
    )
}}

WITH job_skills_exploded AS (
    SELECT 
        job_id,
        created_on,
        jsonb_array_elements(skills::jsonb) AS skill_element
    FROM {{ ref('fact_job_postings') }}
    WHERE skills is not null 
        AND jsonb_array_length(skills::jsonb) > 0
)

SELECT
    job_id,
    (skill_element->>'skillId')::integer AS skill_id,
    skill_element->>'skillName'          AS skill_name,
    created_on
FROM job_skills_exploded
WHERE skill_element->>'skillId' IS NOT null


    