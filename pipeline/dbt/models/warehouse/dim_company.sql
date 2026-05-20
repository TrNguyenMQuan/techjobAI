-- Dimension: Companies
WITH companies AS (
    SELECT DISTINCT
        company_id,
        company_name,
        company_logo,
        industry
    FROM {{ ref('stg_jobs') }}
    WHERE company_name IS NOT NULL AND company_name != ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY company_id) AS id,
    company_id AS source_company_id,
    company_name,
    company_logo AS logo_url,
    industry,
    NOW() AS created_at
FROM companies
