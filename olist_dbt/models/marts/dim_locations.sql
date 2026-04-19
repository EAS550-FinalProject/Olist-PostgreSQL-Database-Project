select
    zip_code_prefix,
    city,
    state
from {{ ref('stg_locations') }}
