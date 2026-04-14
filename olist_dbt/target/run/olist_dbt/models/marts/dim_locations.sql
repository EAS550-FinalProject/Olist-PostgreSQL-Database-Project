
  
    

  create  table "neondb"."public"."dim_locations__dbt_tmp"
  
  
    as
  
  (
    select
    zip_code_prefix,
    city,
    state
from "neondb"."public"."stg_locations"
  );
  