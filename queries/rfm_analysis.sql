-- =============================================================================
-- Query 1: Customer RFM (Recency, Frequency, Monetary) Analysis
-- Uses CTEs and window functions (NTILE, RANK) to segment customers
-- =============================================================================

with customer_orders as (
    -- Aggregate order-level metrics per unique customer
    select
        c.customer_unique_id,
        count(distinct o.order_id) as total_orders,
        sum(oi.price + oi.freight_value) as total_spent,
        max(o.purchase_timestamp) as last_purchase_date,
        min(o.purchase_timestamp) as first_purchase_date
    from customers c
    inner join orders o
        on c.customer_id = o.customer_id
    inner join order_items oi
        on o.order_id = oi.order_id
    where o.order_status = 'delivered'
    group by c.customer_unique_id
),

rfm_scores as (
    -- Calculate RFM scores using NTILE to split into quartiles
    select
        customer_unique_id,
        total_orders,
        total_spent,
        last_purchase_date,
        first_purchase_date,
        extract(
            day from (
                (select max(purchase_timestamp) from orders)
                - last_purchase_date
            )
        )::int as recency_days,
        ntile(4) over (order by last_purchase_date asc) as recency_score,
        ntile(4) over (order by total_orders asc) as frequency_score,
        ntile(4) over (order by total_spent asc) as monetary_score
    from customer_orders
),

rfm_segments as (
    select
        *,
        recency_score + frequency_score + monetary_score as rfm_total,
        rank() over (order by total_spent desc) as spending_rank,
        case
            when recency_score >= 3 and frequency_score >= 3 and monetary_score >= 3
                then 'Champions'
            when recency_score >= 3 and frequency_score >= 2
                then 'Loyal Customers'
            when recency_score >= 3 and monetary_score >= 2
                then 'Potential Loyalists'
            when recency_score <= 2 and frequency_score >= 3
                then 'At Risk'
            when recency_score <= 1 and frequency_score <= 1
                then 'Lost'
            else 'Others'
        end as customer_segment
    from rfm_scores
)

select
    customer_segment,
    count(*) as customer_count,
    round(avg(recency_days),1) as avg_recency_days,
    round(avg(total_orders),2) as avg_orders,
    round(avg(total_spent)::numeric,2) as avg_total_spent,
    round(min(total_spent)::numeric,2) as min_spent,
    round(max(total_spent)::numeric,2) as max_spent
from rfm_segments
group by customer_segment
order by avg_total_spent desc;