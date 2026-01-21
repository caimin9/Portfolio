"""
Example Usage of Options Analytics System
Demonstrates the key features including new notification system.
"""

# ============================================================================
# EXAMPLE 1: Single Ticker Analysis with Breeden-Litzenberger
# ============================================================================

def example_single_ticker():
    """Analyze a single ticker's options chain"""
    from analytics import analyze_options

    print("=" * 70)
    print("EXAMPLE 1: Single Ticker Analysis")
    print("=" * 70)

    ticker = "SPY"
    results = analyze_options(ticker)

    print(f"\nAnalyzing {ticker}...")
    print(f"Current Price: ${results['current_price']:.2f}")
    print(f"Expiration: {results['expiration']} ({results['days_to_exp']} days)")

    if results['implied_distribution']:
        dist = results['implied_distribution']
        summary = results['summary']

        print(f"\n--- Implied Distribution ---")
        print(f"Expected Price: ${dist.expected_price:.2f}")
        print(f"Expected Move: ±${dist.std_dev:.2f} (±{summary['expected_move_pct']:.1f}%)")
        print(f"ATM IV: {dist.atm_iv*100:.1f}%")
        print(f"Skewness: {dist.skewness:.3f} {'(Bearish)' if dist.skewness < 0 else '(Bullish)'}")
        print(f"Excess Kurtosis: {dist.kurtosis:.3f}")

        # Probability calculations
        lower_1s, upper_1s = dist.expected_move(0.68)
        print(f"\n68% Range: ${lower_1s:.2f} - ${upper_1s:.2f}")
        print(f"Prob above current: {summary['prob_above_current']*100:.1f}%")

        # Target probabilities
        print(f"\n--- Target Probabilities ---")
        for pct in [5, 10, 15]:
            target_up = results['current_price'] * (1 + pct/100)
            target_down = results['current_price'] * (1 - pct/100)
            prob_up = dist.probability_above(target_up)
            prob_down = dist.probability_below(target_down)
            print(f"+{pct}% (${target_up:.0f}): {prob_up*100:.1f}% | -{pct}% (${target_down:.0f}): {prob_down*100:.1f}%")


# ============================================================================
# EXAMPLE 2: Portfolio Management with Real-Time Option Pricing
# ============================================================================

def example_portfolio():
    """Demonstrate portfolio management with real option pricing"""
    from portfolio import Portfolio
    from analytics import OptionsAnalyzer

    print("\n" + "=" * 70)
    print("EXAMPLE 2: Portfolio Management (Real-Time Option Pricing)")
    print("=" * 70)

    portfolio = Portfolio()

    # Clear any existing positions
    portfolio.clear()

    # Add stock positions
    portfolio.add_stock('SPY', 100, 450.00, 'Core holding')
    portfolio.add_stock('QQQ', 50, 380.00, 'Tech exposure')

    # Add option positions (will fetch real-time prices)
    portfolio.add_option('AAPL', 'call', 2, 3.50, 180, '2026-02-20', 'Bullish play')

    print(f"\nPortfolio: {len(portfolio.positions)} positions")

    # Calculate P&L with real option prices
    print("\n--- Position P&L (with real-time option pricing) ---")
    pnl_df = portfolio.calculate_pnl()
    print(pnl_df[['ticker', 'type', 'quantity', 'entry_price', 'current_price',
                   'pnl', 'pnl_pct']].to_string(index=False))

    # Portfolio summary
    summary = portfolio.summary()
    print(f"\n--- Portfolio Summary ---")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.1f}%)")

    # Portfolio Greeks
    analyzer = OptionsAnalyzer()
    try:
        greeks = portfolio.get_portfolio_greeks(analyzer)
        print(f"\n--- Portfolio Greeks ---")
        print(f"Delta: {greeks['delta']:.2f}")
        print(f"Gamma: {greeks['gamma']:.4f}")
        print(f"Theta: ${greeks['theta']:.2f}/day")
        print(f"Vega: ${greeks['vega']:.2f}/1% IV")
    except:
        print("\n(Greeks calculation skipped - requires matching option data)")


# ============================================================================
# EXAMPLE 3: Market Scanner with Notifications
# ============================================================================

def example_scanner():
    """Scan watchlist and send notifications for unusual activity"""
    from scanner import OptionsScanner, Watchlist

    print("\n" + "=" * 70)
    print("EXAMPLE 3: Market Scanner with Notifications")
    print("=" * 70)

    # Create/load watchlist
    watchlist = Watchlist()

    # Add some tickers to watch
    for ticker in ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']:
        if ticker not in watchlist.tickers:
            watchlist.add(ticker)

    print(f"\nWatchlist: {', '.join(watchlist.tickers)}")

    # Create scanner
    scanner = OptionsScanner()

    print("\nScanning watchlist...")
    print("(Set send_notifications=True to enable alerts)\n")

    # Scan without notifications (set to True to enable)
    results = scanner.scan_watchlist(watchlist, send_notifications=False)

    # Display results
    print(f"\n--- Scan Results ---")
    for result in results:
        if result.has_alerts:
            print(f"\n⚠️ {result.ticker} @ ${result.current_price:.2f}")
            print(f"   ATM IV: {result.atm_iv*100:.1f}% | P/C: {result.put_call_ratio:.2f}")
            print(f"   Alerts:")
            for alert in result.alerts:
                print(f"     • {alert}")

    # Top movers
    movers = scanner.get_top_movers(results, n=3)

    print("\n--- Top Movers ---")
    print("Highest IV:")
    for item in movers.get('highest_iv', []):
        print(f"  {item['ticker']}: {item['atm_iv']*100:.1f}%")

    print("\nMost Bullish:")
    for item in movers.get('most_bullish', []):
        print(f"  {item['ticker']}: {item['prob_up']*100:.0f}% up probability")


# ============================================================================
# EXAMPLE 4: Forecasting with Monte Carlo
# ============================================================================

def example_forecasting():
    """Generate price forecasts using implied distributions"""
    from forecasting import DistributionForecaster

    print("\n" + "=" * 70)
    print("EXAMPLE 4: Price Forecasting")
    print("=" * 70)

    ticker = "AAPL"
    forecaster = DistributionForecaster()

    print(f"\nGenerating forecast for {ticker}...")

    # Distribution-based forecast
    forecast = forecaster.forecast_from_distribution(ticker)

    if forecast:
        print(forecast.summary())

        # Monte Carlo simulation
        print("\n--- Monte Carlo Simulation (30 days, 10k paths) ---")
        mc_results = forecaster.monte_carlo_forecast(ticker, days=30, num_simulations=10000)

        print(f"Current: ${mc_results['current_price']:.2f}")
        print(f"Expected (MC): ${mc_results['expected']:.2f}")
        print(f"Prob Up: {mc_results['prob_up']*100:.1f}%")

        print("\nPercentiles:")
        for pct, value in mc_results['percentiles'].items():
            print(f"  {pct}th: ${value:.2f}")


# ============================================================================
# EXAMPLE 5: Testing Notifications
# ============================================================================

def example_notifications():
    """Test the notification system"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Testing Notifications")
    print("=" * 70)

    print("\nTo test notifications:")
    print("1. Configure config.py with your email/Discord settings")
    print("2. Run: python notifications.py")
    print("3. Check your email and Discord for test alerts")

    print("\nEmail Setup (Gmail):")
    print("  1. Enable 2FA on Google account")
    print("  2. Generate app password: https://myaccount.google.com/apppasswords")
    print("  3. Update config.py:")
    print("     EMAIL_ENABLED = True")
    print("     EMAIL_FROM = 'your@gmail.com'")
    print("     EMAIL_PASSWORD = 'your_app_password'")
    print("     EMAIL_TO = 'alerts@example.com'")

    print("\nDiscord Setup:")
    print("  1. Create webhook in Discord server settings")
    print("  2. Copy webhook URL")
    print("  3. Update config.py:")
    print("     DISCORD_ENABLED = True")
    print("     DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...'")

    print("\nFor detailed instructions, see: SETUP_NOTIFICATIONS.md")


# ============================================================================
# EXAMPLE 6: Complete Workflow
# ============================================================================

def example_complete_workflow():
    """Demonstrate a complete analysis workflow"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Complete Analysis Workflow")
    print("=" * 70)

    ticker = "TSLA"

    # 1. Quick analysis
    print(f"\n1. Quick Analysis of {ticker}")
    from analytics import analyze_options
    results = analyze_options(ticker)

    if results['implied_distribution']:
        dist = results['implied_distribution']
        print(f"   Expected Move: ±{dist.std_dev/results['current_price']*100:.1f}%")
        print(f"   Skewness: {dist.skewness:.2f} {'📉 Bearish' if dist.skewness < 0 else '📈 Bullish'}")

    # 2. Check unusual activity
    print(f"\n2. Scanning for Unusual Activity")
    from scanner import OptionsScanner
    scanner = OptionsScanner()
    scan_result = scanner.scan_ticker(ticker)

    if scan_result and scan_result.has_alerts:
        print(f"   ⚠️ Found {len(scan_result.alerts)} alerts:")
        for alert in scan_result.alerts[:3]:
            print(f"      • {alert}")
    else:
        print(f"   ✓ No unusual activity detected")

    # 3. Generate forecast
    print(f"\n3. Price Forecast")
    from forecasting import DistributionForecaster
    forecaster = DistributionForecaster()
    forecast = forecaster.forecast_from_distribution(ticker)

    if forecast:
        exp_return = (forecast.expected_price / forecast.current_price - 1) * 100
        print(f"   Expected Return: {exp_return:+.1f}%")
        print(f"   68% Range: ${forecast.range_68[0]:.0f} - ${forecast.range_68[1]:.0f}")
        print(f"   Prob Profit (long): {forecast.prob_profit_long*100:.0f}%")

    print("\n✅ Complete workflow executed!")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys

    # Run all examples
    try:
        example_single_ticker()
        example_portfolio()
        example_scanner()
        example_forecasting()
        example_notifications()
        example_complete_workflow()

        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Configure notifications (see SETUP_NOTIFICATIONS.md)")
        print("2. Run dashboard: streamlit run dashboard.py")
        print("3. Customize watchlist in config.py")
        print("4. Add your portfolio positions")
        print("\nFor full system overview, see: IMPROVEMENTS_SUMMARY.md")

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure all required packages are installed:")
        print("  pip install yfinance numpy pandas scipy matplotlib plotly streamlit requests")
        sys.exit(1)
