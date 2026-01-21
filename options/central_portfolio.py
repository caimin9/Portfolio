"""
Centralized Portfolio Management System
Single source of truth for all portfolio data and analytics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

from portfolio import Portfolio, Position
from analytics import OptionsAnalyzer
from correlation_analysis import CorrelationAnalyzer
from forecasting import DistributionForecaster
from config import PORTFOLIO_FILE


@dataclass
class PortfolioAnalytics:
    """Complete portfolio analytics container"""
    # Basic metrics
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    daily_pnl: float

    # Greeks
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float

    # Risk metrics
    portfolio_beta: float
    portfolio_var_95: float  # 95% VaR
    portfolio_volatility: float  # Annual

    # Correlation metrics
    avg_correlation: float
    diversification_ratio: float

    # Distribution metrics
    expected_move_1d: float
    expected_move_1w: float
    prob_profit: float

    # Top positions
    largest_positions: List[Dict]
    highest_risk_positions: List[Dict]

    # Alerts
    alerts: List[str] = field(default_factory=list)


class CentralPortfolio:
    """
    Centralized portfolio management with integrated analytics.

    Single source of truth that feeds all dashboard pages and analysis.
    Automatically calculates:
    - Real-time P&L
    - Portfolio Greeks
    - Beta and correlations
    - Risk metrics
    - Implied distributions
    """

    def __init__(self, portfolio_file: str = None):
        """Initialize central portfolio"""
        if portfolio_file is None:
            portfolio_file = PORTFOLIO_FILE
        self.portfolio = Portfolio(portfolio_file)

        # Analytics engines (lazy load for performance)
        self._options_analyzer = None
        self._corr_analyzer = None
        self._forecaster = None

        # Cache for expensive calculations
        self._analytics_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

    @property
    def options_analyzer(self):
        """Lazy load options analyzer"""
        if self._options_analyzer is None:
            self._options_analyzer = OptionsAnalyzer()
        return self._options_analyzer

    @property
    def corr_analyzer(self):
        """Lazy load correlation analyzer"""
        if self._corr_analyzer is None:
            self._corr_analyzer = CorrelationAnalyzer(window=60)
        return self._corr_analyzer

    @property
    def forecaster(self):
        """Lazy load forecaster"""
        if self._forecaster is None:
            self._forecaster = DistributionForecaster()
        return self._forecaster

    def add_stock(self, ticker: str, quantity: int, entry_price: float, notes: str = ""):
        """Add stock position and reload"""
        self.portfolio.add_stock(ticker, quantity, entry_price, notes)
        self.portfolio.load()  # CRITICAL: Reload from disk
        self._invalidate_cache()

    def add_option(self, ticker: str, option_type: str, quantity: int,
                   entry_price: float, strike: float, expiration: str, notes: str = ""):
        """Add option position and reload"""
        self.portfolio.add_option(ticker, option_type, quantity, entry_price,
                                 strike, expiration, notes)
        self.portfolio.load()  # CRITICAL: Reload from disk
        self._invalidate_cache()

    def remove_position(self, index: int):
        """Remove position and reload"""
        self.portfolio.remove_position(index)
        self.portfolio.load()  # CRITICAL: Reload from disk
        self._invalidate_cache()

    def clear(self):
        """Clear all positions and reload"""
        self.portfolio.clear()
        self.portfolio.load()  # CRITICAL: Reload from disk
        self._invalidate_cache()

    def _invalidate_cache(self):
        """Invalidate analytics cache"""
        self._analytics_cache = {}
        self._cache_timestamp = None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cache_timestamp is None:
            return False
        age = (datetime.now() - self._cache_timestamp).seconds
        return age < self._cache_ttl

    def get_positions_df(self) -> pd.DataFrame:
        """Get positions as DataFrame with current prices and P&L"""
        return self.portfolio.calculate_pnl()

    def get_portfolio_summary(self) -> Dict:
        """Get basic portfolio summary"""
        return self.portfolio.summary()

    def get_unique_tickers(self) -> List[str]:
        """Get list of unique tickers"""
        return self.portfolio.get_unique_tickers()

    def analyze_portfolio(self, force_refresh: bool = False) -> PortfolioAnalytics:
        """
        Complete portfolio analysis with all metrics.

        Calculates:
        - P&L and value
        - Greeks (delta, gamma, theta, vega)
        - Beta and systematic risk
        - Correlations and diversification
        - Risk metrics (VaR, volatility)
        - Expected moves

        Results are cached for 5 minutes unless force_refresh=True
        """
        # Check cache
        if not force_refresh and self._is_cache_valid() and 'analytics' in self._analytics_cache:
            return self._analytics_cache['analytics']

        print("Calculating comprehensive portfolio analytics...")

        # Get basic metrics
        summary = self.portfolio.summary()
        pnl_df = self.portfolio.calculate_pnl()

        if pnl_df.empty:
            return self._empty_analytics()

        # Get tickers
        tickers = self.get_unique_tickers()

        # Calculate Greeks
        try:
            greeks = self.portfolio.get_portfolio_greeks(self.options_analyzer)
        except:
            greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}

        # Calculate portfolio beta (value-weighted)
        portfolio_beta = self._calculate_portfolio_beta(pnl_df, tickers)

        # Calculate correlation metrics
        corr_metrics = self._calculate_correlation_metrics(tickers, pnl_df)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(tickers, pnl_df)

        # Calculate expected moves
        expected_moves = self._calculate_expected_moves(tickers, pnl_df)

        # Identify top positions
        largest_positions = self._get_largest_positions(pnl_df, n=5)
        highest_risk = self._get_highest_risk_positions(pnl_df, portfolio_beta, n=5)

        # Generate alerts
        alerts = self._generate_alerts(pnl_df, greeks, portfolio_beta, corr_metrics)

        # Build analytics object
        analytics = PortfolioAnalytics(
            total_value=summary['total_value'],
            total_pnl=summary['total_pnl'],
            total_pnl_pct=summary['total_pnl_pct'],
            daily_pnl=0,  # TODO: Calculate daily change

            total_delta=greeks['delta'],
            total_gamma=greeks['gamma'],
            total_theta=greeks['theta'],
            total_vega=greeks['vega'],

            portfolio_beta=portfolio_beta,
            portfolio_var_95=risk_metrics['var_95'],
            portfolio_volatility=risk_metrics['volatility'],

            avg_correlation=corr_metrics['avg_correlation'],
            diversification_ratio=corr_metrics['diversification_ratio'],

            expected_move_1d=expected_moves['one_day'],
            expected_move_1w=expected_moves['one_week'],
            prob_profit=expected_moves['prob_profit'],

            largest_positions=largest_positions,
            highest_risk_positions=highest_risk,

            alerts=alerts
        )

        # Cache results
        self._analytics_cache['analytics'] = analytics
        self._cache_timestamp = datetime.now()

        print("✓ Portfolio analytics calculated")

        return analytics

    def _empty_analytics(self) -> PortfolioAnalytics:
        """Return empty analytics for empty portfolio"""
        return PortfolioAnalytics(
            total_value=0, total_pnl=0, total_pnl_pct=0, daily_pnl=0,
            total_delta=0, total_gamma=0, total_theta=0, total_vega=0,
            portfolio_beta=1.0, portfolio_var_95=0, portfolio_volatility=0,
            avg_correlation=0, diversification_ratio=1.0,
            expected_move_1d=0, expected_move_1w=0, prob_profit=0.5,
            largest_positions=[], highest_risk_positions=[], alerts=[]
        )

    def _calculate_portfolio_beta(self, pnl_df: pd.DataFrame, tickers: List[str]) -> float:
        """Calculate value-weighted portfolio beta"""
        try:
            total_value = pnl_df['market_value'].sum()
            if total_value == 0:
                return 1.0

            weighted_beta = 0
            for ticker in tickers:
                # Get positions for this ticker
                ticker_positions = pnl_df[pnl_df['ticker'] == ticker]
                ticker_value = ticker_positions['market_value'].sum()
                weight = ticker_value / total_value

                # Get beta
                try:
                    beta_result = self.corr_analyzer.rolling_beta(ticker, 'SPY', period='1y')
                    beta = beta_result.current_beta
                except:
                    beta = 1.0  # Default to market beta

                weighted_beta += weight * beta

            return weighted_beta
        except:
            return 1.0

    def _calculate_correlation_metrics(self, tickers: List[str],
                                       pnl_df: pd.DataFrame) -> Dict:
        """Calculate correlation and diversification metrics"""
        if len(tickers) < 2:
            return {'avg_correlation': 0, 'diversification_ratio': 1.0}

        try:
            # Get weights
            total_value = pnl_df['market_value'].sum()
            weights = []
            tickers_clean = []

            for ticker in tickers:
                ticker_value = pnl_df[pnl_df['ticker'] == ticker]['market_value'].sum()
                if ticker_value > 0:
                    weights.append(ticker_value / total_value)
                    tickers_clean.append(ticker)

            if len(tickers_clean) < 2:
                return {'avg_correlation': 0, 'diversification_ratio': 1.0}

            # Calculate diversification metrics
            metrics = self.corr_analyzer.analyze_portfolio_diversification(
                tickers_clean, weights, period='1y'
            )

            return {
                'avg_correlation': metrics['avg_correlation'],
                'diversification_ratio': metrics['diversification_ratio']
            }
        except:
            return {'avg_correlation': 0, 'diversification_ratio': 1.0}

    def _calculate_risk_metrics(self, tickers: List[str], pnl_df: pd.DataFrame) -> Dict:
        """Calculate VaR and volatility"""
        try:
            # Fetch historical data
            prices = self.corr_analyzer.fetch_price_data(tickers, period='1y')
            returns = self.corr_analyzer.calculate_returns(prices)

            # Get weights
            total_value = pnl_df['market_value'].sum()
            weights = []

            for ticker in tickers:
                ticker_value = pnl_df[pnl_df['ticker'] == ticker]['market_value'].sum()
                weights.append(ticker_value / total_value)

            weights = np.array(weights)

            # Portfolio returns
            portfolio_returns = (returns * weights).sum(axis=1)

            # VaR (95%)
            var_95 = np.percentile(portfolio_returns, 5) * total_value

            # Volatility (annualized)
            volatility = portfolio_returns.std() * np.sqrt(252)

            return {
                'var_95': abs(var_95),
                'volatility': volatility
            }
        except:
            return {'var_95': 0, 'volatility': 0}

    def _calculate_expected_moves(self, tickers: List[str], pnl_df: pd.DataFrame) -> Dict:
        """Calculate expected price moves"""
        try:
            total_value = pnl_df['market_value'].sum()

            # Simple volatility-based estimate
            prices = self.corr_analyzer.fetch_price_data(tickers, period='1y')
            returns = self.corr_analyzer.calculate_returns(prices)

            # Get weights
            weights = []
            for ticker in tickers:
                ticker_value = pnl_df[pnl_df['ticker'] == ticker]['market_value'].sum()
                weights.append(ticker_value / total_value)

            weights = np.array(weights)
            portfolio_returns = (returns * weights).sum(axis=1)

            # Daily std
            daily_std = portfolio_returns.std()
            weekly_std = daily_std * np.sqrt(5)

            # Expected moves (1 std)
            move_1d = daily_std * total_value
            move_1w = weekly_std * total_value

            # Prob of profit (simplistic)
            mean_return = portfolio_returns.mean()
            prob_profit = 0.5 + (mean_return / (daily_std * 2)) if daily_std > 0 else 0.5
            prob_profit = max(0, min(1, prob_profit))

            return {
                'one_day': abs(move_1d),
                'one_week': abs(move_1w),
                'prob_profit': prob_profit
            }
        except:
            return {'one_day': 0, 'one_week': 0, 'prob_profit': 0.5}

    def _get_largest_positions(self, pnl_df: pd.DataFrame, n: int = 5) -> List[Dict]:
        """Get N largest positions by value"""
        sorted_df = pnl_df.sort_values('market_value', ascending=False).head(n)

        results = []
        for _, row in sorted_df.iterrows():
            results.append({
                'ticker': row['ticker'],
                'type': row['type'],
                'value': row['market_value'],
                'pnl': row['pnl'],
                'pnl_pct': row['pnl_pct']
            })

        return results

    def _get_highest_risk_positions(self, pnl_df: pd.DataFrame,
                                    portfolio_beta: float, n: int = 5) -> List[Dict]:
        """Get N highest risk positions (by beta * value)"""
        results = []

        for _, row in pnl_df.iterrows():
            try:
                beta_result = self.corr_analyzer.rolling_beta(
                    row['ticker'], 'SPY', period='1y'
                )
                beta = beta_result.current_beta
            except:
                beta = 1.0

            risk_score = beta * row['market_value']

            results.append({
                'ticker': row['ticker'],
                'type': row['type'],
                'value': row['market_value'],
                'beta': beta,
                'risk_score': risk_score
            })

        # Sort by risk score
        results.sort(key=lambda x: x['risk_score'], reverse=True)

        return results[:n]

    def _generate_alerts(self, pnl_df: pd.DataFrame, greeks: Dict,
                        portfolio_beta: float, corr_metrics: Dict) -> List[str]:
        """Generate portfolio alerts"""
        alerts = []

        # High beta warning
        if portfolio_beta > 1.5:
            alerts.append(f"⚠️ High portfolio beta ({portfolio_beta:.2f}) - elevated market risk")

        # Concentration warning
        if not pnl_df.empty:
            total_value = pnl_df['market_value'].sum()
            max_position = pnl_df['market_value'].max()
            concentration = max_position / total_value if total_value > 0 else 0

            if concentration > 0.4:
                alerts.append(f"⚠️ High concentration ({concentration*100:.0f}% in one position)")

        # Low diversification
        if corr_metrics['avg_correlation'] > 0.7:
            alerts.append("⚠️ High correlation - poor diversification")

        # Large theta decay
        if greeks['theta'] < -500:
            alerts.append(f"⚠️ High theta decay (${greeks['theta']:.0f}/day)")

        # Large negative delta (bearish exposure)
        if greeks['delta'] < -100:
            alerts.append(f"⚠️ Large negative delta ({greeks['delta']:.0f}) - bearish exposure")

        return alerts

    def export_to_json(self, filepath: str):
        """Export portfolio and analytics to JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'positions': [pos.to_dict() for pos in self.portfolio.positions],
            'summary': self.get_portfolio_summary(),
            'analytics': self.analyze_portfolio().__dict__
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def import_from_json(self, filepath: str):
        """Import portfolio from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.portfolio.clear()

        for pos_dict in data['positions']:
            pos = Position.from_dict(pos_dict)
            self.portfolio.add_position(pos)

        self._invalidate_cache()


# Global instance (singleton pattern)
_central_portfolio = None

def get_central_portfolio() -> CentralPortfolio:
    """Get the global central portfolio instance"""
    global _central_portfolio
    if _central_portfolio is None:
        _central_portfolio = CentralPortfolio()
    return _central_portfolio
