
  
    

  create  table "neondb"."public"."dim_customers__dbt_tmp"
  
  
    as
  
  (
    with customers as (
    select * from "neondb"."public"."stg_customers"
),

locations as (
    select * from "neondb"."public"."stg_locations"
)

select
    c.customer_id,
    c.customer_unique_id,
    c.zip_code_prefix,
    l.city as customer_city,
    l.state as customer_state
from customers as c
left join locations as l
    on c.zip_code_prefix = l.zip_code_prefix
  );
  