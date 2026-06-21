{{
    config(
        materialized="table",
        schema="marts"
    )
}}

WITH job_locations_exploded AS(
    SELECT job_id,
           jsonb_array_elements(working_locations) AS location_element
    FROM {{ ref('fact_job_postings') }}
    WHERE working_locations IS NOT null
        AND jsonb_array_length(working_locations) > 0
)

SELECT
    (location_element->>'cityId')::integer AS city_id,
    location_element->>'cityNameVI'        AS city_name_vi,
    COUNT(DISTINCT job_id)                 AS job_count
FROM job_locations_exploded
WHERE location_element->>'cityId' IS NOT null
GROUP BY (location_element->>'cityId')::integer, location_element->>'cityNameVI'
ORDER BY job_count DESC