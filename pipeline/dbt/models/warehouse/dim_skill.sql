-- Dimension: Skills (explode from JSON arrays)
WITH job_skills AS (
    SELECT
        jsonb_array_elements_text(skills_json::jsonb) AS skill_name
    FROM {{ ref('stg_jobs') }}
    WHERE skills_json IS NOT NULL 
      AND skills_json != '' 
      AND skills_json != '[]'
),

unique_skills AS (
    SELECT DISTINCT TRIM(skill_name) AS skill_name
    FROM job_skills
    WHERE TRIM(skill_name) != ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY skill_name) AS id,
    skill_name,
    NOW() AS created_at
FROM unique_skills
