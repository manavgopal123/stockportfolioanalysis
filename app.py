"""Stock Portfolio Analysis dashboard."""

from datetime import datetime

import pandas as pd
import streamlit as st

from analysis import charts, metrics
from data import persistence, portfolio as portfolio_data

NAVY = "#00274C"
MAIZE = "#FFCB05"
POSITIVE = "#3DDC84"
NEGATIVE = "#FF6B6B"
NEUTRAL = "#FFFFFF"

st.set_page_config(page_title="Stock Portfolio Analysis", layout="wide", page_icon="📈")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #0e1117; }}
    h1, h2, h3 {{ color: {MAIZE}; }}
    .metric-card {{
        background-color: {NAVY};
        border: 1px solid #1f3a5f;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }}
    .metric-label {{
        color: {MAIZE};
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }}
    .metric-value {{
        font-size: clamp(1rem, 2.1vw, 1.6rem);
        font-weight: 700;
        white-space: nowrap;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_metric(col, label: str, value_str: str, sentiment: str | None = None) -> None:
    """Render a metric card with optional green/red color coding."""
    color = {"pos": POSITIVE, "neg": NEGATIVE}.get(sentiment, NEUTRAL)
    col.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sentiment_of(value: float) -> str | None:
    if pd.isna(value):
        return None
    return "pos" if value >= 0 else "neg"


# ---------------------------------------------------------------------------
# Session state / sidebar controls
# ---------------------------------------------------------------------------

if "portfolio" not in st.session_state:
    loaded, persistence_ok = persistence.load_portfolio()
    st.session_state.persistence_ok = persistence_ok
    if loaded is not None:
        st.session_state.portfolio = loaded
    else:
        st.session_state.portfolio = dict(portfolio_data.DEFAULT_PORTFOLIO)
        if persistence_ok:
            persistence.save_portfolio(st.session_state.portfolio)
    st.session_state._last_saved_portfolio = dict(st.session_state.portfolio)

st.sidebar.title("Portfolio Settings")
if st.session_state.persistence_ok:
    st.sidebar.caption("Synced to Supabase")
else:
    st.sidebar.caption("Offline — changes won't be saved (check Supabase connection)")

with st.sidebar.form("add_ticker_form", clear_on_submit=True):
    st.markdown("**Add Holdings**")
    new_tickers = st.text_input("Ticker(s), comma separated", placeholder="e.g. NFLX, DIS")
    new_shares = st.number_input("Shares per new ticker", min_value=1, value=10, step=1)
    if st.form_submit_button("Add") and new_tickers.strip():
        for t in [x.strip().upper() for x in new_tickers.split(",") if x.strip()]:
            st.session_state.portfolio[t] = new_shares

def sync_portfolio() -> None:
    """Save the current portfolio to Supabase if it differs from what's saved."""
    if (
        st.session_state.persistence_ok
        and st.session_state.portfolio != st.session_state._last_saved_portfolio
    ):
        if persistence.save_portfolio(st.session_state.portfolio):
            st.session_state._last_saved_portfolio = dict(st.session_state.portfolio)


st.sidebar.markdown("**Current Holdings**")
if not st.session_state.portfolio:
    st.sidebar.caption("No holdings yet — add a ticker above.")
else:
    for ticker in list(st.session_state.portfolio.keys()):
        col1, col2, col3 = st.sidebar.columns([2, 2, 1])
        col1.markdown(f"`{ticker}`")
        shares_val = col2.number_input(
            f"shares_{ticker}", min_value=0, step=1,
            value=int(st.session_state.portfolio[ticker]),
            label_visibility="collapsed", key=f"shares_{ticker}",
        )
        st.session_state.portfolio[ticker] = shares_val
        if col3.button("Remove", key=f"remove_{ticker}"):
            del st.session_state.portfolio[ticker]
            sync_portfolio()
            st.rerun()

sync_portfolio()

st.sidebar.divider()
period_label = st.sidebar.selectbox(
    "Date Range", portfolio_data.PERIOD_OPTIONS, index=portfolio_data.PERIOD_OPTIONS.index("1Y")
)

if st.sidebar.button("Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Stock Portfolio Analysis")
st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}")

tickers = list(st.session_state.portfolio.keys())
shares = dict(st.session_state.portfolio)

if not tickers:
    st.info("Add at least one ticker in the sidebar to see your dashboard.")
    st.stop()

period = portfolio_data.PERIOD_MAP[period_label]

with st.spinner("Fetching market data..."):
    prices, failed = portfolio_data.fetch_price_history(tuple(tickers), period=period)
    benchmark = portfolio_data.fetch_benchmark(period=period)

if failed:
    st.warning(f"Could not fetch data for: {', '.join(failed)}. They are excluded below.")

if prices.empty:
    st.error("No price data could be retrieved for any of your holdings. Try different tickers.")
    st.stop()

valid_tickers = list(prices.columns)
valid_shares = {t: shares[t] for t in valid_tickers}


# ---------------------------------------------------------------------------
# Shared calculations
# ---------------------------------------------------------------------------

port_value = metrics.portfolio_value(prices, valid_shares)
port_returns = metrics.daily_returns(port_value)
benchmark_returns = metrics.daily_returns(benchmark) if not benchmark.empty else pd.Series(dtype=float)
weights = metrics.portfolio_weights(prices, valid_shares)
returns_df = metrics.daily_returns(prices)
per_stock_metrics = metrics.per_stock_metrics_table(prices, benchmark_returns)

total_value = port_value.iloc[-1] if not port_value.empty else 0.0
total_return_pct = (port_value.iloc[-1] / port_value.iloc[0] - 1) if len(port_value) > 1 else 0.0
ann_return = metrics.annualized_return(port_returns)
ann_vol = metrics.annualized_volatility(port_returns)
sharpe = metrics.sharpe_ratio(port_returns)
mdd = metrics.max_drawdown(port_value)
port_beta = metrics.beta(port_returns, benchmark_returns) if not benchmark_returns.empty else float("nan")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["Portfolio Overview", "Performance Analysis", "Risk Analysis"])

with tab1:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    render_metric(c1, "Total Value", f"${total_value:,.0f}")
    render_metric(c2, "Total Return", f"{total_return_pct:+.1%}", sentiment_of(total_return_pct))
    render_metric(
        c3, "Annualized Return",
        f"{ann_return:+.1%}" if pd.notna(ann_return) else "N/A", sentiment_of(ann_return),
    )
    render_metric(
        c4, "Sharpe Ratio",
        f"{sharpe:.2f}" if pd.notna(sharpe) else "N/A", sentiment_of(sharpe),
    )
    render_metric(
        c5, "Max Drawdown",
        f"{mdd:.1%}" if pd.notna(mdd) else "N/A", sentiment_of(mdd),
    )
    render_metric(c6, "Portfolio Beta", f"{port_beta:.2f}" if pd.notna(port_beta) else "N/A")

    st.plotly_chart(
        charts.portfolio_vs_benchmark_chart(port_value, benchmark), use_container_width=True
    )

    col_pie, col_table = st.columns([1, 1.4])
    with col_pie:
        st.plotly_chart(charts.allocation_pie_chart(weights), use_container_width=True)
    with col_table:
        st.markdown("**Holdings**")
        latest = portfolio_data.current_prices(prices)
        prev = portfolio_data.previous_close(prices)
        first = prices.iloc[0]
        holdings_rows = []
        for t in valid_tickers:
            market_value = latest[t] * valid_shares[t]
            daily_change = (latest[t] / prev[t] - 1) if prev[t] else float("nan")
            total_ret = (latest[t] / first[t] - 1) if first[t] else float("nan")
            holdings_rows.append(
                {
                    "Ticker": t,
                    "Shares": valid_shares[t],
                    "Current Price": latest[t],
                    "Market Value": market_value,
                    "Daily Change %": daily_change,
                    "Total Return %": total_ret,
                }
            )
        holdings_df = pd.DataFrame(holdings_rows).set_index("Ticker")

        def _color_signed(v: float) -> str:
            if pd.isna(v):
                return ""
            return f"color: {POSITIVE}" if v >= 0 else f"color: {NEGATIVE}"

        st.dataframe(
            holdings_df.style.format(
                {
                    "Current Price": "${:,.2f}",
                    "Market Value": "${:,.2f}",
                    "Daily Change %": "{:+.2%}",
                    "Total Return %": "{:+.2%}",
                }
            ).map(_color_signed, subset=["Daily Change %", "Total Return %"]),
            use_container_width=True,
        )

with tab2:
    st.plotly_chart(
        charts.normalized_performance_chart(prices, benchmark), use_container_width=True
    )
    st.plotly_chart(
        charts.cumulative_returns_chart(prices, benchmark), use_container_width=True
    )
    st.plotly_chart(
        charts.rolling_volatility_chart(metrics.rolling_volatility(prices)), use_container_width=True
    )

    st.markdown("**Per-Stock Metrics**")

    def _color_signed(v: float) -> str:
        if pd.isna(v):
            return ""
        return f"color: {POSITIVE}" if v >= 0 else f"color: {NEGATIVE}"

    st.dataframe(
        per_stock_metrics.style.format(
            {
                "Annualized Return": "{:+.2%}",
                "Volatility": "{:.2%}",
                "Sharpe Ratio": "{:.2f}",
                "Beta": "{:.2f}",
                "Max Drawdown": "{:.2%}",
            }
        ).map(_color_signed, subset=["Annualized Return", "Sharpe Ratio", "Max Drawdown"]),
        use_container_width=True,
    )

with tab3:
    st.plotly_chart(charts.correlation_heatmap(metrics.correlation_matrix(prices)), use_container_width=True)
    st.plotly_chart(charts.returns_distribution_grid(returns_df), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(
            charts.portfolio_vs_benchmark_scatter(port_returns, benchmark_returns),
            use_container_width=True,
        )
    with col_b:
        st.plotly_chart(
            charts.risk_return_scatter(per_stock_metrics, weights), use_container_width=True
        )
