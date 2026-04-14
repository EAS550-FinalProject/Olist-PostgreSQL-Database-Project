
  create view "neondb"."public"."stg_order_payments__dbt_tmp"
    
    
  as (
    select
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
from "neondb"."public"."order_payments"
  );