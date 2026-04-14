select
    p.product_id,
    p.weight_g as product_weight_g,
    p.length_cm as product_length_cm,
    p.height_cm as product_height_cm,
    p.width_cm as product_width_cm,
    coalesce(pc.category_name_english, p.category_name) as product_category
from {{ source('olist', 'products') }} as p
left join {{ source('olist', 'product_categories') }} as pc
    on p.category_name = pc.category_name
