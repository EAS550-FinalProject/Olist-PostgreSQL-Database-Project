
  
    

  create  table "neondb"."public"."dim_sellers__dbt_tmp"
  
  
    as
  
  (
    with sellers as (
    select * from "neondb"."public"."stg_sellers"
),

locations as (
    select * from "neondb"."public"."stg_locations"
)

select
    s.seller_id,
    s.zip_code_prefix,
    l.city as seller_city,
    l.state as seller_state
from sellers as s
left join locations as l
    on s.zip_code_prefix = l.zip_code_prefix
  );
  