"""Shared visual style for the Olist Analytics dashboard.

Defines the project palette, an Altair theme, and a CSS bundle that gets
injected on every page. Keeping this in one place means a tweak here flows
through every page.
"""

from __future__ import annotations

from datetime import datetime

import altair as alt
import streamlit as st


PRIMARY = "#DC2626"        # ember red
PRIMARY_LIGHT = "#F87171"  # softer red for gradients
ACCENT = "#F59E0B"         # amber
SUCCESS = "#10B981"        # green (kept for "delivered" status etc.)
DANGER = "#7F1D1D"         # deep wine for "bad" indicators
INFO = "#0891B2"           # teal as a cool counterpoint
NEUTRAL = "#475569"        # slate

DARK = "#1F2937"           # charcoal — used in hero gradient
DARK_DEEP = "#111827"      # deepest charcoal

CHART_PALETTE = [
    "#DC2626",  # ember red
    "#F59E0B",  # amber
    "#1F2937",  # charcoal
    "#F97316",  # orange
    "#10B981",  # green
    "#7C3AED",  # violet (rare contrast)
    "#0891B2",  # teal
    "#64748B",  # slate
]

SEGMENT_COLORS = {
    "Champions": "#F59E0B",          # amber — top of the warm scale
    "Loyal Customers": "#DC2626",    # ember red
    "Potential Loyalists": "#F97316",  # orange
    "At Risk": "#7C3AED",            # violet — visual contrast for "danger"
    "Lost": "#1F2937",               # charcoal — out of the volcano palette
    "Others": "#94A3B8",             # slate
}


_CSS = """
<style>
    :root {
        --primary: #DC2626;
        --primary-light: #F87171;
        --primary-deep: #991B1B;
        --accent: #F59E0B;
        --dark: #1F2937;
        --bg-soft: #FAFAF9;
        --card: #FFFFFF;
        --border: #E7E5E4;
        --text: #1C1917;
        --muted: #57534E;
    }

    .main > div:first-child {
        padding-top: 2rem;
    }

    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        color: var(--text);
    }

    h2 {
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        margin-top: 1.5rem !important;
        color: var(--text);
    }

    h3 {
        font-weight: 600 !important;
        color: var(--text);
    }

    .hero-card {
        background: linear-gradient(135deg, #1F2937 0%, #DC2626 100%);
        color: white;
        padding: 1.75rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(220, 38, 38, 0.22);
    }
    .hero-card h1 {
        color: white !important;
        margin: 0 0 0.4rem 0;
        font-size: 2rem;
    }
    .hero-card p {
        color: rgba(255, 255, 255, 0.92);
        font-size: 1rem;
        margin: 0;
        line-height: 1.5;
    }
    .hero-card .pill {
        display: inline-block;
        background: rgba(255, 255, 255, 0.18);
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 500;
        margin-right: 0.4rem;
        margin-top: 0.6rem;
    }

    [data-testid="stMetric"] {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: var(--muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
    }

    .insight {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border-left: 4px solid var(--primary);
        padding: 0.9rem 1.1rem;
        border-radius: 8px;
        margin: 0.6rem 0 1.25rem 0;
        font-size: 0.93rem;
        color: #7F1D1D;
        line-height: 1.55;
    }
    .insight strong { color: #7F1D1D; }

    .insight-warn {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border-left-color: var(--accent);
        color: #78350F;
    }
    .insight-warn strong { color: #78350F; }

    .section-caption {
        color: var(--muted);
        font-size: 0.92rem;
        margin: -0.4rem 0 1rem 0;
        line-height: 1.5;
    }

    .data-note {
        font-size: 0.88rem;
        color: #334155;
        padding: 0.6rem 0.85rem 0.6rem 1rem;
        border-left: 3px solid #CBD5E1;
        background: #F8FAFC;
        border-radius: 4px;
        margin: 0.6rem 0 1.5rem 0;
        line-height: 1.6;
    }
    .data-note .label {
        color: var(--primary);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        margin-right: 0.4rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FAFAF9 0%, #FEF3C7 100%);
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--primary);
    }

    .sidebar-brand {
        background: linear-gradient(135deg, #1F2937 0%, #DC2626 100%);
        border-radius: 10px;
        padding: 1rem 1rem 0.9rem 1rem;
        margin: 0 0 1rem 0;
        color: white;
        box-shadow: 0 4px 14px rgba(220, 38, 38, 0.22);
    }
    .sidebar-brand .accent {
        width: 28px; height: 4px; border-radius: 2px;
        background: var(--accent);
        margin-bottom: 0.6rem;
    }
    .sidebar-brand .name {
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        margin: 0;
        line-height: 1.2;
    }
    .sidebar-brand .tagline {
        font-size: 0.74rem;
        opacity: 0.92;
        margin: 0.25rem 0 0 0;
        font-weight: 500;
        letter-spacing: 0.02em;
    }

    .sidebar-section-label {
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.08em;
        font-weight: 700;
        color: var(--muted);
        margin: 0.25rem 0 0.4rem 0;
    }

    .page-footer {
        border-top: 1px solid var(--border);
        margin-top: 2.5rem;
        padding: 1rem 0 0.4rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: var(--muted);
        font-size: 0.82rem;
        flex-wrap: wrap;
        gap: 0.6rem;
    }
    .page-footer .meta {
        font-variant-numeric: tabular-nums;
    }
    .page-footer .dot {
        display: inline-block;
        width: 7px; height: 7px; border-radius: 50%;
        background: #10B981;
        margin-right: 0.4rem;
        vertical-align: middle;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }

    hr { border-color: var(--border); }
    [data-testid="stHorizontalBlock"] { gap: 1rem; }
</style>
"""


def _olist_altair_theme() -> dict:
    return {
        "config": {
            "background": "white",
            "view": {"strokeWidth": 0, "continuousHeight": 320},
            "axis": {
                "labelFont": "Source Sans Pro, sans-serif",
                "titleFont": "Source Sans Pro, sans-serif",
                "labelColor": "#475569",
                "titleColor": "#0F172A",
                "titleFontSize": 12,
                "labelFontSize": 11,
                "titleFontWeight": 600,
                "gridColor": "#E2E8F0",
                "domainColor": "#CBD5E1",
                "tickColor": "#CBD5E1",
            },
            "legend": {
                "labelFont": "Source Sans Pro, sans-serif",
                "titleFont": "Source Sans Pro, sans-serif",
                "labelColor": "#475569",
                "titleColor": "#0F172A",
                "titleFontSize": 12,
                "labelFontSize": 11,
            },
            "title": {
                "font": "Source Sans Pro, sans-serif",
                "fontSize": 14,
                "fontWeight": 600,
                "color": "#0F172A",
                "anchor": "start",
            },
            "range": {"category": CHART_PALETTE},
        }
    }


def apply_style() -> None:
    """Inject CSS and register the Altair theme. Call once at the top of every page."""
    st.markdown(_CSS, unsafe_allow_html=True)
    alt.themes.register("olist", _olist_altair_theme)
    alt.themes.enable("olist")


def hero(title: str, subtitle: str, pills: list[str] | None = None) -> None:
    pills_html = "".join(f'<span class="pill">{p}</span>' for p in (pills or []))
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div>{pills_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight(text: str, *, kind: str = "info") -> None:
    cls = "insight" if kind == "info" else "insight insight-warn"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


def caption(text: str) -> None:
    st.markdown(f'<p class="section-caption">{text}</p>', unsafe_allow_html=True)


def note(text: str, label: str = "Note") -> None:
    """Interpretation note shown directly below a chart."""
    st.markdown(
        f'<div class="data-note"><span class="label">{label}</span>{text}</div>',
        unsafe_allow_html=True,
    )


_PAGES = [
    ("Overview.py", "Overview"),
    ("pages/1_RFM_Analysis.py", "RFM Analysis"),
    ("pages/2_Seller_Performance.py", "Seller Performance"),
    ("pages/3_Cohort_Retention.py", "Cohort Retention"),
]


def brand_sidebar(tagline: str = "Phase 3 · Live BI Dashboard") -> None:
    """Render the brand block, page nav, and a refresh button at the top of the sidebar."""
    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="accent"></div>
            <p class="name">OLIST ANALYTICS</p>
            <p class="tagline">{tagline}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # st.page_link requires an entrypoint context; skip when not available
    # (e.g. headless AppTest invocations) so the page can still render.
    try:
        st.sidebar.markdown('<p class="sidebar-section-label">Pages</p>', unsafe_allow_html=True)
        for path, label in _PAGES:
            st.sidebar.page_link(path, label=label)
        st.sidebar.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    except Exception:
        pass
    if st.sidebar.button("Refresh data", use_container_width=True, help="Clear all cached queries and re-fetch from Neon"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.divider()


def footer() -> None:
    """Page-level footer with attribution and live render timestamp."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f"""
        <div class="page-footer">
            <span><span class="dot"></span>Olist Analytics · powered by Neon Postgres + dbt + Streamlit</span>
            <span class="meta">Page rendered {now} · cache TTL 10 min</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
