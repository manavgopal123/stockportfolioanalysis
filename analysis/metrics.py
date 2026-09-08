"""Financial metrics calculations."""

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.05


def daily_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Simple daily percentage returns."""
    return prices.pct_change().dropna(how="all")


def cumulative_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Cumulative return from the first observation, as a fraction (0.10 = +10%)."""
    returns = daily_returns(prices)
    return (1 + returns).cumprod() - 1


def normalized_prices(prices: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    """Rebase each column to `base` at the first available date."""
    if prices.empty:
        return prices
    return prices.div(prices.iloc[0]).mul(base)


def portfolio_value(prices: pd.DataFrame, shares: dict) -> pd.Series:
    """Total portfolio market value over time."""
    if prices.empty:
        return pd.Series(dtype=float)
    share_series = pd.Series(shares)
    cols = [t for t in prices.columns if t in share_series.index]
    return prices[cols].mul(share_series[cols], axis=1).sum(axis=1)


def annualized_return(returns: pd.Series) -> float:
    """Annualized return from a series of daily returns."""
    returns = returns.dropna()
    n = len(returns)
    if n == 0:
        return np.nan
    total_return = (1 + returns).prod() - 1
    years = n / TRADING_DAYS_PER_YEAR
    if years <= 0:
        return np.nan
    return (1 + total_return) ** (1 / years) - 1


def annualized_volatility(returns: pd.Series) -> float:
    """Annualized volatility (standard deviation) from daily returns."""
    returns = returns.dropna()
    if len(returns) < 2:
        return np.nan
    return returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE) -> float:
    """Sharpe ratio: (annualized return - risk free rate) / annualized volatility."""
    ann_return = annualized_return(returns)
    ann_vol = annualized_volatility(returns)
    if not ann_vol or np.isnan(ann_vol) or ann_vol == 0:
        return np.nan
    return (ann_return - risk_free_rate) / ann_vol


def max_drawdown(value_series: pd.Series) -> float:
    """Maximum peak-to-trough decline, as a negative fraction (e.g. -0.23)."""
    value_series = value_series.dropna()
    if value_series.empty:
        return np.nan
    running_max = value_series.cummax()
    drawdown = (value_series - running_max) / running_max
    return drawdown.min()


def beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """Beta of a stock vs the market: cov(stock, market) / var(market)."""
    aligned = pd.concat([stock_returns, market_returns], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return np.nan
    covariance = aligned.iloc[:, 0].cov(aligned.iloc[:, 1])
    market_variance = aligned.iloc[:, 1].var()
    if market_variance == 0:
        return np.nan
    return covariance / market_variance


def correlation_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix of daily returns between all holdings."""
    return daily_returns(prices).corr()


def rolling_volatility(prices: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Rolling annualized volatility over a trailing window (in trading days)."""
    returns = daily_returns(prices)
    return returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def per_stock_metrics_table(prices: pd.DataFrame, market_returns: pd.Series) -> pd.DataFrame:
    """Build a summary table of key metrics for each holding."""
    returns = daily_returns(prices)
    rows = []
    for ticker in prices.columns:
        stock_returns = returns[ticker]
        rows.append(
            {
                "Ticker": ticker,
                "Annualized Return": annualized_return(stock_returns),
                "Volatility": annualized_volatility(stock_returns),
                "Sharpe Ratio": sharpe_ratio(stock_returns),
                "Beta": beta(stock_returns, market_returns),
                "Max Drawdown": max_drawdown((1 + stock_returns.fillna(0)).cumprod()),
            }
        )
    return pd.DataFrame(rows).set_index("Ticker")


def portfolio_weights(prices: pd.DataFrame, shares: dict) -> pd.Series:
    """Current allocation weight of each holding, based on latest prices."""
    if prices.empty:
        return pd.Series(dtype=float)
    latest = prices.ffill().iloc[-1]
    share_series = pd.Series(shares)
    cols = [t for t in prices.columns if t in share_series.index]
    values = latest[cols] * share_series[cols]
    total = values.sum()
    if total == 0:
        return pd.Series(dtype=float)
    return values / total
