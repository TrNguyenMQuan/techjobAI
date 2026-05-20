{{ config(materialized='table') }}

WITH source AS (
    SELECT * FROM {{ ref('stg_jobs') }}
),

salary_normalized AS (
    SELECT
        *,
        -- Detect if salary is yearly
        CASE
            WHEN salary_text ILIKE '%/năm%' OR salary_text ILIKE '%/year%' THEN TRUE
            ELSE FALSE
        END AS is_yearly,

        -- Detect real currency: nếu salary_min > 100,000 thì chắc chắn là VND dù display có $
        CASE
            WHEN salary_min > 100000 THEN 'VND'
            WHEN salary_currency = 'USD' THEN 'USD'
            WHEN salary_text ILIKE '%$%' OR salary_text ILIKE '%usd%' THEN 'USD'
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
            WHEN real_currency = 'USD' AND is_yearly THEN (salary_min * 26300) / 12
            WHEN real_currency = 'USD' THEN salary_min * 26300
            WHEN is_yearly THEN salary_min / 12
            -- VND > 100 triệu → likely yearly → divide by 12
            WHEN real_currency = 'VND' AND salary_min > 100000000 THEN salary_min / 12
            ELSE salary_min
        END AS salary_min_vnd_raw,

        CASE
            WHEN salary_max IS NULL OR salary_max = 0 THEN NULL
            WHEN real_currency = 'USD' AND is_yearly THEN (salary_max * 26300) / 12
            WHEN real_currency = 'USD' THEN salary_max * 26300
            WHEN is_yearly THEN salary_max / 12
            WHEN real_currency = 'VND' AND salary_max > 100000000 THEN salary_max / 12
            ELSE salary_max
        END AS salary_max_vnd_raw


    FROM salary_normalized
),

final AS (
    SELECT
        source_id,
        id AS job_id,
        title,
        company_name,
        company_logo,
        company_id,
        industry,
        primary_city,
        location_raw,
        salary_text,
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
        work_mode,
        description,
        requirements,
        skills_json,
        benefits_json,
        source_url,
        posted_date,
        deadline,
        ingested_at AS extracted_at
    FROM salary_converted
)

SELECT * FROM final
