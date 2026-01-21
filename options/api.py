"""
FastAPI Backend for Portfolio Terminal
Serves portfolio data to Next.js frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from central_portfolio import get_central_portfolio
from correlation_analysis import CorrelationAnalyzer

app = FastAPI(title="Portfolio Terminal API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AddPositionRequest(BaseModel):
    ticker: str
    quantity: int
    entry_price: float
    notes: Optional[str] = ""


# Global instances
portfolio = get_central_portfolio()
corr_analyzer = CorrelationAnalyzer(window=60)


@app.get("/")
def root():
    return {"message": "Portfolio Terminal API", "version": "1.0.0"}


@app.get("/api/debug/beta/{ticker}")
def debug_beta(ticker: str):
    """Debug endpoint to test beta calculation"""
    try:
        ticker = ticker.upper()
        beta_result = corr_analyzer.rolling_beta(ticker, 'SPY', period='1y', window=60)

        return {
            'success': True,
            'current_beta': float(beta_result.current_beta),
            'alpha': float(beta_result.alpha),
            'r_squared': float(beta_result.r_squared),
            'data_points': len(beta_result.rolling_beta),
            'sample_data': beta_result.rolling_beta.tail(5).to_dict()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@app.get("/api/portfolio/summary")
def get_portfolio_summary():
    """Get portfolio summary metrics"""
    try:
        summary = portfolio.get_portfolio_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/positions")
def get_positions():
    """Get all portfolio positions"""
    try:
        positions_df = portfolio.get_positions_df()

        if positions_df.empty:
            return []

        # Convert to list of dicts
        positions = positions_df.to_dict('records')
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/analytics")
def get_portfolio_analytics():
    """Get comprehensive portfolio analytics"""
    try:
        analytics = portfolio.analyze_portfolio()
        positions_df = portfolio.get_positions_df()

        if positions_df.empty:
            raise HTTPException(status_code=404, detail="No positions in portfolio")

        tickers = portfolio.get_unique_tickers()

        # Get beta history for each ticker
        beta_history = []
        for ticker in tickers:
            try:
                beta_result = corr_analyzer.rolling_beta(ticker, 'SPY', period='1y', window=60)
                beta_df = beta_result.rolling_beta.reset_index()
                beta_df.columns = ['date', 'beta']
                beta_df['date'] = beta_df['date'].astype(str)

                beta_history.append({
                    'ticker': ticker,
                    'data': beta_df.to_dict('records')
                })
            except:
                pass

        # Get correlation matrix
        try:
            prices = corr_analyzer.fetch_price_data(tickers, period='1y')
            returns = corr_analyzer.calculate_returns(prices)
            corr_matrix = returns.corr()
            correlation_matrix = corr_matrix.values.tolist()
        except:
            correlation_matrix = []

        return {
            'portfolio_beta': analytics.portfolio_beta,
            'volatility': analytics.portfolio_volatility,
            'var_95': analytics.portfolio_var_95,
            'avg_correlation': analytics.avg_correlation,
            'total_delta': analytics.total_delta,
            'total_gamma': analytics.total_gamma,
            'total_theta': analytics.total_theta,
            'total_vega': analytics.total_vega,
            'beta_history': beta_history,
            'correlation_matrix': correlation_matrix,
            'tickers': tickers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ticker}")
def get_stock_detail(ticker: str):
    """Get detailed stock data including position info, charts, and fundamentals"""
    try:
        ticker = ticker.upper()

        # Get position data
        positions_df = portfolio.get_positions_df()

        if positions_df.empty or ticker not in positions_df['ticker'].values:
            raise HTTPException(status_code=404, detail=f"Position {ticker} not found")

        position = positions_df[positions_df['ticker'] == ticker].iloc[0]

        # Calculate portfolio weight
        total_value = positions_df['market_value'].sum()
        weight = (position['market_value'] / total_value * 100) if total_value > 0 else 0

        # Fetch price history
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1y')

        if not hist.empty:
            price_history = []
            for date, row in hist.iterrows():
                price_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': float(row['Close']),
                    'volume': int(row['Volume'])
                })
        else:
            price_history = []

        # Fetch beta data
        try:
            beta_result = corr_analyzer.rolling_beta(ticker, 'SPY', period='1y', window=60)
            beta_df = beta_result.rolling_beta.reset_index()
            beta_df.columns = ['date', 'beta']
            beta_df['date'] = beta_df['date'].astype(str)
            beta_data = beta_df.to_dict('records')
        except Exception as e:
            print(f"Beta calculation failed for {ticker}: {e}")
            beta_data = []

        # Fetch correlation data with SPY
        try:
            corr_series = corr_analyzer.rolling_correlation(ticker, 'SPY', period='1y', window=60)
            corr_df = corr_series.reset_index()
            corr_df.columns = ['date', 'correlation']
            corr_df['date'] = corr_df['date'].astype(str)
            correlation_data = corr_df.to_dict('records')
        except Exception as e:
            print(f"Correlation calculation failed for {ticker}: {e}")
            correlation_data = []

        # Fetch implied distribution (Breeden-Litzenberger)
        try:
            from analytics import OptionsAnalyzer
            options_analyzer = OptionsAnalyzer()
            results = options_analyzer.analyze_ticker(ticker, 0)  # Nearest expiration

            if results['implied_distribution']:
                dist = results['implied_distribution']

                # Create distribution data points
                distribution_data = []
                for i, strike in enumerate(dist.strikes):
                    distribution_data.append({
                        'strike': float(strike),
                        'probability': float(dist.probabilities[i])
                    })

                distribution_info = {
                    'current_price': float(dist.current_price),
                    'atm_iv': float(dist.atm_iv),
                    'std_dev': float(dist.std_dev),
                    'skewness': float(dist.skewness),
                    'data': distribution_data
                }
            else:
                distribution_info = None
        except Exception as e:
            print(f"Distribution calculation failed for {ticker}: {e}")
            distribution_info = None

        # Fetch analyst data
        info = stock.info
        analyst_data = {
            'consensus': info.get('recommendationKey', 'N/A'),
            'target_price': float(info.get('targetMeanPrice', 0)),
            'num_analysts': int(info.get('numberOfAnalystOpinions', 0))
        }

        # Fetch fundamentals
        fundamentals = {
            'market_cap': float(info.get('marketCap', 0)),
            'pe_ratio': float(info.get('trailingPE', 0)),
            'dividend_yield': float(info.get('dividendYield', 0)),
            'sector': info.get('sector', 'Unknown')
        }

        return {
            'position': {
                'quantity': int(position['quantity']),
                'entry_price': float(position['entry_price']),
                'current_price': float(position['current_price']),
                'market_value': float(position['market_value']),
                'pnl': float(position['pnl']),
                'pnl_pct': float(position['pnl_pct']),
                'weight': float(weight)
            },
            'price_history': price_history[-252:],  # Last year
            'beta_data': beta_data[-60:],  # Last 60 data points
            'correlation_data': correlation_data[-60:],  # Last 60 data points
            'distribution_data': distribution_info,
            'analyst_data': analyst_data,
            'fundamentals': fundamentals
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/portfolio/add")
def add_position(request: AddPositionRequest):
    """Add a new position to the portfolio"""
    try:
        portfolio.add_stock(
            ticker=request.ticker.upper(),
            quantity=request.quantity,
            entry_price=request.entry_price,
            notes=request.notes
        )
        return {"message": f"Added {request.quantity} shares of {request.ticker}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/portfolio/remove/{ticker}")
def remove_position(ticker: str):
    """Remove a position from the portfolio"""
    try:
        ticker = ticker.upper()
        positions_df = portfolio.get_positions_df()

        if positions_df.empty or ticker not in positions_df['ticker'].values:
            raise HTTPException(status_code=404, detail=f"Position {ticker} not found")

        # Find index of position
        index = positions_df[positions_df['ticker'] == ticker].index[0]
        portfolio.remove_position(index)

        return {"message": f"Removed {ticker}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/portfolio/clear")
def clear_portfolio():
    """Clear all positions from portfolio"""
    try:
        portfolio.clear()
        return {"message": "Portfolio cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("Starting Portfolio Terminal API on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
