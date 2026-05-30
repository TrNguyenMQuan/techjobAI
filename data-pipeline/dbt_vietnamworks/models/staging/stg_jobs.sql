--Staging view for way to read silver.jobs

with source as (
    select * from {{ source('silver', 'jobs') }}
),
renamed as (
    select 
        -- ID
        job_id,
        company_id,

        -- Job info
        job_title,
        job_level_id,
        type_working_id,

        -- Company
        company_name,
        company_logo,

        -- Salary
        salary_min,
        salary_max,
        is_salary_visible,
        pretty_salary,
        salary_currency,

        -- Job level text
        job_level,
        job_level_vi,

        -- URL
        job_url,

        -- Timestamp
        created_on,
        expired_on,
        approved_on,
        ingested_at,

        -- JSONB
        skills,
        working_locations,
        benefits,
        job_functions_v3,

        -- Text content
        job_description,
        job_requirement
    
    from source
)

select * from renamed