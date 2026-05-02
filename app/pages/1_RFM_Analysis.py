"""RFM (Recency, Frequency, Monetary) customer segmentation.

Mirrors the Phase 2 analytical query queries/rfm_analysis.sql but lets the
user adjust segment thresholds and re-runs against live data.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from db import run_query, to_csv_bytes
from style import SEGMENT_COLORS, apply_style, brand_sidebar, caption, footer, hero, insight, note

st.set_page_config(
    page_title="RFM Analysis · Olist", page_icon=":busts_in_silhouette:", layout="wide"
)
apply_style()
brand_sidebar("RFM Segmentation")


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
        """,
        {"high": high, "low": low},
    )


SEGMENT_BLURBS = {
    "Champions": "Recent, frequent, high spenders. Reward and upsell.",
    "Loyal Customers": "Buy regularly. Worth a loyalty program.",
    "Potential Loyalists": "Recent buyers with promise. Nurture toward loyalty.",
    "At Risk": "Used to spend a lot, gone quiet. Win-back targets.",
    "Lost": "Long inactive, low engagement. Low priority.",
    "Others": "Everyone else — baseline customers.",
}


with st.sidebar:
    st.markdown("### Segment thresholds")
    high_score = st.slider(
        "High R/F/M score (Champions, Loyal)",
        min_value=2,
        max_value=4,
        value=3,
        help="Customers' R/F/M scores are 1–4 (NTILE quartiles). Raising this makes Champions a smaller, more elite group.",
    )
    low_score = st.slider(
        "Low R/F/M score (Lost, At Risk)",
        min_value=1,
        max_value=2,
        value=2,
    )
    st.divider()
    st.markdown("### Methodology")
    st.markdown(
        """
        * **Recency** — days since last delivered order
        * **Frequency** — total delivered orders
        * **Monetary** — total BRL spent (price + freight)

        Each axis is split into quartiles (NTILE 1–4); segments are then defined by combinations of those scores.
        """
    )

hero(
    "Customer RFM Segmentation",
    "Recency, Frequency, and Monetary value scoring identifies who to retain, who to win back, "
    "and who deserves a thank-you campaign. Segments are computed live from delivered orders.",
    pills=["Live OLTP query", "NTILE quartiles", "Adjustable thresholds"],
)

df = fetch_rfm(high_score, low_score)

if df.empty:
    st.warning("No RFM data returned.")
    st.stop()

df = df.sort_values("avg_total_spent", ascending=False).reset_index(drop=True)

total_customers = int(df["customer_count"].sum())
total_revenue = float(df["segment_revenue"].sum())

champions = df[df["customer_segment"] == "Champions"]
champ_count = int(champions["customer_count"].sum()) if not champions.empty else 0
champ_revenue = float(champions["segment_revenue"].sum()) if not champions.empty else 0
at_risk = df[df["customer_segment"].isin(["At Risk", "Lost"])]
at_risk_count = int(at_risk["customer_count"].sum()) if not at_risk.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers segmented", f"{total_customers:,}")
c2.metric("Total revenue", f"R$ {total_revenue / 1_000_000:.2f}M")
c3.metric(
    "Champions",
    f"{champ_count:,}",
    delta=f"{(champ_revenue / total_revenue * 100):.1f}% of revenue" if total_revenue else None,
    delta_color="normal",
)
c4.metric(
    "Win-back pool",
    f"{at_risk_count:,}",
    help="At Risk + Lost — customers worth a marketing nudge",
)

if total_revenue and champ_count:
    pct_customers = champ_count / total_customers * 100
    pct_revenue = champ_revenue / total_revenue * 100
    multiple = pct_revenue / pct_customers if pct_customers else 0
    insight(
        f"<strong>Champions are {pct_customers:.1f}% of customers</strong> but generate "
        f"<strong>{pct_revenue:.1f}% of revenue</strong> — roughly {multiple:.1f}× their per-capita share. "
        f"At Risk + Lost customers ({at_risk_count:,}) are the most addressable win-back pool."
    )

st.divider()

left, right = st.columns([3, 2])

with left:
    st.subheader("Customers per Segment")
    caption("Bar length is segment headcount; color encodes the segment identity used across all charts.")
    bar = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("customer_count:Q", title="Customers", axis=alt.Axis(format=",")),
            y=alt.Y("customer_segment:N", sort="-x", title=None),
            color=alt.Color(
                "customer_segment:N",
                scale=alt.Scale(
                    domain=list(SEGMENT_COLORS.keys()),
                    range=list(SEGMENT_COLORS.values()),
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("customer_segment:N", title="Segment"),
                alt.Tooltip("customer_count:Q", title="Customers", format=","),
                alt.Tooltip("avg_total_spent:Q", title="Avg Spend (BRL)", format=",.2f"),
                alt.Tooltip("segment_revenue:Q", title="Segment Revenue", format=",.0f"),
            ],
        )
        .properties(height=340)
    )
    labels = (
        alt.Chart(df)
        .mark_text(align="left", baseline="middle", dx=6, color="#475569", fontSize=11)
        .encode(
            x="customer_count:Q",
            y=alt.Y("customer_segment:N", sort="-x"),
            text=alt.Text("customer_count:Q", format=","),
        )
    )
    st.altair_chart(bar + labels, use_container_width=True)
    note(
        "<strong>Others</strong> is usually the largest bucket — those customers don't fit any "
        "prescriptive rule (mid-range across all three axes). Champions, Loyal, and Potential "
        "Loyalists are the actively-engaged tiers; At Risk and Lost are the win-back targets."
    )

with right:
    st.subheader("Revenue Share")
    caption("Where the BRL actually comes from. Often tells a different story than headcount.")
    pie = (
        alt.Chart(df)
        .mark_arc(innerRadius=65, outerRadius=130, cornerRadius=4)
        .encode(
            theta=alt.Theta("segment_revenue:Q"),
            color=alt.Color(
                "customer_segment:N",
                title=None,
                scale=alt.Scale(
                    domain=list(SEGMENT_COLORS.keys()),
                    range=list(SEGMENT_COLORS.values()),
                ),
            ),
            tooltip=[
                alt.Tooltip("customer_segment:N", title="Segment"),
                alt.Tooltip("segment_revenue:Q", title="Revenue (BRL)", format=",.0f"),
            ],
        )
        .properties(height=340)
    )
    st.altair_chart(pie, use_container_width=True)
    if total_revenue and champ_count:
        note(
            f"Champions punch well above their weight: <strong>{(champ_count / total_customers * 100):.1f}%</strong> "
            f"of customers, <strong>{(champ_revenue / total_revenue * 100):.1f}%</strong> of revenue. "
            "Losing one Champion is worth roughly losing several 'Others'."
        )

st.subheader("Segment Detail")
caption("Per-segment averages and totals. Use this to decide which segments deserve which campaigns.")

display = df.copy()
display["Segment"] = display["customer_segment"]
display["Customers"] = display["customer_count"].astype(int).map("{:,}".format)
display["Avg Recency (days)"] = display["avg_recency_days"].astype(float).round(0).astype(int)
display["Avg Orders"] = display["avg_orders"].round(2)
display["Avg Spend (BRL)"] = display["avg_total_spent"].apply(lambda v: f"R$ {v:,.2f}")
display["Segment Revenue (BRL)"] = display["segment_revenue"].apply(lambda v: f"R$ {v:,.0f}")
display["Recommended action"] = display["customer_segment"].map(SEGMENT_BLURBS).fillna("—")

table_cols = [
    "Segment",
    "Customers",
    "Avg Recency (days)",
    "Avg Orders",
    "Avg Spend (BRL)",
    "Segment Revenue (BRL)",
    "Recommended action",
]
st.dataframe(display[table_cols], hide_index=True, use_container_width=True)

st.download_button(
    "Download segment data (CSV)",
    data=to_csv_bytes(display[table_cols]),
    file_name="rfm_segments.csv",
    mime="text/csv",
    help="Export the segment summary as CSV",
)

with st.expander("How is this calculated?"):
    st.markdown(
        """
        For every unique customer (`customer_unique_id`) we compute:

        - **Recency** = days between today and the customer's most recent delivered order
        - **Frequency** = number of delivered orders
        - **Monetary** = sum of `price + freight_value` over all order items

        Each metric is bucketed into NTILE quartiles (1 = lowest, 4 = highest).
        Segments are then assigned by combinations of the three scores using the thresholds in the sidebar.
        Champions require **all three** scores to be at or above the high threshold; Lost requires recency and frequency at 1.
        """
    )

footer()
