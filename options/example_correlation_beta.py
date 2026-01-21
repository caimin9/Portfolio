"""
Example Usage: Rolling Correlations and Beta Analysis
Demonstrates correlation and systematic risk analysis.
"""

from correlation_analysis import (
    CorrelationAnalyzer,
    CorrelationVisualizer,
    quick_correlation,
    quick_beta,
    analyze_portfolio_correlations
)
import matplotlib.pyplot as plt


# ============================================================================
# EXAMPLE 1: Rolling Correlation Between Two Stocks
# ============================================================================

def example_rolling_correlation():
    """Analyze how correlation between two stocks changes over time"""
    print("=" * 70)
    print("EXAMPLE 1: Rolling Correlation Analysis")
    print("=" * 70)

    # Compare two tech stocks
    ticker1 = "AAPL"
    ticker2 = "MSFT"

    print(f"\nAnalyzing correlation between {ticker1} and {ticker2}...")

    # Quick correlation with auto-plotting
    rolling_corr = quick_correlation(ticker1, ticker2, window=60, period='2y', plot=True)

    # Interpretation
    current = rolling_corr.iloc[-1]
    mean = rolling_corr.mean()

    print(f"\n--- Interpretation ---")
    if current > 0.7:
        print(f"⚠️ HIGH positive correlation ({current:.3f})")
        print("   Assets move very similarly - limited diversification benefit")
    elif current > 0.3:
        print(f"✓ MODERATE positive correlation ({current:.3f})")
        print("   Assets tend to move together but with some independence")
    elif current > -0.3:
        print(f"✓✓ LOW correlation ({current:.3f})")
        print("   Good diversification - assets move relatively independently")
    else:
        print(f"✓✓✓ NEGATIVE correlation ({current:.3f})")
        print("   Excellent diversification - assets move in opposite directions")

    if abs(current - mean) > 0.3:
        direction = "increased" if current > mean else "decreased"
        print(f"\n⚠️ Correlation has {direction} significantly from historical mean")
        print(f"   This could indicate a regime change")


# ============================================================================
# EXAMPLE 2: Rolling Beta Analysis
# ============================================================================

def example_rolling_beta():
    """Analyze systematic risk (beta) of a stock relative to market"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Rolling Beta Analysis")
    print("=" * 70)

    # Analyze Tesla vs S&P 500
    ticker = "TSLA"
    benchmark = "SPY"

    print(f"\nAnalyzing beta for {ticker} vs {benchmark}...")

    # Quick beta with auto-plotting
    beta_result = quick_beta(ticker, benchmark, window=60, period='2y', plot=True)

    # Interpretation
    print(f"\n--- What This Means ---")

    beta = beta_result.current_beta
    alpha = beta_result.alphas[-1] * 252 * 100  # Annualized %
    r_squared = beta_result.r_squared[-1]

    print(f"\nBeta = {beta:.3f}")
    if beta > 1.5:
        print("   🔴 VERY HIGH volatility")
        print("   - If market rises 1%, stock tends to rise ~{:.1f}%".format(beta))
        print("   - If market falls 1%, stock tends to fall ~{:.1f}%".format(beta))
        print("   - High risk, high potential reward")
    elif beta > 1.0:
        print("   🟠 HIGHER than market volatility")
        print("   - More aggressive than market")
        print("   - Amplified gains and losses")
    elif beta > 0.5:
        print("   🟢 LOWER than market volatility")
        print("   - More defensive than market")
        print("   - Dampened swings")
    else:
        print("   🔵 VERY LOW volatility")
        print("   - Much less volatile than market")
        print("   - Very defensive position")

    print(f"\nAlpha = {alpha:.2f}%")
    if alpha > 5:
        print("   🟢 STRONG outperformance vs benchmark")
    elif alpha > 0:
        print("   🟢 Outperforming benchmark (positive alpha)")
    elif alpha > -5:
        print("   🔴 Underperforming benchmark (negative alpha)")
    else:
        print("   🔴 STRONG underperformance vs benchmark")

    print(f"\nR² = {r_squared:.3f}")
    if r_squared > 0.7:
        print(f"   {r_squared*100:.0f}% of price movement explained by market")
        print("   - Highly correlated to market")
    elif r_squared > 0.4:
        print(f"   {r_squared*100:.0f}% of price movement explained by market")
        print("   - Moderate market correlation")
    else:
        print(f"   {r_squared*100:.0f}% of price movement explained by market")
        print("   - More idiosyncratic (company-specific) risk")

    # Beta regime
    regime = beta_result.get_regime()
    print(f"\nCurrent Beta Regime: {regime}")
    if regime == "HIGH":
        print("   ⚠️ Beta is higher than normal - increased systematic risk")
    elif regime == "LOW":
        print("   ✓ Beta is lower than normal - reduced systematic risk")
    else:
        print("   ✓ Beta is in normal range")


# ============================================================================
# EXAMPLE 3: Portfolio Correlation Matrix
# ============================================================================

def example_portfolio_correlations():
    """Analyze correlations across entire portfolio"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Portfolio Correlation Matrix")
    print("=" * 70)

    # Tech-heavy portfolio
    portfolio = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'GOOGL']

    print(f"\nAnalyzing correlations for {len(portfolio)} assets...")

    # Analyze correlations
    corr_matrix = analyze_portfolio_correlations(portfolio, window=60, period='2y', plot=True)

    print(f"\n--- Diversification Analysis ---")

    if corr_matrix.avg_correlation < 0.3:
        print("✓✓✓ EXCELLENT diversification")
        print("    Assets move relatively independently")
    elif corr_matrix.avg_correlation < 0.5:
        print("✓✓ GOOD diversification")
        print("    Reasonable independence between assets")
    elif corr_matrix.avg_correlation < 0.7:
        print("✓ MODERATE diversification")
        print("    Some clustering - consider more diverse assets")
    else:
        print("⚠️ POOR diversification")
        print("    Assets are highly correlated - limited hedging")

    # Check for specific issues
    high_corr = corr_matrix.get_pairs_by_correlation(0.7)
    if high_corr:
        print(f"\n⚠️ Found {len(high_corr)} highly correlated pairs:")
        for t1, t2, corr in high_corr[:5]:  # Show top 5
            print(f"   {t1} ↔ {t2}: {corr:.3f}")
        print("\n   Consider: Replace one from each pair with uncorrelated assets")


# ============================================================================
# EXAMPLE 4: Diversification Metrics
# ============================================================================

def example_diversification_metrics():
    """Calculate portfolio diversification metrics"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Portfolio Diversification Metrics")
    print("=" * 70)

    analyzer = CorrelationAnalyzer(window=60)

    # Portfolio with weights
    tickers = ['SPY', 'TLT', 'GLD', 'VNQ']  # Stocks, Bonds, Gold, Real Estate
    weights = [0.5, 0.3, 0.1, 0.1]  # 50% stocks, 30% bonds, 10% gold, 10% RE

    print(f"\nAnalyzing diversified portfolio:")
    for ticker, weight in zip(tickers, weights):
        print(f"  {ticker}: {weight*100:.0f}%")

    try:
        metrics = analyzer.analyze_portfolio_diversification(
            tickers, weights, period='2y'
        )

        print(f"\n--- Diversification Metrics ---")
        print(f"Average Correlation: {metrics['avg_correlation']:.3f}")
        print(f"Weighted Avg Correlation: {metrics['weighted_avg_correlation']:.3f}")
        print(f"Diversification Ratio: {metrics['diversification_ratio']:.3f}")
        print(f"   (Higher is better - max is √n where n = number of assets)")
        print(f"Portfolio Volatility (annual): {metrics['portfolio_vol_annual']*100:.1f}%")

        print("\n--- Interpretation ---")
        if metrics['diversification_ratio'] > 1.5:
            print("✓✓✓ Excellent diversification")
        elif metrics['diversification_ratio'] > 1.2:
            print("✓✓ Good diversification")
        else:
            print("✓ Moderate diversification")

        if metrics['high_correlation_pairs']:
            print(f"\n⚠️ High correlation pairs detected:")
            for t1, t2, corr in metrics['high_correlation_pairs']:
                print(f"   {t1} ↔ {t2}: {corr:.3f}")

    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# EXAMPLE 5: Correlation Regime Change Detection
# ============================================================================

def example_regime_change():
    """Detect when correlations break down or strengthen"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Correlation Regime Change Detection")
    print("=" * 70)

    analyzer = CorrelationAnalyzer(window=60)

    ticker1 = "SPY"
    ticker2 = "TLT"  # Treasury bonds - should be negatively correlated

    print(f"\nDetecting regime changes in {ticker1} vs {ticker2} correlation...")

    try:
        changes = analyzer.detect_correlation_regime_change(
            ticker1, ticker2, period='2y', threshold=0.3
        )

        if changes:
            print(f"\nFound {len(changes)} significant regime changes:")
            for change in changes[-5:]:  # Show last 5
                date = change['date'].strftime('%Y-%m-%d')
                print(f"\n{date}:")
                print(f"  Correlation: {change['from_corr']:.3f} → {change['to_corr']:.3f}")
                print(f"  Change: {change['change']:+.3f}")
                print(f"  Regime: {change['regime'].upper()}")

                if change['regime'] == 'breakdown':
                    print("  ⚠️ Correlation weakened - diversification improved")
                else:
                    print("  ⚠️ Correlation strengthened - diversification reduced")
        else:
            print("✓ No major regime changes detected - stable correlation")

    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# EXAMPLE 6: Sector Rotation Analysis
# ============================================================================

def example_sector_rotation():
    """Analyze correlations between sector ETFs"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Sector Rotation Analysis")
    print("=" * 70)

    # Sector ETFs
    sectors = {
        'XLK': 'Technology',
        'XLF': 'Financials',
        'XLE': 'Energy',
        'XLV': 'Healthcare',
        'XLY': 'Consumer Discretionary',
        'XLP': 'Consumer Staples'
    }

    tickers = list(sectors.keys())

    print("\nAnalyzing sector correlations...")
    for ticker, name in sectors.items():
        print(f"  {ticker}: {name}")

    try:
        analyzer = CorrelationAnalyzer(window=60)
        corr_matrix = analyzer.rolling_correlation_matrix(tickers, period='2y')

        print(f"\n--- Current Sector Correlations ---")
        print(corr_matrix.correlation_matrix.round(2))

        # Find least correlated sectors
        min_corr = 1.0
        min_pair = None

        n = len(tickers)
        for i in range(n):
            for j in range(i+1, n):
                corr = corr_matrix.correlation_matrix.iloc[i, j]
                if corr < min_corr:
                    min_corr = corr
                    min_pair = (tickers[i], tickers[j])

        if min_pair:
            print(f"\n✓ Best diversification pair:")
            print(f"  {min_pair[0]} ({sectors[min_pair[0]]}) ↔ "
                  f"{min_pair[1]} ({sectors[min_pair[1]]})")
            print(f"  Correlation: {min_corr:.3f}")

    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# EXAMPLE 7: Hedge Effectiveness
# ============================================================================

def example_hedge_effectiveness():
    """Analyze how effective a hedge is using correlation and beta"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Hedge Effectiveness Analysis")
    print("=" * 70)

    position = "SPY"  # Long position
    hedge = "SH"      # Short S&P 500 ETF (inverse)

    print(f"\nLong Position: {position}")
    print(f"Hedge: {hedge}")

    analyzer = CorrelationAnalyzer(window=60)

    try:
        # Check correlation
        print("\n--- Correlation Analysis ---")
        rolling_corr = analyzer.rolling_correlation(position, hedge, period='1y')

        current_corr = rolling_corr.iloc[-1]
        print(f"Current Correlation: {current_corr:.3f}")

        if current_corr < -0.7:
            print("✓✓✓ EXCELLENT hedge - strong negative correlation")
            print("    Hedge should protect well during downturn")
        elif current_corr < -0.5:
            print("✓✓ GOOD hedge - moderate negative correlation")
        elif current_corr < -0.3:
            print("✓ MODERATE hedge")
        else:
            print("⚠️ POOR hedge - weak/positive correlation")
            print("    Consider alternative hedging instruments")

        # Check hedge beta
        print("\n--- Hedge Beta Analysis ---")
        beta_result = analyzer.rolling_beta(hedge, position, period='1y')

        hedge_beta = beta_result.current_beta
        print(f"Hedge Beta: {hedge_beta:.3f}")

        if hedge_beta < -0.9:
            print("✓ Near-perfect inverse relationship")
            print(f"  For every 1% drop in {position}, {hedge} gains ~{abs(hedge_beta):.1f}%")
        elif hedge_beta < -0.7:
            print("✓ Good inverse relationship")
        else:
            print("⚠️ Weak inverse relationship")

    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys

    try:
        # Run examples
        example_rolling_correlation()
        example_rolling_beta()
        example_portfolio_correlations()
        example_diversification_metrics()
        example_regime_change()
        example_sector_rotation()
        example_hedge_effectiveness()

        print("\n" + "=" * 70)
        print("All correlation & beta examples completed!")
        print("=" * 70)
        print("\nCheck the plots/ folder for visualizations")
        print("\nNext steps:")
        print("1. Run dashboard: streamlit run dashboard.py")
        print("2. Go to 'Correlations & Beta' page")
        print("3. Analyze your portfolio correlations")
        print("4. Monitor beta regimes for your holdings")

        # Show plots
        plt.show()

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure required packages are installed:")
        print("  pip install yfinance numpy pandas scipy matplotlib seaborn")
        import traceback
        traceback.print_exc()
        sys.exit(1)
