"""Market data fetching (Yahoo Finance via yfinance)."""

import pandas as pd
import streamlit as st
import yfinance as yf

BENCHMARK_TICKER = "^GSPC"
BENCHMARK_NAME = "S&P 500"

PERIOD_MONTHS = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12, "2Y": 24, "5Y": 60}
PERIOD_OPTIONS = list(PERIOD_MONTHS)


def history_period(window_label: str) -> str:
    """yfinance period to download. Never less than 2y so long moving averages have data."""
    return "5y" if window_label == "5Y" else "2y"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(tickers: tuple, period: str) -> tuple[pd.DataFrame, list]:
    """Fetch daily closing prices (split-adjusted, dividends not added back).

    Returns (prices, failed). prices has one column per ticker that returned
    data; failed lists tickers Yahoo had no data for.
    """
    tickers = list(tickers)
    if not tickers:
        return pd.DataFrame(), []

    try:
        raw = yf.download(
            tickers, period=period, auto_adjust=False, progress=False, group_by="column"
        )
    except Exception:
        return pd.DataFrame(), tickers

    if raw.empty or "Close" not in raw.columns.get_level_values(0):
        return pd.DataFrame(), tickers

    closes = raw["Close"].dropna(axis=1, how="all")
    failed = [t for t in tickers if t not in closes.columns]
    closes = closes.dropna(axis=0, how="all").ffill()
    return closes[[t for t in tickers if t in closes.columns]], failed


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_benchmark(period: str) -> pd.Series:
    """S&P 500 closing prices as a Series (empty if unavailable)."""
    prices, failed = fetch_price_history((BENCHMARK_TICKER,), period)
    if BENCHMARK_TICKER in failed or prices.empty:
        return pd.Series(dtype=float, name=BENCHMARK_NAME)
    return prices[BENCHMARK_TICKER].rename(BENCHMARK_NAME)
