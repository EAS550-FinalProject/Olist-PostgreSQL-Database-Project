select
    zip_code_prefix,
    city,
    state
from {{ source('olist', 'locations') }}
