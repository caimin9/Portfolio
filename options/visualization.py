"""
Visualization Module
Generate and save publication-quality plots for options analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import seaborn as sns
from datetime import datetime
import os

from config import PLOTS_DIR
from analytics import ImpliedDistribution


def setup_style():
    """Set up matplotlib style for dark theme"""
    plt.style.use('dark_background')
    plt.rcParams['figure.facecolor'] = '#1e1e1e'
    plt.rcParams['axes.facecolor'] = '#2d2d2d'
    plt.rcParams['axes.edgecolor'] = '#555555'
    plt.rcParams['axes.labelcolor'] = 'white'
    plt.rcParams['text.color'] = 'white'
    plt.rcParams['xtick.color'] = 'white'
    plt.rcParams['ytick.color'] = 'white'
    plt.rcParams['grid.color'] = '#444444'
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['font.size'] = 10


def plot_distribution_analysis(dist: ImpliedDistribution, current_price: float,
                                ticker: str, exp_date: str,
                                save: bool = True) -> plt.Figure:
    """
    Create comprehensive distribution analysis figure.
    
    Includes:
    - Probability density function
    - Cumulative distribution function
    - Key statistics
    - Probability regions
    """
    setup_style()
    
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1], hspace=0.25, wspace=0.2)
    
    # Main distribution plot
    ax1 = fig.add_subplot(gs[0, :])
    
    # PDF bars
    bar_width = (dist.strikes[-1] - dist.strikes[0]) / len(dist.strikes) * 0.8
    ax1.bar(dist.strikes, dist.density, width=bar_width, 
            alpha=0.7, color='steelblue', edgecolor='none', label='Implied Distribution')
    
    # Current price
    ax1.axvline(current_price, color='lime', linestyle='--', linewidth=2, 
                label=f'Current: ${current_price:.2f}')
    
    # Expected price
    ax1.axvline(dist.expected_price, color='red', linestyle='--', linewidth=2,
                label=f'Expected: ${dist.expected_price:.2f}')
    
    # 1 sigma range
    lower_1s, upper_1s = dist.expected_move(0.68)
    ax1.axvspan(lower_1s, upper_1s, alpha=0.15, color='orange',
                label=f'68% Range: ${lower_1s:.0f} - ${upper_1s:.0f}')
    
    # 2 sigma range  
    lower_2s, upper_2s = dist.expected_move(0.95)
    ax1.axvspan(lower_2s, lower_1s, alpha=0.08, color='yellow')
    ax1.axvspan(upper_1s, upper_2s, alpha=0.08, color='yellow',
                label=f'95% Range: ${lower_2s:.0f} - ${upper_2s:.0f}')
    
    ax1.set_xlabel('Price ($)', fontsize=12)
    ax1.set_ylabel('Probability Density', fontsize=12)
    ax1.set_title(f'{ticker} Implied Price Distribution\nExpiration: {exp_date} ({dist.days_to_exp} days)',
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', framealpha=0.8)
    ax1.grid(True, alpha=0.3)
    
    # CDF plot
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(dist.strikes, dist.cdf, color='cyan', linewidth=2)
    ax2.axhline(0.5, color='gray', linestyle=':', alpha=0.5, label='Median')
    ax2.axvline(current_price, color='lime', linestyle='--', alpha=0.7)
    
    # Add probability at current price
    current_cdf = np.interp(current_price, dist.strikes, dist.cdf)
    ax2.plot(current_price, current_cdf, 'o', color='lime', markersize=10)
    ax2.annotate(f'{current_cdf*100:.0f}% below', 
                 (current_price, current_cdf),
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=9, color='lime')
    
    ax2.set_xlabel('Price ($)', fontsize=11)
    ax2.set_ylabel('Cumulative Probability', fontsize=11)
    ax2.set_title('Cumulative Distribution', fontsize=12)
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)
    
    # Statistics box
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')
    
    stats_text = f"""
    DISTRIBUTION STATISTICS
    ════════════════════════
    
    Current Price:     ${current_price:.2f}
    Expected Price:    ${dist.expected_price:.2f}
    Expected Move:     ±${dist.std_dev:.2f} (±{dist.std_dev/current_price*100:.1f}%)
    
    ATM IV:           {dist.atm_iv*100:.1f}%
    Skewness:         {dist.skewness:.3f}
    Excess Kurtosis:  {dist.kurtosis:.3f}
    
    PROBABILITIES
    ─────────────
    Price > Current:  {dist.probability_above(current_price)*100:.1f}%
    Price < Current:  {dist.probability_below(current_price)*100:.1f}%
    
    68% Range:        ${lower_1s:.2f} - ${upper_1s:.2f}
    95% Range:        ${lower_2s:.2f} - ${upper_2s:.2f}
    """
    
    ax3.text(0.1, 0.95, stats_text, transform=ax3.transAxes,
             fontfamily='monospace', fontsize=10,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='#1a1a2e', edgecolor='#555'))
    
    plt.tight_layout()
    
    if save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(PLOTS_DIR, f'{ticker}_distribution_analysis_{timestamp}.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {filepath}")
    
    return fig


def plot_iv_surface(iv_surface: pd.DataFrame, current_price: float,
                     ticker: str, save: bool = True) -> plt.Figure:
    """Plot implied volatility smile/skew"""
    setup_style()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    calls = iv_surface[iv_surface['type'] == 'call'].sort_values('strike')
    puts = iv_surface[iv_surface['type'] == 'put'].sort_values('strike')
    
    # Plot calls and puts
    ax.plot(calls['moneyness'], calls['impliedVolatility'] * 100, 
            'o-', color='#00ff88', label='Calls', markersize=6, linewidth=1.5)
    ax.plot(puts['moneyness'], puts['impliedVolatility'] * 100,
            's-', color='#ff4444', label='Puts', markersize=6, linewidth=1.5)
    
    # ATM line
    ax.axvline(1.0, color='white', linestyle='--', alpha=0.5, label='ATM')
    
    # Highlight regions
    ax.axvspan(0.5, 0.9, alpha=0.05, color='red', label='OTM Puts')
    ax.axvspan(1.1, 1.5, alpha=0.05, color='green', label='OTM Calls')
    
    ax.set_xlabel('Moneyness (Strike / Spot)', fontsize=12)
    ax.set_ylabel('Implied Volatility (%)', fontsize=12)
    ax.set_title(f'{ticker} Volatility Smile', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Set reasonable x limits
    ax.set_xlim(0.7, 1.3)
    
    plt.tight_layout()
    
    if save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(PLOTS_DIR, f'{ticker}_iv_smile_{timestamp}.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {filepath}")
    
    return fig


def plot_greeks_heatmap(calls: pd.DataFrame, puts: pd.DataFrame,
                         ticker: str, current_price: float,
                         save: bool = True) -> plt.Figure:
    """Create heatmap of Greeks across strikes"""
    setup_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Prepare data - filter to reasonable range
    calls = calls[(calls['strike'] > current_price * 0.8) & 
                  (calls['strike'] < current_price * 1.2)].copy()
    puts = puts[(puts['strike'] > current_price * 0.8) & 
                (puts['strike'] < current_price * 1.2)].copy()
    
    greeks = ['delta', 'gamma', 'theta', 'vega']
    titles = ['Delta', 'Gamma', 'Theta ($/day)', 'Vega ($/1% IV)']
    
    for idx, (greek, title) in enumerate(zip(greeks, titles)):
        ax = axes[idx // 2, idx % 2]
        
        # Combine calls and puts
        x_calls = calls['strike'].values
        y_calls = calls[greek].values if greek in calls.columns else np.zeros(len(calls))
        x_puts = puts['strike'].values
        y_puts = puts[greek].values if greek in puts.columns else np.zeros(len(puts))
        
        ax.bar(x_calls - 1, y_calls, width=2, alpha=0.7, color='#00ff88', label='Calls')
        ax.bar(x_puts + 1, y_puts, width=2, alpha=0.7, color='#ff4444', label='Puts')
        
        ax.axvline(current_price, color='white', linestyle='--', alpha=0.5)
        ax.set_xlabel('Strike')
        ax.set_ylabel(title)
        ax.set_title(title, fontsize=12)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    fig.suptitle(f'{ticker} Greeks Analysis @ ${current_price:.2f}', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(PLOTS_DIR, f'{ticker}_greeks_{timestamp}.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {filepath}")
    
    return fig


def plot_scanner_results(results: list, save: bool = True) -> plt.Figure:
    """Create visualization of scanner results"""
    setup_style()
    
    if not results:
        return None
    
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 3, hspace=0.3, wspace=0.3)
    
    # Extract data
    tickers = [r.ticker for r in results]
    ivs = [r.atm_iv * 100 for r in results]
    skews = [r.skewness for r in results]
    prob_ups = [r.prob_up * 100 for r in results]
    pc_ratios = [r.put_call_ratio for r in results]
    vol_oi = [r.volume_oi_ratio for r in results]
    
    # 1. IV comparison
    ax1 = fig.add_subplot(gs[0, 0])
    colors = plt.cm.RdYlGn_r(np.array(ivs) / max(ivs))
    bars = ax1.barh(tickers, ivs, color=colors)
    ax1.set_xlabel('ATM IV (%)')
    ax1.set_title('Implied Volatility', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # 2. Skewness
    ax2 = fig.add_subplot(gs[0, 1])
    colors = ['#ff4444' if s < 0 else '#00ff88' for s in skews]
    ax2.barh(tickers, skews, color=colors)
    ax2.axvline(0, color='white', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Skewness')
    ax2.set_title('Distribution Skew (- = Bearish)', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # 3. Probability of up move
    ax3 = fig.add_subplot(gs[0, 2])
    colors = plt.cm.RdYlGn(np.array(prob_ups) / 100)
    ax3.barh(tickers, prob_ups, color=colors)
    ax3.axvline(50, color='white', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Probability Up (%)')
    ax3.set_title('Bullish Probability', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Put/Call ratio
    ax4 = fig.add_subplot(gs[1, 0])
    colors = ['#ff4444' if pc > 1 else '#00ff88' for pc in pc_ratios]
    ax4.barh(tickers, pc_ratios, color=colors)
    ax4.axvline(1, color='white', linestyle='--', alpha=0.5, label='Neutral')
    ax4.set_xlabel('Put/Call Ratio')
    ax4.set_title('Put/Call Ratio (>1 = Bearish)', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')
    
    # 5. Volume/OI ratio (unusual activity)
    ax5 = fig.add_subplot(gs[1, 1])
    colors = ['#ffaa00' if v > 2 else '#4488ff' for v in vol_oi]
    ax5.barh(tickers, vol_oi, color=colors)
    ax5.axvline(1, color='white', linestyle='--', alpha=0.5)
    ax5.axvline(2, color='orange', linestyle='--', alpha=0.5, label='Unusual')
    ax5.set_xlabel('Volume / Open Interest')
    ax5.set_title('Unusual Activity (>2x = Alert)', fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='x')
    
    # 6. Summary scatter
    ax6 = fig.add_subplot(gs[1, 2])
    scatter = ax6.scatter(skews, prob_ups, c=ivs, s=np.array(vol_oi)*50,
                          cmap='plasma', alpha=0.7, edgecolors='white')
    
    # Add ticker labels
    for i, ticker in enumerate(tickers):
        ax6.annotate(ticker, (skews[i], prob_ups[i]), fontsize=8,
                     xytext=(5, 5), textcoords='offset points')
    
    ax6.axhline(50, color='white', linestyle='--', alpha=0.3)
    ax6.axvline(0, color='white', linestyle='--', alpha=0.3)
    ax6.set_xlabel('Skewness')
    ax6.set_ylabel('Prob Up (%)')
    ax6.set_title('Market Sentiment Map', fontweight='bold')
    
    plt.colorbar(scatter, ax=ax6, label='ATM IV (%)')
    
    fig.suptitle(f'Options Market Scanner - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                 fontsize=14, fontweight='bold')
    
    if save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(PLOTS_DIR, f'scanner_results_{timestamp}.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {filepath}")
    
    return fig


def plot_forecast_comparison(forecasts: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot comparison of forecasts across tickers"""
    setup_style()
    
    if forecasts.empty:
        return None
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    tickers = forecasts['ticker'].values
    
    # Expected return
    ax1 = axes[0, 0]
    colors = ['#00ff88' if r > 0 else '#ff4444' for r in forecasts['expected_return']]
    ax1.barh(tickers, forecasts['expected_return'], color=colors)
    ax1.axvline(0, color='white', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Expected Return (%)')
    ax1.set_title('Expected Return by Expiration', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # ATM IV
    ax2 = axes[0, 1]
    ax2.barh(tickers, forecasts['atm_iv'], color='#4488ff')
    ax2.set_xlabel('ATM IV (%)')
    ax2.set_title('Implied Volatility', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # Probability up
    ax3 = axes[1, 0]
    colors = plt.cm.RdYlGn(forecasts['prob_up'].values / 100)
    ax3.barh(tickers, forecasts['prob_up'], color=colors)
    ax3.axvline(50, color='white', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Probability Up (%)')
    ax3.set_title('Bullish Probability', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Skewness
    ax4 = axes[1, 1]
    colors = ['#ff4444' if s < 0 else '#00ff88' for s in forecasts['skewness']]
    ax4.barh(tickers, forecasts['skewness'], color=colors)
    ax4.axvline(0, color='white', linestyle='-', alpha=0.3)
    ax4.set_xlabel('Skewness')
    ax4.set_title('Distribution Skew', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')
    
    fig.suptitle('Forecast Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(PLOTS_DIR, f'forecast_comparison_{timestamp}.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {filepath}")
    
    return fig


if __name__ == "__main__":
    # Test visualizations
    from analytics import OptionsAnalyzer
    
    analyzer = OptionsAnalyzer()
    results = analyzer.analyze_ticker("SPY")
    
    if results['implied_distribution']:
        plot_distribution_analysis(
            results['implied_distribution'],
            results['current_price'],
            "SPY",
            results['expiration']
        )
        
        plot_iv_surface(results['iv_surface'], results['current_price'], "SPY")
        
        plot_greeks_heatmap(results['calls'], results['puts'],
                           "SPY", results['current_price'])
    
    plt.show()
