"""Supabase-backed persistence for the watchlist and the keep/sell rules."""

import streamlit as st
from supabase import Client, create_client

WATCHLIST_TABLE = "watchlist"
SETTINGS_TABLE = "app_settings"
RULES_KEY = "rules"


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def load_watchlist() -> tuple[dict, bool]:
    """Returns ({ticker: buy_price}, ok). ok is False only if Supabase could not be reached."""
    try:
        rows = _client().table(WATCHLIST_TABLE).select("ticker, buy_price").execute().data
    except Exception:
        return {}, False
    return {row["ticker"]: float(row["buy_price"] or 0) for row in rows}, True


def save_watchlist(watchlist: dict) -> bool:
    """Make the saved watchlist match `watchlist`. Upserts first so it is never briefly empty."""
    try:
        client = _client()
        if watchlist:
            rows = [{"ticker": t, "buy_price": p} for t, p in watchlist.items()]
            client.table(WATCHLIST_TABLE).upsert(rows).execute()
            client.table(WATCHLIST_TABLE).delete().not_.in_("ticker", list(watchlist)).execute()
        else:
            client.table(WATCHLIST_TABLE).delete().neq("ticker", "").execute()
        return True
    except Exception:
        return False


def load_rules() -> tuple[dict | None, bool]:
    """Returns (rules, ok). rules is None if none have been saved yet."""
    try:
        rows = (
            _client().table(SETTINGS_TABLE).select("value").eq("key", RULES_KEY).execute().data
        )
    except Exception:
        return None, False
    return (rows[0]["value"] if rows else None), True


def save_rules(rules: dict) -> bool:
    try:
        _client().table(SETTINGS_TABLE).upsert({"key": RULES_KEY, "value": rules}).execute()
        return True
    except Exception:
        return False
