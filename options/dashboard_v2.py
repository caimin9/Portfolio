"""
Professional Terminal Dashboard with Drill-Down Views
Multi-page dashboard with portfolio overview, analytics, and individual stock drill-down
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict

from central_portfolio import get_central_portfolio, CentralPortfolio
from analytics import OptionsAnalyzer
from correlation_analysis import CorrelationAnalyzer
from forecasting import DistributionForecaster
from scanner import OptionsScanner, Watchlist

# Page config
st.set_page_config(
    page_title="Portfolio Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0f;
    }
    .metric-card {
        background-color: #1a1a28;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2a2a38;
    }
    .chart-container {
        background-color: #1a1a28;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #4f46e5;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    # Navigation state
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'portfolio'

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'overview'

    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = None

    if 'expanded_chart' not in st.session_state:
        st.session_state.expanded_chart = None

    if 'lookback_days' not in st.session_state:
        st.session_state.lookback_days = 60

    # Portfolio instance
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = get_central_portfolio()

    # Analytics instances
    if 'options_analyzer' not in st.session_state:
        st.session_state.options_analyzer = OptionsAnalyzer()

    if 'corr_analyzer' not in st.session_state:
        st.session_state.corr_analyzer = CorrelationAnalyzer(window=60)

    if 'forecaster' not in st.session_state:
        st.session_state.forecaster = DistributionForecaster()

    # Watchlist
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = Watchlist()

    if 'scanner' not in st.session_state:
        st.session_state.scanner = OptionsScanner()


# ============================================================================
# PORTFOLIO OVERVIEW PAGE
# ============================================================================

def show_portfolio_overview():
    """Display portfolio overview with pie chart and clickable positions table"""
    st.title("📊 Portfolio Overview")

    portfolio = st.session_state.portfolio
    positions_df = portfolio.get_positions_df()

    if positions_df.empty:
        st.info("📭 No positions. Go to 'Manage Positions' to add some!")
        return

    # Top metrics
    summary = portfolio.get_portfolio_summary()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Value", f"${summary['total_value']:,.0f}")
    col2.metric("Total P&L", f"${summary['total_pnl']:,.0f}",
                delta=f"{summary['total_pnl_pct']:.1f}%")
    col3.metric("Positions", summary['total_positions'])

    # Calculate winners
    winners = len(positions_df[positions_df['pnl'] > 0])
    col4.metric("Winners", f"{winners}/{summary['total_positions']}")

    # Calculate beta
    try:
        analytics = portfolio.analyze_portfolio()
        col5.metric("Portfolio β", f"{analytics.portfolio_beta:.2f}")
    except:
        col5.metric("Portfolio β", "Calculating...")

    st.markdown("---")

    # Main content: Pie chart + Table
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎯 Allocation")
        fig = create_portfolio_pie_chart(positions_df)
        st.plotly_chart(fig, use_container_width=True)

        # Top holdings summary
        st.markdown("### 📈 Top 3 Holdings")
        top3 = positions_df.nlargest(3, 'market_value')
        for _, row in top3.iterrows():
            pct = (row['market_value'] / summary['total_value']) * 100
            st.markdown(f"**{row['ticker']}** - {pct:.1f}%")

    with col2:
        st.markdown("### 💼 Positions")
        show_clickable_positions_table(positions_df)


def create_portfolio_pie_chart(positions_df: pd.DataFrame):
    """Create donut chart showing allocation by dollar value"""
    fig = go.Figure(data=[go.Pie(
        labels=positions_df['ticker'],
        values=positions_df['market_value'],
        hole=0.45,
        marker=dict(
            colors=px.colors.qualitative.Bold,
            line=dict(color='#0a0a0f', width=2)
        ),
        textposition='auto',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Value: $%{value:,.0f}<br>%{percent}<extra></extra>'
    )])

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(26, 26, 40, 0.8)',
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig


def show_clickable_positions_table(positions_df: pd.DataFrame):
    """Display positions with click-to-drill-down functionality"""
    # Table header
    cols = st.columns([2, 1, 1, 1, 1, 1, 1])
    cols[0].markdown("**Ticker**")
    cols[1].markdown("**Type**")
    cols[2].markdown("**Qty**")
    cols[3].markdown("**Entry**")
    cols[4].markdown("**Current**")
    cols[5].markdown("**P&L**")
    cols[6].markdown("**Action**")

    st.markdown("---")

    # Each position row
    for idx, row in positions_df.iterrows():
        cols = st.columns([2, 1, 1, 1, 1, 1, 1])

        cols[0].markdown(f"**{row['ticker']}**")
        cols[1].write(row['type'])
        cols[2].write(str(row['quantity']))
        cols[3].write(f"${row['entry_price']:.2f}")
        cols[4].write(f"${row['current_price']:.2f}")

        pnl_color = "🟢" if row['pnl'] >= 0 else "🔴"
        cols[5].markdown(f"{pnl_color} ${row['pnl']:,.0f}")

        if cols[6].button("🔍", key=f"view_{row['ticker']}_{idx}"):
            st.session_state.selected_ticker = row['ticker']
            st.rerun()


# ============================================================================
# MANAGE POSITIONS PAGE
# ============================================================================

def show_manage_positions():
    """Dedicated page for adding/removing positions"""
    st.title("⚙️ Manage Portfolio Positions")

    portfolio = st.session_state.portfolio

    tab1, tab2 = st.tabs(["➕ Add Position", "🗑️ Remove Positions"])

    with tab1:
        st.markdown("### Add New Position")

        position_type = st.selectbox("Type", ["Stock", "Call Option", "Put Option"])

        col1, col2, col3 = st.columns(3)

        with col1:
            ticker = st.text_input("Ticker Symbol", value="", key="add_ticker").upper()
            quantity = st.number_input("Quantity", min_value=1, value=100, step=1, key="add_qty")

        with col2:
            entry_price = st.number_input("Entry Price ($)", min_value=0.01, value=100.0, step=0.01, key="add_price")

            if position_type != "Stock":
                strike = st.number_input("Strike Price ($)", min_value=0.01, value=100.0, step=0.01, key="add_strike")

        with col3:
            if position_type != "Stock":
                expiration = st.date_input("Expiration Date", key="add_exp")

            notes = st.text_area("Notes (optional)", height=100, key="add_notes")

        # Add button
        if st.button("➕ Add Position", type="primary", use_container_width=True):
            if not ticker:
                st.error("Please enter a ticker symbol")
            else:
                try:
                    if position_type == "Stock":
                        portfolio.add_stock(ticker, quantity, entry_price, notes)
                        st.success(f"✅ Added {quantity} shares of {ticker}")
                    else:
                        opt_type = 'call' if position_type == "Call Option" else 'put'
                        exp_str = expiration.strftime('%Y-%m-%d')
                        portfolio.add_option(ticker, opt_type, quantity, entry_price,
                                            strike, exp_str, notes)
                        st.success(f"✅ Added {quantity} {ticker} {opt_type}s")

                    # Reload and redirect
                    st.rerun()

                except Exception as e:
                    st.error(f"Error adding position: {e}")

    with tab2:
        st.markdown("### Current Positions")

        positions_df = portfolio.get_positions_df()

        if not positions_df.empty:
            # Show positions with remove buttons
            for idx, row in positions_df.iterrows():
                with st.expander(f"{row['ticker']} - {row['type']} - ${row['market_value']:,.0f}"):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**Quantity:** {row['quantity']}")
                        st.write(f"**Entry:** ${row['entry_price']:.2f}")
                        st.write(f"**Current:** ${row['current_price']:.2f}")

                    with col2:
                        st.write(f"**Value:** ${row['market_value']:,.0f}")
                        pnl_emoji = "🟢" if row['pnl'] >= 0 else "🔴"
                        st.write(f"**P&L:** {pnl_emoji} ${row['pnl']:,.0f} ({row['pnl_pct']:+.1f}%)")

                    with col3:
                        if st.button("Remove", key=f"remove_{idx}", type="secondary"):
                            portfolio.remove_position(idx)
                            st.success(f"Removed {row['ticker']}")
                            st.rerun()

            # Clear all button
            st.markdown("---")
            if st.button("🗑️ Clear All Positions", type="secondary"):
                confirm = st.checkbox("⚠️ Confirm clear all")
                if confirm:
                    portfolio.clear()
                    st.success("All positions cleared")
                    st.rerun()
        else:
            st.info("No positions to remove")


# ============================================================================
# STOCK DETAIL DRILL-DOWN PAGE
# ============================================================================

def show_stock_detail(ticker: str):
    """Show detailed analysis for individual stock with 2x3 grid"""
    st.title(f"🔍 {ticker} - Detailed Analysis")

    portfolio = st.session_state.portfolio
    positions_df = portfolio.get_positions_df()

    # Get position
    position_data = positions_df[positions_df['ticker'] == ticker]
    if position_data.empty:
        st.error(f"Position {ticker} not found")
        return

    position = position_data.iloc[0]

    # Back button
    if st.button("← Back to Portfolio"):
        st.session_state.selected_ticker = None
        st.session_state.current_page = 'overview'
        st.rerun()

    # Header - Position Details
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_value = positions_df['market_value'].sum()
    portfolio_weight = (position['market_value'] / total_value) * 100 if total_value > 0 else 0

    col1.metric("Shares", position['quantity'])
    col2.metric("Entry", f"${position['entry_price']:.2f}")
    col3.metric("Current", f"${position['current_price']:.2f}")
    col4.metric("Value", f"${position['market_value']:,.0f}")
    col5.metric("P&L", f"${position['pnl']:,.0f}", delta=f"{position['pnl_pct']:+.1f}%")
    col6.metric("Weight", f"{portfolio_weight:.1f}%")

    st.markdown("---")

    # Check if expanded chart mode
    if st.session_state.expanded_chart:
        show_expanded_chart(ticker, st.session_state.expanded_chart, position)
        if st.button("✕ Close", type="secondary"):
            st.session_state.expanded_chart = None
            st.rerun()
        return

    # 2×3 Grid
    st.markdown("### 📊 Analytics (Click any chart to expand)")

    # ROW 1
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Price History")
        fig = create_price_chart_with_entry(ticker, position['entry_price'])
        st.plotly_chart(fig, use_container_width=True)
        if st.button("🔍 Expand", key="expand_price"):
            st.session_state.expanded_chart = 'price'
            st.rerun()

    with col2:
        st.markdown("#### 📊 Rolling Beta")
        fig = create_stock_beta_chart(ticker)
        st.plotly_chart(fig, use_container_width=True)
        if st.button("🔍 Expand", key="expand_beta"):
            st.session_state.expanded_chart = 'beta'
            st.rerun()

    # ROW 2
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔗 Portfolio Correlation")
        fig = create_correlation_bars(ticker, portfolio)
        st.plotly_chart(fig, use_container_width=True)
        if st.button("🔍 Expand", key="expand_corr"):
            st.session_state.expanded_chart = 'correlation'
            st.rerun()

    with col2:
        st.markdown("#### 📉 Implied Distribution")
        fig = create_distribution_chart(ticker)
        st.plotly_chart(fig, use_container_width=True)
        if st.button("🔍 Expand", key="expand_dist"):
            st.session_state.expanded_chart = 'distribution'
            st.rerun()

    # ROW 3
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ⭐ Analyst Ratings")
        show_analyst_ratings_panel(ticker)

    with col2:
        st.markdown("#### 📊 IV Percentile")
        fig = create_iv_percentile_chart(ticker)
        st.plotly_chart(fig, use_container_width=True)
        if st.button("🔍 Expand", key="expand_iv"):
            st.session_state.expanded_chart = 'iv_percentile'
            st.rerun()

    # Bottom tabs
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Fundamentals", "🏢 Sector Comparison", "📈 Volume Analysis", "📰 News (Future)"])

    with tab1:
        show_fundamentals(ticker)

    with tab2:
        show_sector_comparison(ticker)

    with tab3:
        show_volume_analysis(ticker)

    with tab4:
        st.info("📰 News integration coming soon")
        st.markdown("**Placeholder for:** Latest news, earnings, SEC filings")


def show_expanded_chart(ticker: str, chart_type: str, position):
    """Show full-screen version of selected chart"""
    st.markdown(f"### {ticker} - {chart_type.replace('_', ' ').title()}")

    if chart_type == 'price':
        fig = create_price_chart_detailed(ticker, position['entry_price'])
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == 'beta':
        fig = create_beta_chart_detailed(ticker)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == 'correlation':
        fig = create_correlation_detailed(ticker)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == 'distribution':
        fig = create_distribution_detailed(ticker)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == 'iv_percentile':
        fig = create_iv_detailed(ticker)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# CHART HELPER FUNCTIONS
# ============================================================================

def create_price_chart_with_entry(ticker: str, entry_price: float):
    """Candlestick chart with entry price marked"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1y')

        if hist.empty:
            return create_empty_chart("No price data available")

        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            shared_xaxes=True,
            vertical_spacing=0.03
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Price'
        ), row=1, col=1)

        # Entry price line
        fig.add_hline(
            y=entry_price,
            line_dash="dash",
            line_color="#f59e0b",
            annotation_text=f"Entry: ${entry_price:.2f}",
            annotation_position="right",
            row=1, col=1
        )

        # Moving averages
        hist['MA20'] = hist['Close'].rolling(20).mean()
        hist['MA50'] = hist['Close'].rolling(50).mean()

        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['MA20'],
            name='MA20', line=dict(color='orange', width=1)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['MA50'],
            name='MA50', line=dict(color='purple', width=1)
        ), row=1, col=1)

        # Volume
        colors = ['#10b981' if hist['Close'].iloc[i] >= hist['Open'].iloc[i]
                  else '#ef4444' for i in range(len(hist))]

        fig.add_trace(go.Bar(
            x=hist.index, y=hist['Volume'],
            name='Volume', marker_color=colors, opacity=0.5
        ), row=2, col=1)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading price data: {e}")


def create_price_chart_detailed(ticker: str, entry_price: float):
    """Detailed full-screen price chart"""
    return create_price_chart_with_entry(ticker, entry_price)


def create_stock_beta_chart(ticker: str):
    """Create rolling beta chart for single stock"""
    try:
        corr_analyzer = st.session_state.corr_analyzer
        beta_result = corr_analyzer.rolling_beta(ticker, 'SPY', period='1y', window=60)

        fig = go.Figure()

        # Beta line
        fig.add_trace(go.Scatter(
            x=beta_result.rolling_beta.index,
            y=beta_result.rolling_beta,
            name='Rolling Beta',
            line=dict(color='#6366f1', width=2)
        ))

        # Current beta line
        fig.add_hline(
            y=beta_result.current_beta,
            line_dash="dash",
            line_color="#10b981",
            annotation_text=f"Current β: {beta_result.current_beta:.2f}"
        )

        # Beta = 1 reference
        fig.add_hline(y=1.0, line_dash="dot", line_color="gray", opacity=0.5)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            yaxis_title="Beta vs SPY",
            xaxis_title="Date",
            showlegend=True
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Beta calculation unavailable: {e}")


def create_beta_chart_detailed(ticker: str):
    """Detailed beta chart with more metrics"""
    try:
        corr_analyzer = st.session_state.corr_analyzer
        beta_result = corr_analyzer.rolling_beta(ticker, 'SPY', period='1y', window=60)

        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=['Rolling Beta', 'R² (Correlation Quality)']
        )

        # Beta
        fig.add_trace(go.Scatter(
            x=beta_result.rolling_beta.index,
            y=beta_result.rolling_beta,
            name='Beta',
            line=dict(color='#6366f1', width=2)
        ), row=1, col=1)

        fig.add_hline(y=1.0, line_dash="dot", line_color="gray", row=1, col=1)

        # R²
        fig.add_trace(go.Scatter(
            x=beta_result.rolling_beta.index,
            y=beta_result.r_squared,
            name='R²',
            line=dict(color='#f59e0b', width=2),
            fill='tozeroy'
        ), row=2, col=1)

        fig.update_layout(
            template="plotly_dark",
            height=600,
            showlegend=True
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Error: {e}")


def create_correlation_bars(ticker: str, portfolio: CentralPortfolio):
    """Create bar chart of correlations with other portfolio positions"""
    try:
        corr_analyzer = st.session_state.corr_analyzer
        tickers = portfolio.get_unique_tickers()
        other_tickers = [t for t in tickers if t != ticker]

        if not other_tickers:
            return create_empty_chart("No other positions to correlate")

        correlations = []
        for other in other_tickers:
            try:
                rolling_corr = corr_analyzer.rolling_correlation(ticker, other, period='1y')
                if not rolling_corr.empty:
                    current_corr = rolling_corr.iloc[-1]
                    correlations.append({'ticker': other, 'correlation': current_corr})
            except:
                pass

        if not correlations:
            return create_empty_chart("Unable to calculate correlations")

        corr_df = pd.DataFrame(correlations)

        # Bar chart
        fig = go.Figure(data=[go.Bar(
            x=corr_df['ticker'],
            y=corr_df['correlation'],
            marker_color=['#10b981' if c >= 0 else '#ef4444' for c in corr_df['correlation']]
        )])

        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            yaxis_range=[-1, 1],
            yaxis_title="Correlation",
            xaxis_title="Ticker"
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Error: {e}")


def create_correlation_detailed(ticker: str):
    """Detailed correlation analysis"""
    return create_correlation_bars(ticker, st.session_state.portfolio)


def create_distribution_chart(ticker: str):
    """Create implied distribution chart from options"""
    try:
        analyzer = st.session_state.options_analyzer
        results = analyzer.analyze_ticker(ticker, 0)

        if results['implied_distribution'] is None:
            return create_empty_chart("No options data available")

        dist = results['implied_distribution']

        fig = go.Figure()

        # Distribution curve
        fig.add_trace(go.Scatter(
            x=dist.strikes,
            y=dist.probabilities,
            name='Implied Distribution',
            line=dict(color='#6366f1', width=2),
            fill='tozeroy'
        ))

        # Current price
        fig.add_vline(
            x=dist.current_price,
            line_dash="dash",
            line_color="#10b981",
            annotation_text="Current"
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            height=350,
            xaxis_title="Price ($)",
            yaxis_title="Probability Density",
            showlegend=True
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Distribution unavailable: {e}")


def create_distribution_detailed(ticker: str):
    """Detailed distribution with more metrics"""
    return create_distribution_chart(ticker)


def create_iv_percentile_chart(ticker: str):
    """Show current IV vs historical percentiles"""
    try:
        analyzer = st.session_state.options_analyzer
        results = analyzer.analyze_ticker(ticker, 0)

        if results['implied_distribution']:
            current_iv = results['implied_distribution'].atm_iv

            fig = go.Figure()

            # Gauge chart
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=current_iv * 100,
                title={'text': "ATM IV (%)"},
                delta={'reference': 20, 'suffix': ""},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#6366f1"},
                    'steps': [
                        {'range': [0, 20], 'color': "#10b981"},
                        {'range': [20, 40], 'color': "#3b82f6"},
                        {'range': [40, 60], 'color': "#f59e0b"},
                        {'range': [60, 100], 'color': "#ef4444"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 2},
                        'thickness': 0.75,
                        'value': current_iv * 100
                    }
                }
            ))

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(26, 26, 40, 0.8)',
                height=350,
                margin=dict(l=20, r=20, t=50, b=20)
            )

            return fig

    except:
        pass

    return create_empty_chart("No options data available")


def create_iv_detailed(ticker: str):
    """Detailed IV analysis"""
    return create_iv_percentile_chart(ticker)


def show_analyst_ratings_panel(ticker: str):
    """Display analyst ratings and recommendations"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Key metrics
        col1, col2, col3 = st.columns(3)

        recommendation = info.get('recommendationKey', 'N/A')
        target = info.get('targetMeanPrice', None)
        num_analysts = info.get('numberOfAnalystOpinions', 0)

        # Color code recommendation
        rec_colors = {
            'strong_buy': '🟢',
            'buy': '🟢',
            'hold': '🟡',
            'sell': '🔴',
            'strong_sell': '🔴'
        }
        rec_emoji = rec_colors.get(recommendation, '⚪')

        col1.metric("Consensus", f"{rec_emoji} {recommendation.replace('_', ' ').title()}")
        col2.metric("Price Target", f"${target:.2f}" if target else "N/A")
        col3.metric("Analysts", num_analysts)

        # Upside/downside to target
        if target:
            current = info.get('currentPrice', info.get('regularMarketPrice', 0))
            if current:
                upside = ((target / current) - 1) * 100
                if upside > 10:
                    st.success(f"📈 {upside:+.1f}% upside to target")
                elif upside < -10:
                    st.warning(f"📉 {upside:+.1f}% downside to target")
                else:
                    st.info(f"Target: {upside:+.1f}%")

    except Exception as e:
        st.warning("Analyst data not available")


def show_fundamentals(ticker: str):
    """Show key fundamental metrics"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        col1, col2, col3, col4 = st.columns(4)

        market_cap = info.get('marketCap', 0)
        col1.metric("Market Cap", f"${market_cap/1e9:.1f}B" if market_cap else "N/A")

        pe = info.get('trailingPE', 0)
        col2.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")

        div_yield = info.get('dividendYield', 0)
        col3.metric("Dividend Yield", f"{div_yield*100:.2f}%" if div_yield else "N/A")

        beta = info.get('beta', 0)
        col4.metric("Beta (Stated)", f"{beta:.2f}" if beta else "N/A")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
            st.write(f"**Industry:** {info.get('industry', 'N/A')}")

        with col2:
            high_52w = info.get('fiftyTwoWeekHigh', 0)
            low_52w = info.get('fiftyTwoWeekLow', 0)
            st.write(f"**52W High:** ${high_52w:.2f}" if high_52w else "**52W High:** N/A")
            st.write(f"**52W Low:** ${low_52w:.2f}" if low_52w else "**52W Low:** N/A")

    except Exception as e:
        st.error(f"Error loading fundamentals: {e}")


def show_volume_analysis(ticker: str):
    """Analyze recent volume patterns"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='3mo')

        if hist.empty:
            st.warning("No volume data available")
            return

        # Calculate average volume
        avg_volume = hist['Volume'].rolling(20).mean()
        recent_volume = hist['Volume'].iloc[-1]
        volume_ratio = recent_volume / avg_volume.iloc[-1] if len(avg_volume) > 0 and avg_volume.iloc[-1] > 0 else 1

        col1, col2, col3 = st.columns(3)

        col1.metric("Recent Volume", f"{recent_volume/1e6:.1f}M")
        col2.metric("20D Avg", f"{avg_volume.iloc[-1]/1e6:.1f}M")
        col3.metric("Ratio", f"{volume_ratio:.2f}x")

        if volume_ratio > 2:
            st.warning("🔥 Unusual volume detected (>2x average)")
        elif volume_ratio > 1.5:
            st.info("Elevated volume")
        else:
            st.success("Normal volume")

        # Volume chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            name='Volume',
            marker_color='#6366f1'
        ))

        fig.add_trace(go.Scatter(
            x=hist.index,
            y=avg_volume,
            name='20D Average',
            line=dict(color='#f59e0b', width=2)
        ))

        fig.update_layout(
            template="plotly_dark",
            height=300,
            yaxis_title="Volume",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading volume data: {e}")


def show_sector_comparison(ticker: str):
    """Compare performance vs sector ETF"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', None)

        # Map sectors to ETFs
        sector_etfs = {
            'Technology': 'XLK',
            'Financials': 'XLF',
            'Healthcare': 'XLV',
            'Energy': 'XLE',
            'Consumer Cyclical': 'XLY',
            'Consumer Defensive': 'XLP',
            'Industrials': 'XLI',
            'Real Estate': 'XLRE',
            'Utilities': 'XLU',
            'Communication Services': 'XLC',
            'Basic Materials': 'XLB'
        }

        sector_etf = sector_etfs.get(sector, 'SPY')

        st.write(f"**Sector:** {sector} (ETF: {sector_etf})")

        # Fetch performance data
        stock_hist = stock.history(period='1y')
        sector_hist = yf.Ticker(sector_etf).history(period='1y')

        if stock_hist.empty or sector_hist.empty:
            st.warning("Unable to fetch comparison data")
            return

        # Calculate returns
        stock_return = ((stock_hist['Close'].iloc[-1] / stock_hist['Close'].iloc[0]) - 1) * 100
        sector_return = ((sector_hist['Close'].iloc[-1] / sector_hist['Close'].iloc[0]) - 1) * 100

        relative_strength = stock_return - sector_return

        col1, col2, col3 = st.columns(3)
        col1.metric(f"{ticker} Return", f"{stock_return:+.1f}%")
        col2.metric(f"{sector_etf} Return", f"{sector_return:+.1f}%")
        col3.metric("Relative Strength", f"{relative_strength:+.1f}%",
                    delta="Outperforming" if relative_strength > 5 else ("Underperforming" if relative_strength < -5 else None))

        # Comparison chart - normalize to 100
        stock_norm = (stock_hist['Close'] / stock_hist['Close'].iloc[0]) * 100
        sector_norm = (sector_hist['Close'] / sector_hist['Close'].iloc[0]) * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=stock_hist.index, y=stock_norm,
            name=ticker, line=dict(color='#6366f1', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=sector_hist.index, y=sector_norm,
            name=sector_etf, line=dict(color='#f59e0b', width=2)
        ))

        fig.update_layout(
            template="plotly_dark",
            height=300,
            yaxis_title="Normalized Performance (Base=100)",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading sector data: {e}")


def create_empty_chart(message: str):
    """Create empty chart with message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="#888888")
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(26, 26, 40, 0.8)',
        height=350,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig


# ============================================================================
# PORTFOLIO ANALYTICS PAGE
# ============================================================================

def show_portfolio_analytics():
    """Display portfolio-level analytics"""
    st.title("📊 Portfolio Analytics")

    portfolio = st.session_state.portfolio
    positions_df = portfolio.get_positions_df()

    if positions_df.empty:
        st.info("No positions to analyze")
        return

    # Get analytics
    with st.spinner("Calculating analytics..."):
        analytics = portfolio.analyze_portfolio()

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Portfolio Beta", f"{analytics.portfolio_beta:.2f}")
    col2.metric("Volatility", f"{analytics.portfolio_volatility*100:.1f}%")
    col3.metric("VaR (95%)", f"${analytics.portfolio_var_95:,.0f}")
    col4.metric("Avg Correlation", f"{analytics.avg_correlation:.2f}")

    st.markdown("---")

    # 2x2 grid of charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Rolling Beta by Position")
        fig = create_multi_beta_chart(portfolio)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Correlation Matrix")
        fig = create_correlation_matrix(portfolio)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Portfolio Greeks")
        fig = create_greeks_chart(analytics)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Risk Metrics")
        show_risk_metrics(analytics)

    # Alerts section
    if analytics.alerts:
        st.markdown("---")
        st.markdown("### ⚠️ Alerts")
        for alert in analytics.alerts:
            st.warning(alert)


def create_multi_beta_chart(portfolio: CentralPortfolio):
    """Create chart with beta for each position"""
    try:
        tickers = portfolio.get_unique_tickers()
        corr_analyzer = st.session_state.corr_analyzer

        fig = go.Figure()

        for ticker in tickers:
            try:
                beta_result = corr_analyzer.rolling_beta(ticker, 'SPY', period='1y', window=60)
                fig.add_trace(go.Scatter(
                    x=beta_result.rolling_beta.index,
                    y=beta_result.rolling_beta,
                    name=ticker,
                    mode='lines'
                ))
            except:
                pass

        fig.add_hline(y=1.0, line_dash="dot", line_color="gray", opacity=0.5)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            height=400,
            yaxis_title="Beta vs SPY",
            xaxis_title="Date",
            showlegend=True
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Error: {e}")


def create_correlation_matrix(portfolio: CentralPortfolio):
    """Create correlation heatmap"""
    try:
        tickers = portfolio.get_unique_tickers()

        if len(tickers) < 2:
            return create_empty_chart("Need at least 2 positions")

        corr_analyzer = st.session_state.corr_analyzer
        prices = corr_analyzer.fetch_price_data(tickers, period='1y')
        returns = corr_analyzer.calculate_returns(prices)
        corr_matrix = returns.corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdYlGn',
            zmid=0,
            text=corr_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(26, 26, 40, 0.8)',
            height=400,
            xaxis_title="",
            yaxis_title=""
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Error: {e}")


def create_greeks_chart(analytics):
    """Create bar chart of portfolio Greeks"""
    greeks_data = {
        'Delta': analytics.total_delta,
        'Gamma': analytics.total_gamma,
        'Theta': analytics.total_theta,
        'Vega': analytics.total_vega
    }

    fig = go.Figure(data=[go.Bar(
        x=list(greeks_data.keys()),
        y=list(greeks_data.values()),
        marker_color=['#6366f1', '#10b981', '#ef4444', '#f59e0b']
    )])

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(26, 26, 40, 0.8)',
        height=400,
        yaxis_title="Value",
        showlegend=False
    )

    return fig


def show_risk_metrics(analytics):
    """Display risk metrics"""
    st.metric("Value at Risk (95%)", f"${analytics.portfolio_var_95:,.0f}")
    st.metric("Annualized Volatility", f"{analytics.portfolio_volatility*100:.1f}%")
    st.metric("Diversification Ratio", f"{analytics.diversification_ratio:.2f}")

    st.markdown("---")

    st.metric("Expected Move (1D)", f"${analytics.expected_move_1d:,.0f}")
    st.metric("Expected Move (1W)", f"${analytics.expected_move_1w:,.0f}")
    st.metric("Prob of Profit", f"{analytics.prob_profit*100:.1f}%")


# ============================================================================
# WATCHLIST SCANNER PAGE
# ============================================================================

def show_watchlist_scanner():
    """Display watchlist scanner"""
    st.title("🔍 Watchlist Scanner")

    watchlist = st.session_state.watchlist
    scanner = st.session_state.scanner

    # Watchlist management
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Current Watchlist:**")
        if watchlist.tickers:
            st.write(", ".join(watchlist.tickers))
        else:
            st.write("Empty - add tickers below")

    with col2:
        if st.button("🔍 Scan Now", type="primary"):
            if not watchlist.tickers:
                st.error("Add tickers to watchlist first")
            else:
                with st.spinner("Scanning..."):
                    results = scanner.scan_watchlist(watchlist)
                    st.session_state.scan_results = results
                    st.success(f"Scanned {len(results)} tickers")

    # Manage watchlist
    with st.expander("⚙️ Manage Watchlist"):
        new_ticker = st.text_input("Add ticker").upper()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add to Watchlist") and new_ticker:
                watchlist.add(new_ticker)
                st.success(f"Added {new_ticker}")
                st.rerun()
        with col2:
            if st.button("Clear Watchlist"):
                watchlist.clear()
                st.success("Cleared")
                st.rerun()

    # Show results if available
    if 'scan_results' in st.session_state and st.session_state.scan_results:
        results = st.session_state.scan_results

        st.markdown("---")
        st.markdown("### Scan Results")

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with_alerts = [r for r in results if r.has_alerts]

        col1.metric("Scanned", len(results))
        col2.metric("Alerts", len(with_alerts))

        if results:
            avg_iv = np.mean([r.atm_iv for r in results if r.atm_iv])
            col3.metric("Avg IV", f"{avg_iv*100:.1f}%")

        # Display alerts
        if with_alerts:
            st.markdown("### ⚠️ Opportunities")
            for result in with_alerts:
                with st.expander(f"{result.ticker} - {len(result.alerts)} alerts"):
                    for alert in result.alerts:
                        st.warning(alert)

                    # Quick add button
                    if st.button(f"View {result.ticker} Details", key=f"view_{result.ticker}"):
                        st.info(f"Add {result.ticker} to portfolio first to view details")


# ============================================================================
# MAIN NAVIGATION
# ============================================================================

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    portfolio = st.session_state.portfolio

    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 📊 Terminal")

        mode = st.radio("Mode", ["Portfolio", "Watchlist"])
        st.session_state.view_mode = mode.lower()

        st.markdown("---")

        if mode == "Portfolio":
            if st.session_state.selected_ticker:
                # In drill-down mode
                st.markdown(f"### Viewing: {st.session_state.selected_ticker}")
                if st.button("← Back to Overview"):
                    st.session_state.selected_ticker = None
                    st.rerun()
            else:
                # Normal portfolio navigation
                page = st.radio("Page", ["Overview", "Analytics", "Manage Positions"])
                st.session_state.current_page = page.lower().replace(' ', '_')
        else:
            # Watchlist mode
            st.session_state.current_page = 'watchlist'

        # Global controls
        st.markdown("---")
        st.markdown("### Controls")
        lookback = st.selectbox(
            "Lookback Period",
            [30, 60, 90, 120, 180, 252],
            index=1
        )
        st.session_state.lookback_days = lookback

    # Route to appropriate page
    if st.session_state.selected_ticker:
        show_stock_detail(st.session_state.selected_ticker)
    elif st.session_state.current_page == 'overview':
        show_portfolio_overview()
    elif st.session_state.current_page == 'analytics':
        show_portfolio_analytics()
    elif st.session_state.current_page == 'manage_positions':
        show_manage_positions()
    elif st.session_state.current_page == 'watchlist':
        show_watchlist_scanner()


if __name__ == "__main__":
    main()
