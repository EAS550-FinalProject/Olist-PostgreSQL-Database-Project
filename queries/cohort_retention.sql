-- =============================================================================
-- Query 3: Monthly Cohort Retention Analysis
-- Uses CTEs, window functions (LAG, ROW_NUMBER), and date manipulation
-- =============================================================================

with customer_first_purchase as (
    -- Identify each customer's first purchase month (cohort)
    select
        c.customer_unique_id,
        date_trunc('month', min(o.purchase_timestamp))::date as cohort_month
    from customers c
    inner join orders o
        on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
    group by c.customer_unique_id
),

customer_monthly_activity as (
    -- Track each customer's monthly purchase activity
    select distinct
        c.customer_unique_id,
        date_trunc('month', o.purchase_timestamp)::date as activity_month
    from customers c
    inner join orders o
        on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
),

cohort_activity as (
    -- Join cohort assignment with activity and calculate months since first purchase
    select
        cfp.cohort_month,
        cma.activity_month,
        (
            (extract(year from cma.activity_month) - extract(year from cfp.cohort_month)) * 12
            + (extract(month from cma.activity_month) - extract(month from cfp.cohort_month))
        ) as months_since_first_purchase,
        count(distinct cfp.customer_unique_id) as active_customers
    from customer_first_purchase as cfp
    inner join customer_monthly_activity as cma
        on cfp.customer_unique_id = cma.customer_unique_id
    group by
        cfp.cohort_month,
        cma.activity_month
),

cohort_sizes as (
    -- Get the initial size of each cohort
    select
        cohort_month,
        count(distinct customer_unique_id) as cohort_size
    from customer_first_purchase
    group by cohort_month
),

retention_table as (
    select
        ca.cohort_month,
        cs.cohort_size,
        ca.months_since_first_purchase,
        ca.active_customers,
        round((ca.active_customers::numeric / cs.cohort_size) * 100,2) as retention_rate,
        lag(ca.active_customers) over (
            partition by ca.cohort_month
            order by ca.months_since_first_purchase
        ) as prev_month_active,
        row_number() over (
            partition by ca.cohort_month
            order by ca.months_since_first_purchase
        ) as month_number
    from cohort_activity as ca
    inner join cohort_sizes as cs
        on ca.cohort_month = cs.cohort_month
    where ca.months_since_first_purchase between 0 and 12
)

select
    cohort_month,
    cohort_size,
    months_since_first_purchase,
    active_customers,
    retention_rate,
    prev_month_active,
    case
        when prev_month_active is not null and prev_month_active > 0 then
            round(
                ((active_customers - prev_month_active)::numeric / prev_month_active) * 100,
                2
            )
        else null
    end as month_over_month_change_pct
from retention_table
order by cohort_month, months_since_first_purchase;