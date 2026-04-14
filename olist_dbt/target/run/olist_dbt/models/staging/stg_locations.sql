
  create view "neondb"."public"."stg_locations__dbt_tmp"
    
    
  as (
    select
    zip_code_prefix,
    city,
    state
from "neondb"."public"."locations"
  );