select
    seller_id,
    zip_code_prefix
from {{ source('olist', 'sellers') }}
