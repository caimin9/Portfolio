# Options Analytics System

A comprehensive options analysis toolkit with portfolio monitoring, market scanning, and price forecasting.

## Features

### 1. **Analytics Engine** (`analytics.py`)
- **Breeden-Litzenberger Implementation**: Extracts risk-neutral probability density from option prices
- **Black-Scholes Greeks**: Delta, Gamma, Theta, Vega, Rho calculations
- **IV Surface Analysis**: Volatility smile/skew visualization
- **Distribution Statistics**: Expected price, standard deviation, skewness, kurtosis

### 2. **Portfolio Management** (`portfolio.py`)
- Track stock and option positions
- Calculate P&L with **real-time option pricing** (fetches actual bid/ask from chains)
- Aggregate portfolio Greeks
- Export/import portfolio data

### 3. **Market Scanner** (`scanner.py`)
- Scan watchlist for opportunities
- Detect unusual options activity (volume spikes)
- IV percentile ranking
- Put/Call ratio alerts
- Distribution skew changes
- **Real-time notifications** via email and Discord

### 6. **Notifications** (`notifications.py`)
- **Email alerts** via SMTP (Gmail, Outlook, etc.)
- **Discord webhooks** for instant notifications
- Configurable alert thresholds
- Cooldown to prevent spam
- Rich formatted alerts with key metrics

### 7. **Correlation & Beta Analysis** (`correlation_analysis.py`) - NEW!
- **Rolling correlations** between asset pairs
- **Rolling beta** calculation (systematic risk)
- **Correlation matrices** for portfolios
- **Diversification metrics** (diversification ratio, weighted correlations)
- **Regime change detection** (correlation breakdowns)
- **Hedge effectiveness analysis**
- Portfolio risk decomposition

### 4. **Forecasting** (`forecasting.py`)
- Distribution-based price forecasts
- Monte Carlo simulations
- Scenario analysis (probability of reaching targets)
- Multi-ticker comparison

### 5. **Dashboard** (`dashboard.py`)
- Streamlit-based web interface
- Real-time analysis
- Interactive charts
- Portfolio monitoring

## Installation

**From project root:**
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install all dependencies
pip install -r requirements.txt
```

This installs all 68 required packages including:
- yfinance, pandas, numpy, scipy (data analysis)
- matplotlib, plotly, seaborn (visualization)
- streamlit (dashboards)
- fastapi, uvicorn (API server)
- And all their dependencies

## Usage

### Launch Dashboard
```bash
streamlit run dashboard.py
```

### Quick Analysis
```python
from analytics import analyze_options

results = analyze_options("AAPL")
print(f"Expected Move: ±{results['summary']['expected_move_pct']:.1f}%")
```

### Scan Market with Notifications
```python
from scanner import scan_market

# Scan and send alerts for unusual activity
results = scan_market(["SPY", "QQQ", "AAPL"], send_notifications=True)
```

### Generate Forecast
```python
from forecasting import quick_forecast

forecast = quick_forecast("TSLA")
print(forecast.summary())
```

### Analyze Correlations & Beta
```python
from correlation_analysis import quick_correlation, quick_beta

# Rolling correlation between two assets
corr = quick_correlation("AAPL", "MSFT", window=60, plot=True)

# Rolling beta (systematic risk)
beta = quick_beta("TSLA", "SPY", window=60, plot=True)

# Portfolio correlation matrix
from correlation_analysis import analyze_portfolio_correlations
corr_matrix = analyze_portfolio_correlations(["SPY", "QQQ", "TLT", "GLD"])
```

### Configure Notifications
See [SETUP_NOTIFICATIONS.md](SETUP_NOTIFICATIONS.md) for detailed setup instructions for email and Discord alerts.

## File Structure

```
options/
├── api.py                        # FastAPI backend server
├── analytics.py                  # Core analysis engine (Breeden-Litzenberger)
├── central_portfolio.py          # Central portfolio management
├── portfolio.py                  # Portfolio class with real-time pricing
├── scanner.py                    # Market scanner with notification support
├── forecasting.py                # Price forecasting (Monte Carlo, distributions)
├── notifications.py              # Email & Discord alert system
├── correlation_analysis.py       # Rolling correlations & beta analysis
├── visualization.py              # Plot generation
├── dashboard.py                  # Streamlit dashboard
├── config.py                     # Configuration
├── example_usage.py              # Usage examples
├── example_correlation_beta.py   # Correlation/beta examples
├── SETUP_NOTIFICATIONS.md        # Notification setup guide
├── README.md                     # This file
├── data/
│   ├── portfolio.json            # Saved portfolio
│   └── watchlist.json            # Watchlist tickers
├── plots/                        # Saved visualizations
└── logs/                         # Alert logs
```

## Key Concepts

### Breeden-Litzenberger Formula
The risk-neutral probability density function (PDF) can be extracted from option prices:

$$PDF(K) = e^{rT} \frac{\partial^2 C}{\partial K^2}$$

Where:
- C = Call option price
- K = Strike price
- r = Risk-free rate
- T = Time to expiration

### Expected Move
The 1-sigma expected move is calculated as:

$$Expected Move = Price \times IV_{ATM} \times \sqrt{T}$$

This represents the range where the market expects the price to be ~68% of the time.

### Unusual Activity Detection
The scanner flags:
- **Volume/OI > 2x**: Unusual trading activity
- **IV > 80th percentile**: Elevated implied volatility
- **P/C Ratio > 1.5**: Heavy put buying (bearish)
- **Skewness < -0.5**: Bearish distribution skew

## Alerts

The system generates alerts for:
1. Unusual volume spikes
2. IV percentile extremes
3. Put/Call ratio imbalances
4. Distribution skew changes
5. Large expected move changes

## Dashboard Features

- **Single Ticker Analysis**: Deep-dive into one stock's options
- **Portfolio Monitor**: Track your positions and Greeks
- **Market Scanner**: Scan watchlist for opportunities
- **Forecasting**: Price predictions and scenarios
- **Correlations & Beta**: Rolling correlations, beta analysis, portfolio diversification
- **Settings**: Configure alerts and watchlist
