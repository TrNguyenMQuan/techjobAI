{{
    config(
        materialized="table",
        schema="marts"
    )
}}

WITH jobs_with_salary AS(
    SELECT job_id, salary_min, salary_max, job_level_id
    FROM {{ ref('fact_job_postings') }}
    WHERE is_salary_visible = true
        AND salary_min IS NOT NULL
        AND salary_max IS NOT NULL
),

job_skill_salary AS(
    SELECT fjs.skill_id,
           fjs.skill_name,
           jws.job_level_id,
           jws.salary_min,
           jws.salary_max
    FROM {{ ref('fact_job_skills') }} AS fjs
    INNER JOIN jobs_with_salary AS jws USING (job_id)
)

SELECT jss.skill_id,
       jss.skill_name,
       jss.job_level_id,
       COALESCE(lvl.level_name_vi, 'Chưa map (id=' || jss.job_level_id || ')') AS level_name_vi,
       COALESCE(lvl.seniority_order, 99)                                        AS seniority_order,
       COUNT(*) AS sample_size,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_min)::integer as median_salary_min,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_max)::integer as median_salary_max
FROM job_skill_salary AS jss
LEFT JOIN {{ ref('dim_job_level') }} AS lvl USING (job_level_id)
GROUP BY jss.skill_id, jss.skill_name, jss.job_level_id,
         lvl.level_name_vi, lvl.seniority_order
HAVING COUNT(*) >= 3 -- ignore combination have < 3 sample because meadian isnot meaningful
