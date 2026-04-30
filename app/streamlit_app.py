"""Olist Analytics — Overview page.

Top-level KPIs and trend visualizations sourced from the dbt mart layer
(fact_order_items joined to dim_dates / dim_products). The date range slider
filters every chart and KPI on this page.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import altair as alt
import pandas as pd
import streamlit as st

from db import run_query

st.set_page_config(
    page_title="Olist Analytics",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("Olist E-Commerce Analytics")
st.caption(
    "Phase 3 dashboard backed by the dbt star schema on Neon Postgres. "
    "Each page below queries the live database; results are cached for 10 minutes."
)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_date_bounds() -> tuple[date, date]:
    df = run_query(
        """
        select
            min(order_purchase_timestamp)::date as min_date,
            max(order_purchase_timestamp)::date as max_date
        from fact_order_items
        where order_purchase_timestamp is not null
        """
    )
    return df["min_date"].iloc[0], df["max_date"].iloc[0]


@st.cache_data(ttl=600, show_spinner=False)
def fetch_kpis(start: date, end: date) -> pd.DataFrame:
    return run_query(
        """
        select
            count(distinct order_id) as orders,
            count(distinct customer_id) as customers,
            sum(total_item_value) as gross_revenue,
            avg(avg_review_score) as avg_review,
            avg(case when delivered_on_time then 1.0 else 0.0 end) as on_time_rate
        from fact_order_items
        where order_purchase_timestamp::date between :start and :end
        """,
        {"start": start, "end": end},
    )


@st.cache_data(ttl=600, show_spinner=False)
def fetch_monthly_revenue(start: date, end: date) -> pd.DataFrame:
    return run_query(
        """
        select
            date_trunc('month', order_purchase_timestamp)::date as month,
            sum(total_item_value) as revenue,
            count(distinct order_id) as orders
        from fact_order_items
        where order_purchase_timestamp::date between :start and :end
        group by 1
        order by 1
        """,
        {"start": start, "end": end},
    )


@st.cache_data(ttl=600, show_spinner=False)
def fetch_top_categories(start: date, end: date, limit: int = 10) -> pd.DataFrame:
    return run_query(
        """
        select
            coalesce(p.product_category, 'unknown') as category,
            sum(f.total_item_value) as revenue,
            count(*) as items_sold
        from fact_order_items f
        left join dim_products p on f.product_id = p.product_id
        where f.order_purchase_timestamp::date between :start and :end
        group by 1
        order by revenue desc
        limit :limit
        """,
        {"start": start, "end": end, "limit": limit},
    )


@st.cache_data(ttl=600, show_spinner=False)
def fetch_status_breakdown(start: date, end: date) -> pd.DataFrame:
    return run_query(
        """
        select order_status, count(distinct order_id) as orders
        from fact_order_items
        where order_purchase_timestamp::date between :start and :end
        group by 1
        order by orders desc
        """,
        {"start": start, "end": end},
    )


min_date, max_date = fetch_date_bounds()

with st.sidebar:
    st.header("Filters")
    start_date, end_date = st.slider(
        "Order purchase date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
    )
    st.caption(
        "Active range: "
        f"**{start_date:%Y-%m-%d}** → **{end_date:%Y-%m-%d}**"
    )

kpis = fetch_kpis(start_date, end_date).iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Orders", f"{int(kpis['orders']):,}")
col2.metric("Customers", f"{int(kpis['customers']):,}")
col3.metric("Gross Revenue (BRL)", f"R$ {float(kpis['gross_revenue'] or 0):,.0f}")
col4.metric(
    "Avg Review",
    f"{float(kpis['avg_review'] or 0):.2f} / 5",
)
col5.metric(
    "On-Time Delivery",
    f"{float(kpis['on_time_rate'] or 0) * 100:.1f}%",
)

st.divider()

left, right = st.columns([3, 2])

with left:
    st.subheader("Monthly Revenue")
    monthly = fetch_monthly_revenue(start_date, end_date)
    if monthly.empty:
        st.info("No orders in this range.")
    else:
        chart = (
            alt.Chart(monthly)
            .mark_area(opacity=0.55, line=True, color="#4c78a8")
            .encode(
                x=alt.X("month:T", title="Month"),
                y=alt.Y("revenue:Q", title="Revenue (BRL)"),
                tooltip=[
                    alt.Tooltip("month:T", title="Month"),
                    alt.Tooltip("revenue:Q", title="Revenue", format=",.2f"),
                    alt.Tooltip("orders:Q", title="Orders", format=","),
                ],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

with right:
    st.subheader("Order Status")
    statuses = fetch_status_breakdown(start_date, end_date)
    if statuses.empty:
        st.info("No orders in this range.")
    else:
        st.dataframe(statuses, hide_index=True, use_container_width=True)

st.divider()

st.subheader("Top 10 Product Categories by Revenue")
top_cats = fetch_top_categories(start_date, end_date)
if top_cats.empty:
    st.info("No category data in this range.")
else:
    cat_chart = (
        alt.Chart(top_cats)
        .mark_bar(color="#54a24b")
        .encode(
            x=alt.X("revenue:Q", title="Revenue (BRL)"),
            y=alt.Y("category:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("revenue:Q", title="Revenue", format=",.2f"),
                alt.Tooltip("items_sold:Q", title="Items Sold", format=","),
            ],
        )
        .properties(height=360)
    )
    st.altair_chart(cat_chart, use_container_width=True)

st.divider()
st.caption(
    "Data source: dbt mart `fact_order_items` joined to `dim_products` on Neon "
    "Postgres. Use the sidebar pages to drill into RFM segmentation, seller "
    "performance, and cohort retention."
)
