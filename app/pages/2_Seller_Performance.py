"""Seller performance leaderboard.

Mirrors queries/seller_performance.sql but exposes a state filter and a
leaderboard size widget so the user can drill into geographic performance.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from db import run_query

st.set_page_config(page_title="Seller Performance", page_icon=":shopping_bags:", layout="wide")

st.title("Seller Performance")
st.caption(
    "Revenue, review percentile, and state-level rank for each seller. "
    "Computed across delivered orders only."
)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_states() -> list[str]:
    df = run_query(
        """
        select distinct l.state
        from sellers s
        inner join locations l on s.zip_code_prefix = l.zip_code_prefix
        where l.state is not null
        order by l.state
        """
    )
    return df["state"].tolist()


@st.cache_data(ttl=600, show_spinner="Loading seller performance…")
def fetch_seller_performance(states: tuple[str, ...], top_n: int) -> pd.DataFrame:
    state_filter = ""
    params: dict = {"limit": top_n}
    if states:
        state_filter = "and l.state = any(:states)"
        params["states"] = list(states)

    return run_query(
        f"""
        with seller_metrics as (
            select
                s.seller_id,
                l.city as seller_city,
                l.state as seller_state,
                count(distinct oi.order_id) as total_orders,
                count(oi.order_item_id) as total_items_sold,
                round(sum(oi.price)::numeric, 2) as total_revenue,
                round(avg(oi.price)::numeric, 2) as avg_item_price,
                round(avg(r.review_score)::numeric, 2) as avg_review_score,
                count(distinct r.review_id) as total_reviews
            from sellers s
            inner join order_items oi on s.seller_id = oi.seller_id
            inner join orders o on oi.order_id = o.order_id
            left join locations l on s.zip_code_prefix = l.zip_code_prefix
            left join order_reviews r on o.order_id = r.order_id and r.review_id is not null
            where o.order_status = 'delivered'
              {state_filter}
            group by s.seller_id, l.city, l.state
        ),
        seller_rankings as (
            select
                *,
                rank() over (order by total_revenue desc) as revenue_rank,
                round(percent_rank() over (order by avg_review_score)::numeric, 4) as review_percentile,
                rank() over (
                    partition by seller_state order by total_revenue desc
                ) as state_revenue_rank
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
            round(review_percentile * 100, 2) as review_percentile_pct
        from seller_rankings
        where revenue_rank <= :limit
        order by revenue_rank
        """,
        params,
    )


@st.cache_data(ttl=600, show_spinner=False)
def fetch_state_revenue() -> pd.DataFrame:
    return run_query(
        """
        select
            l.state as seller_state,
            count(distinct s.seller_id) as sellers,
            round(sum(oi.price)::numeric, 2) as total_revenue
        from sellers s
        inner join order_items oi on s.seller_id = oi.seller_id
        inner join orders o on oi.order_id = o.order_id
        left join locations l on s.zip_code_prefix = l.zip_code_prefix
        where o.order_status = 'delivered' and l.state is not null
        group by l.state
        order by total_revenue desc
        """
    )


with st.sidebar:
    st.header("Filters")
    states = fetch_states()
    selected_states = st.multiselect(
        "Filter by seller state",
        options=states,
        default=[],
        help="Leave empty to include all states.",
    )
    top_n = st.slider("Leaderboard size", min_value=10, max_value=200, value=50, step=10)

sellers = fetch_seller_performance(tuple(selected_states), top_n)
state_rev = fetch_state_revenue()

if sellers.empty:
    st.warning("No sellers match the current filters.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Sellers shown", f"{len(sellers):,}")
c2.metric("Combined revenue (BRL)", f"R$ {sellers['total_revenue'].sum():,.0f}")
c3.metric(
    "Avg review score",
    f"{sellers['avg_review_score'].dropna().mean():.2f} / 5"
    if sellers["avg_review_score"].notna().any()
    else "n/a",
)

st.divider()

st.subheader(f"Top {len(sellers)} sellers by revenue")
top_chart = (
    alt.Chart(sellers.head(20))
    .mark_bar(color="#4c78a8")
    .encode(
        x=alt.X("total_revenue:Q", title="Revenue (BRL)"),
        y=alt.Y("seller_id:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("seller_id:N", title="Seller"),
            alt.Tooltip("seller_city:N", title="City"),
            alt.Tooltip("seller_state:N", title="State"),
            alt.Tooltip("total_revenue:Q", title="Revenue", format=",.2f"),
            alt.Tooltip("total_orders:Q", title="Orders", format=","),
            alt.Tooltip("avg_review_score:Q", title="Avg Review", format=".2f"),
        ],
    )
    .properties(height=420)
)
st.altair_chart(top_chart, use_container_width=True)

st.subheader("Revenue by seller state")
state_chart = (
    alt.Chart(state_rev)
    .mark_bar(color="#54a24b")
    .encode(
        x=alt.X("total_revenue:Q", title="Revenue (BRL)"),
        y=alt.Y("seller_state:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("seller_state:N", title="State"),
            alt.Tooltip("sellers:Q", title="Sellers", format=","),
            alt.Tooltip("total_revenue:Q", title="Revenue", format=",.2f"),
        ],
    )
    .properties(height=520)
)
st.altair_chart(state_chart, use_container_width=True)

st.subheader("Seller detail")
st.dataframe(sellers, hide_index=True, use_container_width=True)
