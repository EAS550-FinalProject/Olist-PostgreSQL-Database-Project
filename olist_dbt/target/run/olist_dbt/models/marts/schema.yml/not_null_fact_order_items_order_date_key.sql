
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select order_date_key
from "neondb"."public"."fact_order_items"
where order_date_key is null



  
  
      
    ) dbt_internal_test