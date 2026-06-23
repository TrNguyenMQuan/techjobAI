-- fact_job_postings: 1 row per job posting with salary normalization and cleaning.
-- Incremental materialization to preserve ML embeddings and speed up runs.

{{
    config(
        materialized='incremental',
        unique_key='job_id'
    )
}}

WITH source AS (
    SELECT * FROM {{ ref('stg_jobs') }}
    {% if is_incremental() %}
        WHERE ingested_at > (SELECT MAX(ingested_at) FROM {{ this }})
    {% endif %}
),

salary_normalized AS (
    SELECT
        *,
        -- Detect if salary is yearly
        CASE
            WHEN pretty_salary ILIKE '%/năm%' OR pretty_salary ILIKE '%/year%' THEN TRUE
            ELSE FALSE
        END AS is_yearly,

        -- Detect real currency
        CASE
            WHEN salary_min > 100000 THEN 'VND'
            WHEN salary_currency = 'USD' THEN 'USD'
            WHEN pretty_salary ILIKE '%$%' OR pretty_salary ILIKE '%usd%' THEN 'USD'
            ELSE 'VND'
        END AS real_currency

    FROM source
),

salary_converted AS (
    SELECT
        *,
        -- Convert to VND/tháng
        CASE
            WHEN salary_min IS NULL OR salary_min = 0 THEN NULL
            WHEN real_currency = 'USD' AND is_yearly THEN (salary_min::bigint * 26300) / 12
            WHEN real_currency = 'USD' THEN salary_min::bigint * 26300
            WHEN is_yearly THEN salary_min / 12
            -- VND > 100 triệu -> likely yearly -> divide by 12
            WHEN real_currency = 'VND' AND salary_min > 100000000 THEN salary_min / 12
            ELSE salary_min
        END AS salary_min_vnd_raw,

        CASE
            WHEN salary_max IS NULL OR salary_max = 0 THEN NULL
            WHEN real_currency = 'USD' AND is_yearly THEN (salary_max::bigint * 26300) / 12
            WHEN real_currency = 'USD' THEN salary_max::bigint * 26300
            WHEN is_yearly THEN salary_max / 12
            WHEN real_currency = 'VND' AND salary_max > 100000000 THEN salary_max / 12
            ELSE salary_max
        END AS salary_max_vnd_raw

    FROM salary_normalized
),

final AS (
    SELECT
        job_id,
        company_id,
        job_title,
        job_level_id,
        type_working_id,
        
        -- Cap: loại bỏ outlier > 200 triệu/tháng
        CASE WHEN salary_min_vnd_raw > 200000000 THEN NULL ELSE salary_min_vnd_raw END AS salary_min,
        CASE WHEN salary_max_vnd_raw > 300000000 THEN NULL ELSE salary_max_vnd_raw END AS salary_max,
        
        is_salary_visible,
        created_on,
        expired_on,
        approved_on,
        ingested_at,
        
        -- Text cleaning
        regexp_replace(job_description, '<[^>]+>', '', 'g') AS job_description,
        regexp_replace(job_requirement, '<[^>]+>', '', 'g') AS job_requirement,
        
        -- JSONB
        skills,
        working_locations,
        benefits,
        job_functions_v3
        
    FROM salary_converted
)

SELECT * FROM final
