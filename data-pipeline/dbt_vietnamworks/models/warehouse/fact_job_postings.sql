-- fact_job_posting: 1 row per job posting
-- Incremental + UPSERT

{{
    config(
        materialized='incremental',
        unique_key='job_id'
    )
}}

with source as (
    select * from {{ ref('stg_jobs') }}
    {% if is_incremental() %}
        where ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
),

final as (
    select
        job_id,
        company_id,
        job_title,
        job_level_id,
        type_working_id,
        salary_min,
        salary_max,
        is_salary_visible,
        created_on,
        expired_on,
        approved_on,
        ingested_at,
        regexp_replace(job_description, '<[^>]+>', '', 'g') as job_description,
        regexp_replace(job_requirement, '<[^>]+>', '', 'g') as job_requirement,
        skills,
        working_locations,
        benefits,
        job_functions_v3
    from source
)

select * from final 