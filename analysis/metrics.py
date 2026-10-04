"""Per-stock metrics and the keep / review / sell-candidate rules."""

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

STATUS_KEEP = "Keep"
STATUS_REVIEW = "Review"
STATUS_SELL = "Sell candidate"
STATUS_RANK = {STATUS_SELL: 0, STATUS_REVIEW: 1, STATUS_KEEP: 2}

DEFAULT_RULES = {
    "loss_on": True, "loss_pct": 15,
    "gain_on": True, "gain_pct": 40,
    "ma_on": True, "ma_days": 200,
    "dd_on": True, "dd_pct": 20,
    "rel_on": True, "rel_pct": 10,
    "sell_at": 2,
}


def _period_return(series: pd.Series, start: pd.Timestamp) -> float:
    series = series.dropna()
    window = series[series.index >= start]
    if len(window) < 2:
        return np.nan
    return window.iloc[-1] / window.iloc[0] - 1


def stock_snapshot(
    close: pd.Series, benchmark: pd.Series, buy_price: float, start: pd.Timestamp, ma_days: int
) -> dict:
    """Every number shown for one stock. `start` is the beginning of the selected window."""
    close = close.dropna()
    window = close[close.index >= start]
    latest = close.iloc[-1]
    previous = close.iloc[-2] if len(close) > 1 else np.nan
    buy = buy_price if buy_price and buy_price > 0 else np.nan
    ma = close.rolling(ma_days).mean().iloc[-1] if len(close) >= ma_days else np.nan
    daily = window.pct_change().dropna()

    period_return = _period_return(close, start)
    market_return = _period_return(benchmark, start) if not benchmark.empty else np.nan

    return {
        "price": latest,
        "today": latest / previous - 1 if pd.notna(previous) else np.nan,
        "buy_price": buy,
        # Compared at cent precision, the same as the buy price and the displayed price.
        "vs_buy": round(latest, 2) / buy - 1 if pd.notna(buy) else np.nan,
        "period_return": period_return,
        "vs_market": period_return - market_return,
        "from_high": latest / window.max() - 1 if len(window) else np.nan,
        "ma": ma,
        "vs_ma": latest / ma - 1 if pd.notna(ma) else np.nan,
        "volatility": daily.std() * np.sqrt(TRADING_DAYS_PER_YEAR) if len(daily) > 1 else np.nan,
    }


def evaluate_rules(snap: dict, rules: dict, window_label: str) -> list[dict]:
    """Run each rule against a snapshot.

    Each check has a state of triggered, ok, n/a (data missing) or off.
    """
    checks = []

    def add(rule, enabled, value, triggered, detail, missing="Not enough data"):
        if not enabled:
            checks.append({"rule": rule, "state": "off", "detail": "Rule is off"})
        elif pd.isna(value):
            checks.append({"rule": rule, "state": "n/a", "detail": missing})
        else:
            state = "triggered" if triggered else "ok"
            checks.append({"rule": rule, "state": state, "detail": detail})

    vs_buy, vs_ma = snap["vs_buy"], snap["vs_ma"]
    from_high, vs_market = snap["from_high"], snap["vs_market"]

    add(
        f"Down more than {rules['loss_pct']}% from buy price", rules["loss_on"], vs_buy,
        vs_buy <= -rules["loss_pct"] / 100, f"{vs_buy:+.1%} vs buy price",
        missing="Set a buy price to use this rule",
    )
    add(
        f"Up more than {rules['gain_pct']}% from buy price", rules["gain_on"], vs_buy,
        vs_buy >= rules["gain_pct"] / 100, f"{vs_buy:+.1%} vs buy price",
        missing="Set a buy price to use this rule",
    )
    add(
        f"Price below its {rules['ma_days']}-day average", rules["ma_on"], vs_ma,
        vs_ma < 0, f"{vs_ma:+.1%} vs {rules['ma_days']}-day average",
        missing="Needs more price history",
    )
    add(
        f"Down more than {rules['dd_pct']}% from its {window_label} high", rules["dd_on"],
        from_high, from_high <= -rules["dd_pct"] / 100, f"{from_high:+.1%} from the {window_label} high",
    )
    add(
        f"Lagging the S&P 500 by more than {rules['rel_pct']} pts over {window_label}",
        rules["rel_on"], vs_market, vs_market <= -rules["rel_pct"] / 100,
        f"{vs_market * 100:+.1f} pts vs S&P 500",
    )
    return checks


def signal(checks: list[dict], sell_at: int) -> str:
    """Keep if nothing triggered, Review if something did, Sell candidate at `sell_at` or more."""
    triggered = sum(c["state"] == "triggered" for c in checks)
    if triggered >= sell_at:
        return STATUS_SELL
    if triggered >= 1:
        return STATUS_REVIEW
    return STATUS_KEEP
