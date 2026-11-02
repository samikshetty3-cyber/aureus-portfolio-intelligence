# Aureus — Portfolio Intelligence

A navy-and-gold wealth-management portfolio analytics prototype, built with Python and Streamlit. No API key, payment, or login required for the demo.

## Features
- Upload a holdings CSV and calculate market values, allocation, concentration, and HHI.
- Interactive portfolio charts and holdings tables.
- Optional uploaded historical price data for volatility, growth and drawdowns.
- Hypothetical uniform portfolio stress test.
- Downloadable advisor PDF report and CSV export.
- Fictional sample portfolio included; no live market data is claimed.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for free
1. Create a new public GitHub repository and upload `app.py`, `requirements.txt`, `.streamlit/config.toml`, and `data/`.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Select the repository, branch, and `app.py` as the main file. Click Deploy.
4. Test CSV upload, risk page, and PDF download using fictional sample data.

Free hosting availability and usage limits may change. Public app code and sample data are visible to others.

## Input format
Holdings CSV: `ticker,shares,price` required; `name,asset_class,sector` optional. Prices must be positive; shares must be positive. Each ticker must be unique. Example in `data/sample_holdings.csv`.

Historical prices CSV: `date` and one column per ticker. All prices positive, dates unique, at least three observations. Example in `data/sample_prices.csv`. Choose the correct frequency in the app. The demo sample prices are entirely fictional.

## Financial methodology
- Market value = shares × supplied price.
- Weight = holding market value / total market value.
- HHI = sum(weights²); effective holdings = 1 / HHI.
- Historical periodic portfolio price return = sum(fixed current weights × periodic ticker price returns). Assumes periodic rebalancing.
- Annualized volatility = sample standard deviation of periodic portfolio returns × sqrt(periods/year).
- Maximum drawdown = min(cumulative growth / running maximum growth − 1).
- Stress scenario applies a uniform hypothetical shock to all positions.

## Important limitations
Not an investment advisory service. Do not upload real-client personal data. No live prices, tax calculations, ETF look-through, or automated suitability recommendations. Historical results exclude dividends, transaction costs, and taxes. This demo has not been independently audited or validated for production advisory use.
