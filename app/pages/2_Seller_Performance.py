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

from db import run_query, to_csv_bytes
from style import (
    ACCENT,
    PRIMARY,
    PRIMARY_LIGHT,
    SUCCESS,
    apply_style,
    brand_sidebar,
    caption,
    footer,
    hero,
    insight,
    note,
)

st.set_page_config(
    page_title="Seller Performance · Olist", page_icon=":shopping_bags:", layout="wide"
)
apply_style()
brand_sidebar("Seller Performance")


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
            round(sum(oi.price)::numeric, 2) as total_revenue,
            count(distinct oi.order_id) as total_orders
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
    st.markdown("### Filters")
    states = fetch_states()
    selected_states = st.multiselect(
        "Filter by seller state",
        options=states,
        default=[],
        help="Leave empty to include all 27 Brazilian states.",
    )
    top_n = st.slider("Leaderboard size", min_value=10, max_value=200, value=50, step=10)
    st.divider()
    st.markdown("### About this view")
    st.markdown(
        """
        Sellers are ranked across **delivered** orders only. We compute:
        - revenue rank (overall and within state)
        - review-score percentile
        - average item price and review score

        The marketplace is dominated by São Paulo (SP) sellers; the state filter helps surface regional leaders.
        """
    )

hero(
    "Marketplace Seller Performance",
    "Olist hosts thousands of sellers across 27 Brazilian states. This page ranks them by gross revenue, "
    "compares each against state peers, and surfaces review-quality outliers.",
    pills=["Live OLTP", "Window functions", "State drill-down"],
)

sellers = fetch_seller_performance(tuple(selected_states), top_n)
state_rev = fetch_state_revenue()

if sellers.empty:
    st.warning("No sellers match the current filters.")
    st.stop()

sellers["short_id"] = sellers["seller_id"].str[:8]
sellers["seller_label"] = (
    "#"
    + sellers["revenue_rank"].astype(int).astype(str)
    + " · "
    + sellers["seller_city"].fillna("?").str.title()
    + ", "
    + sellers["seller_state"].fillna("--")
)

combined_rev = float(sellers["total_revenue"].sum())
top10_rev = float(sellers.head(10)["total_revenue"].sum())
top10_share = (top10_rev / combined_rev * 100) if combined_rev else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sellers shown", f"{len(sellers):,}")
c2.metric("Combined revenue", f"R$ {combined_rev / 1_000_000:.2f}M")
c3.metric(
    "Avg review score",
    f"{sellers['avg_review_score'].dropna().mean():.2f} / 5"
    if sellers["avg_review_score"].notna().any()
    else "n/a",
)
c4.metric(
    "Top 10 share",
    f"{top10_share:.1f}%",
    help="Share of leaderboard revenue from the top 10 sellers — a concentration metric",
)

leader = sellers.iloc[0]
runner = sellers.iloc[1] if len(sellers) > 1 else None
multiple = (leader["total_revenue"] / runner["total_revenue"]) if runner is not None else None

if runner is not None:
    insight(
        f"<strong>{leader['short_id']}</strong> in <strong>{leader['seller_city'].title() if leader['seller_city'] else '—'}, "
        f"{leader['seller_state']}</strong> tops the board with R$ {leader['total_revenue']:,.0f} — "
        f"{multiple:.1f}× the runner-up. The top 10 sellers contribute "
        f"<strong>{top10_share:.1f}%</strong> of the leaderboard's revenue, hinting at a long-tail marketplace."
    )

st.divider()

st.subheader(f"Top {min(20, len(sellers))} Sellers by Revenue")
caption("Each bar is a seller, labelled with the first 8 chars of the seller ID and city/state.")
top20 = sellers.head(20)
top_chart = (
    alt.Chart(top20)
    .mark_bar(cornerRadiusEnd=4, color=PRIMARY)
    .encode(
        x=alt.X("total_revenue:Q", title="Revenue (BRL)", axis=alt.Axis(format="~s")),
        y=alt.Y("seller_label:N", sort="-x", title=None),
        color=alt.Color(
            "avg_review_score:Q",
            title="Avg Review",
            scale=alt.Scale(scheme="oranges", domain=[3.0, 5.0]),
            legend=alt.Legend(orient="top-right"),
        ),
        tooltip=[
            alt.Tooltip("seller_id:N", title="Seller ID"),
            alt.Tooltip("seller_city:N", title="City"),
            alt.Tooltip("seller_state:N", title="State"),
            alt.Tooltip("total_revenue:Q", title="Revenue", format=",.0f"),
            alt.Tooltip("total_orders:Q", title="Orders", format=","),
            alt.Tooltip("total_items_sold:Q", title="Items", format=","),
            alt.Tooltip("avg_review_score:Q", title="Avg Review", format=".2f"),
            alt.Tooltip("review_percentile_pct:Q", title="Review percentile", format=".1f"),
        ],
    )
    .properties(height=520)
)
st.altair_chart(top_chart, use_container_width=True)
note(
    "Color encodes the seller's average review score (1–5). Watch for high-revenue bars "
    "in lighter shades — those sellers are moving volume despite mediocre reviews and "
    "are quality-risk outliers worth investigating."
)

st.subheader("Revenue by Seller State")
caption("São Paulo dominates Brazilian e-commerce; this chart shows the gap.")
state_rev["pct"] = state_rev["total_revenue"] / state_rev["total_revenue"].sum() * 100
state_chart = (
    alt.Chart(state_rev)
    .mark_bar(cornerRadiusEnd=4)
    .encode(
        x=alt.X("total_revenue:Q", title="Revenue (BRL)", axis=alt.Axis(format="~s")),
        y=alt.Y("seller_state:N", sort="-x", title=None),
        color=alt.Color(
            "total_revenue:Q",
            scale=alt.Scale(scheme="reds"),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("seller_state:N", title="State"),
            alt.Tooltip("sellers:Q", title="Sellers", format=","),
            alt.Tooltip("total_orders:Q", title="Orders", format=","),
            alt.Tooltip("total_revenue:Q", title="Revenue (BRL)", format=",.0f"),
            alt.Tooltip("pct:Q", title="Share %", format=".1f"),
        ],
    )
    .properties(height=560)
)
st.altair_chart(state_chart, use_container_width=True)
sp_share = float(state_rev.loc[state_rev["seller_state"] == "SP", "pct"].sum() if (state_rev["seller_state"] == "SP").any() else 0)
note(
    f"São Paulo (SP) hosts <strong>{sp_share:.0f}%</strong> of marketplace revenue alone — "
    "Olist is São Paulo–centric, with Rio de Janeiro (RJ), Minas Gerais (MG), and Paraná (PR) "
    "forming a clear second tier. Many states have fewer than 100 active sellers."
)

st.subheader("Full Leaderboard")
caption("Sortable, filterable view. Reviewing the **review percentile** column surfaces sellers with quality issues despite high revenue.")

leader_view = sellers.copy()
leader_view["Rank"] = leader_view["revenue_rank"].astype(int)
leader_view["Seller"] = leader_view["short_id"]
leader_view["City"] = leader_view["seller_city"].fillna("—").str.title()
leader_view["State"] = leader_view["seller_state"].fillna("—")
leader_view["Orders"] = leader_view["total_orders"].astype(int).map("{:,}".format)
leader_view["Items"] = leader_view["total_items_sold"].astype(int).map("{:,}".format)
leader_view["Revenue (BRL)"] = leader_view["total_revenue"].apply(lambda v: f"R$ {v:,.0f}")
leader_view["Avg Item Price"] = leader_view["avg_item_price"].apply(lambda v: f"R$ {v:,.2f}")
leader_view["_review_raw"] = leader_view["avg_review_score"]
leader_view["Avg Review"] = leader_view["avg_review_score"].apply(
    lambda v: f"{v:.2f}" if pd.notna(v) else "—"
)
leader_view["Review %ile"] = leader_view["review_percentile_pct"].apply(
    lambda v: f"{v:.1f}" if pd.notna(v) else "—"
)
leader_view["State rank"] = leader_view["state_revenue_rank"].astype(int)

leader_cols = [
    "Rank", "Seller", "City", "State", "Orders", "Items",
    "Revenue (BRL)", "Avg Item Price", "Avg Review", "Review %ile", "State rank",
]


def _color_review_row(row):
    raw = row["_review_raw"]
    color = ""
    if pd.notna(raw):
        if raw >= 4.5:
            color = "color: #047857; font-weight: 600;"
        elif raw >= 4.0:
            color = "color: #059669; font-weight: 500;"
        elif raw >= 3.5:
            color = "color: #B45309;"
        elif raw >= 3.0:
            color = "color: #B91C1C;"
        else:
            color = "color: #7F1D1D; font-weight: 600;"
    return [color if col == "Avg Review" else "" for col in row.index]


styled_leader = leader_view[leader_cols + ["_review_raw"]].style.apply(_color_review_row, axis=1)
st.dataframe(
    styled_leader,
    hide_index=True,
    use_container_width=True,
    column_order=leader_cols,
    column_config={"_review_raw": None},
)

st.download_button(
    "Download leaderboard (CSV)",
    data=to_csv_bytes(leader_view[leader_cols]),
    file_name=f"seller_leaderboard_top{len(sellers)}.csv",
    mime="text/csv",
)
note(
    "<strong>Avg Review</strong> is color-coded: green for 4.0+, amber for 3.5–4.0, red below. "
    "<strong>Review %ile</strong> is the seller's percentile rank by review score across all sellers — "
    "100 = best reviews, 0 = worst. Sort by State rank to see who tops each region."
)

footer()
