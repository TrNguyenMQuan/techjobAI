-- dim_location: 1 row per uniqure city explode from JSONB

with source as (
    select working_locations
    from {{ ref('stg_jobs') }}
    where working_locations is not null 
        and jsonb_array_length(working_locations::jsonb) > 0
),

exploded as (
    select
        (loc ->> 'cityId')::integer as city_id,
        loc ->> 'cityNameVI'        as city_name_vi
    from source,
        jsonb_array_elements(working_locations::jsonb) as loc
),

final as (
    select distinct
        city_id,
        city_name_vi
    from exploded 
    where city_id is not null 
)

select * from final 
order by city_id