"""Plotly chart builders. Every function returns a `go.Figure`."""

import pandas as pd
import plotly.graph_objects as go

TEMPLATE = "plotly_dark"
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


def stock_price_chart(close: pd.Series, start: pd.Timestamp, buy_price: float, ma_days: int) -> go.Figure:
    """Price with 50-day and N-day averages and the buy price line, over the selected window."""
    close = close.dropna()
    if close.empty:
        return _empty_fig()

    visible = close.index >= start
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=close.index[visible], y=close[visible], name="Price",
            line=dict(color=MAIZE, width=2.5),
        )
    )
    windows = [50] if ma_days == 50 else [50, ma_days]
    for days, color in zip(windows, ("#5B9BD5", "#70AD47")):
        average = close.rolling(days).mean()[visible]
        fig.add_trace(
            go.Scatter(
                x=average.index, y=average, name=f"{days}-day avg",
                line=dict(color=color, width=1.6, dash="dot"),
            )
        )
    if buy_price and buy_price > 0:
        fig.add_hline(
            y=buy_price, line_dash="dash", line_color="white",
            annotation_text=f"Buy ${buy_price:,.2f}", annotation_position="bottom right",
        )
    fig.update_layout(
        template=TEMPLATE, xaxis_title="Date", yaxis_title="Price ($)", height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def normalized_performance_chart(prices: pd.DataFrame, benchmark: pd.Series | None = None) -> go.Figure:
    """Every stock (and the benchmark) rebased to 100 at the start of the window."""
    if prices.empty:
        return _empty_fig()

    normalized = prices.div(prices.bfill().iloc[0]).mul(100)
    fig = go.Figure()
    for i, col in enumerate(normalized.columns):
        fig.add_trace(
            go.Scatter(
                x=normalized.index, y=normalized[col], name=col,
                line=dict(color=LINE_COLORS[i % len(LINE_COLORS)], width=1.8),
            )
        )
    if benchmark is not None and not benchmark.empty:
        rebased = benchmark.div(benchmark.dropna().iloc[0]).mul(100)
        fig.add_trace(
            go.Scatter(
                x=rebased.index, y=rebased.values, name=benchmark.name or "S&P 500",
                line=dict(color="white", width=2.5, dash="dash"),
            )
        )
    fig.update_layout(
        template=TEMPLATE, title="All stocks vs S&P 500 (start of window = 100)",
        xaxis_title="Date", yaxis_title="Indexed value", height=450, hovermode="x unified",
    )
    return fig
