"""Monthly cohort retention heatmap.

Mirrors queries/cohort_retention.sql, rendered as a heatmap of retention
percentages with cohort month on the y-axis and months-since-first-purchase
on the x-axis. The user can pick a max horizon to widen or tighten the view.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from db import run_query

st.set_page_config(page_title="Cohort Retention", page_icon=":calendar:", layout="wide")

st.title("Monthly Cohort Retention")
st.caption(
    "Customers are bucketed into a cohort by their first delivered-order month. "
    "Each cell shows the percentage of that cohort still active N months later."
)

with st.sidebar:
    st.header("Horizon")
    max_horizon = st.slider(
        "Months since first purchase",
        min_value=3,
        max_value=18,
        value=12,
    )


@st.cache_data(ttl=600, show_spinner="Computing cohorts…")
def fetch_cohorts(max_horizon: int) -> pd.DataFrame:
    return run_query(
        """
        with customer_first_purchase as (
            select
                c.customer_unique_id,
                date_trunc('month', min(o.purchase_timestamp))::date as cohort_month
            from customers c
            inner join orders o on c.customer_id = o.customer_id
            where o.order_status = 'delivered'
            group by c.customer_unique_id
        ),
        customer_monthly_activity as (
            select distinct
                c.customer_unique_id,
                date_trunc('month', o.purchase_timestamp)::date as activity_month
            from customers c
            inner join orders o on c.customer_id = o.customer_id
            where o.order_status = 'delivered'
        ),
        cohort_activity as (
            select
                cfp.cohort_month,
                cma.activity_month,
                (
                    (extract(year from cma.activity_month) - extract(year from cfp.cohort_month)) * 12
                    + (extract(month from cma.activity_month) - extract(month from cfp.cohort_month))
                ) as months_since_first_purchase,
                count(distinct cfp.customer_unique_id) as active_customers
            from customer_first_purchase cfp
            inner join customer_monthly_activity cma
                on cfp.customer_unique_id = cma.customer_unique_id
            group by cfp.cohort_month, cma.activity_month
        ),
        cohort_sizes as (
            select cohort_month, count(distinct customer_unique_id) as cohort_size
            from customer_first_purchase
            group by cohort_month
        )
        select
            ca.cohort_month,
            cs.cohort_size,
            ca.months_since_first_purchase,
            ca.active_customers,
            round((ca.active_customers::numeric / cs.cohort_size) * 100, 2) as retention_rate
        from cohort_activity ca
        inner join cohort_sizes cs on ca.cohort_month = cs.cohort_month
        where ca.months_since_first_purchase between 0 and :horizon
        order by ca.cohort_month, ca.months_since_first_purchase
        """,
        {"horizon": max_horizon},
    )


df = fetch_cohorts(max_horizon)

if df.empty:
    st.warning("No cohort data returned.")
    st.stop()

df["cohort_label"] = pd.to_datetime(df["cohort_month"]).dt.strftime("%Y-%m")

c1, c2, c3 = st.columns(3)
c1.metric("Cohorts", df["cohort_month"].nunique())
c2.metric(
    "Total customers tracked",
    f"{df.drop_duplicates('cohort_month')['cohort_size'].sum():,}",
)
month_1 = df.loc[df["months_since_first_purchase"] == 1, "retention_rate"]
c3.metric(
    "Avg month-1 retention",
    f"{month_1.mean():.2f}%" if not month_1.empty else "n/a",
)

st.divider()

st.subheader("Retention heatmap (% of cohort active)")
heatmap = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("months_since_first_purchase:O", title="Months since first purchase"),
        y=alt.Y("cohort_label:O", title="Cohort", sort="ascending"),
        color=alt.Color(
            "retention_rate:Q",
            title="Retention %",
            scale=alt.Scale(scheme="blues"),
        ),
        tooltip=[
            alt.Tooltip("cohort_label:N", title="Cohort"),
            alt.Tooltip("months_since_first_purchase:Q", title="Month #"),
            alt.Tooltip("active_customers:Q", title="Active", format=","),
            alt.Tooltip("cohort_size:Q", title="Cohort size", format=","),
            alt.Tooltip("retention_rate:Q", title="Retention %", format=".2f"),
        ],
    )
    .properties(height=520)
)
text = (
    alt.Chart(df)
    .mark_text(baseline="middle", fontSize=10)
    .encode(
        x=alt.X("months_since_first_purchase:O"),
        y=alt.Y("cohort_label:O", sort="ascending"),
        text=alt.Text("retention_rate:Q", format=".0f"),
        color=alt.condition(
            "datum.retention_rate > 50", alt.value("white"), alt.value("black")
        ),
    )
)
st.altair_chart(heatmap + text, use_container_width=True)

st.subheader("Cohort sizes")
sizes = df.drop_duplicates("cohort_month")[["cohort_label", "cohort_size"]]
size_chart = (
    alt.Chart(sizes)
    .mark_bar(color="#4c78a8")
    .encode(
        x=alt.X("cohort_label:N", title="Cohort"),
        y=alt.Y("cohort_size:Q", title="New customers"),
        tooltip=[
            alt.Tooltip("cohort_label:N", title="Cohort"),
            alt.Tooltip("cohort_size:Q", title="Customers", format=","),
        ],
    )
    .properties(height=240)
)
st.altair_chart(size_chart, use_container_width=True)

st.subheader("Raw cohort data")
st.dataframe(
    df[
        [
            "cohort_label",
            "cohort_size",
            "months_since_first_purchase",
            "active_customers",
            "retention_rate",
        ]
    ].rename(columns={"cohort_label": "cohort_month"}),
    hide_index=True,
    use_container_width=True,
)
