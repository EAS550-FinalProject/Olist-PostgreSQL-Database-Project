with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

payments as (
    select
        order_id,
        sum(payment_value) as total_payment_value,
        count(payment_sequential) as payment_count,
        string_agg(distinct payment_type, ', ') as payment_types
    from {{ ref('stg_order_payments') }}
    group by order_id
),

reviews as (
    select
        order_id,
        avg(review_score) as avg_review_score,
        count(*) as review_count
    from {{ ref('stg_order_reviews') }}
    group by order_id
)

select
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    o.customer_id,
    o.order_purchase_timestamp::date as order_date_key,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value as total_item_value,
    p.total_payment_value as order_payment_value,
    p.payment_count,
    p.payment_types,
    r.avg_review_score,
    r.review_count,
    case
        when o.order_delivered_customer_date <= o.order_estimated_delivery_date
            then true
        else false
    end as delivered_on_time
from order_items as oi
inner join orders as o
    on oi.order_id = o.order_id
left join payments as p
    on oi.order_id = p.order_id
left join reviews as r
    on oi.order_id = r.order_id
