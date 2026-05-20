-- Dimension: Locations
WITH locations AS (
    SELECT DISTINCT
        primary_city
    FROM {{ ref('stg_jobs') }}
    WHERE primary_city IS NOT NULL AND primary_city != ''
)

SELECT
    ROW_NUMBER() OVER (ORDER BY primary_city) AS id,
    primary_city AS city_name,
    CASE primary_city
        WHEN 'Hồ Chí Minh' THEN 'Ho Chi Minh'
        WHEN 'Hà Nội' THEN 'Ha Noi'
        WHEN 'Đà Nẵng' THEN 'Da Nang'
        ELSE primary_city
    END AS city_name_en,
    NOW() AS created_at
FROM locations
