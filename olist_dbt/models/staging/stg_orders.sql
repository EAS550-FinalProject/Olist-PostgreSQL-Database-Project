select
    order_id,
    customer_id,
    order_status,
    purchase_timestamp as order_purchase_timestamp,
    approved_at as order_approved_at,
    delivered_carrier_date as order_delivered_carrier_date,
    delivered_customer_date as order_delivered_customer_date,
    estimated_delivery_date as order_estimated_delivery_date
from {{ source('olist', 'orders') }}
