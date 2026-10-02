# Stock Portfolio Analysis

An interactive personal stock portfolio analytics dashboard built with Streamlit. It pulls live and historical price data from Yahoo Finance and turns it into the kind of return, risk, and correlation analysis you'd normally need a brokerage terminal for — running entirely on your own machine, against your own holdings.

## Motivation

Most "portfolio trackers" just show you what you own and what it's worth today. This project goes a step further: it computes the metrics that actually describe how a portfolio is performing — annualized return, volatility, Sharpe ratio, beta, drawdown, correlation — and visualizes them so patterns (concentration risk, correlated holdings, drawdown periods) are easy to spot at a glance.

## Features

- **Configurable portfolio** — add or remove any ticker and set share counts directly from the sidebar
- **Selectable date ranges** — 1M, 3M, 6M, 1Y, 2Y, 5Y
- **Portfolio Overview** — total value, total/annualized return, Sharpe ratio, max drawdown, and beta as headline metric cards, plus a portfolio-vs-S&P-500 chart, allocation pie chart, and a full holdings table
- **Performance Analysis** — normalized (base-100) performance across all holdings, cumulative returns, rolling 30-day volatility, and a per-stock metrics table
- **Risk Analysis** — correlation heatmap, daily-return distribution histograms, portfolio-vs-benchmark scatter, and a risk/return bubble chart sized by portfolio weight
- **Graceful error handling** — invalid or delisted tickers are reported and excluded rather than breaking the app
- **Cached data fetching** — market data is cached for an hour so navigating the dashboard doesn't re-hit Yahoo Finance on every interaction
- **Persistent holdings** — your portfolio is saved to Supabase as you edit it, so it survives page refreshes instead of resetting to the default

## Tech Stack

- [Streamlit](https://streamlit.io/) — web dashboard framework
- [yfinance](https://github.com/ranaroussi/yfinance) — live/historical market data
- [pandas](https://pandas.pydata.org/) — data manipulation and financial calculations
- [Plotly](https://plotly.com/python/) — interactive charts
- [NumPy](https://numpy.org/) — numerical calculations
- [Supabase](https://supabase.com/) — persists your portfolio holdings across sessions

## Installing and Running Locally

```bash
# clone the repo
git clone https://github.com/manavgopal123/stockportfolioanalysis.git
cd stockportfolioanalysis

# create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# install dependencies
pip install -r requirements.txt

# run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. The sidebar comes pre-loaded with a default 8-stock portfolio (AAPL, MSFT, GOOGL, AMZN, TSLA, JPM, V, NVDA) — customize it freely from there.

### Setting up persistence (Supabase)

Holdings are saved to Supabase so they survive a page refresh. To enable it:

1. Create a free project at [supabase.com](https://supabase.com)
2. In the SQL Editor, create the table (with Row Level Security enabled):
   ```sql
   create table portfolio_holdings (
     ticker text primary key,
     shares numeric not null
   );

   alter table portfolio_holdings enable row level security;

   create policy "Allow app access to portfolio_holdings"
   on portfolio_holdings
   for all
   to anon
   using (true)
   with check (true);
   ```
3. From **Project Settings → API**, copy the **Project URL** and **anon public key**
4. Create `.streamlit/secrets.toml` (already gitignored) with:
   ```toml
   SUPABASE_URL = "your-project-url"
   SUPABASE_KEY = "your-anon-public-key"
   ```

Without this file, the app still runs fine — it just falls back to the default portfolio every session instead of persisting changes (the sidebar will show "Offline" instead of "Synced to Supabase").

## Screenshots

*(placeholder — add screenshots of the three dashboard pages here)*

## Future Improvements

- Support for multiple saved portfolios / watchlists
- Sector-level allocation breakdown (currently allocation is by individual holding only)
- Configurable risk-free rate and benchmark ticker
- Export holdings/metrics to CSV or PDF
- Deploy a hosted version on Streamlit Community Cloud (Vercel isn't compatible — Streamlit needs a persistent process, which doesn't fit Vercel's serverless model), making the app installable to a phone's home screen
