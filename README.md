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

## Tech Stack

- [Streamlit](https://streamlit.io/) — web dashboard framework
- [yfinance](https://github.com/ranaroussi/yfinance) — live/historical market data
- [pandas](https://pandas.pydata.org/) — data manipulation and financial calculations
- [Plotly](https://plotly.com/python/) — interactive charts
- [NumPy](https://numpy.org/) — numerical calculations

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

## Screenshots

*(placeholder — add screenshots of the three dashboard pages here)*

## Future Improvements

- Persist custom portfolios across sessions (e.g. via Supabase) instead of resetting on reload
- Support for multiple saved portfolios / watchlists
- Sector-level allocation breakdown (currently allocation is by individual holding only)
- Configurable risk-free rate and benchmark ticker
- Export holdings/metrics to CSV or PDF
- Deploy a hosted version (e.g. Streamlit Community Cloud or Vercel)
