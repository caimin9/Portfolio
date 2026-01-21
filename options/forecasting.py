"""
Forecasting Module
Uses implied distributions for price forecasting and scenario analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import yfinance as yf
from datetime import datetime, timedelta

from analytics import OptionsAnalyzer, ImpliedDistribution


@dataclass
class Forecast:
    """Container for forecast results"""
    ticker: str
    current_price: float
    forecast_date: str
    days_ahead: int
    
    # Point estimates
    expected_price: float
    median_price: float
    mode_price: float
    
    # Ranges
    range_50: Tuple[float, float]  # 50% confidence
    range_68: Tuple[float, float]  # 1 sigma
    range_95: Tuple[float, float]  # 2 sigma
    range_99: Tuple[float, float]  # 3 sigma
    
    # Probabilities
    prob_profit_long: float  # Prob of price increase
    prob_profit_short: float  # Prob of price decrease
    
    # Target probabilities
    target_probs: Dict[float, float]  # Price -> Probability of reaching
    
    # Distribution characteristics
    atm_iv: float
    skewness: float
    kurtosis: float
    
    def summary(self) -> str:
        """Return formatted summary"""
        lines = [
            f"Forecast for {self.ticker} - {self.days_ahead} days ahead",
            f"Current: ${self.current_price:.2f}",
            f"",
            f"Expected: ${self.expected_price:.2f} ({(self.expected_price/self.current_price - 1)*100:+.1f}%)",
            f"Median: ${self.median_price:.2f}",
            f"",
            f"50% Range: ${self.range_50[0]:.2f} - ${self.range_50[1]:.2f}",
            f"68% Range: ${self.range_68[0]:.2f} - ${self.range_68[1]:.2f}",
            f"95% Range: ${self.range_95[0]:.2f} - ${self.range_95[1]:.2f}",
            f"",
            f"Prob Up: {self.prob_profit_long*100:.1f}%",
            f"Prob Down: {self.prob_profit_short*100:.1f}%",
            f"",
            f"ATM IV: {self.atm_iv*100:.1f}%",
            f"Skewness: {self.skewness:.2f}",
        ]
        return "\n".join(lines)


class DistributionForecaster:
    """
    Generates price forecasts using options-implied distributions.
    
    Methods:
    1. Direct distribution forecast - Uses the risk-neutral distribution
    2. Monte Carlo simulation - Simulates paths using IV
    3. Scenario analysis - Probability of reaching specific targets
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.r = risk_free_rate
        self.analyzer = OptionsAnalyzer(risk_free_rate)
    
    def forecast_from_distribution(self, ticker: str, 
                                    expiration_index: int = 0) -> Optional[Forecast]:
        """
        Generate forecast directly from implied distribution.
        """
        try:
            results = self.analyzer.analyze_ticker(ticker, expiration_index)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return None
        
        impl_dist = results['implied_distribution']
        if impl_dist is None:
            print(f"Could not extract distribution for {ticker}")
            return None
        
        current_price = results['current_price']
        days_ahead = results['days_to_exp']
        exp_date = results['expiration']
        
        # Point estimates
        expected_price = impl_dist.expected_price
        
        # Median (50th percentile)
        cdf = impl_dist.cdf
        strikes = impl_dist.strikes
        median_idx = np.searchsorted(cdf, 0.5)
        median_idx = min(median_idx, len(strikes) - 1)
        median_price = strikes[median_idx]
        
        # Mode (peak of density)
        mode_idx = np.argmax(impl_dist.density)
        mode_price = strikes[mode_idx]
        
        # Confidence ranges
        range_50 = impl_dist.expected_move(0.50)
        range_68 = impl_dist.expected_move(0.68)
        range_95 = impl_dist.expected_move(0.95)
        range_99 = impl_dist.expected_move(0.99)
        
        # Direction probabilities
        prob_up = impl_dist.probability_above(current_price)
        prob_down = impl_dist.probability_below(current_price)
        
        # Target probabilities
        target_probs = self._calculate_target_probs(impl_dist, current_price)
        
        return Forecast(
            ticker=ticker,
            current_price=current_price,
            forecast_date=exp_date,
            days_ahead=days_ahead,
            expected_price=expected_price,
            median_price=median_price,
            mode_price=mode_price,
            range_50=range_50,
            range_68=range_68,
            range_95=range_95,
            range_99=range_99,
            prob_profit_long=prob_up,
            prob_profit_short=prob_down,
            target_probs=target_probs,
            atm_iv=impl_dist.atm_iv,
            skewness=impl_dist.skewness,
            kurtosis=impl_dist.kurtosis
        )
    
    def monte_carlo_forecast(self, ticker: str, days: int = 30,
                             num_simulations: int = 10000,
                             expiration_index: int = 0) -> Dict:
        """
        Monte Carlo simulation using implied volatility.
        
        Uses geometric Brownian motion with IV from options market.
        """
        try:
            results = self.analyzer.analyze_ticker(ticker, expiration_index)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return {}
        
        impl_dist = results['implied_distribution']
        current_price = results['current_price']
        
        # Get IV (use ATM or provided)
        if impl_dist:
            sigma = impl_dist.atm_iv
        else:
            sigma = results['summary'].get('iv_mean', 0.3)
        
        # Time parameters
        dt = 1 / 252  # Daily steps
        T = days / 252
        n_steps = days
        
        # Generate paths
        np.random.seed(42)  # For reproducibility
        
        # Random shocks
        Z = np.random.standard_normal((num_simulations, n_steps))
        
        # Drift adjusted for risk-neutral
        drift = (self.r - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt)
        
        # Simulate log returns
        log_returns = drift + diffusion * Z
        
        # Cumulative returns
        log_paths = np.cumsum(log_returns, axis=1)
        
        # Price paths
        price_paths = current_price * np.exp(log_paths)
        
        # Terminal prices
        terminal_prices = price_paths[:, -1]
        
        # Statistics
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        pct_values = np.percentile(terminal_prices, percentiles)
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'days': days,
            'iv_used': sigma,
            'num_simulations': num_simulations,
            'expected': np.mean(terminal_prices),
            'std_dev': np.std(terminal_prices),
            'percentiles': dict(zip(percentiles, pct_values)),
            'prob_up': np.mean(terminal_prices > current_price),
            'prob_down': np.mean(terminal_prices < current_price),
            'max': np.max(terminal_prices),
            'min': np.min(terminal_prices),
            'paths': price_paths  # Full paths for visualization
        }
    
    def scenario_analysis(self, ticker: str, targets: List[float],
                          expiration_index: int = 0) -> pd.DataFrame:
        """
        Calculate probability of reaching various price targets.
        """
        try:
            results = self.analyzer.analyze_ticker(ticker, expiration_index)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return pd.DataFrame()
        
        impl_dist = results['implied_distribution']
        current_price = results['current_price']
        
        if impl_dist is None:
            return pd.DataFrame()
        
        scenarios = []
        for target in targets:
            pct_change = (target / current_price - 1) * 100
            
            if target > current_price:
                prob = impl_dist.probability_above(target)
                direction = 'above'
            else:
                prob = impl_dist.probability_below(target)
                direction = 'below'
            
            scenarios.append({
                'target': target,
                'pct_change': pct_change,
                'direction': direction,
                'probability': prob,
                'odds': f"1 in {int(1/prob)}" if prob > 0.001 else "< 1 in 1000"
            })
        
        return pd.DataFrame(scenarios)
    
    def _calculate_target_probs(self, impl_dist: ImpliedDistribution,
                                 current_price: float) -> Dict[float, float]:
        """Calculate probabilities for standard targets"""
        targets = {}
        
        # Percentage moves
        for pct in [-20, -15, -10, -5, -2, 2, 5, 10, 15, 20]:
            target = current_price * (1 + pct/100)
            if pct > 0:
                prob = impl_dist.probability_above(target)
            else:
                prob = impl_dist.probability_below(target)
            targets[pct] = prob
        
        return targets
    
    def compare_forecasts(self, tickers: List[str],
                          expiration_index: int = 0) -> pd.DataFrame:
        """Compare forecasts across multiple tickers"""
        records = []
        
        for ticker in tickers:
            forecast = self.forecast_from_distribution(ticker, expiration_index)
            if forecast:
                records.append({
                    'ticker': ticker,
                    'price': forecast.current_price,
                    'expected': forecast.expected_price,
                    'expected_return': (forecast.expected_price / forecast.current_price - 1) * 100,
                    'atm_iv': forecast.atm_iv * 100,
                    'prob_up': forecast.prob_profit_long * 100,
                    'skewness': forecast.skewness,
                    '1sigma_range': f"{forecast.range_68[0]:.0f}-{forecast.range_68[1]:.0f}",
                    'days': forecast.days_ahead
                })
        
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('prob_up', ascending=False)
        
        return df


def quick_forecast(ticker: str) -> Forecast:
    """Quick forecast for a single ticker"""
    forecaster = DistributionForecaster()
    forecast = forecaster.forecast_from_distribution(ticker)
    
    if forecast:
        print(forecast.summary())
    
    return forecast


def compare_tickers(tickers: List[str]) -> pd.DataFrame:
    """Compare forecasts for multiple tickers"""
    forecaster = DistributionForecaster()
    df = forecaster.compare_forecasts(tickers)
    print(df.to_string())
    return df


if __name__ == "__main__":
    # Demo
    print("=" * 60)
    print("FORECAST DEMO")
    print("=" * 60)
    
    # Single forecast
    ticker = input("Enter ticker (default SPY): ").strip().upper() or "SPY"
    forecast = quick_forecast(ticker)
    
    # Scenario analysis
    if forecast:
        print("\n" + "-" * 40)
        print("SCENARIO ANALYSIS")
        print("-" * 40)
        
        forecaster = DistributionForecaster()
        
        # Generate targets around current price
        current = forecast.current_price
        targets = [
            current * 0.85,
            current * 0.90,
            current * 0.95,
            current * 1.05,
            current * 1.10,
            current * 1.15
        ]
        
        scenarios = forecaster.scenario_analysis(ticker, targets)
        print(scenarios.to_string(index=False))
    
    # Compare tickers
    print("\n" + "-" * 40)
    print("COMPARING TOP TICKERS")
    print("-" * 40)
    
    compare_tickers(['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA'])
