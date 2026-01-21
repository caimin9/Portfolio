"""
Modern Options Analytics Dashboard
Professional Bloomberg-inspired UI with centralized portfolio management.

Design inspired by:
- Bloomberg Terminal (multi-panel, professional black interface)
- 2026 Financial Dashboard Trends (dark themes, neon accents, modular design)
- TailAdmin & Modern Fintech UIs

Run with: streamlit run dashboard_modern.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf

# Import modules
from central_portfolio import get_central_portfolio, PortfolioAnalytics
from analytics import OptionsAnalyzer
from scanner import OptionsScanner, Watchlist
from forecasting import DistributionForecaster
from correlation_analysis import CorrelationAnalyzer


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Options Analytics Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)


# ============================================================================
# CUSTOM CSS - BLOOMBERG-INSPIRED PROFESSIONAL DESIGN
# ============================================================================

def load_custom_css():
    st.markdown("""
    <style>
    /* Import Professional Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Force Dark Theme on Everything */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background: #0a0a0f !important;
        color: #e0e0e8 !important;
    }

    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Main Background - Deep Professional Black */
    .main, .block-container {
        background: linear-gradient(135deg, #0a0a0f 0%, #12121a 100%) !important;
        color: #e0e0e8 !important;
    }

    /* Force all text to be light colored */
    p, span, div, label {
        color: #e0e0e8 !important;
    }

    /* Sidebar - Elegant Dark */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d14 0%, #1a1a24 100%) !important;
        border-right: 1px solid #2d2d3d !important;
    }

    [data-testid="stSidebar"] .element-container {
        padding: 0.5rem 1rem !important;
    }

    [data-testid="stSidebar"] * {
        color: #e0e0e8 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e0e0e8 !important;
    }

    /* Sidebar widgets */
    [data-testid="stSidebar"] .stMetric {
        background: #1a1a28 !important;
    }

    /* Headers - Professional Typography */
    h1 {
        font-weight: 700;
        font-size: 2.5rem !important;
        color: #ffffff;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
    }

    h2 {
        font-weight: 600;
        font-size: 1.75rem !important;
        color: #ffffff;
        letter-spacing: -0.01em;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        padding-bottom: 0.5rem;
    }

    h3 {
        font-weight: 600;
        font-size: 1.25rem !important;
        color: #c0c0d0;
        margin-bottom: 0.75rem !important;
    }

    /* Premium Metric Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a28 0%, #22222f 100%);
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #2d2d3d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: #6366f1;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
    }

    [data-testid="stMetric"] label {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9090a8 !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    /* Premium Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
        transform: translateY(-2px);
    }

    /* Input Fields - Modern Look */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1a1a28 !important;
        border: 1px solid #2d2d3d !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.65rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
        background: #1a1a28 !important;
        color: #ffffff !important;
    }

    /* Force input labels to be visible */
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stDateInput > label,
    .stTextArea > label {
        color: #9090a8 !important;
        font-weight: 600 !important;
    }

    /* DataFrames - Professional Table Style */
    .dataframe {
        background: #1a1a28 !important;
        border: 1px solid #2d2d3d !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    .dataframe thead tr th {
        background: linear-gradient(135deg, #22222f 0%, #2a2a3a 100%) !important;
        color: #9090a8 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.75rem !important;
        padding: 1rem 0.75rem !important;
        border-bottom: 2px solid #6366f1 !important;
    }

    .dataframe tbody tr {
        border-bottom: 1px solid #2d2d3d !important;
        transition: background 0.2s ease;
    }

    .dataframe tbody tr:hover {
        background: rgba(99, 102, 241, 0.08) !important;
    }

    .dataframe tbody tr td {
        padding: 0.75rem !important;
        color: #e0e0e8 !important;
    }

    /* Tabs - Elegant Design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: #12121a;
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid #2d2d3d;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #9090a8;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1);
        color: #c0c0d0;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }

    /* Expanders - Clean Accordion */
    .streamlit-expanderHeader {
        background: #1a1a28 !important;
        border: 1px solid #2d2d3d !important;
        border-radius: 8px !important;
        padding: 1rem 1.25rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }

    .streamlit-expanderHeader:hover {
        border-color: #6366f1 !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }

    .streamlit-expanderContent {
        background: #12121a !important;
        border: 1px solid #2d2d3d !important;
        border-top: none !important;
        color: #e0e0e8 !important;
    }

    /* Checkboxes */
    .stCheckbox {
        color: #e0e0e8 !important;
    }

    .stCheckbox > label {
        color: #e0e0e8 !important;
    }

    /* Widget backgrounds */
    [data-testid="stWidgetLabel"] {
        color: #9090a8 !important;
    }

    /* Force spinner to be visible */
    .stSpinner > div > div {
        border-top-color: #6366f1 !important;
        border-right-color: rgba(99, 102, 241, 0.3) !important;
        border-bottom-color: rgba(99, 102, 241, 0.3) !important;
        border-left-color: rgba(99, 102, 241, 0.3) !important;
    }

    /* Alert Boxes */
    .stAlert {
        background: #1a1a28;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }

    /* Success Message */
    .element-container:has(.stSuccess) {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Warning Message */
    .element-container:has(.stWarning) {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Error Message */
    .element-container:has(.stError) {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Info Box */
    .element-container:has(.stInfo) {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Sidebar Navigation Radio */
    .stRadio > label {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9090a8 !important;
        margin-bottom: 0.75rem !important;
    }

    .stRadio > div {
        gap: 0.5rem;
    }

    .stRadio > div > label {
        background: #1a1a28;
        border: 1px solid #2d2d3d;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .stRadio > div > label:hover {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.05);
    }

    .stRadio > div > label > div[data-checked="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-color: #6366f1;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #12121a;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
    }

    /* Loading Spinner */
    .stSpinner > div {
        border-top-color: #6366f1 !important;
    }

    /* Plotly Charts - Dark Theme Integration */
    .js-plotly-plot {
        border-radius: 12px !important;
        overflow: hidden !important;
        background: #1a1a28 !important;
    }

    .plotly {
        background: #1a1a28 !important;
    }

    /* All containers should be dark */
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    [data-testid="column"] {
        background: transparent !important;
    }

    /* Info/Success/Warning/Error boxes - already styled but ensure dark */
    .stAlert, .element-container div[data-testid="stNotification"] {
        background: #1a1a28 !important;
        color: #e0e0e8 !important;
    }

    /* Custom Badge Styles */
    .metric-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0.25rem;
    }

    .badge-success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .badge-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-danger {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .badge-info {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    /* All markdown text */
    [data-testid="stMarkdownContainer"] {
        color: #e0e0e8 !important;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] strong {
        color: #e0e0e8 !important;
    }

    /* Captions */
    .caption, [data-testid="stCaptionContainer"] {
        color: #9090a8 !important;
    }

    /* Code blocks */
    code {
        background: #1a1a28 !important;
        color: #c0c0d0 !important;
        padding: 0.2em 0.4em !important;
        border-radius: 4px !important;
    }

    pre {
        background: #1a1a28 !important;
        border: 1px solid #2d2d3d !important;
        border-radius: 8px !important;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Force header toolbar to be dark */
    [data-testid="stToolbar"] {
        background: #0a0a0f !important;
    }

    [data-testid="stDecoration"] {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)


load_custom_css()


# ============================================================================
# INITIALIZE SESSION STATE & GLOBAL OBJECTS
# ============================================================================

# Central portfolio (singleton)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = get_central_portfolio()

if 'options_analyzer' not in st.session_state:
    st.session_state.options_analyzer = OptionsAnalyzer()

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = Watchlist()

if 'scanner' not in st.session_state:
    st.session_state.scanner = OptionsScanner()


# ============================================================================
# SIDEBAR - NAVIGATION & STATUS
# ============================================================================

with st.sidebar:
    st.markdown("# 📊 OPTIONS TERMINAL")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "🏠 Portfolio Overview",
            "➕ Manage Positions",
            "📈 Options Analysis",
            "🔍 Market Scanner",
            "📊 Risk & Correlations",
            "🔮 Forecasting"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Portfolio quick stats
    portfolio = st.session_state.portfolio
    summary = portfolio.get_portfolio_summary()

    st.markdown("### Portfolio Status")

    if summary['total_positions'] > 0:
        st.metric("Positions", summary['total_positions'])
        st.metric("Total Value", f"${summary['total_value']:,.0f}")
        st.metric("Total P&L", f"${summary['total_pnl']:,.0f}",
                 delta=f"{summary['total_pnl_pct']:.1f}%")
    else:
        st.info("No positions yet")

    st.markdown("---")

    # Market status
    st.markdown("### Market Status")
    try:
        spy = yf.Ticker("SPY")
        spy_data = spy.history(period='2d')
        if len(spy_data) >= 2:
            spy_price = spy_data['Close'].iloc[-1]
            spy_change = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-2]) - 1) * 100
            st.metric("SPY", f"${spy_price:.2f}", delta=f"{spy_change:+.2f}%")
    except:
        pass

    st.markdown("---")
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    st.caption("Built with Claude & Streamlit")


# ============================================================================
# PAGE: PORTFOLIO OVERVIEW
# ============================================================================

if page == "🏠 Portfolio Overview":
    st.title("Portfolio Overview")

    portfolio = st.session_state.portfolio

    if portfolio.portfolio.positions:
        # Calculate analytics
        with st.spinner("Calculating portfolio analytics..."):
            analytics = portfolio.analyze_portfolio()

        # Top metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Value", f"${analytics.total_value:,.0f}")
        with col2:
            st.metric("Total P&L", f"${analytics.total_pnl:,.0f}",
                     delta=f"{analytics.total_pnl_pct:.1f}%")
        with col3:
            st.metric("Portfolio Beta", f"{analytics.portfolio_beta:.2f}")
        with col4:
            st.metric("Volatility", f"{analytics.portfolio_volatility*100:.1f}%")
        with col5:
            st.metric("VaR (95%)", f"${analytics.portfolio_var_95:,.0f}")

        # Alerts
        if analytics.alerts:
            st.markdown("### ⚠️ Alerts")
            for alert in analytics.alerts:
                st.warning(alert)

        # Greeks row
        st.markdown("### Portfolio Greeks")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Delta", f"{analytics.total_delta:.2f}")
        with col2:
            st.metric("Gamma", f"{analytics.total_gamma:.4f}")
        with col3:
            st.metric("Theta", f"${analytics.total_theta:.2f}/day")
        with col4:
            st.metric("Vega", f"${analytics.total_vega:.2f}")

        # Risk metrics
        st.markdown("### Risk & Diversification")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg Correlation", f"{analytics.avg_correlation:.3f}")
        with col2:
            st.metric("Diversification", f"{analytics.diversification_ratio:.2f}")
        with col3:
            st.metric("Expected Move (1D)", f"${analytics.expected_move_1d:,.0f}")
        with col4:
            st.metric("Prob Profit", f"{analytics.prob_profit*100:.1f}%")

        # Position breakdown
        st.markdown("### Positions")

        tab1, tab2 = st.tabs(["All Positions", "Top Positions"])

        with tab1:
            positions_df = portfolio.get_positions_df()
            st.dataframe(positions_df, use_container_width=True, height=400)

        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Largest Positions**")
                for pos in analytics.largest_positions:
                    pnl_color = "🟢" if pos['pnl'] >= 0 else "🔴"
                    st.markdown(f"{pnl_color} **{pos['ticker']}** - ${pos['value']:,.0f} ({pos['pnl_pct']:+.1f}%)")

            with col2:
                st.markdown("**Highest Risk Positions**")
                for pos in analytics.highest_risk_positions:
                    beta_badge = "🔴" if pos['beta'] > 1.5 else "🟡" if pos['beta'] > 1.0 else "🟢"
                    st.markdown(f"{beta_badge} **{pos['ticker']}** - β={pos['beta']:.2f}, ${pos['value']:,.0f}")

    else:
        st.info("👋 No positions in portfolio yet. Go to 'Manage Positions' to add some!")


# ============================================================================
# PAGE: MANAGE POSITIONS
# ============================================================================

elif page == "➕ Manage Positions":
    st.title("Manage Portfolio Positions")

    portfolio = st.session_state.portfolio

    tab1, tab2 = st.tabs(["Add Position", "View & Remove"])

    with tab1:
        st.markdown("### Add New Position")

        position_type = st.selectbox("Position Type", ["Stock", "Call Option", "Put Option"])

        col1, col2, col3 = st.columns(3)

        with col1:
            ticker = st.text_input("Ticker", value="AAPL").upper()
            quantity = st.number_input("Quantity", min_value=1, value=100, step=1)

        with col2:
            entry_price = st.number_input("Entry Price", min_value=0.01, value=100.0, step=0.01)

            if position_type in ["Call Option", "Put Option"]:
                strike = st.number_input("Strike Price", min_value=0.01, value=100.0, step=0.01)
            else:
                strike = None

        with col3:
            if position_type in ["Call Option", "Put Option"]:
                expiration = st.date_input("Expiration Date")
                exp_str = expiration.strftime('%Y-%m-%d')
            else:
                exp_str = None

            notes = st.text_input("Notes (optional)")

        if st.button("➕ Add Position", type="primary"):
            try:
                if position_type == "Stock":
                    portfolio.add_stock(ticker, quantity, entry_price, notes)
                else:
                    opt_type = "call" if position_type == "Call Option" else "put"
                    portfolio.add_option(ticker, opt_type, quantity, entry_price,
                                        strike, exp_str, notes)

                st.success(f"✅ Added {position_type}: {ticker}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding position: {e}")

    with tab2:
        st.markdown("### Current Positions")

        if portfolio.portfolio.positions:
            positions_df = portfolio.get_positions_df()

            for idx, row in positions_df.iterrows():
                with st.expander(f"{row['ticker']} - {row['type'].upper()} - ${row['market_value']:,.0f}"):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.markdown(f"**Quantity:** {row['quantity']}")
                        st.markdown(f"**Entry:** ${row['entry_price']:.2f}")
                        st.markdown(f"**Current:** ${row['current_price']:.2f}")

                    with col2:
                        st.markdown(f"**Cost Basis:** ${row['cost_basis']:,.0f}")
                        st.markdown(f"**Market Value:** ${row['market_value']:,.0f}")
                        pnl_color = "🟢" if row['pnl'] >= 0 else "🔴"
                        st.markdown(f"**P&L:** {pnl_color} ${row['pnl']:,.0f} ({row['pnl_pct']:+.1f}%)")

                    with col3:
                        if st.button("🗑️ Remove", key=f"remove_{idx}"):
                            portfolio.remove_position(row['index'])
                            st.success("Position removed")
                            st.rerun()

            if st.button("🗑️ Clear All Positions", type="secondary"):
                if st.checkbox("Confirm clear all"):
                    portfolio.clear()
                    st.success("All positions cleared")
                    st.rerun()
        else:
            st.info("No positions to display")


# ============================================================================
# PAGE: OPTIONS ANALYSIS
# ============================================================================

elif page == "📈 Options Analysis":
    st.title("Options Chain Analysis")

    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input("Ticker Symbol", value="SPY").upper()

    with col2:
        analyze_btn = st.button("🔍 Analyze", type="primary")

    if analyze_btn and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                analyzer = st.session_state.options_analyzer
                results = analyzer.analyze_ticker(ticker, 0)

                # Metrics
                col1, col2, col3, col4, col5 = st.columns(5)

                col1.metric("Price", f"${results['current_price']:.2f}")
                col2.metric("Days to Exp", results['days_to_exp'])

                if results['implied_distribution']:
                    dist = results['implied_distribution']
                    summary = results['summary']

                    col3.metric("ATM IV", f"{dist.atm_iv*100:.1f}%")
                    col4.metric("Expected Move", f"±{summary['expected_move_pct']:.1f}%")
                    col5.metric("P/C Ratio", f"{summary['put_call_ratio']:.2f}")

                    # Distribution chart
                    st.markdown("### Implied Price Distribution")

                    fig = go.Figure()

                    fig.add_trace(go.Bar(
                        x=dist.strikes,
                        y=dist.density,
                        name='Distribution',
                        marker_color='rgba(99, 102, 241, 0.7)'
                    ))

                    fig.add_vline(x=results['current_price'], line_dash="dash",
                                 line_color="lime", annotation_text="Current")
                    fig.add_vline(x=dist.expected_price, line_dash="dash",
                                 line_color="red", annotation_text="Expected")

                    fig.update_layout(
                        template="plotly_dark",
                        height=400,
                        xaxis_title="Strike Price",
                        yaxis_title="Probability Density",
                        paper_bgcolor='rgba(26, 26, 40, 0.8)',
                        plot_bgcolor='rgba(26, 26, 40, 0.8)'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Stats
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Skewness", f"{dist.skewness:.3f}")
                    with col2:
                        st.metric("Kurtosis", f"{dist.kurtosis:.3f}")
                    with col3:
                        st.metric("Prob Above", f"{summary['prob_above_current']*100:.1f}%")

            except Exception as e:
                st.error(f"Error analyzing {ticker}: {e}")


# ============================================================================
# PAGE: MARKET SCANNER
# ============================================================================

elif page == "🔍 Market Scanner":
    st.title("Market Scanner")

    watchlist = st.session_state.watchlist
    scanner = st.session_state.scanner

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Watchlist:** " + ", ".join(watchlist.tickers))

    with col2:
        if st.button("🔍 Scan Now", type="primary"):
            with st.spinner("Scanning market..."):
                results = scanner.scan_watchlist(watchlist)
                st.session_state.scan_results = results

    if 'scan_results' in st.session_state and st.session_state.scan_results:
        results = st.session_state.scan_results

        with_alerts = [r for r in results if r.has_alerts]

        col1, col2, col3 = st.columns(3)
        col1.metric("Scanned", len(results))
        col2.metric("With Alerts", len(with_alerts))
        col3.metric("Avg IV", f"{np.mean([r.atm_iv for r in results])*100:.1f}%")

        if with_alerts:
            st.markdown("### ⚠️ Alerts")
            for result in with_alerts:
                with st.expander(f"**{result.ticker}** - {len(result.alerts)} alerts"):
                    for alert in result.alerts:
                        st.warning(alert)


# ============================================================================
# PAGE: RISK & CORRELATIONS
# ============================================================================

elif page == "📊 Risk & Correlations":
    st.title("Portfolio Risk & Correlations")

    portfolio = st.session_state.portfolio
    tickers = portfolio.get_unique_tickers()

    if len(tickers) < 2:
        st.warning("Add at least 2 positions to your portfolio to analyze correlations")
    else:
        tab1, tab2 = st.tabs(["Correlation Matrix", "Beta Analysis"])

        with tab1:
            st.markdown("### Portfolio Correlation Matrix")

            with st.spinner("Calculating correlations..."):
                try:
                    corr_analyzer = portfolio.corr_analyzer
                    corr_matrix = corr_analyzer.rolling_correlation_matrix(tickers, period='1y')

                    st.metric("Average Correlation", f"{corr_matrix.avg_correlation:.3f}")

                    # Heatmap
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.correlation_matrix.values,
                        x=corr_matrix.tickers,
                        y=corr_matrix.tickers,
                        colorscale='RdYlGn',
                        zmid=0,
                        text=corr_matrix.correlation_matrix.values,
                        texttemplate='%{text:.2f}',
                        textfont={"size": 10}
                    ))

                    fig.update_layout(
                        template="plotly_dark",
                        height=500,
                        paper_bgcolor='rgba(26, 26, 40, 0.8)',
                        plot_bgcolor='rgba(26, 26, 40, 0.8)'
                    )

                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

        with tab2:
            st.markdown("### Beta Analysis")

            beta_data = []

            for ticker in tickers:
                try:
                    beta_result = portfolio.corr_analyzer.rolling_beta(ticker, 'SPY', period='1y')
                    beta_data.append({
                        'Ticker': ticker,
                        'Beta': beta_result.current_beta,
                        'Alpha': beta_result.alphas[-1] * 252 * 100,
                        'R²': beta_result.r_squared[-1]
                    })
                except:
                    pass

            if beta_data:
                beta_df = pd.DataFrame(beta_data)
                st.dataframe(beta_df, use_container_width=True)


# ============================================================================
# PAGE: FORECASTING
# ============================================================================

elif page == "🔮 Forecasting":
    st.title("Price Forecasting")

    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input("Ticker", value="SPY", key="forecast_ticker").upper()

    with col2:
        if st.button("🔮 Forecast", type="primary"):
            with st.spinner(f"Generating forecast for {ticker}..."):
                try:
                    forecaster = DistributionForecaster()
                    forecast = forecaster.forecast_from_distribution(ticker)

                    if forecast:
                        st.markdown(f"### Forecast: {ticker}")

                        col1, col2, col3, col4 = st.columns(4)

                        exp_return = (forecast.expected_price / forecast.current_price - 1) * 100

                        col1.metric("Current", f"${forecast.current_price:.2f}")
                        col2.metric("Expected", f"${forecast.expected_price:.2f}", delta=f"{exp_return:+.1f}%")
                        col3.metric("Prob Up", f"{forecast.prob_profit_long*100:.1f}%")
                        col4.metric("ATM IV", f"{forecast.atm_iv*100:.1f}%")

                        st.markdown("### Expected Ranges")

                        ranges_df = pd.DataFrame({
                            'Confidence': ['50%', '68%', '95%'],
                            'Lower': [forecast.range_50[0], forecast.range_68[0], forecast.range_95[0]],
                            'Upper': [forecast.range_50[1], forecast.range_68[1], forecast.range_95[1]]
                        })

                        st.dataframe(ranges_df, use_container_width=True)

                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9090a8; font-size: 0.85rem;'>
    <strong>Options Analytics Terminal</strong> | Professional Risk Management & Portfolio Analytics<br>
    Powered by Breeden-Litzenberger • Real-Time Greeks • Systematic Risk Analysis
</div>
""", unsafe_allow_html=True)
