"""
Options Analytics Terminal - Professional Single-Page View
All critical analytics visible at once with live updating charts.

Inspired by Bloomberg Terminal multi-panel layout.
Run with: streamlit run dashboard_terminal.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf

from central_portfolio import get_central_portfolio
from analytics import OptionsAnalyzer
from scanner import OptionsScanner, Watchlist
from correlation_analysis import CorrelationAnalyzer


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Options Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================================
# PROFESSIONAL TERMINAL CSS
# ============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Force everything dark */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
.main, .block-container, * {
    background-color: #0a0a0f !important;
    color: #e0e0e8 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Header bar */
.terminal-header {
    background: linear-gradient(135deg, #1a1a28 0%, #22222f 100%);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid #2d2d3d;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* Control panel */
.control-panel {
    background: #1a1a28;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #2d2d3d;
}

/* Chart container */
.chart-container {
    background: linear-gradient(135deg, #1a1a28 0%, #1f1f2e 100%);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid #2d2d3d;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
    height: 100%;
}

/* Metric cards - compact for header */
[data-testid="stMetric"] {
    background: rgba(99, 102, 241, 0.1);
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

[data-testid="stMetric"] label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9090a8 !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    font-size: 0.85rem;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
    transform: translateY(-1px);
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background: #1a1a28 !important;
    border: 1px solid #2d2d3d !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: #12121a;
    border-radius: 8px;
    padding: 0.25rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 6px;
    color: #9090a8;
    font-weight: 600;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white !important;
}

/* Sidebar (collapsed by default) */
[data-testid="stSidebar"] {
    background: #0d0d14 !important;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Title styling */
h1 {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0 !important;
    letter-spacing: -0.02em;
}

h3 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #c0c0d0 !important;
    margin: 0.5rem 0 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Plotly charts */
.js-plotly-plot {
    border-radius: 8px;
}

/* Expander for settings */
.streamlit-expanderHeader {
    background: #1a1a28 !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    color: #9090a8 !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# INITIALIZE
# ============================================================================

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = get_central_portfolio()

if 'lookback_days' not in st.session_state:
    st.session_state.lookback_days = 60

if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_pnl_timeseries_chart(portfolio, lookback_days=60):
    """Create cumulative P&L time series"""
    # Get portfolio historical data
    tickers = portfolio.get_unique_tickers()

    if not tickers:
        # Empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="Add positions to see P&L timeline",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#9090a8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    # Fetch historical prices
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    # Get position data
    positions_df = portfolio.get_positions_df()

    # Calculate P&L over time (simplified - using stock prices)
    try:
        prices = portfolio.corr_analyzer.fetch_price_data(tickers, period=f'{lookback_days}d')

        # Calculate portfolio value over time
        portfolio_values = []

        for date in prices.index:
            total_value = 0
            for _, pos in positions_df.iterrows():
                if pos['ticker'] in prices.columns:
                    current_price = prices.loc[date, pos['ticker']]

                    if pos['type'] == 'stock':
                        value = current_price * pos['quantity']
                    else:
                        # Simplified for options
                        value = current_price * pos['quantity'] * 100

                    total_value += value

            portfolio_values.append(total_value)

        # Calculate P&L (vs cost basis)
        cost_basis = positions_df['cost_basis'].sum()
        pnl_series = np.array(portfolio_values) - cost_basis

        # Create chart
        fig = go.Figure()

        # P&L line
        fig.add_trace(go.Scatter(
            x=prices.index,
            y=pnl_series,
            mode='lines',
            name='P&L',
            line=dict(color='#6366f1', width=2),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        ))

        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="#9090a8", opacity=0.5)

        # Add current P&L annotation
        if len(pnl_series) > 0:
            current_pnl = pnl_series[-1]
            color = '#10b981' if current_pnl >= 0 else '#ef4444'

            fig.add_annotation(
                x=prices.index[-1],
                y=current_pnl,
                text=f"${current_pnl:,.0f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor=color,
                font=dict(color=color, size=12, family='JetBrains Mono'),
                bgcolor='rgba(26, 26, 40, 0.9)',
                bordercolor=color,
                borderwidth=2
            )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Date",
            yaxis_title="Cumulative P&L ($)",
            showlegend=False,
            hovermode='x unified'
        )

        return fig

    except Exception as e:
        # Fallback empty chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data: {str(e)[:50]}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="#ef4444")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig


def create_rolling_beta_chart(portfolio, lookback_days=60):
    """Create rolling beta chart for portfolio"""
    tickers = portfolio.get_unique_tickers()

    if not tickers:
        fig = go.Figure()
        fig.add_annotation(
            text="Add positions to see portfolio beta",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#9090a8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    try:
        # Get position weights
        positions_df = portfolio.get_positions_df()
        total_value = positions_df['market_value'].sum()

        # Calculate rolling beta for each position
        fig = go.Figure()

        # Market beta line
        fig.add_hline(y=1.0, line_dash="dash", line_color="#9090a8",
                     opacity=0.5, annotation_text="Market β=1.0")

        # Plot beta for largest positions
        for _, pos in positions_df.nlargest(3, 'market_value').iterrows():
            try:
                beta_result = portfolio.corr_analyzer.rolling_beta(
                    pos['ticker'], 'SPY', period=f'{lookback_days*2}d'
                )

                weight = pos['market_value'] / total_value

                fig.add_trace(go.Scatter(
                    x=beta_result.dates,
                    y=beta_result.betas,
                    mode='lines',
                    name=f"{pos['ticker']} ({weight*100:.0f}%)",
                    line=dict(width=2)
                ))
            except:
                pass

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Date",
            yaxis_title="Beta",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=10)
            ),
            hovermode='x unified'
        )

        return fig

    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Loading beta data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="#9090a8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig


def create_rolling_correlation_chart(portfolio, lookback_days=60):
    """Create rolling correlation heatmap"""
    tickers = portfolio.get_unique_tickers()

    if len(tickers) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Add 2+ positions to see correlations",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#9090a8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    try:
        # Get correlation matrix
        corr_analyzer = CorrelationAnalyzer(window=lookback_days)
        corr_matrix = corr_analyzer.rolling_correlation_matrix(tickers, period='1y')

        # Create heatmap
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
            colorbar=dict(
                title="Correlation",
                titleside="right",
                tickmode="linear",
                tick0=-1,
                dtick=0.5
            )
        ))

        # Add average correlation annotation
        avg_corr = corr_matrix.avg_correlation
        color = '#ef4444' if avg_corr > 0.7 else '#f59e0b' if avg_corr > 0.5 else '#10b981'

        fig.add_annotation(
            text=f"Avg: {avg_corr:.2f}",
            xref="paper", yref="paper",
            x=1.15, y=0.5,
            showarrow=False,
            font=dict(size=14, color=color, family='JetBrains Mono'),
            bgcolor='rgba(26, 26, 40, 0.9)',
            bordercolor=color,
            borderwidth=2
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=60, t=40, b=20),
            xaxis={'side': 'bottom'},
            yaxis={'autorange': 'reversed'}
        )

        return fig

    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text="Loading correlation data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="#9090a8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig


def create_forecast_distribution_chart(portfolio):
    """Create implied distribution forecast for largest position"""
    positions_df = portfolio.get_positions_df()

    if positions_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Add positions to see forecasts",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#9090a8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            plot_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    # Get largest position
    largest = positions_df.nlargest(1, 'market_value').iloc[0]
    ticker = largest['ticker']

    try:
        # Get implied distribution
        analyzer = OptionsAnalyzer()
        results = analyzer.analyze_ticker(ticker, 0)

        if results['implied_distribution']:
            dist = results['implied_distribution']
            current_price = results['current_price']

            fig = go.Figure()

            # Distribution bars
            fig.add_trace(go.Bar(
                x=dist.strikes,
                y=dist.density,
                name='Distribution',
                marker_color='rgba(99, 102, 241, 0.7)',
                hovertemplate='Strike: $%{x:.0f}<br>Probability: %{y:.4f}<extra></extra>'
            ))

            # Current price
            fig.add_vline(x=current_price, line_dash="dash", line_color="#10b981",
                         annotation_text=f"Current: ${current_price:.2f}",
                         annotation_position="top")

            # Expected price
            fig.add_vline(x=dist.expected_price, line_dash="dash", line_color="#ef4444",
                         annotation_text=f"Expected: ${dist.expected_price:.2f}",
                         annotation_position="top")

            # 68% range
            lower_1s, upper_1s = dist.expected_move(0.68)
            fig.add_vrect(x0=lower_1s, x1=upper_1s, fillcolor="orange", opacity=0.1,
                         annotation_text="68%", annotation_position="top left")

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(26, 26, 40, 0.8)',
                plot_bgcolor='rgba(26, 26, 40, 0.8)',
                height=350,
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis_title="Strike Price ($)",
                yaxis_title="Probability Density",
                showlegend=False,
                title=f"{ticker} - {results['days_to_exp']} days",
                title_font=dict(size=12)
            )

            return fig
    except:
        pass

    # Fallback
    fig = go.Figure()
    fig.add_annotation(
        text=f"No options data for {ticker}",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=12, color="#9090a8")
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(26, 26, 40, 0.8)',
        plot_bgcolor='rgba(26, 26, 40, 0.8)',
        height=350,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

portfolio = st.session_state.portfolio

# Title and timestamp
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# 📊 OPTIONS ANALYTICS TERMINAL")
with col2:
    st.markdown(f"<div style='text-align: right; color: #9090a8; padding-top: 1rem;'>🕐 {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

st.markdown("---")

# Header - Portfolio Summary
summary = portfolio.get_portfolio_summary()

if summary['total_positions'] > 0:
    # Calculate analytics
    with st.spinner("Calculating analytics..."):
        analytics = portfolio.analyze_portfolio()

    # Top metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Portfolio Value", f"${analytics.total_value:,.0f}")
    with col2:
        st.metric("Total P&L", f"${analytics.total_pnl:,.0f}", delta=f"{analytics.total_pnl_pct:.1f}%")
    with col3:
        st.metric("Beta", f"{analytics.portfolio_beta:.2f}")
    with col4:
        st.metric("Volatility", f"{analytics.portfolio_volatility*100:.1f}%")
    with col5:
        st.metric("Correlation", f"{analytics.avg_correlation:.2f}")
    with col6:
        st.metric("Positions", summary['total_positions'])

    # Alerts
    if analytics.alerts:
        st.markdown("### ⚠️ Active Alerts")
        cols = st.columns(len(analytics.alerts))
        for idx, alert in enumerate(analytics.alerts):
            with cols[idx]:
                st.warning(alert)

    st.markdown("---")

    # Control Panel
    with st.expander("⚙️ Controls", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            lookback = st.selectbox(
                "Lookback Period",
                options=[30, 60, 90, 120, 180, 252],
                index=1,
                format_func=lambda x: f"{x} days (~{x//21} months)"
            )
            st.session_state.lookback_days = lookback

        with col2:
            if st.button("🔄 Refresh Data", type="primary"):
                st.session_state.refresh_counter += 1
                st.rerun()

        with col3:
            if st.button("➕ Manage Positions"):
                st.info("Add/remove positions in sidebar")

    # Main Charts Grid (2x2)
    st.markdown("### 📈 Live Analytics")

    # Top row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cumulative P&L")
        fig_pnl = create_pnl_timeseries_chart(portfolio, st.session_state.lookback_days)
        st.plotly_chart(fig_pnl, use_container_width=True, key="pnl_chart")

    with col2:
        st.markdown(f"#### Rolling Beta ({st.session_state.lookback_days}d)")
        fig_beta = create_rolling_beta_chart(portfolio, st.session_state.lookback_days)
        st.plotly_chart(fig_beta, use_container_width=True, key="beta_chart")

    # Bottom row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### Correlation Matrix ({st.session_state.lookback_days}d)")
        fig_corr = create_rolling_correlation_chart(portfolio, st.session_state.lookback_days)
        st.plotly_chart(fig_corr, use_container_width=True, key="corr_chart")

    with col2:
        st.markdown("#### Price Forecast (Largest Position)")
        fig_forecast = create_forecast_distribution_chart(portfolio)
        st.plotly_chart(fig_forecast, use_container_width=True, key="forecast_chart")

    # Additional scrollable sections
    st.markdown("---")
    st.markdown("### 📊 Additional Analytics")

    tab1, tab2, tab3 = st.tabs(["Greeks", "Positions", "Risk Metrics"])

    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Delta", f"{analytics.total_delta:.2f}")
        col2.metric("Gamma", f"{analytics.total_gamma:.4f}")
        col3.metric("Theta", f"${analytics.total_theta:.2f}/day")
        col4.metric("Vega", f"${analytics.total_vega:.2f}")

    with tab2:
        positions_df = portfolio.get_positions_df()
        st.dataframe(
            positions_df[['ticker', 'type', 'quantity', 'current_price', 'market_value', 'pnl', 'pnl_pct']],
            use_container_width=True,
            height=300
        )

    with tab3:
        col1, col2, col3 = st.columns(3)
        col1.metric("VaR (95%)", f"${analytics.portfolio_var_95:,.0f}")
        col2.metric("Expected Move (1D)", f"${analytics.expected_move_1d:,.0f}")
        col3.metric("Diversification Ratio", f"{analytics.diversification_ratio:.2f}")

else:
    # Empty portfolio message
    st.info("👋 **No positions yet!** Add positions using the sidebar to see live analytics.")

    with st.expander("➕ Quick Add Position"):
        col1, col2, col3 = st.columns(3)

        with col1:
            ticker = st.text_input("Ticker", value="AAPL").upper()
            quantity = st.number_input("Quantity", min_value=1, value=100)

        with col2:
            entry_price = st.number_input("Entry Price", min_value=0.01, value=150.0)
            position_type = st.selectbox("Type", ["Stock", "Call", "Put"])

        with col3:
            if st.button("Add Position", type="primary"):
                if position_type == "Stock":
                    portfolio.add_stock(ticker, quantity, entry_price)
                st.success(f"Added {ticker}!")
                st.rerun()


# Sidebar for position management (collapsed by default)
with st.sidebar:
    st.markdown("## Position Management")

    if portfolio.portfolio.positions:
        st.markdown("### Current Positions")

        for idx, pos in enumerate(portfolio.portfolio.positions):
            with st.expander(f"{pos.ticker} - {pos.position_type}"):
                st.write(f"Quantity: {pos.quantity}")
                st.write(f"Entry: ${pos.entry_price:.2f}")

                if st.button(f"Remove", key=f"remove_{idx}"):
                    portfolio.remove_position(idx)
                    st.rerun()

    st.markdown("---")

    st.markdown("### Quick Add")
    new_ticker = st.text_input("Ticker", key="sidebar_ticker").upper()
    new_qty = st.number_input("Qty", min_value=1, value=100, key="sidebar_qty")
    new_price = st.number_input("Price", min_value=0.01, value=100.0, key="sidebar_price")

    if st.button("Add Stock", key="sidebar_add"):
        if new_ticker:
            portfolio.add_stock(new_ticker, new_qty, new_price)
            st.rerun()


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6366f1; font-size: 0.9rem; font-weight: 600;'>
    Options Analytics Terminal • Built with Breeden-Litzenberger & Real-Time Greeks
</div>
""", unsafe_allow_html=True)
