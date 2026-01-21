"""
Options Chain Analysis with Implied Distribution
Fetches options data from yfinance and calculates the implied probability distribution
"""

import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.interpolate import interp1d
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Create plots folder
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)


def get_options_chain(ticker: str, expiration_index: int = 0) -> tuple:
    """
    Fetch options chain for a given ticker.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    expiration_index : int
        Index of expiration date to use (0 = nearest expiration)
    
    Returns:
    --------
    tuple : (calls_df, puts_df, expiration_date, current_price, days_to_exp)
    """
    stock = yf.Ticker(ticker)
    
    # Get current stock price
    current_price = stock.history(period='1d')['Close'].iloc[-1]
    
    # Get available expiration dates
    expirations = stock.options
    if len(expirations) == 0:
        raise ValueError(f"No options available for {ticker}")
    
    # Select expiration date
    exp_date = expirations[min(expiration_index, len(expirations) - 1)]
    
    # Calculate days to expiration
    exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_exp = (exp_datetime - today).days
    days_to_exp = max(1, days_to_exp)  # At least 1 day
    
    # Get options chain
    opt_chain = stock.option_chain(exp_date)
    calls = opt_chain.calls
    puts = opt_chain.puts
    
    print(f"Ticker: {ticker}")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Expiration Date: {exp_date} ({days_to_exp} days)")
    print(f"Available Expirations: {expirations[:5]}...")
    print(f"Calls: {len(calls)} contracts | Puts: {len(puts)} contracts")
    
    return calls, puts, exp_date, current_price, days_to_exp


def calculate_implied_distribution(calls: pd.DataFrame, puts: pd.DataFrame, 
                                    current_price: float, days_to_exp: int,
                                    risk_free_rate: float = 0.05) -> tuple:
    """
    Calculate the implied probability distribution from options prices.
    Uses the Breeden-Litzenberger formula: PDF ≈ e^(rT) * d²C/dK²
    Also calculates expected move using ATM implied volatility.
    
    Parameters:
    -----------
    calls : pd.DataFrame
        Call options data
    puts : pd.DataFrame
        Put options data
    current_price : float
        Current stock price
    days_to_exp : int
        Days until expiration
    risk_free_rate : float
        Risk-free interest rate
    
    Returns:
    --------
    tuple : (strikes, probabilities, expected_price, implied_move, atm_iv)
    """
    # Time to expiration in years
    T = days_to_exp / 365.0
    
    # Combine and sort by strike
    calls_clean = calls[['strike', 'lastPrice', 'impliedVolatility', 'volume', 'openInterest']].copy()
    calls_clean = calls_clean[calls_clean['lastPrice'] > 0]
    calls_clean = calls_clean[calls_clean['impliedVolatility'] > 0]
    calls_clean = calls_clean.sort_values('strike')
    
    # Also clean puts for ATM IV calculation
    puts_clean = puts[['strike', 'lastPrice', 'impliedVolatility', 'volume', 'openInterest']].copy()
    puts_clean = puts_clean[puts_clean['lastPrice'] > 0]
    puts_clean = puts_clean[puts_clean['impliedVolatility'] > 0]
    
    if len(calls_clean) < 5:
        raise ValueError("Not enough valid call options to calculate distribution")
    
    # Find ATM options (closest to current price)
    calls_clean['atm_diff'] = abs(calls_clean['strike'] - current_price)
    puts_clean['atm_diff'] = abs(puts_clean['strike'] - current_price)
    
    atm_call = calls_clean.loc[calls_clean['atm_diff'].idxmin()]
    atm_put = puts_clean.loc[puts_clean['atm_diff'].idxmin()] if len(puts_clean) > 0 else None
    
    # Average ATM IV from calls and puts
    if atm_put is not None:
        atm_iv = (atm_call['impliedVolatility'] + atm_put['impliedVolatility']) / 2
    else:
        atm_iv = atm_call['impliedVolatility']
    
    # Calculate expected move using ATM IV
    # Expected move = Price * IV * sqrt(T)
    # For 1 standard deviation (68% probability)
    implied_move = current_price * atm_iv * np.sqrt(T)
    
    strikes = calls_clean['strike'].values
    prices = calls_clean['lastPrice'].values
    
    # Calculate second derivative using finite differences (Breeden-Litzenberger)
    # d²C/dK² approximates the risk-neutral probability density
    probabilities = []
    valid_strikes = []
    
    for i in range(1, len(strikes) - 1):
        dk1 = strikes[i] - strikes[i-1]
        dk2 = strikes[i+1] - strikes[i]
        
        if dk1 > 0 and dk2 > 0:
            # Second derivative approximation
            d2c_dk2 = (prices[i+1] - 2*prices[i] + prices[i-1]) / ((dk1 + dk2) / 2)**2
            
            # Probability must be non-negative
            prob = max(0, d2c_dk2)
            probabilities.append(prob)
            valid_strikes.append(strikes[i])
    
    probabilities = np.array(probabilities)
    valid_strikes = np.array(valid_strikes)
    
    # Normalize to create a proper probability distribution
    if probabilities.sum() > 0:
        probabilities = probabilities / probabilities.sum()
    
    # Calculate expected price from distribution
    expected_price = np.sum(valid_strikes * probabilities)
    
    return valid_strikes, probabilities, expected_price, implied_move, atm_iv


def plot_implied_distribution(strikes: np.ndarray, probabilities: np.ndarray,
                               current_price: float, expected_price: float, 
                               implied_move: float, atm_iv: float, 
                               ticker: str, exp_date: str, days_to_exp: int,
                               save_path: str = None):
    """
    Plot the implied probability distribution and save to file.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Bar plot of implied distribution
    bar_width = (strikes[-1] - strikes[0]) / len(strikes) * 0.8 if len(strikes) > 1 else 1
    ax.bar(strikes, probabilities, width=bar_width, 
           alpha=0.7, color='steelblue', edgecolor='navy', label='Implied Distribution')
    
    # Add vertical lines for key prices
    ax.axvline(current_price, color='green', linestyle='--', linewidth=2, 
               label=f'Current Price: ${current_price:.2f}')
    ax.axvline(expected_price, color='red', linestyle='--', linewidth=2,
               label=f'Expected Price: ${expected_price:.2f}')
    
    # Add shaded region for expected move (1 std dev)
    ax.axvspan(current_price - implied_move, current_price + implied_move, 
               alpha=0.2, color='orange', 
               label=f'Expected Move: ±${implied_move:.2f} ({implied_move/current_price*100:.1f}%)')
    
    ax.set_xlabel('Strike Price ($)', fontsize=12)
    ax.set_ylabel('Probability', fontsize=12)
    ax.set_title(f'{ticker} Implied Price Distribution\nExpiration: {exp_date} ({days_to_exp} days) | ATM IV: {atm_iv*100:.1f}%', fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {save_path}")
    
    return fig


def plot_price_history(ticker: str, period: str = '1y', save_path: str = None):
    """
    Plot historical price time series for the stock and save to file.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    period : str
        Time period for historical data ('1mo', '3mo', '6mo', '1y', '2y', '5y')
    save_path : str
        Path to save the plot
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    
    if hist.empty:
        raise ValueError(f"No historical data available for {ticker}")
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Price chart with moving averages
    ax1 = axes[0]
    ax1.plot(hist.index, hist['Close'], label='Close Price', color='steelblue', linewidth=1.5)
    
    # Add moving averages
    if len(hist) >= 20:
        ma20 = hist['Close'].rolling(window=20).mean()
        ax1.plot(hist.index, ma20, label='20-day MA', color='orange', linewidth=1, alpha=0.8)
    
    if len(hist) >= 50:
        ma50 = hist['Close'].rolling(window=50).mean()
        ax1.plot(hist.index, ma50, label='50-day MA', color='red', linewidth=1, alpha=0.8)
    
    # Fill between high and low
    ax1.fill_between(hist.index, hist['Low'], hist['High'], alpha=0.2, color='steelblue')
    
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.set_title(f'{ticker} Stock Price - {period.upper()} History', fontsize=14)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Volume chart
    ax2 = axes[1]
    colors = ['green' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else 'red' 
              for i in range(len(hist))]
    ax2.bar(hist.index, hist['Volume'], color=colors, alpha=0.7, width=0.8)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Format volume axis
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {save_path}")
    
    return fig, hist


def analyze_options(ticker: str, expiration_index: int = 0, history_period: str = '1y'):
    """
    Complete options analysis: fetch chain, calculate implied distribution, and plot results.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'SPY')
    expiration_index : int
        Which expiration date to use (0 = nearest)
    history_period : str
        Historical price period ('1mo', '3mo', '6mo', '1y', '2y')
    
    Returns:
    --------
    dict : Analysis results including options data and statistics
    """
    print("=" * 60)
    print(f"OPTIONS CHAIN ANALYSIS: {ticker}")
    print("=" * 60)
    
    # Get options chain
    calls, puts, exp_date, current_price, days_to_exp = get_options_chain(ticker, expiration_index)
    
    print("\n" + "-" * 40)
    print("CALLS (Top 10 by Volume):")
    print(calls.nlargest(10, 'volume')[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']])
    
    print("\n" + "-" * 40)
    print("PUTS (Top 10 by Volume):")
    print(puts.nlargest(10, 'volume')[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']])
    
    # Calculate implied distribution
    print("\n" + "-" * 40)
    print("CALCULATING IMPLIED DISTRIBUTION...")
    
    try:
        strikes, probs, expected, implied_move, atm_iv = calculate_implied_distribution(
            calls, puts, current_price, days_to_exp
        )
        
        print(f"\nImplied Distribution Statistics:")
        print(f"  Current Price:    ${current_price:.2f}")
        print(f"  Expected Price:   ${expected:.2f}")
        print(f"  Days to Exp:      {days_to_exp}")
        print(f"  ATM Implied Vol:  {atm_iv*100:.1f}%")
        print(f"  Expected Move:    ±${implied_move:.2f} (±{implied_move/current_price*100:.1f}%)")
        print(f"  1σ Range:         ${current_price - implied_move:.2f} - ${current_price + implied_move:.2f}")
        print(f"  2σ Range:         ${current_price - 2*implied_move:.2f} - ${current_price + 2*implied_move:.2f}")
        
        # Plot implied distribution
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dist_path = os.path.join(PLOTS_DIR, f'{ticker}_implied_distribution_{timestamp}.png')
        fig1 = plot_implied_distribution(
            strikes, probs, current_price, expected, implied_move, atm_iv, 
            ticker, exp_date, days_to_exp, save_path=dist_path
        )
        
    except ValueError as e:
        print(f"Could not calculate implied distribution: {e}")
        strikes, probs, expected, implied_move, atm_iv = None, None, None, None, None
        fig1 = None
    
    # Plot price history
    print("\n" + "-" * 40)
    print("FETCHING PRICE HISTORY...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    price_path = os.path.join(PLOTS_DIR, f'{ticker}_price_history_{timestamp}.png')
    fig2, hist = plot_price_history(ticker, history_period, save_path=price_path)
    
    # Calculate some price statistics
    print(f"\nPrice Statistics ({history_period}):")
    print(f"  Latest Close:  ${hist['Close'].iloc[-1]:.2f}")
    print(f"  52-week High:  ${hist['High'].max():.2f}")
    print(f"  52-week Low:   ${hist['Low'].min():.2f}")
    print(f"  Avg Volume:    {hist['Volume'].mean()/1e6:.2f}M")
    
    # Historical volatility
    returns = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
    hist_vol = returns.std() * np.sqrt(252) * 100
    print(f"  Historical Vol: {hist_vol:.1f}%")
    
    return {
        'ticker': ticker,
        'current_price': current_price,
        'expiration': exp_date,
        'days_to_expiration': days_to_exp,
        'calls': calls,
        'puts': puts,
        'strikes': strikes,
        'probabilities': probs,
        'expected_price': expected,
        'implied_move': implied_move,
        'atm_iv': atm_iv,
        'history': hist,
        'historical_volatility': hist_vol
    }


# Example usage
if __name__ == "__main__":
    # Analyze a stock - change ticker as needed
    ticker = input("Enter stock ticker (e.g., AAPL, TSLA, SPY): ").strip().upper()
    
    if not ticker:
        ticker = "SPY"  # Default to SPY
    
    # Run the analysis
    results = analyze_options(
        ticker=ticker,
        expiration_index=0,  # Use nearest expiration
        history_period='1y'  # 1 year of price history
    )
    
    print("\n" + "=" * 60)
    print(f"Analysis complete! Plots saved to: {PLOTS_DIR}")
    print("=" * 60)
