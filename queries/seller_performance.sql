-- =============================================================================
-- Query 2: Seller Performance Dashboard
-- Uses CTEs, window functions (RANK, PERCENT_RANK, AVG OVER), and aggregations
-- =============================================================================

with seller_metrics as (
    -- Core seller-level aggregations
    select
        s.seller_id,
        l.city as seller_city,
        l.state as seller_state,
        count(distinct oi.order_id) as total_orders,
        count(oi.order_item_id) as total_items_sold,
        round(sum(oi.price)::numeric, 2) as total_revenue,
        round(avg(oi.price)::numeric, 2) as avg_item_price,
        round(sum(oi.freight_value)::numeric, 2) as total_freight_collected,
        round(avg(r.review_score)::numeric, 2) as avg_review_score,
        count(distinct r.review_id) as total_reviews
    from sellers s
    inner join order_items oi on s.seller_id = oi.seller_id
    inner join orders o on oi.order_id = o.order_id
    left join locations l on s.zip_code_prefix = l.zip_code_prefix
    left join order_reviews r on o.order_id = r.order_id and r.review_id is not null
    where o.order_status = 'delivered'
    group by s.seller_id, l.city, l.state
),

seller_rankings as (
    select
        *,
        -- Revenue ranking
        rank() over (order by total_revenue desc) as revenue_rank,
        -- Percentile ranking for review scores
        round(percent_rank() over (order by avg_review_score)::numeric, 4) as review_percentile,
        -- State-level revenue ranking
        rank() over (
            partition by seller_state
            order by total_revenue desc
        ) as state_revenue_rank,
        -- Running average revenue across all sellers ordered by revenue
        round(
            avg(total_revenue) over (
                order by total_revenue desc
                rows between 4 preceding and current row
            )::numeric, 2
        ) as rolling_5_avg_revenue
    from seller_metrics
)

select
    seller_id,
    seller_city,
    seller_state,
    total_orders,
    total_items_sold,
    total_revenue,
    avg_item_price,
    avg_review_score,
    total_reviews,
    revenue_rank,
    state_revenue_rank,
    round(review_percentile * 100, 2) as review_percentile_pct,
    rolling_5_avg_revenue
from seller_rankings
where revenue_rank <= 50
order by revenue_rank;
