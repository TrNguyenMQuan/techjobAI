-- fact_job: 1 row per job posting with salary normalization and cleaning.
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
        WHERE ingested_at > (SELECT MAX(extracted_at) FROM {{ this }})
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
        'vnw_' || job_id::text AS source_id,
        job_id,
        job_title AS title,
        company_name,
        company_logo,
        company_id,
        -- Extract primary industry
        COALESCE(job_functions_v3 ->> 'jobFunctionV3NameVI', '') AS industry,
        -- Extract primary city
        CASE
            WHEN jsonb_array_length(working_locations) > 0 THEN
                COALESCE(working_locations -> 0 ->> 'cityNameVI', working_locations -> 0 ->> 'cityName', '')
            ELSE ''
        END AS primary_city,
        working_locations::text AS location_raw,
        pretty_salary AS salary_text,
        salary_currency,
        real_currency,
        salary_min,
        salary_max,
        -- Cap: loại bỏ outlier > 200 triệu/tháng
        CASE WHEN salary_min_vnd_raw > 200000000 THEN NULL ELSE salary_min_vnd_raw END AS salary_min_vnd,
        CASE WHEN salary_max_vnd_raw > 300000000 THEN NULL ELSE salary_max_vnd_raw END AS salary_max_vnd,
        CASE
            WHEN salary_min_vnd_raw IS NULL OR salary_min_vnd_raw > 200000000 THEN 'Thương lượng'
            WHEN salary_min_vnd_raw < 10000000 THEN 'Dưới 10 triệu'
            WHEN salary_min_vnd_raw < 20000000 THEN '10-20 triệu'
            WHEN salary_min_vnd_raw < 30000000 THEN '20-30 triệu'
            WHEN salary_min_vnd_raw < 50000000 THEN '30-50 triệu'
            WHEN salary_min_vnd_raw < 80000000 THEN '50-80 triệu'
            ELSE 'Trên 80 triệu'
        END AS salary_band,
        job_level_vi,
        job_level,
        -- Map work_mode from type_working_id
        CASE type_working_id
            WHEN 1 THEN 'office'
            WHEN 2 THEN 'remote'
            WHEN 3 THEN 'hybrid'
            ELSE 'unknown'
        END AS work_mode,
        regexp_replace(job_description, '<[^>]+>', '', 'g') AS description,
        regexp_replace(job_requirement, '<[^>]+>', '', 'g') AS requirements,
        skills::text AS skills_json,
        benefits::text AS benefits_json,
        job_url AS source_url,
        created_on AS posted_date,
        expired_on AS deadline,
        ingested_at AS extracted_at,
        CAST(NULL AS vector(384)) AS embedding
    FROM salary_converted
)

SELECT * FROM final
