
  create view "neondb"."public"."stg_customers__dbt_tmp"
    
    
  as (
    select
    customer_id,
    customer_unique_id,
    zip_code_prefix
from "neondb"."public"."customers"
  );