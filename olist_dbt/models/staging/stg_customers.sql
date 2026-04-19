select
    customer_id,
    customer_unique_id,
    zip_code_prefix
from {{ source('olist', 'customers') }}
