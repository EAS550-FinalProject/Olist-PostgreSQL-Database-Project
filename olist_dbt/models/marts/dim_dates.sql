with order_dates as (
    select distinct order_purchase_timestamp::date as date_day
    from {{ ref('stg_orders') }}
    where order_purchase_timestamp is not null
)

select
    date_day as date_key,
    extract(year from date_day)::int as date_year,
    extract(quarter from date_day)::int as date_quarter,
    extract(month from date_day)::int as date_month,
    extract(day from date_day)::int as date_day_of_month,
    extract(dow from date_day)::int as day_of_week,
    to_char(date_day, 'Day') as day_name,
    to_char(date_day, 'Month') as month_name,
    extract(dow from date_day) in (0, 6) as is_weekend
from order_dates
