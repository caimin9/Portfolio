"""
Correlation and Beta Analysis Module
Calculate and track rolling correlations and betas for risk management and diversification.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from config import PLOTS_DIR
import os


@dataclass
class RollingBeta:
    """Container for rolling beta results"""
    ticker: str
    benchmark: str
    dates: np.ndarray
    betas: np.ndarray
    alphas: np.ndarray
    r_squared: np.ndarray
    current_beta: float
    avg_beta: float
    beta_std: float

    def get_regime(self) -> str:
        """Classify current beta regime"""
        if self.current_beta > self.avg_beta + self.beta_std:
            return "HIGH"
        elif self.current_beta < self.avg_beta - self.beta_std:
            return "LOW"
        else:
            return "NORMAL"


@dataclass
class CorrelationMatrix:
    """Container for correlation matrix results"""
    tickers: List[str]
    correlation_matrix: pd.DataFrame
    dates: pd.DatetimeIndex
    rolling_correlations: Dict[Tuple[str, str], pd.Series]
    avg_correlation: float

    def get_pairs_by_correlation(self, threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """Get ticker pairs above correlation threshold"""
        pairs = []
        n = len(self.tickers)
        for i in range(n):
            for j in range(i + 1, n):
                corr = self.correlation_matrix.iloc[i, j]
                if abs(corr) >= threshold:
                    pairs.append((self.tickers[i], self.tickers[j], corr))
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)


class CorrelationAnalyzer:
    """
    Analyze rolling correlations and betas for risk management.

    Features:
    - Rolling correlation between asset pairs
    - Rolling correlation matrices
    - Rolling beta calculation
    - Correlation regime detection
    - Beta regime analysis
    - Diversification metrics
    """

    def __init__(self, window: int = 60, min_periods: int = 30):
        """
        Parameters:
        -----------
        window : int
            Rolling window size in trading days (default 60 = ~3 months)
        min_periods : int
            Minimum periods required for calculation
        """
        self.window = window
        self.min_periods = min_periods

    def fetch_price_data(self, tickers: List[str], period: str = '2y') -> pd.DataFrame:
        """
        Fetch historical price data for multiple tickers.

        Parameters:
        -----------
        tickers : List[str]
            List of ticker symbols
        period : str
            Historical period ('1y', '2y', '5y', 'max')

        Returns:
        --------
        DataFrame with adjusted close prices for each ticker
        """
        print(f"Fetching data for {len(tickers)} tickers...")

        data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    data[ticker] = hist['Close']
                    print(f"  ✓ {ticker}: {len(hist)} days")
                else:
                    print(f"  ✗ {ticker}: No data")
            except Exception as e:
                print(f"  ✗ {ticker}: Error - {e}")

        if not data:
            raise ValueError("No data fetched for any ticker")

        df = pd.DataFrame(data)

        # Forward fill missing values (up to 5 days)
        df = df.fillna(method='ffill', limit=5)

        # Drop rows with any remaining NaN
        df = df.dropna()

        print(f"\nFinal dataset: {len(df)} days, {len(df.columns)} tickers")

        return df

    def calculate_returns(self, prices: pd.DataFrame, method: str = 'log') -> pd.DataFrame:
        """
        Calculate returns from prices.

        Parameters:
        -----------
        prices : DataFrame
            Price data
        method : str
            'simple' or 'log' returns

        Returns:
        --------
        DataFrame of returns
        """
        if method == 'log':
            returns = np.log(prices / prices.shift(1))
        else:  # simple
            returns = prices.pct_change()

        return returns.dropna()

    def rolling_correlation(self, ticker1: str, ticker2: str,
                           period: str = '2y') -> pd.Series:
        """
        Calculate rolling correlation between two tickers.

        Parameters:
        -----------
        ticker1, ticker2 : str
            Ticker symbols
        period : str
            Historical period

        Returns:
        --------
        Series of rolling correlations
        """
        # Fetch data
        prices = self.fetch_price_data([ticker1, ticker2], period)

        # Calculate returns
        returns = self.calculate_returns(prices)

        # Calculate rolling correlation
        rolling_corr = returns[ticker1].rolling(
            window=self.window,
            min_periods=self.min_periods
        ).corr(returns[ticker2])

        return rolling_corr.dropna()

    def rolling_correlation_matrix(self, tickers: List[str],
                                   period: str = '2y') -> CorrelationMatrix:
        """
        Calculate rolling correlations for multiple tickers.

        Parameters:
        -----------
        tickers : List[str]
            List of ticker symbols
        period : str
            Historical period

        Returns:
        --------
        CorrelationMatrix object
        """
        # Fetch data
        prices = self.fetch_price_data(tickers, period)
        returns = self.calculate_returns(prices)

        # Current correlation matrix
        current_corr = returns.corr()

        # Calculate rolling correlations for all pairs
        rolling_corrs = {}
        n = len(tickers)

        print("\nCalculating rolling correlations...")
        for i in range(n):
            for j in range(i + 1, n):
                ticker_i = tickers[i]
                ticker_j = tickers[j]

                roll_corr = returns[ticker_i].rolling(
                    window=self.window,
                    min_periods=self.min_periods
                ).corr(returns[ticker_j])

                rolling_corrs[(ticker_i, ticker_j)] = roll_corr.dropna()
                print(f"  ✓ {ticker_i} vs {ticker_j}")

        # Calculate average correlation
        avg_corr = current_corr.values[np.triu_indices_from(current_corr.values, k=1)].mean()

        return CorrelationMatrix(
            tickers=tickers,
            correlation_matrix=current_corr,
            dates=returns.index,
            rolling_correlations=rolling_corrs,
            avg_correlation=avg_corr
        )

    def rolling_beta(self, ticker: str, benchmark: str = 'SPY',
                    period: str = '2y') -> RollingBeta:
        """
        Calculate rolling beta of ticker vs benchmark.

        Beta = Cov(asset, benchmark) / Var(benchmark)

        Also calculates alpha and R-squared.

        Parameters:
        -----------
        ticker : str
            Asset ticker
        benchmark : str
            Benchmark ticker (default SPY)
        period : str
            Historical period

        Returns:
        --------
        RollingBeta object
        """
        # Fetch data
        prices = self.fetch_price_data([ticker, benchmark], period)
        returns = self.calculate_returns(prices)

        # Calculate rolling beta, alpha, R²
        betas = []
        alphas = []
        r_squareds = []
        dates = []

        print(f"\nCalculating rolling beta for {ticker} vs {benchmark}...")

        for i in range(self.min_periods, len(returns)):
            # Get window
            window_returns = returns.iloc[max(0, i - self.window):i]

            if len(window_returns) < self.min_periods:
                continue

            y = window_returns[ticker].values
            x = window_returns[benchmark].values

            # Remove NaN
            mask = ~(np.isnan(x) | np.isnan(y))
            x = x[mask]
            y = y[mask]

            if len(x) < self.min_periods:
                continue

            # Calculate beta via covariance
            cov_matrix = np.cov(x, y)
            beta = cov_matrix[0, 1] / cov_matrix[0, 0]

            # Calculate alpha (Jensen's alpha)
            alpha = np.mean(y) - beta * np.mean(x)

            # Calculate R²
            y_pred = alpha + beta * x
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            betas.append(beta)
            alphas.append(alpha)
            r_squareds.append(r_squared)
            dates.append(returns.index[i])

        betas = np.array(betas)
        alphas = np.array(alphas)
        r_squareds = np.array(r_squareds)
        dates = np.array(dates)

        print(f"  ✓ Calculated {len(betas)} rolling beta values")

        return RollingBeta(
            ticker=ticker,
            benchmark=benchmark,
            dates=dates,
            betas=betas,
            alphas=alphas,
            r_squared=r_squareds,
            current_beta=betas[-1] if len(betas) > 0 else 0,
            avg_beta=np.mean(betas),
            beta_std=np.std(betas)
        )

    def analyze_portfolio_diversification(self, tickers: List[str],
                                         weights: Optional[List[float]] = None,
                                         period: str = '2y') -> Dict:
        """
        Analyze portfolio diversification using correlation analysis.

        Parameters:
        -----------
        tickers : List[str]
            Portfolio tickers
        weights : List[float], optional
            Position weights (default equal weight)
        period : str
            Historical period

        Returns:
        --------
        Dict with diversification metrics
        """
        if weights is None:
            weights = [1.0 / len(tickers)] * len(tickers)

        weights = np.array(weights)
        weights = weights / weights.sum()  # Normalize

        # Get correlation matrix
        corr_matrix = self.rolling_correlation_matrix(tickers, period)

        # Calculate weighted average correlation
        corr_values = corr_matrix.correlation_matrix.values
        n = len(tickers)

        weighted_corr = 0
        total_weight = 0

        for i in range(n):
            for j in range(i + 1, n):
                pair_weight = weights[i] * weights[j]
                weighted_corr += pair_weight * corr_values[i, j]
                total_weight += pair_weight

        avg_weighted_corr = weighted_corr / total_weight if total_weight > 0 else 0

        # Calculate diversification ratio
        # DR = (sum of weighted individual vols) / (portfolio vol)
        prices = self.fetch_price_data(tickers, period)
        returns = self.calculate_returns(prices)

        individual_vols = returns.std() * np.sqrt(252)  # Annualized
        weighted_vol_sum = np.sum(weights * individual_vols)

        # Portfolio volatility
        cov_matrix = returns.cov() * 252  # Annualized
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))

        diversification_ratio = weighted_vol_sum / portfolio_vol if portfolio_vol > 0 else 1

        return {
            'tickers': tickers,
            'weights': weights.tolist(),
            'avg_correlation': corr_matrix.avg_correlation,
            'weighted_avg_correlation': avg_weighted_corr,
            'diversification_ratio': diversification_ratio,
            'portfolio_vol_annual': portfolio_vol,
            'correlation_matrix': corr_matrix.correlation_matrix,
            'high_correlation_pairs': corr_matrix.get_pairs_by_correlation(0.7)
        }

    def detect_correlation_regime_change(self, ticker1: str, ticker2: str,
                                        period: str = '2y',
                                        threshold: float = 0.3) -> List[Dict]:
        """
        Detect significant changes in correlation regime.

        Parameters:
        -----------
        ticker1, ticker2 : str
            Ticker pair
        period : str
            Historical period
        threshold : float
            Minimum correlation change to flag (default 0.3)

        Returns:
        --------
        List of regime change events
        """
        rolling_corr = self.rolling_correlation(ticker1, ticker2, period)

        # Calculate rolling mean and std
        mean_corr = rolling_corr.rolling(window=60).mean()
        std_corr = rolling_corr.rolling(window=60).std()

        # Detect regime changes
        changes = []

        for i in range(1, len(rolling_corr)):
            curr_corr = rolling_corr.iloc[i]
            prev_corr = rolling_corr.iloc[i-1]

            change = curr_corr - prev_corr

            if abs(change) >= threshold:
                changes.append({
                    'date': rolling_corr.index[i],
                    'from_corr': prev_corr,
                    'to_corr': curr_corr,
                    'change': change,
                    'regime': 'breakdown' if change < 0 else 'strengthening'
                })

        return changes


class CorrelationVisualizer:
    """Visualization tools for correlation and beta analysis"""

    @staticmethod
    def plot_rolling_correlation(ticker1: str, ticker2: str,
                                 rolling_corr: pd.Series,
                                 save: bool = True) -> plt.Figure:
        """Plot rolling correlation between two tickers"""
        fig, ax = plt.subplots(figsize=(14, 6))

        # Plot rolling correlation
        ax.plot(rolling_corr.index, rolling_corr.values,
               linewidth=2, color='steelblue', label='Rolling Correlation')

        # Add mean line
        mean_corr = rolling_corr.mean()
        ax.axhline(mean_corr, color='green', linestyle='--',
                  alpha=0.7, label=f'Mean: {mean_corr:.3f}')

        # Add ±1 std bands
        std_corr = rolling_corr.std()
        ax.axhline(mean_corr + std_corr, color='orange', linestyle=':',
                  alpha=0.5, label=f'±1 Std')
        ax.axhline(mean_corr - std_corr, color='orange', linestyle=':', alpha=0.5)

        # Zero line
        ax.axhline(0, color='gray', linestyle='-', alpha=0.3)

        # Shading for correlation regimes
        ax.axhspan(0.7, 1.0, alpha=0.1, color='green', label='High +Corr')
        ax.axhspan(-1.0, -0.7, alpha=0.1, color='red', label='High -Corr')

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Correlation', fontsize=12)
        ax.set_title(f'Rolling {len(rolling_corr)} Day Correlation: {ticker1} vs {ticker2}',
                    fontsize=14, fontweight='bold')
        ax.set_ylim(-1, 1)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(PLOTS_DIR,
                                   f'rolling_corr_{ticker1}_{ticker2}_{timestamp}.png')
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Saved: {filepath}")

        return fig

    @staticmethod
    def plot_rolling_beta(beta_result: RollingBeta, save: bool = True) -> plt.Figure:
        """Plot rolling beta with alpha and R²"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # Beta plot
        ax1 = axes[0]
        ax1.plot(beta_result.dates, beta_result.betas,
                linewidth=2, color='steelblue', label='Rolling Beta')
        ax1.axhline(beta_result.avg_beta, color='green', linestyle='--',
                   label=f'Mean: {beta_result.avg_beta:.3f}')
        ax1.axhline(1.0, color='gray', linestyle='-', alpha=0.3, label='Market Beta')

        # Beta regime bands
        ax1.axhspan(beta_result.avg_beta - beta_result.beta_std,
                   beta_result.avg_beta + beta_result.beta_std,
                   alpha=0.1, color='orange', label='±1 Std')

        ax1.set_ylabel('Beta', fontsize=12)
        ax1.set_title(f'Rolling Beta Analysis: {beta_result.ticker} vs {beta_result.benchmark}',
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # Add current regime indicator
        regime = beta_result.get_regime()
        regime_color = {'HIGH': 'red', 'LOW': 'blue', 'NORMAL': 'green'}
        ax1.scatter(beta_result.dates[-1], beta_result.current_beta,
                   s=100, c=regime_color[regime], marker='o',
                   edgecolors='black', linewidth=2, zorder=5,
                   label=f'Current: {beta_result.current_beta:.3f} ({regime})')
        ax1.legend(loc='best')

        # Alpha plot
        ax2 = axes[1]
        ax2.plot(beta_result.dates, beta_result.alphas * 252 * 100,  # Annualized %
                linewidth=2, color='purple', label='Rolling Alpha (Annual %)')
        ax2.axhline(0, color='gray', linestyle='-', alpha=0.3)
        ax2.set_ylabel('Alpha (%)', fontsize=12)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        # R² plot
        ax3 = axes[2]
        ax3.plot(beta_result.dates, beta_result.r_squared,
                linewidth=2, color='orange', label='R² (Explanatory Power)')
        ax3.axhline(0.5, color='gray', linestyle='--', alpha=0.3, label='50%')
        ax3.set_ylabel('R²', fontsize=12)
        ax3.set_xlabel('Date', fontsize=12)
        ax3.set_ylim(0, 1)
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(PLOTS_DIR,
                                   f'rolling_beta_{beta_result.ticker}_{timestamp}.png')
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Saved: {filepath}")

        return fig

    @staticmethod
    def plot_correlation_heatmap(corr_matrix: CorrelationMatrix,
                                save: bool = True) -> plt.Figure:
        """Plot correlation matrix heatmap"""
        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(corr_matrix.correlation_matrix,
                   annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                   vmin=-1, vmax=1, square=True, linewidths=0.5,
                   cbar_kws={'label': 'Correlation'}, ax=ax)

        ax.set_title('Correlation Matrix', fontsize=14, fontweight='bold')

        plt.tight_layout()

        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(PLOTS_DIR, f'correlation_heatmap_{timestamp}.png')
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Saved: {filepath}")

        return fig

    @staticmethod
    def plot_correlation_matrix_evolution(corr_matrix: CorrelationMatrix,
                                         save: bool = True) -> plt.Figure:
        """Plot evolution of correlations over time"""
        pairs = list(corr_matrix.rolling_correlations.keys())
        n_pairs = len(pairs)

        # Create subplots
        n_cols = 2
        n_rows = (n_pairs + 1) // 2

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4 * n_rows))
        axes = axes.flatten() if n_pairs > 1 else [axes]

        for idx, (ticker1, ticker2) in enumerate(pairs):
            ax = axes[idx]
            corr_series = corr_matrix.rolling_correlations[(ticker1, ticker2)]

            ax.plot(corr_series.index, corr_series.values,
                   linewidth=2, color='steelblue')
            ax.axhline(corr_series.mean(), color='green', linestyle='--',
                      alpha=0.7, label=f'Mean: {corr_series.mean():.3f}')
            ax.axhline(0, color='gray', linestyle='-', alpha=0.3)

            ax.set_title(f'{ticker1} vs {ticker2}', fontsize=12, fontweight='bold')
            ax.set_ylabel('Correlation')
            ax.set_ylim(-1, 1)
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)

        # Hide unused subplots
        for idx in range(n_pairs, len(axes)):
            axes[idx].axis('off')

        fig.suptitle('Rolling Correlation Evolution', fontsize=16, fontweight='bold', y=1.00)
        plt.tight_layout()

        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(PLOTS_DIR, f'correlation_evolution_{timestamp}.png')
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Saved: {filepath}")

        return fig


# Convenience functions

def quick_correlation(ticker1: str, ticker2: str, window: int = 60,
                     period: str = '2y', plot: bool = True) -> pd.Series:
    """Quick rolling correlation analysis"""
    analyzer = CorrelationAnalyzer(window=window)
    rolling_corr = analyzer.rolling_correlation(ticker1, ticker2, period)

    print(f"\n{ticker1} vs {ticker2} Correlation Analysis")
    print(f"Current: {rolling_corr.iloc[-1]:.3f}")
    print(f"Mean: {rolling_corr.mean():.3f}")
    print(f"Std: {rolling_corr.std():.3f}")
    print(f"Min: {rolling_corr.min():.3f}")
    print(f"Max: {rolling_corr.max():.3f}")

    if plot:
        viz = CorrelationVisualizer()
        viz.plot_rolling_correlation(ticker1, ticker2, rolling_corr)

    return rolling_corr


def quick_beta(ticker: str, benchmark: str = 'SPY', window: int = 60,
              period: str = '2y', plot: bool = True) -> RollingBeta:
    """Quick rolling beta analysis"""
    analyzer = CorrelationAnalyzer(window=window)
    beta_result = analyzer.rolling_beta(ticker, benchmark, period)

    print(f"\n{ticker} vs {benchmark} Beta Analysis")
    print(f"Current Beta: {beta_result.current_beta:.3f} ({beta_result.get_regime()})")
    print(f"Average Beta: {beta_result.avg_beta:.3f}")
    print(f"Beta Std Dev: {beta_result.beta_std:.3f}")
    print(f"Current Alpha (annual): {beta_result.alphas[-1] * 252 * 100:.2f}%")
    print(f"Current R²: {beta_result.r_squared[-1]:.3f}")

    if plot:
        viz = CorrelationVisualizer()
        viz.plot_rolling_beta(beta_result)

    return beta_result


def analyze_portfolio_correlations(tickers: List[str], window: int = 60,
                                   period: str = '2y', plot: bool = True) -> CorrelationMatrix:
    """Analyze correlations for multiple tickers"""
    analyzer = CorrelationAnalyzer(window=window)
    corr_matrix = analyzer.rolling_correlation_matrix(tickers, period)

    print(f"\nCorrelation Matrix Analysis for {len(tickers)} tickers")
    print(f"Average Correlation: {corr_matrix.avg_correlation:.3f}")

    print("\nCurrent Correlation Matrix:")
    print(corr_matrix.correlation_matrix.round(3))

    high_corr_pairs = corr_matrix.get_pairs_by_correlation(0.7)
    if high_corr_pairs:
        print(f"\nHigh Correlation Pairs (|r| > 0.7):")
        for t1, t2, corr in high_corr_pairs:
            print(f"  {t1} - {t2}: {corr:.3f}")

    if plot:
        viz = CorrelationVisualizer()
        viz.plot_correlation_heatmap(corr_matrix)
        viz.plot_correlation_matrix_evolution(corr_matrix)

    return corr_matrix


if __name__ == "__main__":
    # Demo examples
    print("=" * 70)
    print("CORRELATION & BETA ANALYSIS DEMO")
    print("=" * 70)

    # Example 1: Rolling correlation
    print("\n1. Rolling Correlation: AAPL vs MSFT")
    quick_correlation('AAPL', 'MSFT', window=60, period='2y')

    # Example 2: Rolling beta
    print("\n2. Rolling Beta: TSLA vs SPY")
    quick_beta('TSLA', 'SPY', window=60, period='2y')

    # Example 3: Portfolio correlation matrix
    print("\n3. Portfolio Correlation Matrix")
    portfolio_tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
    analyze_portfolio_correlations(portfolio_tickers, window=60, period='2y')

    print("\n" + "=" * 70)
    print("Analysis complete! Check the plots/ folder for visualizations.")
    plt.show()
