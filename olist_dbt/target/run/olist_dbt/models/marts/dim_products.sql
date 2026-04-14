
  
    

  create  table "neondb"."public"."dim_products__dbt_tmp"
  
  
    as
  
  (
    select
    product_id,
    product_category,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from "neondb"."public"."stg_products"
  );
  