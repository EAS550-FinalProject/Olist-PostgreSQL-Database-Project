"""Shared visual style for the Olist Analytics dashboard.

Defines the project palette, an Altair theme, and a CSS bundle that gets
injected on every page. Keeping this in one place means a tweak here flows
through every page.
"""

from __future__ import annotations

import altair as alt
import streamlit as st


PRIMARY = "#1E40AF"
PRIMARY_LIGHT = "#3B82F6"
ACCENT = "#F59E0B"
SUCCESS = "#10B981"
DANGER = "#EF4444"
INFO = "#06B6D4"
NEUTRAL = "#64748B"

CHART_PALETTE = [
    "#1E40AF",
    "#F59E0B",
    "#06B6D4",
    "#10B981",
    "#EF4444",
    "#A855F7",
    "#64748B",
    "#F97316",
]

SEGMENT_COLORS = {
    "Champions": "#F59E0B",
    "Loyal Customers": "#1E40AF",
    "Potential Loyalists": "#06B6D4",
    "At Risk": "#EF4444",
    "Lost": "#475569",
    "Others": "#94A3B8",
}


_CSS = """
<style>
    :root {
        --primary: #1E40AF;
        --primary-light: #3B82F6;
        --accent: #F59E0B;
        --bg-soft: #F8FAFC;
        --card: #FFFFFF;
        --border: #E2E8F0;
        --text: #0F172A;
        --muted: #64748B;
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
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        color: white;
        padding: 1.75rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(30, 64, 175, 0.18);
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
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-left: 4px solid var(--primary);
        padding: 0.9rem 1.1rem;
        border-radius: 8px;
        margin: 0.6rem 0 1.25rem 0;
        font-size: 0.93rem;
        color: #1E3A8A;
        line-height: 1.55;
    }
    .insight strong { color: #1E3A8A; }

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

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--primary);
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
