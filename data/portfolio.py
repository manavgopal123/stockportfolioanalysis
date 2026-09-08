"""Portfolio data fetching and processing."""

import pandas as pd
import streamlit as st
import yfinance as yf

BENCHMARK_TICKER = "^GSPC"
BENCHMARK_NAME = "S&P 500"

DEFAULT_PORTFOLIO = {
    "AAPL": 15,
    "MSFT": 10,
    "GOOGL": 8,
    "AMZN": 6,
    "TSLA": 5,
    "JPM": 12,
    "V": 10,
    "NVDA": 7,
}

PERIOD_OPTIONS = ["1M", "3M", "6M", "1Y", "2Y", "5Y"]
PERIOD_MAP = {
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "2Y": "2y",
    "5Y": "5y",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(tickers: tuple, period: str = "1y") -> tuple[pd.DataFrame, list]:
    """Fetch adjusted close price history for a list of tickers.

    Returns (prices_df, failed_tickers). prices_df has one column per
    ticker that returned usable data; failed_tickers lists tickers that
    yfinance could not return data for (invalid symbol, delisted, etc).
    """
    tickers = list(tickers)
    if not tickers:
        return pd.DataFrame(), []

    try:
        raw = yf.download(
            tickers, period=period, auto_adjust=True, progress=False, group_by="column"
        )
    except Exception:
        return pd.DataFrame(), tickers

    if raw.empty or "Close" not in raw.columns.get_level_values(0):
        return pd.DataFrame(), tickers

    closes = raw["Close"]
    closes = closes.dropna(axis=1, how="all")
    failed = [t for t in tickers if t not in closes.columns]
    closes = closes.dropna(axis=0, how="all").ffill()
    return closes[[t for t in tickers if t in closes.columns]], failed


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_benchmark(period: str = "1y") -> pd.Series:
    """Fetch S&P 500 close price history as a Series."""
    prices, failed = fetch_price_history((BENCHMARK_TICKER,), period=period)
    if BENCHMARK_TICKER in failed or prices.empty:
        return pd.Series(dtype=float, name=BENCHMARK_NAME)
    series = prices[BENCHMARK_TICKER].rename(BENCHMARK_NAME)
    return series


def current_prices(prices: pd.DataFrame) -> pd.Series:
    """Latest available close price per ticker from a price history DataFrame."""
    if prices.empty:
        return pd.Series(dtype=float)
    return prices.ffill().iloc[-1]


def previous_close(prices: pd.DataFrame) -> pd.Series:
    """Second-to-last available close price per ticker (for daily change %)."""
    if prices.shape[0] < 2:
        return current_prices(prices)
    return prices.ffill().iloc[-2]


def portfolio_market_values(prices: pd.DataFrame, shares: dict) -> pd.DataFrame:
    """Market value of each holding over time: price * shares."""
    if prices.empty:
        return pd.DataFrame()
    share_series = pd.Series(shares)
    aligned = prices[[t for t in prices.columns if t in share_series.index]]
    return aligned.mul(share_series[aligned.columns], axis=1)
