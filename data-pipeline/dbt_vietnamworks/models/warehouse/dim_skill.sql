-- dim_skill: 1 row per unique skill, explode from JSONB skills array
with source as(

    select
        job_id,
        skills
    from {{ ref('stg_jobs') }}
    where skills is not null and
          jsonb_array_length(skills::jsonb) > 0
),

exploded as(
    select
        (skill ->> 'skillId')::integer as skill_id,
        skill ->> 'skillName'          as skill_name
    from source,
         jsonb_array_elements(skills::jsonb) as skill 
),

final as (
    select distinct
        skill_id,
        skill_name
    from exploded
    where skill_id is not null 
)

select * from final 
order by skill_id