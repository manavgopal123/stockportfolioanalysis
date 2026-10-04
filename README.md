# Stock Portfolio Analysis

A personal stock tracker built with Streamlit. Add stocks with a buy price, and for each one see how it is doing over a time window you choose, using price-based metrics and rules you set. Each stock is flagged **Keep**, **Review**, or **Sell candidate** so you can decide what to hold.

The flags are rule-based prompts to take a second look at a stock. They are not financial advice, and price history can't predict the future.

## Features

- **Watchlist with editable buy prices** — add any ticker, leave the buy price at 0 to use today's price, and change it any time in the sidebar. Tickers Yahoo doesn't recognize are rejected when you add them.
- **Time windows** — 1M, 3M, 6M, 1Y, 2Y, 5Y
- **One table for every stock** — gain/loss vs your buy price, today's move, return over the window, performance vs the S&P 500, drop from the window high, position vs a moving average, volatility, and the reasons behind each signal
- **Adjustable rules** — loss from buy price, gain from buy price, price below a moving average, drop from window high, lagging the S&P 500. Each can be switched off and has its own threshold, and you choose how many triggered rules make a Sell candidate.
- **Inspect a stock** — price chart with 50-day and long moving averages and your buy price line, plus a rule-by-rule checklist showing what triggered and why
- **Everything saved** — your stocks, buy prices and rules are stored in Supabase, so they survive a refresh and are the same on every device

## How the numbers are calculated

- Prices are daily closes, adjusted for splits but with dividends not added back, so they match the quotes you see. All returns are price returns.
- **vs Buy** = latest price / buy price - 1
- **Window return** = latest price / price at the start of the window - 1
- **vs S&P 500** = the stock's window return minus the S&P 500's, in percentage points
- **From High** = latest price / highest close in the window - 1
- **vs N-day average** = latest price / its N-day average close - 1
- **Volatility** = standard deviation of daily returns in the window x sqrt(252)
- **Signal** = number of triggered rules: 0 is Keep, 1 or more is Review, and at or above the "sell candidate" count is Sell candidate

## Tech Stack

- [Streamlit](https://streamlit.io/) — web app
- [yfinance](https://github.com/ranaroussi/yfinance) — market data
- [pandas](https://pandas.pydata.org/) and [NumPy](https://numpy.org/) — calculations
- [Plotly](https://plotly.com/python/) — charts
- [Supabase](https://supabase.com/) — saves the watchlist and rules

## Installing and Running Locally

```bash
git clone https://github.com/manavgopal123/stockportfolioanalysis.git
cd stockportfolioanalysis

python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### Setting up Supabase

1. Create a free project at [supabase.com](https://supabase.com)
2. In the SQL Editor, run:
   ```sql
   create table if not exists watchlist (
     ticker text primary key,
     buy_price numeric not null default 0
   );

   create table if not exists app_settings (
     key text primary key,
     value jsonb not null
   );

   alter table watchlist enable row level security;
   alter table app_settings enable row level security;

   create policy "Allow app access to watchlist" on watchlist
     for all to anon using (true) with check (true);

   create policy "Allow app access to app_settings" on app_settings
     for all to anon using (true) with check (true);
   ```
3. From **Project Settings → API**, copy the **Project URL** and **anon public key**
4. Create `.streamlit/secrets.toml` (already gitignored) with:
   ```toml
   SUPABASE_URL = "your-project-url"
   SUPABASE_KEY = "your-anon-public-key"
   ```

Without this, the app still runs, but the sidebar shows "Offline" and nothing is saved between sessions.

## Deployment

Deployed on [Streamlit Community Cloud](https://share.streamlit.io) from this repo, with `app.py` as the entry point and the Supabase credentials set in the app's Secrets panel (never committed to git). Access is restricted to specific email addresses in the app's sharing settings. The app has no login of its own, so every visitor would otherwise share the same watchlist.

## Future Improvements

- Per-stock rule overrides (for example a tighter loss limit for a volatile stock)
- Company fundamentals (P/E, earnings growth) alongside the price rules
- Alerts when a stock newly becomes a Sell candidate
- Multi-user support: real auth (for example Supabase Auth) and a `user_id` column scoping each person's rows
