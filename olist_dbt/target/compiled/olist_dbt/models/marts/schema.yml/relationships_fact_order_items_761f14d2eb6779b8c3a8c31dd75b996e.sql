
    
    

with child as (
    select order_date_key as from_field
    from "neondb"."public"."fact_order_items"
    where order_date_key is not null
),

parent as (
    select date_key as to_field
    from "neondb"."public"."dim_dates"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


