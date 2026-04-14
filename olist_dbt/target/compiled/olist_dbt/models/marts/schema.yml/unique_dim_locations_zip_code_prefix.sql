
    
    

select
    zip_code_prefix as unique_field,
    count(*) as n_records

from "neondb"."public"."dim_locations"
where zip_code_prefix is not null
group by zip_code_prefix
having count(*) > 1


