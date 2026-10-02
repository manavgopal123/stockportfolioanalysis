"""Supabase-backed persistence for the user's portfolio holdings."""

import streamlit as st
from supabase import Client, create_client

TABLE = "portfolio_holdings"


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def load_portfolio() -> tuple[dict, bool]:
    """Load saved holdings from Supabase.

    Returns (portfolio, ok). portfolio is {} if nothing is saved yet or the
    fetch failed; ok is False only when Supabase could not be reached, so
    callers can tell "no holdings saved" apart from "connection failed".
    """
    try:
        response = _client().table(TABLE).select("ticker, shares").execute()
        return {row["ticker"]: row["shares"] for row in response.data}, True
    except Exception:
        return {}, False


def save_portfolio(portfolio: dict) -> bool:
    """Overwrite saved holdings in Supabase with the current portfolio dict."""
    try:
        client = _client()
        client.table(TABLE).delete().neq("ticker", "").execute()
        if portfolio:
            rows = [{"ticker": t, "shares": s} for t, s in portfolio.items()]
            client.table(TABLE).insert(rows).execute()
        return True
    except Exception:
        return False
