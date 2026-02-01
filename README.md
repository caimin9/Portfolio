# Portfolio Terminal

A comprehensive portfolio management and options analytics platform with real-time tracking, risk analysis, and market insights.

## Features

### Backend (FastAPI)
- **Portfolio Management**: Track stock positions with real-time P&L
- **Options Analytics**: Breeden-Litzenberger implied distribution analysis
- **Risk Metrics**: Portfolio beta, volatility, VaR, correlation matrices
- **Market Data**: Real-time stock prices and options chains via yfinance
- **RESTful API**: Full CRUD operations for portfolio management

### Frontend (Next.js)
- **Terminal Dashboard**: Bloomberg-style interface with real-time updates
- **Portfolio Overview**: Visual breakdown of positions and performance
- **Stock Detail Views**: Price charts, beta analysis, correlation data
- **Distribution Analytics**: Implied probability distributions from options
- **Responsive Design**: Modern UI with Tailwind CSS

### Analytics Tools (Streamlit)
- **Multiple Dashboard Options**: Terminal view, modern UI, and multi-page layouts
- **Correlation & Beta Analysis**: Rolling correlations and systematic risk metrics
- **Market Scanner**: Detect unusual options activity with notifications
- **Forecasting**: Distribution-based price predictions and Monte Carlo simulations

## Installation

### Prerequisites
- **Python 3.12+** (with pip)
- **Node.js 18+** (with npm)
- **Git** (for cloning and version control)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/caimin9/Portfolio.git
   cd Portfolio
   ```

2. **Set up Python virtual environment**
   ```bash
   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   This installs all 68 required packages including:
   - FastAPI & Uvicorn (web server)
   - yfinance (market data)
   - pandas, numpy, scipy (data analysis)
   - matplotlib, plotly, seaborn (visualization)
   - streamlit (dashboards)

4. **Install Node.js dependencies** (for frontend)
   ```bash
   cd terminal-app
   npm install
   cd ..
   ```

## Quick Start

Run the launcher script which starts both backend and frontend:

**Windows:**
```bash
START-TERMINAL.bat
```

**macOS/Linux:**
```bash
./START-TERMINAL.sh  # Coming soon
```

This single script:
1. Cleans up any old processes
2. Starts the FastAPI backend (port 8000)
3. Starts the Next.js frontend (port 3000)
4. Opens your browser to http://localhost:3000

**Access points:**
- **Frontend Terminal**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

### Portfolio Management

**Add a position:**
```bash
curl -X POST http://localhost:8000/api/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "quantity": 10, "entry_price": 150.00}'
```

**View portfolio:**
```bash
curl http://localhost:8000/api/portfolio/summary
```

### Streamlit Dashboard

Launch the analytics dashboard:
```bash
streamlit run options/dashboard.py
```

### Python API

```python
from options.analytics import OptionsAnalyzer
from options.correlation_analysis import CorrelationAnalyzer

# Analyze options distribution
analyzer = OptionsAnalyzer()
results = analyzer.analyze_ticker("AAPL", expiration_index=0)
print(f"Expected Move: ±{results['summary']['expected_move_pct']:.1f}%")

# Calculate rolling beta
corr = CorrelationAnalyzer()
beta_result = corr.rolling_beta("TSLA", "SPY", window=60)
print(f"Current Beta: {beta_result.current_beta:.2f}")
```

## Project Structure

```
Portfolio/
├── options/                      # Backend & Analytics
│   ├── api.py                   # FastAPI server
│   ├── central_portfolio.py     # Portfolio management
│   ├── analytics.py             # Options analytics (Breeden-Litzenberger)
│   ├── correlation_analysis.py  # Beta & correlation tools
│   ├── scanner.py               # Market scanner
│   ├── forecasting.py           # Price predictions
│   ├── dashboard.py             # Streamlit dashboard
│   ├── notifications.py         # Email/Discord alerts
│   └── data/                    # Portfolio & watchlist data
├── terminal-app/                # Next.js Frontend
│   ├── app/                     # Next.js app directory
│   ├── components/              # React components
│   └── package.json
├── requirements.txt             # Python dependencies (68 packages)
├── README.md                    # This file
├── START-TERMINAL.bat          # Windows launcher
└── .gitignore
```

## Documentation

- [options/README.md](options/README.md) - Analytics and API documentation
- [options/CORRELATION_BETA_GUIDE.md](options/CORRELATION_BETA_GUIDE.md) - Risk analysis guide
- [options/SETUP_NOTIFICATIONS.md](options/SETUP_NOTIFICATIONS.md) - Email/Discord alerts

## API Endpoints

### Portfolio Management
- `GET /api/portfolio/summary` - Portfolio metrics
- `GET /api/portfolio/positions` - All positions
- `GET /api/portfolio/analytics` - Risk analytics (beta, VaR, correlations)
- `POST /api/portfolio/add` - Add position
- `DELETE /api/portfolio/remove/{ticker}` - Remove position

### Stock Data
- `GET /api/stock/{ticker}` - Detailed stock data with charts and analytics
- `GET /api/debug/beta/{ticker}` - Beta calculation debug info

See http://localhost:8000/docs for interactive API documentation.

## Key Features

### Breeden-Litzenberger Distribution
Extracts risk-neutral probability density from options prices to visualize market expectations.

### Portfolio Risk Metrics
- **Beta**: Systematic risk relative to SPY
- **Volatility**: Portfolio standard deviation
- **VaR (95%)**: Value at Risk
- **Correlation Matrix**: Asset interdependencies
- **Greeks**: Delta, Gamma, Theta, Vega aggregation

### Market Scanner
Detect unusual activity:
- Volume spikes (Volume/OI > 2x)
- IV percentile extremes (>80th percentile)
- Put/Call ratio imbalances (>1.5)
- Distribution skew changes

## Technologies

**Backend:**
- FastAPI (async web framework)
- yfinance (Yahoo Finance API)
- pandas, numpy, scipy (data science)
- matplotlib, plotly, seaborn (visualization)

**Frontend:**
- Next.js 15 (React framework)
- TypeScript (type safety)
- Tailwind CSS (styling)
- Recharts (charting)

**Dashboards:**
- Streamlit (interactive web apps)


## Repository

GitHub: https://github.com/caimin9/Portfolio


---

Built with FastAPI, Next.js, and Streamlit
