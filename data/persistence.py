"""Supabase-backed persistence for the user's portfolio holdings."""

import streamlit as st
from supabase import Client, create_client

TABLE = "portfolio_holdings"
# Marks the table as set up, so a deliberately empty portfolio isn't mistaken
# for a first run (which would re-seed the defaults).
INITIALIZED_MARKER = "__initialized__"


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def load_portfolio() -> tuple[dict | None, bool]:
    """Load saved holdings from Supabase.

    Returns (portfolio, ok). portfolio is None when nothing has ever been
    saved (first run) or Supabase could not be reached; an empty dict means
    the user deliberately cleared their holdings. ok is False only on a
    connection failure.
    """
    try:
        response = _client().table(TABLE).select("ticker, shares").execute()
    except Exception:
        return None, False

    holdings = {row["ticker"]: row["shares"] for row in response.data}
    was_initialized = INITIALIZED_MARKER in holdings
    holdings.pop(INITIALIZED_MARKER, None)
    if not was_initialized and not holdings:
        return None, True
    return holdings, True


def save_portfolio(portfolio: dict) -> bool:
    """Overwrite saved holdings in Supabase with the current portfolio dict."""
    try:
        client = _client()
        client.table(TABLE).delete().neq("ticker", "").execute()
        rows = [{"ticker": t, "shares": s} for t, s in portfolio.items()]
        rows.append({"ticker": INITIALIZED_MARKER, "shares": 0})
        client.table(TABLE).insert(rows).execute()
        return True
    except Exception:
        return False
