"""Stock Portfolio Analysis: track stocks against a buy price and flag keep / review /
sell-candidate using rules the user sets."""

import pandas as pd
import streamlit as st

from analysis import charts, metrics
from data import market, persistence

NAVY = "#00274C"
MAIZE = "#FFCB05"
POSITIVE = "#3DDC84"
NEGATIVE = "#FF6B6B"
WARNING = "#FFCB05"
NEUTRAL = "#FFFFFF"
MUTED = "#9AA4B2"

STATUS_COLORS = {
    metrics.STATUS_KEEP: POSITIVE,
    metrics.STATUS_REVIEW: WARNING,
    metrics.STATUS_SELL: NEGATIVE,
}
CHECK_STYLE = {
    "triggered": (NEGATIVE, "Triggered"),
    "ok": (POSITIVE, "OK"),
    "n/a": (MUTED, "No data"),
    "off": (MUTED, "Off"),
}

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


def render_metric(col, label: str, value_str: str, color: str = NEUTRAL) -> None:
    col.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def color_signed(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"color: {POSITIVE}" if value >= 0 else f"color: {NEGATIVE}"


def color_status(value: str) -> str:
    return f"color: {STATUS_COLORS.get(value, NEUTRAL)}; font-weight: 700"


# ---------------------------------------------------------------------------
# State: load the saved watchlist and rules once per browser session
# ---------------------------------------------------------------------------

if "watchlist" not in st.session_state:
    saved_watchlist, watchlist_ok = persistence.load_watchlist()
    saved_rules, rules_ok = persistence.load_rules()
    rules = {**metrics.DEFAULT_RULES, **(saved_rules or {})}

    st.session_state.persistence_ok = watchlist_ok and rules_ok
    st.session_state.watchlist = saved_watchlist
    st.session_state._saved_watchlist = dict(saved_watchlist)
    st.session_state.rules = {n: type(d)(rules[n]) for n, d in metrics.DEFAULT_RULES.items()}
    st.session_state._saved_rules = dict(st.session_state.rules)


def current_rules() -> dict:
    return {name: st.session_state[f"rule_{name}"] for name in metrics.DEFAULT_RULES}


def sync_watchlist() -> None:
    """Save the watchlist to Supabase if it changed since the last save."""
    if (
        st.session_state.persistence_ok
        and st.session_state.watchlist != st.session_state._saved_watchlist
    ):
        if persistence.save_watchlist(st.session_state.watchlist):
            st.session_state._saved_watchlist = dict(st.session_state.watchlist)


def sync_rules() -> None:
    """Remember the rules from the widgets, and save them if they changed."""
    st.session_state.rules = current_rules()
    if (
        st.session_state.persistence_ok
        and st.session_state.rules != st.session_state._saved_rules
    ):
        if persistence.save_rules(st.session_state.rules):
            st.session_state._saved_rules = dict(st.session_state.rules)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("Settings")
if st.session_state.persistence_ok:
    st.sidebar.caption("Synced to Supabase")
else:
    st.sidebar.caption("Offline: changes won't be saved (see README to set up Supabase)")

with st.sidebar.form("add_form", clear_on_submit=True):
    st.markdown("**Add stocks**")
    new_tickers = st.text_input("Ticker(s), comma separated", placeholder="e.g. NFLX, DIS")
    new_buy_price = st.number_input(
        "Buy price in $ (0 = use today's price)", min_value=0.0, value=0.0, step=0.01, format="%.2f"
    )
    add_clicked = st.form_submit_button("Add")

if add_clicked and new_tickers.strip():
    names = list(dict.fromkeys(t.strip().upper() for t in new_tickers.split(",") if t.strip()))
    found, not_found = market.fetch_price_history(tuple(names), "5d")
    for name in names:
        if name in found.columns:
            price = new_buy_price or round(float(found[name].dropna().iloc[-1]), 2)
            st.session_state.watchlist[name] = price
            st.session_state[f"buy_{name}"] = price
    if not_found:
        st.sidebar.warning(f"Couldn't find: {', '.join(not_found)}")

st.sidebar.markdown("**Your stocks and buy prices**")
if not st.session_state.watchlist:
    st.sidebar.caption("No stocks yet. Add one above.")
for ticker in list(st.session_state.watchlist):
    c_name, c_price, c_remove = st.sidebar.columns([2, 3, 3])
    c_name.markdown(f"`{ticker}`")
    if f"buy_{ticker}" not in st.session_state:
        st.session_state[f"buy_{ticker}"] = float(st.session_state.watchlist[ticker])
    st.session_state.watchlist[ticker] = c_price.number_input(
        f"Buy price {ticker}", min_value=0.0, step=0.01, format="%.2f",
        label_visibility="collapsed", key=f"buy_{ticker}",
    )
    if c_remove.button("Remove", key=f"remove_{ticker}", width="stretch"):
        del st.session_state.watchlist[ticker]
        st.session_state.pop(f"buy_{ticker}", None)
        sync_watchlist()
        st.rerun()
sync_watchlist()

st.sidebar.divider()
period_label = st.sidebar.selectbox(
    "Time window", market.PERIOD_OPTIONS, index=market.PERIOD_OPTIONS.index("6M")
)

# Streamlit discards a widget's state in any run that doesn't draw it (for example when
# Remove calls st.rerun() before this panel). Re-seed from the remembered rules so a
# dropped widget never falls back to its blank default and gets saved over the real value.
for name in metrics.DEFAULT_RULES:
    if f"rule_{name}" not in st.session_state:
        st.session_state[f"rule_{name}"] = st.session_state.rules[name]

with st.sidebar.expander("Keep / sell rules"):
    st.caption(
        "Each rule that triggers adds one flag. One flag marks a stock Review; "
        "enough flags mark it a Sell candidate."
    )

    def rule_input(label: str, on: str, value: str, low: int, high: int) -> None:
        st.checkbox(label, key=f"rule_{on}")
        st.number_input(
            label, min_value=low, max_value=high, step=1, key=f"rule_{value}",
            label_visibility="collapsed", disabled=not st.session_state[f"rule_{on}"],
        )

    rule_input("Loss from buy price beyond (%)", "loss_on", "loss_pct", 1, 99)
    rule_input("Gain from buy price beyond (%)", "gain_on", "gain_pct", 1, 1000)
    rule_input("Price below moving average of (days)", "ma_on", "ma_days", 20, 250)
    rule_input("Drop from window high beyond (%)", "dd_on", "dd_pct", 1, 99)
    rule_input("Lag behind S&P 500 by more than (pts)", "rel_on", "rel_pct", 1, 100)
    st.number_input(
        "Sell candidate when this many rules trigger", min_value=1, max_value=5, step=1,
        key="rule_sell_at",
    )
sync_rules()

if st.sidebar.button("Refresh data", width="stretch"):
    st.cache_data.clear()
    st.rerun()


# ---------------------------------------------------------------------------
# Main: fetch data and evaluate every stock
# ---------------------------------------------------------------------------

st.title("Stock Portfolio Analysis")
st.caption(
    "Rule-based flags from the thresholds you set. They highlight stocks worth a second "
    "look and are not financial advice."
)

watchlist = dict(st.session_state.watchlist)
if not watchlist:
    st.info("Add a stock in the sidebar to start tracking it.")
    st.stop()

rules = current_rules()
fetch_period = market.history_period(period_label)

with st.spinner("Fetching market data..."):
    prices, failed = market.fetch_price_history(tuple(watchlist), fetch_period)
    benchmark = market.fetch_benchmark(fetch_period)

if failed:
    st.warning(f"No price data for: {', '.join(failed)}. They are left out below.")
if prices.empty:
    st.error("No price data could be retrieved. Check the tickers and try again.")
    st.stop()

as_of = prices.index[-1]
start = as_of - pd.DateOffset(months=market.PERIOD_MONTHS[period_label])
st.caption(f"Prices as of the {as_of:%B %d, %Y} close. Cached for up to an hour.")

ma_col = f"vs {rules['ma_days']}d Avg"
return_col = f"{period_label} Return"
rows, checks_by_ticker = [], {}
for ticker in prices.columns:
    snap = metrics.stock_snapshot(prices[ticker], benchmark, watchlist[ticker], start, rules["ma_days"])
    checks = metrics.evaluate_rules(snap, rules, period_label)
    status = metrics.signal(checks, rules["sell_at"])
    checks_by_ticker[ticker] = (status, checks)
    reasons = "; ".join(c["detail"] for c in checks if c["state"] == "triggered")
    rows.append(
        {
            "Ticker": ticker,
            "Signal": status,
            "Buy Price": snap["buy_price"],
            "Price": snap["price"],
            "vs Buy": snap["vs_buy"],
            "Today": snap["today"],
            return_col: snap["period_return"],
            "vs S&P 500 (pts)": snap["vs_market"] * 100,
            "From High": snap["from_high"],
            ma_col: snap["vs_ma"],
            "Volatility": snap["volatility"],
            "Why": reasons or "No rules triggered",
        }
    )

table = pd.DataFrame(rows)
table["_rank"] = table["Signal"].map(metrics.STATUS_RANK)
table = table.sort_values(["_rank", "vs Buy"]).drop(columns="_rank").set_index("Ticker")

counts = table["Signal"].value_counts()
c1, c2, c3, c4 = st.columns(4)
render_metric(c1, "Stocks tracked", str(len(table)))
render_metric(c2, "Keep", str(counts.get(metrics.STATUS_KEEP, 0)), POSITIVE)
render_metric(c3, "Review", str(counts.get(metrics.STATUS_REVIEW, 0)), WARNING)
render_metric(c4, "Sell candidates", str(counts.get(metrics.STATUS_SELL, 0)), NEGATIVE)

st.subheader("Your stocks")
signed_columns = ["vs Buy", "Today", return_col, "vs S&P 500 (pts)", ma_col]
st.dataframe(
    table.style.format(
        {
            "Buy Price": "${:,.2f}", "Price": "${:,.2f}", "vs Buy": "{:+.1%}", "Today": "{:+.2%}",
            return_col: "{:+.1%}", "vs S&P 500 (pts)": "{:+.1f}", "From High": "{:.1%}",
            ma_col: "{:+.1%}", "Volatility": "{:.1%}",
        },
        na_rep="-",
    )
    .map(color_status, subset=["Signal"])
    .map(color_signed, subset=signed_columns),
    width="stretch",
    column_config={"Why": st.column_config.TextColumn(width="large")},
)

st.subheader("Inspect a stock")
chosen = st.selectbox("Stock", list(table.index))
status, checks = checks_by_ticker[chosen]
col_chart, col_rules = st.columns([2, 1])
with col_chart:
    st.plotly_chart(
        charts.stock_price_chart(prices[chosen], start, watchlist[chosen], rules["ma_days"]),
        width="stretch",
    )
with col_rules:
    st.markdown(
        f"<h3 style='margin-top:0'>{chosen}: "
        f"<span style='color:{STATUS_COLORS[status]}'>{status}</span></h3>",
        unsafe_allow_html=True,
    )
    for check in checks:
        color, label = CHECK_STYLE[check["state"]]
        st.markdown(
            f"<div style='margin-bottom:10px'>"
            f"<span style='color:{color};font-weight:700'>{label}</span> "
            f"{check['rule']}<br><span style='color:{MUTED};font-size:0.85rem'>"
            f"{check['detail']}</span></div>",
            unsafe_allow_html=True,
        )

window_prices = prices[prices.index >= start]
window_benchmark = benchmark[benchmark.index >= start] if not benchmark.empty else benchmark
st.plotly_chart(charts.normalized_performance_chart(window_prices, window_benchmark), width="stretch")

with st.expander("How these numbers are calculated"):
    st.markdown(
        f"""
- **Prices** are daily closes, adjusted for splits but with dividends not added back, so they
  match the prices you see quoted. All returns are price returns.
- **vs Buy**: latest price / your buy price - 1. Change a buy price in the sidebar any time.
- **Today**: latest close / previous close - 1.
- **{return_col}**: latest price / price at the start of the window - 1.
- **vs S&P 500 (pts)**: the stock's window return minus the S&P 500's, in percentage points.
- **From High**: latest price / highest close inside the window - 1 (always 0 or negative).
- **{ma_col}**: latest price / its {rules['ma_days']}-day average close - 1. Negative means
  it trades below that average, a common trend-break check.
- **Volatility**: standard deviation of daily returns in the window x sqrt(252), a yearly figure.
- **Signal**: each rule that triggers adds one flag. 1 flag is Review, {rules['sell_at']} or
  more is Sell candidate. Change the rules and the count in the sidebar.
"""
    )
