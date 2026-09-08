"""Plotly chart builders. Every function returns a `go.Figure`."""

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

TEMPLATE = "plotly_dark"
NAVY = "#00274C"
MAIZE = "#FFCB05"
LINE_COLORS = [
    MAIZE, "#5B9BD5", "#70AD47", "#ED7D31", "#A5A5A5",
    "#C00000", "#7030A0", "#00B0F0", "#92D050", "#FF6699",
]


def _empty_fig(message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(template=TEMPLATE, height=400)
    fig.add_annotation(text=message, showarrow=False, font=dict(size=16))
    return fig


def portfolio_vs_benchmark_chart(portfolio_value: pd.Series, benchmark: pd.Series) -> go.Figure:
    """Portfolio vs S&P 500 performance, both indexed to 100 at the start date
    so they share one axis and are directly comparable."""
    if portfolio_value.empty:
        return _empty_fig()

    normalized_portfolio = portfolio_value.div(portfolio_value.iloc[0]).mul(100)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=normalized_portfolio.index, y=normalized_portfolio.values,
            name="Portfolio", line=dict(color=MAIZE, width=2.5),
        )
    )
    if not benchmark.empty:
        normalized_benchmark = benchmark.div(benchmark.iloc[0]).mul(100)
        fig.add_trace(
            go.Scatter(
                x=normalized_benchmark.index, y=normalized_benchmark.values,
                name=benchmark.name or "S&P 500", line=dict(color="#5B9BD5", width=2, dash="dot"),
            )
        )
    fig.update_layout(
        template=TEMPLATE, title="Portfolio vs S&P 500 (Indexed to 100)",
        xaxis_title="Date", yaxis_title="Indexed Value (Base = 100)", height=450, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def normalized_performance_chart(prices: pd.DataFrame, benchmark: pd.Series | None = None) -> go.Figure:
    """All holdings (and optional benchmark) rebased to 100 at the start date."""
    if prices.empty:
        return _empty_fig()

    normalized = prices.div(prices.iloc[0]).mul(100)
    fig = go.Figure()
    for i, col in enumerate(normalized.columns):
        fig.add_trace(
            go.Scatter(
                x=normalized.index, y=normalized[col], name=col,
                line=dict(color=LINE_COLORS[i % len(LINE_COLORS)], width=1.8),
            )
        )
    if benchmark is not None and not benchmark.empty:
        norm_bench = benchmark.div(benchmark.iloc[0]).mul(100)
        fig.add_trace(
            go.Scatter(
                x=norm_bench.index, y=norm_bench.values, name=benchmark.name or "S&P 500",
                line=dict(color="white", width=2.5, dash="dash"),
            )
        )
    fig.update_layout(
        template=TEMPLATE, title="Normalized Performance (Base = 100)",
        xaxis_title="Date", yaxis_title="Indexed Value", height=450, hovermode="x unified",
    )
    return fig


def cumulative_returns_chart(prices: pd.DataFrame, benchmark: pd.Series | None = None) -> go.Figure:
    """Cumulative return (%) for each holding and the benchmark."""
    if prices.empty:
        return _empty_fig()

    returns = prices.pct_change()
    cumulative = ((1 + returns).cumprod() - 1) * 100
    fig = go.Figure()
    for i, col in enumerate(cumulative.columns):
        fig.add_trace(
            go.Scatter(
                x=cumulative.index, y=cumulative[col], name=col,
                line=dict(color=LINE_COLORS[i % len(LINE_COLORS)], width=1.8),
            )
        )
    if benchmark is not None and not benchmark.empty:
        bench_cum = ((1 + benchmark.pct_change()).cumprod() - 1) * 100
        fig.add_trace(
            go.Scatter(
                x=bench_cum.index, y=bench_cum.values, name=benchmark.name or "S&P 500",
                line=dict(color="white", width=2.5, dash="dash"),
            )
        )
    fig.update_layout(
        template=TEMPLATE, title="Cumulative Returns",
        xaxis_title="Date", yaxis_title="Cumulative Return (%)", height=450, hovermode="x unified",
    )
    return fig


def allocation_pie_chart(weights: pd.Series) -> go.Figure:
    """Current portfolio allocation by market value."""
    if weights.empty:
        return _empty_fig()

    fig = px.pie(
        names=weights.index, values=weights.values, template=TEMPLATE,
        color_discrete_sequence=LINE_COLORS, hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(title="Portfolio Allocation", height=450)
    return fig


def rolling_volatility_chart(rolling_vol: pd.DataFrame, window: int = 30) -> go.Figure:
    """Rolling annualized volatility for each holding."""
    if rolling_vol.empty:
        return _empty_fig()

    fig = go.Figure()
    for i, col in enumerate(rolling_vol.columns):
        fig.add_trace(
            go.Scatter(
                x=rolling_vol.index, y=rolling_vol[col] * 100, name=col,
                line=dict(color=LINE_COLORS[i % len(LINE_COLORS)], width=1.6),
            )
        )
    fig.update_layout(
        template=TEMPLATE, title=f"Rolling {window}-Day Annualized Volatility",
        xaxis_title="Date", yaxis_title="Volatility (%)", height=450, hovermode="x unified",
    )
    return fig


def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    """Correlation matrix heatmap of daily returns."""
    if corr.empty:
        return _empty_fig()

    fig = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1,
        template=TEMPLATE, aspect="auto",
    )
    fig.update_layout(title="Correlation Matrix (Daily Returns)", height=500)
    return fig


def returns_distribution_grid(returns: pd.DataFrame) -> go.Figure:
    """Grid of daily-return distribution histograms, one subplot per stock."""
    if returns.empty:
        return _empty_fig()

    cols = returns.columns.tolist()
    n = len(cols)
    ncols = min(3, n)
    nrows = math.ceil(n / ncols)
    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=cols)

    for i, col in enumerate(cols):
        row, c = divmod(i, ncols)
        fig.add_trace(
            go.Histogram(
                x=returns[col].dropna() * 100, name=col, marker_color=LINE_COLORS[i % len(LINE_COLORS)],
                showlegend=False, nbinsx=40,
            ),
            row=row + 1, col=c + 1,
        )

    fig.update_layout(template=TEMPLATE, title="Daily Returns Distribution", height=300 * nrows)
    fig.update_xaxes(title_text="Daily Return (%)")
    fig.update_yaxes(title_text="Frequency")
    return fig


def portfolio_vs_benchmark_scatter(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> go.Figure:
    """Scatter of portfolio daily returns vs benchmark daily returns."""
    aligned = pd.concat([portfolio_returns, benchmark_returns], axis=1, join="inner").dropna()
    if aligned.empty:
        return _empty_fig()
    aligned.columns = ["Portfolio", "Benchmark"]

    fig = px.scatter(
        aligned, x="Benchmark", y="Portfolio", template=TEMPLATE,
        color_discrete_sequence=[MAIZE],
    )
    fig.update_layout(
        title="Portfolio vs S&P 500 Daily Returns",
        xaxis_title="S&P 500 Daily Return", yaxis_title="Portfolio Daily Return",
        xaxis_tickformat=".1%", yaxis_tickformat=".1%", height=450,
    )
    return fig


def risk_return_scatter(metrics: pd.DataFrame, weights: pd.Series) -> go.Figure:
    """Risk vs return bubble chart: volatility (x), return (y), bubble size = weight."""
    if metrics.empty:
        return _empty_fig()

    df = metrics.copy()
    df["Weight"] = weights.reindex(df.index).fillna(0)
    df = df.dropna(subset=["Volatility", "Annualized Return"])
    if df.empty:
        return _empty_fig()

    fig = px.scatter(
        df, x="Volatility", y="Annualized Return", size="Weight", text=df.index,
        template=TEMPLATE, color_discrete_sequence=[MAIZE], size_max=50,
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        title="Risk vs Return (bubble size = portfolio weight)",
        xaxis_title="Annualized Volatility", yaxis_title="Annualized Return",
        xaxis_tickformat=".1%", yaxis_tickformat=".1%", height=500,
    )
    return fig
