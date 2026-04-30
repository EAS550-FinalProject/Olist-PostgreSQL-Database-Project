"""Database access for the Streamlit app.

Connects to Neon Postgres via SQLAlchemy with a small connection pool tuned
for Neon's free tier (idle compute pauses after 5 minutes). Engine is cached
with @st.cache_resource so the pool is shared across reruns within a session;
query functions cache results with @st.cache_data so the dashboard does not
re-hit Neon on every widget interaction.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        st.error(
            "DATABASE_URL is not configured. Set it as an environment "
            "variable or in .streamlit/secrets.toml."
        )
        st.stop()


@st.cache_resource
def get_engine() -> Engine:
    return create_engine(
        _get_database_url(),
        pool_size=2,
        max_overflow=3,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
    )


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


@st.cache_data(ttl=600, show_spinner=False)
def run_sql_file(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        return run_query(f.read())
