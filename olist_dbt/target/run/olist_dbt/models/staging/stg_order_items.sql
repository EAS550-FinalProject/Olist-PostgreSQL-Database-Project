
  create view "neondb"."public"."stg_order_items__dbt_tmp"
    
    
  as (
    select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value
from "neondb"."public"."order_items"
  );