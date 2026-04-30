"""RFM (Recency, Frequency, Monetary) customer segmentation.

Mirrors the Phase 2 analytical query queries/rfm_analysis.sql but lets the
user pick how aggressive each segment threshold is and re-runs against live
data. Results are cached so the slider changes don't all hit Neon.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from db import run_query

st.set_page_config(page_title="RFM Analysis", page_icon=":busts_in_silhouette:", layout="wide")

st.title("Customer RFM Segmentation")
st.caption(
    "NTILE quartiles over Recency, Frequency, and Monetary value, computed from "
    "delivered orders in the OLTP layer."
)

with st.sidebar:
    st.header("Segment thresholds")
    high_score = st.slider(
        "Score threshold for 'high' R/F/M (Champions, Loyal, …)",
        min_value=2,
        max_value=4,
        value=3,
        help="A customer's R/F/M scores are 1-4 (NTILE quartiles). Raising this makes 'Champions' a smaller, more elite group.",
    )
    low_score = st.slider(
        "Score threshold for 'low' R/F/M (Lost, At Risk)",
        min_value=1,
        max_value=2,
        value=2,
    )


@st.cache_data(ttl=600, show_spinner="Computing RFM segments…")
def fetch_rfm(high: int, low: int) -> pd.DataFrame:
    return run_query(
        """
        with customer_orders as (
            select
                c.customer_unique_id,
                count(distinct o.order_id) as total_orders,
                sum(oi.price + oi.freight_value) as total_spent,
                max(o.purchase_timestamp) as last_purchase_date
            from customers c
            inner join orders o on c.customer_id = o.customer_id
            inner join order_items oi on o.order_id = oi.order_id
            where o.order_status = 'delivered'
            group by c.customer_unique_id
        ),
        rfm_scores as (
            select
                customer_unique_id,
                total_orders,
                total_spent,
                extract(day from (
                    (select max(purchase_timestamp) from orders) - last_purchase_date
                ))::int as recency_days,
                ntile(4) over (order by last_purchase_date asc) as recency_score,
                ntile(4) over (order by total_orders asc) as frequency_score,
                ntile(4) over (order by total_spent asc) as monetary_score
            from customer_orders
        ),
        rfm_segments as (
            select
                *,
                case
                    when recency_score >= :high and frequency_score >= :high and monetary_score >= :high
                        then 'Champions'
                    when recency_score >= :high and frequency_score >= 2 then 'Loyal Customers'
                    when recency_score >= :high and monetary_score >= 2 then 'Potential Loyalists'
                    when recency_score <= :low and frequency_score >= :high then 'At Risk'
                    when recency_score <= 1 and frequency_score <= 1 then 'Lost'
                    else 'Others'
                end as customer_segment
            from rfm_scores
        )
        select
            customer_segment,
            count(*) as customer_count,
            round(avg(recency_days), 1) as avg_recency_days,
            round(avg(total_orders), 2) as avg_orders,
            round(avg(total_spent)::numeric, 2) as avg_total_spent,
            round(sum(total_spent)::numeric, 2) as segment_revenue
        from rfm_segments
        group by customer_segment
        order by avg_total_spent desc
        """,
        {"high": high, "low": low},
    )


df = fetch_rfm(high_score, low_score)

if df.empty:
    st.warning("No RFM data returned.")
    st.stop()

total_customers = int(df["customer_count"].sum())
total_revenue = float(df["segment_revenue"].sum())

c1, c2, c3 = st.columns(3)
c1.metric("Customers segmented", f"{total_customers:,}")
c2.metric("Total revenue (BRL)", f"R$ {total_revenue:,.0f}")
c3.metric("Segments", len(df))

st.divider()

left, right = st.columns([3, 2])

with left:
    st.subheader("Customers per segment")
    bar = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("customer_count:Q", title="Customers"),
            y=alt.Y("customer_segment:N", sort="-x", title=None),
            color=alt.Color("customer_segment:N", legend=None),
            tooltip=[
                alt.Tooltip("customer_segment:N", title="Segment"),
                alt.Tooltip("customer_count:Q", title="Customers", format=","),
                alt.Tooltip("avg_total_spent:Q", title="Avg Spend (BRL)", format=",.2f"),
                alt.Tooltip("segment_revenue:Q", title="Segment Revenue", format=",.0f"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(bar, use_container_width=True)

with right:
    st.subheader("Revenue share")
    pie = (
        alt.Chart(df)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("segment_revenue:Q"),
            color=alt.Color("customer_segment:N", title="Segment"),
            tooltip=[
                alt.Tooltip("customer_segment:N", title="Segment"),
                alt.Tooltip("segment_revenue:Q", title="Revenue (BRL)", format=",.0f"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(pie, use_container_width=True)

st.subheader("Segment detail")
st.dataframe(df, hide_index=True, use_container_width=True)
