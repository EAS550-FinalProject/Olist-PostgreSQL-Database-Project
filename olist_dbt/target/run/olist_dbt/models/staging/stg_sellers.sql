
  create view "neondb"."public"."stg_sellers__dbt_tmp"
    
    
  as (
    select
    seller_id,
    zip_code_prefix
from "neondb"."public"."sellers"
  );