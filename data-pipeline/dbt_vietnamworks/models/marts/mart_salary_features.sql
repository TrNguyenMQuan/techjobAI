{{
    config(
        materialized="table",
        schema="marts"
    )
}}

{% set top_skills = var('top_skills') %}

WITH base AS (
    SELECT job_id,
           job_level_id,
           type_working_id,
           (working_locations::jsonb->0->>'cityId')::integer AS city_id,
           jsonb_array_length(skills::jsonb)                 AS skill_count,
           salary_min,
           salary_max,
           (salary_min + salary_max) / 2              AS salary_midpoint,
           DATE_TRUNC('week', created_on)::date       AS week_start
    FROM {{ ref('fact_job_postings') }}
    WHERE is_salary_visible = true
        AND salary_min IS NOT NULL
        AND salary_max IS NOT NULL
),

skill_flags AS (
    SELECT job_id
        {% for skill in top_skills %},
        bool_or(skill_name = '{{ skill['name'] }}') AS has_{{ skill['slug'] }}
        {% endfor %}
    FROM {{ ref('fact_job_skills') }}
    GROUP BY job_id
)

SELECT b.job_id, 
       b.job_level_id,
       b.type_working_id,
       b.city_id,
       b.skill_count,
       b.salary_min,
       b.salary_max,
       b.salary_midpoint,
       b.week_start
       {% for skill in top_skills %},
       COALESCE(sf.has_{{ skill['slug'] }}, false) AS has_{{ skill['slug'] }}
       {% endfor %}
FROM base AS b 
LEFT JOIN skill_flags AS sf USING (job_id)