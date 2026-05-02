"""Monthly cohort retention heatmap.

Mirrors queries/cohort_retention.sql, rendered as a heatmap of retention
percentages with cohort month on the y-axis and months-since-first-purchase
on the x-axis.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from db import run_query, to_csv_bytes
from style import PRIMARY, apply_style, brand_sidebar, caption, footer, hero, insight, note

st.set_page_config(
    page_title="Cohort Retention · Olist", page_icon=":calendar:", layout="wide"
)
apply_style()
brand_sidebar("Cohort Retention")

with st.sidebar:
    st.markdown("### Horizon")
    max_horizon = st.slider(
        "Months since first purchase",
        min_value=3,
        max_value=18,
        value=12,
    )
    st.divider()
    st.markdown("### Reading the heatmap")
    st.markdown(
        """
        - **Rows** are cohorts — customers grouped by the month of their first delivered order.
        - **Columns** are months elapsed since that first purchase.
        - **Cell value** is the share of the cohort still active that month.
        - **Diagonal staircase** shape is normal for a fixed observation window.
        """
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


hero(
    "Customer Cohort Retention",
    "Each cohort is the set of customers who placed their first delivered order in a given month. "
    "The heatmap shows the percentage of each cohort still active in subsequent months — "
    "Olist is largely transactional, so first-purchase repeats are rare but the patterns are still informative.",
    pills=["Live OLTP", "LAG window function", "Variable horizon"],
)

df = fetch_cohorts(max_horizon)

if df.empty:
    st.warning("No cohort data returned.")
    st.stop()

df["cohort_label"] = pd.to_datetime(df["cohort_month"]).dt.strftime("%Y-%m")

cohorts_count = df["cohort_month"].nunique()
total_customers = int(df.drop_duplicates("cohort_month")["cohort_size"].sum())
month_1 = df.loc[df["months_since_first_purchase"] == 1, "retention_rate"]
avg_m1 = month_1.mean() if not month_1.empty else 0.0
best_m1 = month_1.max() if not month_1.empty else 0.0
best_m1_cohort = (
    df.loc[df["months_since_first_purchase"] == 1].sort_values("retention_rate", ascending=False)
    .iloc[0]
    if not month_1.empty
    else None
)
biggest_cohort = df.drop_duplicates("cohort_month").sort_values("cohort_size", ascending=False).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cohorts", f"{cohorts_count}")
c2.metric("Total customers tracked", f"{total_customers:,}")
c3.metric("Avg month-1 retention", f"{avg_m1:.2f}%")
c4.metric(
    "Biggest cohort",
    pd.to_datetime(biggest_cohort["cohort_month"]).strftime("%b %Y"),
    delta=f"{int(biggest_cohort['cohort_size']):,} customers",
    delta_color="normal",
)

if best_m1_cohort is not None and best_m1 > 0:
    insight(
        f"<strong>Month-1 repeat rate averages {avg_m1:.2f}%</strong> across all cohorts — "
        "low, as expected for transactional commerce where most customers buy a single item. "
        f"The strongest comeback came from <strong>{pd.to_datetime(best_m1_cohort['cohort_month']):%b %Y}</strong> "
        f"with {best_m1:.2f}% returning the next month."
    )

st.divider()

st.subheader("Retention Heatmap (% of cohort active)")
caption(
    "Month 0 (always 100%) is omitted so the meaningful pattern is visible. "
    "Hover any cell for exact counts and original cohort size."
)

heatmap_df = df[df["months_since_first_purchase"] > 0].copy()
color_max = max(heatmap_df["retention_rate"].max(), 5) if not heatmap_df.empty else 5

heatmap = (
    alt.Chart(heatmap_df)
    .mark_rect(stroke="white", strokeWidth=1.2)
    .encode(
        x=alt.X(
            "months_since_first_purchase:O",
            title="Months since first purchase",
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y("cohort_label:O", title="Cohort", sort="ascending"),
        color=alt.Color(
            "retention_rate:Q",
            title="Retention %",
            scale=alt.Scale(scheme="blues", domain=[0, color_max]),
            legend=alt.Legend(orient="right", gradientLength=400),
        ),
        tooltip=[
            alt.Tooltip("cohort_label:N", title="Cohort"),
            alt.Tooltip("months_since_first_purchase:Q", title="Month #"),
            alt.Tooltip("active_customers:Q", title="Active", format=","),
            alt.Tooltip("cohort_size:Q", title="Cohort size", format=","),
            alt.Tooltip("retention_rate:Q", title="Retention %", format=".2f"),
        ],
    )
    .properties(height=620)
)

# Only label cells with meaningful values to keep the grid clean
label_df = heatmap_df[heatmap_df["retention_rate"] >= 1].copy()
text = (
    alt.Chart(label_df)
    .mark_text(baseline="middle", fontSize=10, fontWeight=500)
    .encode(
        x=alt.X("months_since_first_purchase:O"),
        y=alt.Y("cohort_label:O", sort="ascending"),
        text=alt.Text("retention_rate:Q", format=".1f"),
        color=alt.condition(
            f"datum.retention_rate > {color_max * 0.5}",
            alt.value("white"),
            alt.value("#0F172A"),
        ),
    )
)
st.altair_chart(heatmap + text, use_container_width=True)
note(
    "Retention drops sharply by month 1 (typically to 1–7%) and stays low — expected for "
    "transactional commerce where most customers buy a single item. The empty bottom-right "
    "triangle reflects newer cohorts that haven't had time to age a full horizon."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cohort Sizes")
    caption("How many new customers entered the marketplace each month.")
    sizes = df.drop_duplicates("cohort_month")[["cohort_label", "cohort_size"]]
    size_chart = (
        alt.Chart(sizes)
        .mark_bar(cornerRadiusEnd=3, color=PRIMARY)
        .encode(
            x=alt.X("cohort_label:N", title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("cohort_size:Q", title="New customers", axis=alt.Axis(format=",")),
            tooltip=[
                alt.Tooltip("cohort_label:N", title="Cohort"),
                alt.Tooltip("cohort_size:Q", title="Customers", format=","),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(size_chart, use_container_width=True)
    note(
        "New-customer acquisition ramped through 2017 and peaked in late 2017 — likely the "
        "Black Friday / holiday surge. The 2018 falloff is partially the dataset's September "
        "cutoff, not a real decline."
    )

with col2:
    st.subheader("Average Retention Curve")
    caption("Retention averaged across cohorts at each month-since-first-purchase.")
    avg_curve = df.groupby("months_since_first_purchase", as_index=False)["retention_rate"].mean()
    curve = (
        alt.Chart(avg_curve)
        .mark_line(point=alt.OverlayMarkDef(size=80, filled=True, color=PRIMARY), color=PRIMARY, strokeWidth=2.5)
        .encode(
            x=alt.X("months_since_first_purchase:Q", title="Months since first purchase"),
            y=alt.Y("retention_rate:Q", title="Retention %"),
            tooltip=[
                alt.Tooltip("months_since_first_purchase:Q", title="Month #"),
                alt.Tooltip("retention_rate:Q", title="Avg retention %", format=".2f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(curve, use_container_width=True)
    note(
        "The curve is the average across all cohorts at each month. The sharp drop in month 1 "
        "tells the same story as the heatmap. The flat tail past month 3 is the small loyal "
        "sub-population that does come back."
    )

raw_cols = [
    "cohort_label",
    "cohort_size",
    "months_since_first_purchase",
    "active_customers",
    "retention_rate",
]
raw_df = df[raw_cols].rename(columns={"cohort_label": "cohort_month"})

with st.expander("Raw cohort data"):
    st.dataframe(raw_df, hide_index=True, use_container_width=True)

st.download_button(
    "Download cohort data (CSV)",
    data=to_csv_bytes(raw_df),
    file_name=f"cohort_retention_{max_horizon}mo.csv",
    mime="text/csv",
)

footer()
