-- dim_company: 1 row per company
with source as(
    select * from {{ ref('stg_jobs') }}
),

ranked as (
    select
        company_id, 
        company_name,
        company_logo,
        row_number() over(
            partition by company_id
            order by created_on desc
        ) as rn 
    from source
    where company_id is not null
),

final as (
    select
        company_id,
        company_name,
        company_logo
    from ranked
    where rn = 1
)

select * from final 