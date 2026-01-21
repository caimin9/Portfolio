"""
Options Analytics Dashboard
Streamlit-based dashboard for portfolio monitoring, options analysis, and scanning.

Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf

# Import our modules
from analytics import OptionsAnalyzer, ImpliedDistribution
from portfolio import Portfolio
from scanner import OptionsScanner, Watchlist, ScanResult
from forecasting import DistributionForecaster
from correlation_analysis import CorrelationAnalyzer, CorrelationVisualizer
from config import DASHBOARD_REFRESH_SECONDS


# Page config
st.set_page_config(
    page_title="Options Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
    }
    .alert-box {
        background-color: #ff4b4b20;
        border-left: 4px solid #ff4b4b;
        padding: 10px;
        margin: 10px 0;
    }
    .bullish {
        color: #00cc00;
    }
    .bearish {
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = OptionsAnalyzer()
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = Watchlist()
if 'scanner' not in st.session_state:
    st.session_state.scanner = OptionsScanner()
if 'forecaster' not in st.session_state:
    st.session_state.forecaster = DistributionForecaster()


def plot_implied_distribution(dist: ImpliedDistribution, current_price: float, 
                               ticker: str) -> go.Figure:
    """Create plotly figure for implied distribution"""
    fig = go.Figure()
    
    # Distribution bars
    fig.add_trace(go.Bar(
        x=dist.strikes,
        y=dist.density,
        name='Implied Distribution',
        marker_color='steelblue',
        opacity=0.7
    ))
    
    # Current price line
    fig.add_vline(x=current_price, line_dash="dash", line_color="green",
                  annotation_text=f"Current: ${current_price:.2f}")
    
    # Expected price line
    fig.add_vline(x=dist.expected_price, line_dash="dash", line_color="red",
                  annotation_text=f"Expected: ${dist.expected_price:.2f}")
    
    # 1 sigma range
    lower_1s, upper_1s = dist.expected_move(0.68)
    fig.add_vrect(x0=lower_1s, x1=upper_1s, fillcolor="orange", opacity=0.1,
                  annotation_text="68% range")
    
    fig.update_layout(
        title=f"{ticker} Implied Price Distribution",
        xaxis_title="Strike Price ($)",
        yaxis_title="Probability Density",
        template="plotly_dark",
        height=400
    )
    
    return fig


def plot_iv_smile(iv_surface: pd.DataFrame, current_price: float) -> go.Figure:
    """Plot IV smile/skew"""
    fig = go.Figure()
    
    calls = iv_surface[iv_surface['type'] == 'call']
    puts = iv_surface[iv_surface['type'] == 'put']
    
    fig.add_trace(go.Scatter(
        x=calls['moneyness'],
        y=calls['impliedVolatility'] * 100,
        mode='lines+markers',
        name='Calls',
        line=dict(color='green')
    ))
    
    fig.add_trace(go.Scatter(
        x=puts['moneyness'],
        y=puts['impliedVolatility'] * 100,
        mode='lines+markers',
        name='Puts',
        line=dict(color='red')
    ))
    
    fig.add_vline(x=1.0, line_dash="dash", line_color="white",
                  annotation_text="ATM")
    
    fig.update_layout(
        title="Volatility Smile",
        xaxis_title="Moneyness (Strike/Spot)",
        yaxis_title="Implied Volatility (%)",
        template="plotly_dark",
        height=350
    )
    
    return fig


def plot_price_history(ticker: str, period: str = '1y') -> go.Figure:
    """Plot price history with volume"""
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    
    if hist.empty:
        return go.Figure()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=[0.7, 0.3])
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='Price'
    ), row=1, col=1)
    
    # Moving averages
    if len(hist) >= 20:
        ma20 = hist['Close'].rolling(20).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=ma20, name='MA20',
                                 line=dict(color='orange', width=1)), row=1, col=1)
    
    if len(hist) >= 50:
        ma50 = hist['Close'].rolling(50).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=ma50, name='MA50',
                                 line=dict(color='purple', width=1)), row=1, col=1)
    
    # Volume
    colors = ['green' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else 'red'
              for i in range(len(hist))]
    fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume',
                         marker_color=colors, opacity=0.5), row=2, col=1)
    
    fig.update_layout(
        title=f"{ticker} Price History",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    return fig


def plot_monte_carlo(mc_results: dict) -> go.Figure:
    """Plot Monte Carlo simulation paths"""
    fig = go.Figure()
    
    paths = mc_results['paths']
    n_paths_to_show = min(100, paths.shape[0])
    
    # Plot sample paths
    for i in range(n_paths_to_show):
        fig.add_trace(go.Scatter(
            y=paths[i],
            mode='lines',
            line=dict(width=0.5, color='lightblue'),
            opacity=0.3,
            showlegend=False
        ))
    
    # Add percentile lines
    for pct in [5, 50, 95]:
        pct_path = np.percentile(paths, pct, axis=0)
        fig.add_trace(go.Scatter(
            y=pct_path,
            mode='lines',
            name=f'{pct}th percentile',
            line=dict(width=2)
        ))
    
    # Current price
    fig.add_hline(y=mc_results['current_price'], line_dash="dash",
                  annotation_text="Current Price")
    
    fig.update_layout(
        title=f"Monte Carlo Simulation ({mc_results['num_simulations']} paths)",
        xaxis_title="Days",
        yaxis_title="Price ($)",
        template="plotly_dark",
        height=400
    )
    
    return fig


# Sidebar navigation
st.sidebar.title("📊 Options Analytics")
page = st.sidebar.radio("Navigate", [
    "🎯 Single Ticker Analysis",
    "📈 Portfolio Monitor",
    "🔍 Market Scanner",
    "🔮 Forecasting",
    "📊 Correlations & Beta",
    "⚙️ Settings"
])


# ============ SINGLE TICKER ANALYSIS ============
if page == "🎯 Single Ticker Analysis":
    st.title("Options Chain Analysis")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input("Ticker Symbol", value="SPY").upper()
    
    with col2:
        # Get available expirations
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            exp_date = st.selectbox("Expiration", expirations) if expirations else None
        except:
            exp_date = None
            st.warning("Could not fetch expirations")
    
    with col3:
        analyze_btn = st.button("Analyze", type="primary")
    
    if analyze_btn and ticker and exp_date:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                exp_index = list(expirations).index(exp_date)
                results = st.session_state.analyzer.analyze_ticker(ticker, exp_index)
                
                # Top metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                col1.metric("Price", f"${results['current_price']:.2f}")
                col2.metric("Days to Exp", results['days_to_exp'])
                
                if results['implied_distribution']:
                    dist = results['implied_distribution']
                    summary = results['summary']
                    
                    col3.metric("ATM IV", f"{dist.atm_iv*100:.1f}%")
                    col4.metric("Expected Move", f"±{summary['expected_move_pct']:.1f}%")
                    col5.metric("P/C Ratio", f"{summary['put_call_ratio']:.2f}")
                    
                    # Distribution plot
                    st.subheader("Implied Price Distribution")
                    fig_dist = plot_implied_distribution(dist, results['current_price'], ticker)
                    st.plotly_chart(fig_dist, use_container_width=True)
                    
                    # Probability boxes
                    st.subheader("Probability Analysis")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.info(f"**Prob Above Current:** {summary['prob_above_current']*100:.1f}%")
                    with col2:
                        st.info(f"**1σ Range:** ${summary['range_1sigma'][0]:.2f} - ${summary['range_1sigma'][1]:.2f}")
                    with col3:
                        st.info(f"**2σ Range:** ${summary['range_2sigma'][0]:.2f} - ${summary['range_2sigma'][1]:.2f}")
                    
                    # Distribution stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Skewness", f"{dist.skewness:.3f}",
                                 help="Negative = bearish skew, Positive = bullish skew")
                    with col2:
                        st.metric("Excess Kurtosis", f"{dist.kurtosis:.3f}",
                                 help="Higher = fat tails, more extreme move probability")
                
                # IV Smile
                st.subheader("Volatility Smile")
                fig_smile = plot_iv_smile(results['iv_surface'], results['current_price'])
                st.plotly_chart(fig_smile, use_container_width=True)
                
                # Price history
                st.subheader("Price History")
                fig_price = plot_price_history(ticker)
                st.plotly_chart(fig_price, use_container_width=True)
                
                # Options chain tables
                st.subheader("Options Chain")
                tab1, tab2 = st.tabs(["Calls", "Puts"])
                
                with tab1:
                    calls_display = results['calls'][['strike', 'lastPrice', 'bid', 'ask', 
                                                       'volume', 'openInterest', 'impliedVolatility',
                                                       'delta', 'gamma', 'theta', 'vega']].copy()
                    calls_display['impliedVolatility'] = (calls_display['impliedVolatility'] * 100).round(1)
                    st.dataframe(calls_display, use_container_width=True)
                
                with tab2:
                    puts_display = results['puts'][['strike', 'lastPrice', 'bid', 'ask',
                                                     'volume', 'openInterest', 'impliedVolatility',
                                                     'delta', 'gamma', 'theta', 'vega']].copy()
                    puts_display['impliedVolatility'] = (puts_display['impliedVolatility'] * 100).round(1)
                    st.dataframe(puts_display, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error analyzing {ticker}: {e}")


# ============ PORTFOLIO MONITOR ============
elif page == "📈 Portfolio Monitor":
    st.title("Portfolio Monitor")
    
    portfolio = st.session_state.portfolio
    
    # Add position form
    with st.expander("➕ Add Position"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_ticker = st.text_input("Ticker", key="new_ticker").upper()
            pos_type = st.selectbox("Type", ["stock", "call", "put"])
        
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=100)
            entry_price = st.number_input("Entry Price", min_value=0.01, value=100.0)
        
        with col3:
            if pos_type in ['call', 'put']:
                strike = st.number_input("Strike", min_value=0.01, value=100.0)
                exp = st.text_input("Expiration (YYYY-MM-DD)")
            else:
                strike = None
                exp = None
            
            notes = st.text_input("Notes")
        
        if st.button("Add Position"):
            if new_ticker:
                if pos_type == 'stock':
                    portfolio.add_stock(new_ticker, quantity, entry_price, notes)
                else:
                    portfolio.add_option(new_ticker, pos_type, quantity, entry_price,
                                        strike, exp, notes)
                st.success(f"Added {new_ticker} position!")
                st.rerun()
    
    # Portfolio summary
    if portfolio.positions:
        summary = portfolio.summary()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Positions", summary['total_positions'])
        col2.metric("Total Value", f"${summary['total_value']:,.2f}")
        col3.metric("Total P&L", f"${summary['total_pnl']:,.2f}",
                   delta=f"{summary['total_pnl_pct']:.1f}%")
        col4.metric("Win Rate", f"{summary['winners']}/{summary['total_positions']}")
        
        # P&L table
        st.subheader("Positions")
        pnl_df = portfolio.calculate_pnl()
        
        # Style P&L
        def color_pnl(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'white'
            return f'color: {color}'
        
        styled_df = pnl_df.style.applymap(color_pnl, subset=['pnl', 'pnl_pct'])
        st.dataframe(pnl_df, use_container_width=True)
        
        # Portfolio Greeks
        st.subheader("Portfolio Greeks")
        try:
            greeks = portfolio.get_portfolio_greeks(st.session_state.analyzer)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Delta", f"{greeks['delta']:.2f}")
            col2.metric("Gamma", f"{greeks['gamma']:.4f}")
            col3.metric("Theta", f"${greeks['theta']:.2f}/day")
            col4.metric("Vega", f"${greeks['vega']:.2f}/1% IV")
        except Exception as e:
            st.warning(f"Could not calculate Greeks: {e}")
        
        # Clear portfolio button
        if st.button("Clear All Positions", type="secondary"):
            portfolio.clear()
            st.rerun()
    else:
        st.info("No positions in portfolio. Add some above!")


# ============ MARKET SCANNER ============
elif page == "🔍 Market Scanner":
    st.title("Options Market Scanner")
    
    watchlist = st.session_state.watchlist
    scanner = st.session_state.scanner
    
    # Watchlist management
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("**Current Watchlist:**", ", ".join(watchlist.tickers))
    
    with col2:
        new_ticker = st.text_input("Add to watchlist", key="wl_add")
        if st.button("Add") and new_ticker:
            watchlist.add(new_ticker.upper())
            st.rerun()
    
    # Scan button
    if st.button("🔍 Scan Watchlist", type="primary"):
        with st.spinner("Scanning market..."):
            results = scanner.scan_watchlist(watchlist)
            st.session_state.scan_results = results
    
    # Display results
    if 'scan_results' in st.session_state and st.session_state.scan_results:
        results = st.session_state.scan_results
        
        # Summary
        with_alerts = [r for r in results if r.has_alerts]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tickers Scanned", len(results))
        col2.metric("With Alerts", len(with_alerts))
        col3.metric("Avg ATM IV", f"{np.mean([r.atm_iv for r in results])*100:.1f}%")
        
        # Alerts section
        if with_alerts:
            st.subheader("⚠️ Alerts")
            for result in with_alerts:
                with st.expander(f"**{result.ticker}** - {len(result.alerts)} alerts"):
                    for alert in result.alerts:
                        st.warning(alert)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"Price: ${result.current_price:.2f}")
                    col2.write(f"ATM IV: {result.atm_iv*100:.1f}%")
                    col3.write(f"P/C Ratio: {result.put_call_ratio:.2f}")
        
        # Results table
        st.subheader("Scan Results")
        
        df = pd.DataFrame([{
            'Ticker': r.ticker,
            'Price': f"${r.current_price:.2f}",
            'ATM IV': f"{r.atm_iv*100:.1f}%",
            'Exp Move': f"±{r.expected_move_pct:.1f}%",
            'P/C Ratio': f"{r.put_call_ratio:.2f}",
            'Prob Up': f"{r.prob_up*100:.0f}%",
            'Skew': f"{r.skewness:.2f}",
            'Vol/OI': f"{r.volume_oi_ratio:.2f}x",
            'Alerts': len(r.alerts)
        } for r in results])
        
        st.dataframe(df, use_container_width=True)
        
        # Top movers
        movers = scanner.get_top_movers(results)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Highest IV")
            for item in movers.get('highest_iv', []):
                st.write(f"**{item['ticker']}**: {item['atm_iv']*100:.1f}%")
        
        with col2:
            st.subheader("📈 Most Bullish")
            for item in movers.get('most_bullish', []):
                st.write(f"**{item['ticker']}**: {item['prob_up']*100:.0f}% up prob")


# ============ FORECASTING ============
elif page == "🔮 Forecasting":
    st.title("Price Forecasting")
    
    forecaster = st.session_state.forecaster
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input("Ticker", value="SPY", key="fc_ticker").upper()
    
    with col2:
        forecast_days = st.number_input("Forecast Days", min_value=1, max_value=90, value=30)
    
    with col3:
        run_forecast = st.button("Generate Forecast", type="primary")
    
    if run_forecast and ticker:
        with st.spinner("Generating forecast..."):
            # Distribution-based forecast
            forecast = forecaster.forecast_from_distribution(ticker)
            
            if forecast:
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                exp_return = (forecast.expected_price / forecast.current_price - 1) * 100
                
                col1.metric("Current", f"${forecast.current_price:.2f}")
                col2.metric("Expected", f"${forecast.expected_price:.2f}",
                           delta=f"{exp_return:+.1f}%")
                col3.metric("Prob Up", f"{forecast.prob_profit_long*100:.1f}%")
                col4.metric("ATM IV", f"{forecast.atm_iv*100:.1f}%")
                
                # Probability ranges
                st.subheader("Expected Ranges")
                
                range_data = {
                    'Confidence': ['50%', '68% (1σ)', '95% (2σ)', '99%'],
                    'Lower': [forecast.range_50[0], forecast.range_68[0],
                             forecast.range_95[0], forecast.range_99[0]],
                    'Upper': [forecast.range_50[1], forecast.range_68[1],
                             forecast.range_95[1], forecast.range_99[1]]
                }
                range_df = pd.DataFrame(range_data)
                range_df['Lower'] = range_df['Lower'].apply(lambda x: f"${x:.2f}")
                range_df['Upper'] = range_df['Upper'].apply(lambda x: f"${x:.2f}")
                
                st.table(range_df)
                
                # Target probabilities
                st.subheader("Target Probabilities")
                
                target_df = pd.DataFrame([
                    {'Move': f"{pct:+d}%", 'Price': f"${forecast.current_price * (1 + pct/100):.2f}",
                     'Probability': f"{prob*100:.1f}%"}
                    for pct, prob in forecast.target_probs.items()
                ])
                st.table(target_df)
            
            # Monte Carlo simulation
            st.subheader("Monte Carlo Simulation")
            mc_results = forecaster.monte_carlo_forecast(ticker, forecast_days)
            
            if mc_results:
                fig_mc = plot_monte_carlo(mc_results)
                st.plotly_chart(fig_mc, use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("MC Expected", f"${mc_results['expected']:.2f}")
                col2.metric("MC Prob Up", f"{mc_results['prob_up']*100:.1f}%")
                col3.metric("Std Dev", f"${mc_results['std_dev']:.2f}")
    
    # Multi-ticker comparison
    st.subheader("Compare Tickers")
    
    compare_tickers = st.text_input("Enter tickers (comma-separated)", 
                                     value="SPY, QQQ, AAPL, MSFT, NVDA")
    
    if st.button("Compare"):
        tickers = [t.strip().upper() for t in compare_tickers.split(",")]
        
        with st.spinner("Comparing..."):
            comparison = forecaster.compare_forecasts(tickers)
            
            if not comparison.empty:
                st.dataframe(comparison, use_container_width=True)


# ============ CORRELATIONS & BETA ============
elif page == "📊 Correlations & Beta":
    st.title("Correlation & Beta Analysis")

    # Initialize session state for correlation analyzer
    if 'corr_analyzer' not in st.session_state:
        st.session_state.corr_analyzer = CorrelationAnalyzer(window=60)

    analyzer = st.session_state.corr_analyzer

    # Analysis type tabs
    tab1, tab2, tab3 = st.tabs(["Rolling Correlation", "Rolling Beta", "Portfolio Correlations"])

    # ========== TAB 1: ROLLING CORRELATION ==========
    with tab1:
        st.subheader("Pairwise Rolling Correlation")

        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            ticker1 = st.text_input("Ticker 1", value="AAPL", key="corr_t1").upper()
        with col2:
            ticker2 = st.text_input("Ticker 2", value="MSFT", key="corr_t2").upper()
        with col3:
            window = st.number_input("Window (days)", min_value=10, max_value=252, value=60, key="corr_window")
        with col4:
            calc_corr = st.button("Calculate", type="primary", key="calc_corr_btn")

        if calc_corr and ticker1 and ticker2:
            with st.spinner(f"Calculating rolling correlation for {ticker1} vs {ticker2}..."):
                try:
                    analyzer.window = window
                    rolling_corr = analyzer.rolling_correlation(ticker1, ticker2, period='2y')

                    # Store in session state
                    st.session_state.rolling_corr_data = {
                        'ticker1': ticker1,
                        'ticker2': ticker2,
                        'corr': rolling_corr
                    }

                except Exception as e:
                    st.error(f"Error: {e}")

        # Display results if available
        if 'rolling_corr_data' in st.session_state:
            data = st.session_state.rolling_corr_data
            rolling_corr = data['corr']

            # Metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Current", f"{rolling_corr.iloc[-1]:.3f}")
            col2.metric("Mean", f"{rolling_corr.mean():.3f}")
            col3.metric("Std Dev", f"{rolling_corr.std():.3f}")
            col4.metric("Min", f"{rolling_corr.min():.3f}")
            col5.metric("Max", f"{rolling_corr.max():.3f}")

            # Plot using plotly
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=rolling_corr.index,
                y=rolling_corr.values,
                mode='lines',
                name='Rolling Correlation',
                line=dict(color='steelblue', width=2)
            ))

            # Add mean line
            fig.add_hline(y=rolling_corr.mean(), line_dash="dash",
                         line_color="green", annotation_text=f"Mean: {rolling_corr.mean():.3f}")

            # Add std bands
            fig.add_hline(y=rolling_corr.mean() + rolling_corr.std(),
                         line_dash="dot", line_color="orange", opacity=0.5)
            fig.add_hline(y=rolling_corr.mean() - rolling_corr.std(),
                         line_dash="dot", line_color="orange", opacity=0.5)

            # Zero line
            fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)

            fig.update_layout(
                title=f"Rolling {window}-Day Correlation: {data['ticker1']} vs {data['ticker2']}",
                xaxis_title="Date",
                yaxis_title="Correlation",
                template="plotly_dark",
                height=500,
                yaxis_range=[-1, 1]
            )

            st.plotly_chart(fig, use_container_width=True)

            # Regime analysis
            st.subheader("Correlation Regime")
            current = rolling_corr.iloc[-1]

            if current > 0.7:
                st.success(f"🟢 **HIGH POSITIVE** correlation ({current:.3f}) - Assets moving together")
            elif current > 0.3:
                st.info(f"🔵 **MODERATE POSITIVE** correlation ({current:.3f})")
            elif current > -0.3:
                st.warning(f"🟡 **LOW/NEUTRAL** correlation ({current:.3f}) - Good diversification")
            elif current > -0.7:
                st.info(f"🔵 **MODERATE NEGATIVE** correlation ({current:.3f})")
            else:
                st.error(f"🔴 **HIGH NEGATIVE** correlation ({current:.3f}) - Assets moving opposite")

    # ========== TAB 2: ROLLING BETA ==========
    with tab2:
        st.subheader("Rolling Beta Analysis")

        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            beta_ticker = st.text_input("Asset Ticker", value="TSLA", key="beta_ticker").upper()
        with col2:
            benchmark = st.text_input("Benchmark", value="SPY", key="benchmark").upper()
        with col3:
            beta_window = st.number_input("Window (days)", min_value=10, max_value=252, value=60, key="beta_window")
        with col4:
            calc_beta = st.button("Calculate", type="primary", key="calc_beta_btn")

        if calc_beta and beta_ticker and benchmark:
            with st.spinner(f"Calculating rolling beta for {beta_ticker} vs {benchmark}..."):
                try:
                    analyzer.window = beta_window
                    beta_result = analyzer.rolling_beta(beta_ticker, benchmark, period='2y')

                    st.session_state.beta_data = beta_result

                except Exception as e:
                    st.error(f"Error: {e}")

        # Display results if available
        if 'beta_data' in st.session_state:
            beta_result = st.session_state.beta_data

            # Key metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            regime = beta_result.get_regime()
            regime_colors = {'HIGH': '🔴', 'LOW': '🔵', 'NORMAL': '🟢'}

            col1.metric("Current Beta", f"{beta_result.current_beta:.3f}",
                       help=f"Regime: {regime}")
            col2.metric("Average Beta", f"{beta_result.avg_beta:.3f}")
            col3.metric("Beta Std Dev", f"{beta_result.beta_std:.3f}")
            col4.metric("Current Alpha", f"{beta_result.alphas[-1] * 252 * 100:.2f}%",
                       help="Annualized excess return")
            col5.metric("R²", f"{beta_result.r_squared[-1]:.3f}",
                       help="Explanatory power of benchmark")

            st.info(f"{regime_colors[regime]} **Beta Regime: {regime}** - "
                   f"{'Higher than normal systematic risk' if regime == 'HIGH' else 'Lower than normal systematic risk' if regime == 'LOW' else 'Normal systematic risk'}")

            # Create subplots for beta, alpha, and R²
            from plotly.subplots import make_subplots

            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=('Rolling Beta', 'Rolling Alpha (Annualized %)', 'R² (Explanatory Power)'),
                row_heights=[0.4, 0.3, 0.3]
            )

            # Beta plot
            fig.add_trace(go.Scatter(
                x=beta_result.dates,
                y=beta_result.betas,
                mode='lines',
                name='Beta',
                line=dict(color='steelblue', width=2)
            ), row=1, col=1)

            fig.add_hline(y=beta_result.avg_beta, line_dash="dash",
                         line_color="green", row=1, col=1,
                         annotation_text=f"Mean: {beta_result.avg_beta:.3f}")

            fig.add_hline(y=1.0, line_dash="solid",
                         line_color="gray", opacity=0.3, row=1, col=1,
                         annotation_text="Market Beta")

            # Alpha plot
            fig.add_trace(go.Scatter(
                x=beta_result.dates,
                y=beta_result.alphas * 252 * 100,  # Annualized %
                mode='lines',
                name='Alpha',
                line=dict(color='purple', width=2)
            ), row=2, col=1)

            fig.add_hline(y=0, line_dash="solid",
                         line_color="gray", opacity=0.3, row=2, col=1)

            # R² plot
            fig.add_trace(go.Scatter(
                x=beta_result.dates,
                y=beta_result.r_squared,
                mode='lines',
                name='R²',
                line=dict(color='orange', width=2)
            ), row=3, col=1)

            fig.add_hline(y=0.5, line_dash="dash",
                         line_color="gray", opacity=0.3, row=3, col=1,
                         annotation_text="50%")

            fig.update_xaxes(title_text="Date", row=3, col=1)
            fig.update_yaxes(title_text="Beta", row=1, col=1)
            fig.update_yaxes(title_text="Alpha (%)", row=2, col=1)
            fig.update_yaxes(title_text="R²", range=[0, 1], row=3, col=1)

            fig.update_layout(
                height=800,
                template="plotly_dark",
                showlegend=False,
                title_text=f"Rolling Beta Analysis: {beta_result.ticker} vs {beta_result.benchmark}"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Interpretation
            st.subheader("Interpretation")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Beta Interpretation:**")
                if beta_result.current_beta > 1.5:
                    st.write("- 🔴 Very high volatility relative to market")
                    st.write("- Amplified gains AND losses")
                elif beta_result.current_beta > 1.0:
                    st.write("- 🟠 Higher volatility than market")
                    st.write("- Moves more than benchmark")
                elif beta_result.current_beta > 0.5:
                    st.write("- 🟢 Lower volatility than market")
                    st.write("- More defensive")
                else:
                    st.write("- 🔵 Much lower volatility than market")
                    st.write("- Very defensive")

            with col2:
                st.write("**Alpha Interpretation:**")
                current_alpha = beta_result.alphas[-1] * 252 * 100
                if current_alpha > 5:
                    st.write(f"- 🟢 Strong positive alpha ({current_alpha:.1f}%)")
                    st.write("- Outperforming benchmark")
                elif current_alpha > 0:
                    st.write(f"- 🟢 Positive alpha ({current_alpha:.1f}%)")
                elif current_alpha > -5:
                    st.write(f"- 🔴 Negative alpha ({current_alpha:.1f}%)")
                else:
                    st.write(f"- 🔴 Strong negative alpha ({current_alpha:.1f}%)")
                    st.write("- Underperforming benchmark")

    # ========== TAB 3: PORTFOLIO CORRELATIONS ==========
    with tab3:
        st.subheader("Portfolio Correlation Matrix")

        # Ticker input
        tickers_input = st.text_area(
            "Enter tickers (one per line or comma-separated)",
            value="SPY\nQQQ\nAAPL\nMSFT\nNVDA",
            height=100,
            key="portfolio_tickers"
        )

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            portfolio_window = st.number_input("Window (days)", min_value=10, max_value=252, value=60, key="portfolio_window")
        with col2:
            calc_portfolio = st.button("Calculate Matrix", type="primary", key="calc_portfolio_btn")

        if calc_portfolio and tickers_input:
            # Parse tickers
            tickers = [t.strip().upper() for t in tickers_input.replace(',', '\n').split('\n') if t.strip()]

            if len(tickers) < 2:
                st.error("Please enter at least 2 tickers")
            else:
                with st.spinner(f"Calculating correlation matrix for {len(tickers)} tickers..."):
                    try:
                        analyzer.window = portfolio_window
                        corr_matrix = analyzer.rolling_correlation_matrix(tickers, period='2y')

                        st.session_state.corr_matrix_data = corr_matrix

                    except Exception as e:
                        st.error(f"Error: {e}")

        # Display results if available
        if 'corr_matrix_data' in st.session_state:
            corr_matrix = st.session_state.corr_matrix_data

            st.metric("Average Correlation", f"{corr_matrix.avg_correlation:.3f}",
                     help="Mean pairwise correlation across all assets")

            # Correlation heatmap
            st.subheader("Current Correlation Matrix")

            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.correlation_matrix.values,
                x=corr_matrix.tickers,
                y=corr_matrix.tickers,
                colorscale='RdYlGn',
                zmid=0,
                zmin=-1,
                zmax=1,
                text=corr_matrix.correlation_matrix.values,
                texttemplate='%{text:.2f}',
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))

            fig.update_layout(
                title="Correlation Heatmap",
                template="plotly_dark",
                height=600,
                xaxis={'side': 'bottom'},
                yaxis={'autorange': 'reversed'}
            )

            st.plotly_chart(fig, use_container_width=True)

            # High correlation pairs
            high_corr_pairs = corr_matrix.get_pairs_by_correlation(0.7)

            if high_corr_pairs:
                st.subheader("⚠️ High Correlation Pairs (|r| > 0.7)")
                st.write("These pairs move very similarly - consider reducing overlap for better diversification:")

                for t1, t2, corr in high_corr_pairs:
                    sentiment = "🟢" if corr > 0 else "🔴"
                    st.write(f"{sentiment} **{t1}** ↔ **{t2}**: {corr:.3f}")
            else:
                st.success("✓ No high correlation pairs found - good diversification!")

            # Diversification score
            st.subheader("Diversification Score")

            if corr_matrix.avg_correlation < 0.3:
                st.success(f"🟢 **Excellent diversification** (avg correlation: {corr_matrix.avg_correlation:.3f})")
            elif corr_matrix.avg_correlation < 0.5:
                st.info(f"🟡 **Good diversification** (avg correlation: {corr_matrix.avg_correlation:.3f})")
            elif corr_matrix.avg_correlation < 0.7:
                st.warning(f"🟠 **Moderate diversification** (avg correlation: {corr_matrix.avg_correlation:.3f})")
            else:
                st.error(f"🔴 **Poor diversification** (avg correlation: {corr_matrix.avg_correlation:.3f})")


# ============ SETTINGS ============
elif page == "⚙️ Settings":
    st.title("Settings")
    
    st.subheader("Alert Thresholds")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Unusual Volume Threshold", value=2.0,
                       help="Alert when Volume/OI exceeds this ratio")
        st.number_input("IV Percentile Alert", value=80,
                       help="Alert when IV above this percentile")
    
    with col2:
        st.number_input("Put/Call Ratio Alert", value=1.5,
                       help="Alert when P/C ratio exceeds this")
        st.number_input("Dashboard Refresh (seconds)", value=60)
    
    st.subheader("Watchlist")
    
    watchlist = st.session_state.watchlist
    
    # Edit watchlist
    new_watchlist = st.text_area("Edit Watchlist (one ticker per line)",
                                  value="\n".join(watchlist.tickers))
    
    if st.button("Save Watchlist"):
        watchlist.tickers = [t.strip().upper() for t in new_watchlist.split("\n") if t.strip()]
        watchlist.save()
        st.success("Watchlist saved!")
    
    st.subheader("Data")
    
    if st.button("Clear Portfolio"):
        st.session_state.portfolio.clear()
        st.success("Portfolio cleared!")
    
    if st.button("Reset Watchlist to Default"):
        st.session_state.watchlist.tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA']
        st.session_state.watchlist.save()
        st.success("Watchlist reset!")


# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.caption("Options Analytics Dashboard v1.0")
