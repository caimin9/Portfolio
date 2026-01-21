"""
Portfolio Management Module
Track positions, calculate P&L, and aggregate Greeks.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import yfinance as yf

from config import PORTFOLIO_FILE, DATA_DIR


@dataclass
class Position:
    """Represents a single position (stock or option)"""
    ticker: str
    position_type: str  # 'stock', 'call', 'put'
    quantity: int
    entry_price: float
    entry_date: str
    strike: Optional[float] = None  # For options
    expiration: Optional[str] = None  # For options
    notes: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Position':
        return cls(**data)


class Portfolio:
    """
    Portfolio manager for tracking positions and calculating metrics.
    """
    
    def __init__(self, portfolio_file: str = PORTFOLIO_FILE):
        self.portfolio_file = portfolio_file
        self.positions: List[Position] = []
        self.load()
    
    def load(self):
        """Load portfolio from file"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.positions = [Position.from_dict(p) for p in data.get('positions', [])]
            except (json.JSONDecodeError, KeyError):
                self.positions = []
        else:
            self.positions = []
    
    def save(self):
        """Save portfolio to file"""
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        data = {
            'positions': [p.to_dict() for p in self.positions],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.portfolio_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_position(self, position: Position):
        """Add a new position"""
        self.positions.append(position)
        self.save()
    
    def add_stock(self, ticker: str, quantity: int, entry_price: float, 
                  notes: str = "") -> Position:
        """Add a stock position"""
        pos = Position(
            ticker=ticker.upper(),
            position_type='stock',
            quantity=quantity,
            entry_price=entry_price,
            entry_date=datetime.now().strftime('%Y-%m-%d'),
            notes=notes
        )
        self.add_position(pos)
        return pos
    
    def add_option(self, ticker: str, option_type: str, quantity: int,
                   entry_price: float, strike: float, expiration: str,
                   notes: str = "") -> Position:
        """Add an option position"""
        pos = Position(
            ticker=ticker.upper(),
            position_type=option_type.lower(),  # 'call' or 'put'
            quantity=quantity,
            entry_price=entry_price,
            entry_date=datetime.now().strftime('%Y-%m-%d'),
            strike=strike,
            expiration=expiration,
            notes=notes
        )
        self.add_position(pos)
        return pos
    
    def remove_position(self, index: int):
        """Remove position by index"""
        if 0 <= index < len(self.positions):
            self.positions.pop(index)
            self.save()
    
    def clear(self):
        """Clear all positions"""
        self.positions = []
        self.save()
    
    def get_unique_tickers(self) -> List[str]:
        """Get list of unique tickers in portfolio"""
        return list(set(p.ticker for p in self.positions))
    
    def get_current_prices(self) -> Dict[str, float]:
        """Fetch current prices for all tickers"""
        tickers = self.get_unique_tickers()
        prices = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='1d')
                if not hist.empty:
                    prices[ticker] = hist['Close'].iloc[-1]
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        return prices
    
    def get_option_current_price(self, ticker: str, strike: float,
                                  expiration: str, option_type: str) -> float:
        """
        Fetch current option price from options chain.
        Returns mid price (bid+ask)/2 if available, else last price.
        """
        try:
            stock = yf.Ticker(ticker)
            chain = stock.option_chain(expiration)

            # Select calls or puts
            options = chain.calls if option_type == 'call' else chain.puts

            # Find matching strike
            match = options[options['strike'] == strike]

            if match.empty:
                print(f"⚠️ No option found for {ticker} {option_type} ${strike} exp {expiration}")
                return 0

            row = match.iloc[0]

            # Use mid price if bid/ask available
            if 'bid' in row and 'ask' in row and row['bid'] > 0 and row['ask'] > 0:
                return (row['bid'] + row['ask']) / 2

            # Fall back to last price
            return row.get('lastPrice', 0)

        except Exception as e:
            print(f"Error fetching option price for {ticker}: {e}")
            return 0

    def calculate_pnl(self) -> pd.DataFrame:
        """Calculate P&L for all positions with real-time option pricing"""
        if not self.positions:
            return pd.DataFrame()

        prices = self.get_current_prices()

        records = []
        for i, pos in enumerate(self.positions):
            if pos.position_type == 'stock':
                # Stock positions
                current_price = prices.get(pos.ticker, 0)
                market_value = current_price * pos.quantity
                cost_basis = pos.entry_price * pos.quantity
                display_price = current_price

            else:
                # Option positions - fetch real option price
                current_option_price = self.get_option_current_price(
                    pos.ticker, pos.strike, pos.expiration, pos.position_type
                )

                # Options are priced per contract (100 shares)
                market_value = current_option_price * pos.quantity * 100
                cost_basis = pos.entry_price * pos.quantity * 100
                display_price = current_option_price

            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis != 0 else 0

            records.append({
                'index': i,
                'ticker': pos.ticker,
                'type': pos.position_type,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': display_price,
                'strike': pos.strike,
                'expiration': pos.expiration,
                'cost_basis': cost_basis,
                'market_value': market_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'entry_date': pos.entry_date
            })

        return pd.DataFrame(records)
    
    def get_portfolio_greeks(self, analyzer) -> Dict:
        """
        Calculate aggregate portfolio Greeks.
        Requires an OptionsAnalyzer instance.
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        
        for pos in self.positions:
            if pos.position_type == 'stock':
                # Stocks have delta of 1 per share
                total_delta += pos.quantity
            elif pos.position_type in ['call', 'put']:
                # Get Greeks from analyzer
                try:
                    results = analyzer.analyze_ticker(pos.ticker)
                    
                    # Find matching option
                    options = results['calls'] if pos.position_type == 'call' else results['puts']
                    matching = options[
                        (options['strike'] == pos.strike)
                    ]
                    
                    if not matching.empty:
                        row = matching.iloc[0]
                        multiplier = pos.quantity * 100  # 100 shares per contract
                        
                        total_delta += row.get('delta', 0) * multiplier
                        total_gamma += row.get('gamma', 0) * multiplier
                        total_theta += row.get('theta', 0) * multiplier
                        total_vega += row.get('vega', 0) * multiplier
                except Exception as e:
                    print(f"Error calculating Greeks for {pos.ticker}: {e}")
        
        return {
            'delta': total_delta,
            'gamma': total_gamma,
            'theta': total_theta,
            'vega': total_vega
        }
    
    def summary(self) -> Dict:
        """Get portfolio summary"""
        pnl_df = self.calculate_pnl()
        
        if pnl_df.empty:
            return {
                'total_positions': 0,
                'total_value': 0,
                'total_cost': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0
            }
        
        return {
            'total_positions': len(self.positions),
            'unique_tickers': len(self.get_unique_tickers()),
            'total_value': pnl_df['market_value'].sum(),
            'total_cost': pnl_df['cost_basis'].sum(),
            'total_pnl': pnl_df['pnl'].sum(),
            'total_pnl_pct': (pnl_df['pnl'].sum() / pnl_df['cost_basis'].sum() * 100 
                             if pnl_df['cost_basis'].sum() != 0 else 0),
            'winners': len(pnl_df[pnl_df['pnl'] > 0]),
            'losers': len(pnl_df[pnl_df['pnl'] < 0])
        }
    
    def __repr__(self):
        return f"Portfolio({len(self.positions)} positions)"


def create_sample_portfolio():
    """Create a sample portfolio for testing"""
    portfolio = Portfolio()
    portfolio.clear()
    
    # Add some sample positions
    portfolio.add_stock('AAPL', 100, 175.00, 'Long-term hold')
    portfolio.add_stock('MSFT', 50, 380.00, 'Tech exposure')
    portfolio.add_stock('SPY', 200, 450.00, 'Index exposure')
    
    print("Sample portfolio created!")
    print(portfolio.calculate_pnl())
    return portfolio


if __name__ == "__main__":
    # Demo
    portfolio = create_sample_portfolio()
    
    print("\n" + "="*50)
    print("PORTFOLIO SUMMARY")
    print("="*50)
    
    summary = portfolio.summary()
    for key, value in summary.items():
        if 'pnl' in key.lower() and 'pct' not in key.lower():
            print(f"{key}: ${value:,.2f}")
        elif 'pct' in key.lower():
            print(f"{key}: {value:.2f}%")
        elif 'value' in key.lower() or 'cost' in key.lower():
            print(f"{key}: ${value:,.2f}")
        else:
            print(f"{key}: {value}")
