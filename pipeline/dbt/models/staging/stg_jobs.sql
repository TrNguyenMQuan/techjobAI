-- Staging model: clean và chuẩn hóa dữ liệu từ raw_jobs
WITH source AS (
    SELECT * FROM staging.raw_jobs
    WHERE is_processed = FALSE OR is_processed IS NULL
),

cleaned AS (
    SELECT
        id,
        source_id,
        raw_title AS title,
        raw_company_name AS company_name,
        
        -- Parse location: lấy city đầu tiên từ JSON array
        CASE 
            WHEN raw_location LIKE '[%' THEN
                TRIM(BOTH '"' FROM (raw_location::jsonb ->> 0))
            ELSE raw_location
        END AS primary_city,
        raw_location AS location_raw,
        
        -- Salary
        raw_salary AS salary_text,
        COALESCE((raw_payload::jsonb ->> 'salary_min')::numeric, 0) AS salary_min,
        COALESCE((raw_payload::jsonb ->> 'salary_max')::numeric, 0) AS salary_max,
        COALESCE(raw_payload::jsonb ->> 'salary_currency', 'VND') AS salary_currency,
        
        -- Level
        raw_experience AS job_level_vi,
        COALESCE(raw_payload::jsonb ->> 'job_level', '') AS job_level,
        
        -- Type working: 1=Office, 2=Remote, 3=Hybrid
        CASE (raw_payload::jsonb ->> 'type_working_id')::int
            WHEN 1 THEN 'office'
            WHEN 2 THEN 'remote'
            WHEN 3 THEN 'hybrid'
            ELSE 'unknown'
        END AS work_mode,
        
        -- Description (strip HTML tags)
        REGEXP_REPLACE(raw_description, '<[^>]+>', '', 'g') AS description,
        REGEXP_REPLACE(raw_requirements, '<[^>]+>', '', 'g') AS requirements,
        
        -- Benefits
        raw_benefits AS benefits_json,
        
        -- Skills (JSON array of skill names)
        raw_skills AS skills_json,
        
        -- Industry
        COALESCE(raw_payload::jsonb ->> 'industry', '') AS industry,
        
        -- URLs
        raw_logo_url AS company_logo,
        raw_source_url AS source_url,
        
        -- Dates
        CASE
            WHEN raw_posted_date ~ '^\d{4}-\d{2}-\d{2}' THEN raw_posted_date::timestamp
            ELSE NULL
        END AS posted_date,
        CASE
            WHEN raw_deadline ~ '^\d{4}-\d{2}-\d{2}' THEN raw_deadline::timestamp
            ELSE NULL
        END AS deadline,
        
        -- Company ID
        (raw_payload::jsonb ->> 'company_id')::int AS company_id,
        
        ingested_at
        
    FROM source
)

SELECT * FROM cleaned
