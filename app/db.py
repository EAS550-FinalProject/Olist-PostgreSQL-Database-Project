from __future__ import annotations

import logging
import os
import time

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError

load_dotenv()

_log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 4
_BASE_DELAY = 1.0


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


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, OperationalError):
        return True
    if isinstance(exc, DBAPIError):
        # connection_failure, server_closed_connection, etc.
        msg = str(exc).lower()
        return any(
            term in msg
            for term in (
                "connection",
                "timeout",
                "ssl",
                "server closed",
                "could not connect",
                "endpoint is disabled",
            )
        )
    return False


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    last_exc: BaseException | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            with engine.connect() as conn:
                return pd.read_sql(text(sql), conn, params=params or {})
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < _MAX_ATTEMPTS and _is_transient(exc):
                delay = _BASE_DELAY * (2 ** (attempt - 1))
                _log.warning(
                    "DB query failed (attempt %d/%d): %s — retrying in %.1fs",
                    attempt, _MAX_ATTEMPTS, exc, delay,
                )
                time.sleep(delay)
                continue
            raise
    # Unreachable but satisfies type checkers.
    raise last_exc



@st.cache_data(ttl=600, show_spinner=False)
def run_sql_file(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        return run_query(f.read())


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
