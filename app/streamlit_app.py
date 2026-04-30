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
from style import ACCENT, PRIMARY, PRIMARY_LIGHT, SUCCESS, apply_style, caption, hero, insight

st.set_page_config(
    page_title="Olist Analytics",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_style()


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
            count(distinct seller_id) as sellers,
            sum(total_item_value) as gross_revenue,
            avg(avg_review_score) as avg_review,
            avg(case when delivered_on_time then 1.0 else 0.0 end) as on_time_rate,
            count(*) as line_items
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
            count(*) as items_sold,
            avg(f.avg_review_score) as avg_review
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


@st.cache_data(ttl=600, show_spinner=False)
def fetch_payment_mix(start: date, end: date) -> pd.DataFrame:
    return run_query(
        """
        select
            split_part(payment_types, ',', 1) as payment_type,
            count(distinct order_id) as orders,
            sum(order_payment_value) as total
        from fact_order_items
        where order_purchase_timestamp::date between :start and :end
          and payment_types is not null
        group by 1
        order by orders desc
        """,
        {"start": start, "end": end},
    )


min_date, max_date = fetch_date_bounds()

with st.sidebar:
    st.markdown("### Filters")
    start_date, end_date = st.slider(
        "Order purchase date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
    )
    st.caption(f"**{start_date:%b %d, %Y}** → **{end_date:%b %d, %Y}**")

    st.divider()
    st.markdown("### Navigation")
    st.markdown(
        """
        - **Overview** — KPIs and trends
        - **RFM Analysis** — customer segmentation
        - **Seller Performance** — marketplace leaderboard
        - **Cohort Retention** — customer return behavior
        """
    )

hero(
    "Olist E-Commerce Analytics",
    "Live BI dashboard over the Brazilian E-Commerce dataset by Olist. "
    "Explore order trends, customer segmentation, seller performance, and cohort retention "
    "across ~100k orders from 2016 to 2018.",
    pills=[
        "Live Neon Postgres",
        "dbt Star Schema",
        "Cached for 10 min",
    ],
)

kpis = fetch_kpis(start_date, end_date).iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Orders", f"{int(kpis['orders']):,}", help="Distinct orders in the selected window")
col2.metric("Customers", f"{int(kpis['customers']):,}", help="Distinct customers (per-order ID)")
col3.metric(
    "Gross Revenue",
    f"R$ {float(kpis['gross_revenue'] or 0) / 1_000_000:.2f}M",
    help="Sum of price + freight across line items",
)
col4.metric(
    "Avg Review",
    f"{float(kpis['avg_review'] or 0):.2f} / 5",
    help="Order-level average review score (1–5)",
)
col5.metric(
    "On-Time Delivery",
    f"{float(kpis['on_time_rate'] or 0) * 100:.1f}%",
    help="Share of orders delivered on or before the estimate",
)

c1, c2, c3 = st.columns(3)
c1.metric("Active Sellers", f"{int(kpis['sellers']):,}")
c2.metric("Order Line Items", f"{int(kpis['line_items']):,}")
c3.metric(
    "Avg Items / Order",
    f"{float(kpis['line_items']) / max(float(kpis['orders']), 1):.2f}",
)

monthly = fetch_monthly_revenue(start_date, end_date)
total_revenue = float(monthly["revenue"].sum()) if not monthly.empty else 0.0
peak_month = monthly.loc[monthly["revenue"].idxmax()] if not monthly.empty else None

if peak_month is not None:
    insight(
        f"<strong>Peak month:</strong> {pd.to_datetime(peak_month['month']):%B %Y} with "
        f"R$ {peak_month['revenue']:,.0f} in revenue across {int(peak_month['orders']):,} orders. "
        f"<strong>On-time delivery:</strong> {float(kpis['on_time_rate'] or 0) * 100:.1f}% of orders "
        "arrive by the carrier estimate."
    )

st.divider()

left, right = st.columns([3, 2])

with left:
    st.subheader("Monthly Revenue Trend")
    caption("Gross merchandise value (price + freight) bucketed by purchase month.")
    if monthly.empty:
        st.info("No orders in this range.")
    else:
        base = alt.Chart(monthly).encode(
            x=alt.X("month:T", title="Month", axis=alt.Axis(format="%b %Y")),
        )
        area = base.mark_area(
            line={"color": PRIMARY, "strokeWidth": 2.5},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=PRIMARY_LIGHT, offset=0),
                    alt.GradientStop(color="white", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            ),
            opacity=0.5,
        ).encode(
            y=alt.Y("revenue:Q", title="Revenue (BRL)"),
            tooltip=[
                alt.Tooltip("month:T", title="Month", format="%B %Y"),
                alt.Tooltip("revenue:Q", title="Revenue", format=",.0f"),
                alt.Tooltip("orders:Q", title="Orders", format=","),
            ],
        )
        points = base.mark_circle(size=55, color=PRIMARY).encode(y="revenue:Q")
        st.altair_chart((area + points).properties(height=340), use_container_width=True)

with right:
    st.subheader("Order Status Mix")
    caption("Where orders end up in their lifecycle.")
    statuses = fetch_status_breakdown(start_date, end_date)
    if statuses.empty:
        st.info("No orders in this range.")
    else:
        total_orders = int(statuses["orders"].sum())
        statuses["share"] = statuses["orders"] / total_orders
        bar = (
            alt.Chart(statuses)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                y=alt.Y("order_status:N", sort="-x", title=None),
                x=alt.X("orders:Q", title="Orders", axis=alt.Axis(format=",")),
                color=alt.Color(
                    "order_status:N",
                    legend=None,
                    scale=alt.Scale(
                        domain=["delivered", "shipped", "canceled", "invoiced", "processing", "unavailable", "approved", "created"],
                        range=[SUCCESS, PRIMARY_LIGHT, "#EF4444", "#A855F7", ACCENT, "#94A3B8", "#06B6D4", "#64748B"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("order_status:N", title="Status"),
                    alt.Tooltip("orders:Q", title="Orders", format=","),
                    alt.Tooltip("share:Q", title="Share", format=".1%"),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(bar, use_container_width=True)

st.subheader("Top 10 Product Categories by Revenue")
caption("The catalog is long-tail — these ten categories drive most of the marketplace's gross merchandise value.")
top_cats = fetch_top_categories(start_date, end_date)
if top_cats.empty:
    st.info("No category data in this range.")
else:
    top_cats["pretty"] = top_cats["category"].str.replace("_", " ").str.title()
    cat_chart = (
        alt.Chart(top_cats)
        .mark_bar(cornerRadiusEnd=4, color=PRIMARY)
        .encode(
            x=alt.X("revenue:Q", title="Revenue (BRL)", axis=alt.Axis(format="~s")),
            y=alt.Y("pretty:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("pretty:N", title="Category"),
                alt.Tooltip("revenue:Q", title="Revenue", format=",.0f"),
                alt.Tooltip("items_sold:Q", title="Items Sold", format=","),
                alt.Tooltip("avg_review:Q", title="Avg Review", format=".2f"),
            ],
        )
        .properties(height=380)
    )
    labels = (
        alt.Chart(top_cats)
        .mark_text(align="left", baseline="middle", dx=6, color="#475569", fontSize=11)
        .encode(
            x="revenue:Q",
            y=alt.Y("pretty:N", sort="-x"),
            text=alt.Text("revenue:Q", format=",.0f"),
        )
    )
    st.altair_chart(cat_chart + labels, use_container_width=True)

    leader = top_cats.iloc[0]
    insight(
        f"<strong>{leader['pretty']}</strong> is the top revenue category at "
        f"R$ {leader['revenue']:,.0f} from {int(leader['items_sold']):,} items sold "
        f"(avg review {leader['avg_review']:.2f}). "
        f"The top 3 categories account for "
        f"<strong>{top_cats.head(3)['revenue'].sum() / top_cats['revenue'].sum() * 100:.1f}%</strong> of "
        f"these top-10 revenue."
    )

st.divider()

st.subheader("Payment Method Mix")
caption("Brazilian e-commerce skews heavily toward credit cards and boletos.")
payments = fetch_payment_mix(start_date, end_date)
if not payments.empty:
    pay_chart = (
        alt.Chart(payments)
        .mark_arc(innerRadius=70, outerRadius=130, cornerRadius=4)
        .encode(
            theta=alt.Theta("orders:Q"),
            color=alt.Color(
                "payment_type:N",
                title="Payment Type",
                scale=alt.Scale(
                    domain=["credit_card", "boleto", "voucher", "debit_card", "not_defined"],
                    range=[PRIMARY, ACCENT, "#06B6D4", "#10B981", "#94A3B8"],
                ),
            ),
            tooltip=[
                alt.Tooltip("payment_type:N", title="Type"),
                alt.Tooltip("orders:Q", title="Orders", format=","),
                alt.Tooltip("total:Q", title="Total (BRL)", format=",.0f"),
            ],
        )
        .properties(height=320)
    )
    pcol1, pcol2 = st.columns([2, 3])
    with pcol1:
        st.altair_chart(pay_chart, use_container_width=True)
    with pcol2:
        st.dataframe(
            payments.assign(
                share=lambda d: (d["orders"] / d["orders"].sum() * 100).round(2).astype(str) + "%",
                total=lambda d: d["total"].apply(lambda v: f"R$ {v:,.0f}"),
            ).rename(columns={"payment_type": "Payment Type", "orders": "Orders", "total": "Total", "share": "Share"}),
            hide_index=True,
            use_container_width=True,
        )

st.divider()
caption(
    f"Data source: dbt mart <code>fact_order_items</code> on Neon Postgres. "
    f"Window: {start_date:%b %Y} – {end_date:%b %Y}. "
    f"All charts cached for 10 minutes; widget interactions don't re-hit the database."
)
