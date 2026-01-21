"""
Core Options Analytics Module
Implements Breeden-Litzenberger for risk-neutral density extraction,
Black-Scholes Greeks, and implied volatility surface analysis.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.interpolate import CubicSpline, UnivariateSpline
from scipy.optimize import brentq
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


@dataclass
class OptionGreeks:
    """Container for option Greeks"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    
    def to_dict(self) -> dict:
        return {
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'rho': self.rho
        }


@dataclass
class ImpliedDistribution:
    """Container for implied distribution results"""
    strikes: np.ndarray
    density: np.ndarray  # Risk-neutral probability density
    cdf: np.ndarray  # Cumulative distribution
    expected_price: float
    std_dev: float
    skewness: float
    kurtosis: float
    atm_iv: float
    days_to_exp: int
    
    def probability_between(self, low: float, high: float) -> float:
        """Calculate probability of price between low and high"""
        mask = (self.strikes >= low) & (self.strikes <= high)
        if not np.any(mask):
            return 0.0
        # Integrate density
        dk = np.diff(self.strikes)
        dk = np.append(dk, dk[-1])
        return np.sum(self.density[mask] * dk[mask])
    
    def probability_above(self, price: float) -> float:
        """Calculate probability of price above given level"""
        return self.probability_between(price, self.strikes[-1])
    
    def probability_below(self, price: float) -> float:
        """Calculate probability of price below given level"""
        return self.probability_between(self.strikes[0], price)
    
    def expected_move(self, confidence: float = 0.68) -> Tuple[float, float]:
        """Get expected price range at given confidence level"""
        # Find range that contains 'confidence' probability centered on expected
        cumsum = np.cumsum(self.density * np.gradient(self.strikes))
        cumsum = cumsum / cumsum[-1]  # Normalize
        
        lower_pct = (1 - confidence) / 2
        upper_pct = 1 - lower_pct
        
        lower_idx = np.searchsorted(cumsum, lower_pct)
        upper_idx = np.searchsorted(cumsum, upper_pct)
        
        lower_idx = max(0, min(lower_idx, len(self.strikes) - 1))
        upper_idx = max(0, min(upper_idx, len(self.strikes) - 1))
        
        return self.strikes[lower_idx], self.strikes[upper_idx]


class BlackScholes:
    """Black-Scholes option pricing and Greeks"""
    
    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 parameter"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2 parameter"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return BlackScholes.d1(S, K, T, r, sigma) - sigma * np.sqrt(T)
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate call option price"""
        if T <= 0:
            return max(0, S - K)
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        d2 = BlackScholes.d2(S, K, T, r, sigma)
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate put option price"""
        if T <= 0:
            return max(0, K - S)
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        d2 = BlackScholes.d2(S, K, T, r, sigma)
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    @staticmethod
    def implied_volatility(price: float, S: float, K: float, T: float, 
                           r: float, option_type: str = 'call') -> float:
        """Calculate implied volatility using Brent's method"""
        if T <= 0:
            return 0.0
        
        price_func = BlackScholes.call_price if option_type == 'call' else BlackScholes.put_price
        
        def objective(sigma):
            return price_func(S, K, T, r, sigma) - price
        
        try:
            # Search between 1% and 500% volatility
            iv = brentq(objective, 0.01, 5.0, xtol=1e-6)
            return iv
        except (ValueError, RuntimeError):
            return np.nan
    
    @staticmethod
    def greeks(S: float, K: float, T: float, r: float, sigma: float, 
               option_type: str = 'call') -> OptionGreeks:
        """Calculate all Greeks for an option"""
        if T <= 0 or sigma <= 0:
            return OptionGreeks(0, 0, 0, 0, 0)
        
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        d2 = BlackScholes.d2(S, K, T, r, sigma)
        sqrt_T = np.sqrt(T)
        
        # Common terms
        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)
        
        if option_type == 'call':
            delta = cdf_d1
            theta = (-S * pdf_d1 * sigma / (2 * sqrt_T) 
                     - r * K * np.exp(-r * T) * cdf_d2) / 365
            rho = K * T * np.exp(-r * T) * cdf_d2 / 100
        else:  # put
            delta = cdf_d1 - 1
            theta = (-S * pdf_d1 * sigma / (2 * sqrt_T) 
                     + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        # Gamma and Vega are same for calls and puts
        gamma = pdf_d1 / (S * sigma * sqrt_T)
        vega = S * pdf_d1 * sqrt_T / 100  # Per 1% change in IV
        
        return OptionGreeks(delta, gamma, theta, vega, rho)


class BreedenLitzenberger:
    """
    Implements the Breeden-Litzenberger formula for extracting
    risk-neutral probability density from option prices.
    
    Key insight: The second derivative of call prices with respect to strike
    gives the risk-neutral probability density:
    
    PDF(K) = e^(rT) * d²C/dK²
    
    This implementation:
    1. Uses both calls and puts with put-call parity for robustness
    2. Interpolates prices with cubic splines for smoothness
    3. Applies Gaussian smoothing to reduce noise
    4. Handles non-uniform strike spacing
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.r = risk_free_rate
    
    def extract_density(self, calls: pd.DataFrame, puts: pd.DataFrame,
                        current_price: float, days_to_exp: int,
                        num_points: int = 200,
                        smoothing: float = 0.1) -> ImpliedDistribution:
        """
        Extract the implied probability distribution from options data.
        
        Parameters:
        -----------
        calls : pd.DataFrame
            Call options with 'strike', 'lastPrice', 'bid', 'ask', 'impliedVolatility'
        puts : pd.DataFrame
            Put options with same columns
        current_price : float
            Current underlying price
        days_to_exp : int
            Days until expiration
        num_points : int
            Number of interpolation points
        smoothing : float
            Smoothing parameter (higher = smoother)
        
        Returns:
        --------
        ImpliedDistribution object
        """
        T = days_to_exp / 365.0
        discount = np.exp(-self.r * T)
        
        # Clean and prepare data
        calls_clean = self._clean_options(calls, current_price, 'call')
        puts_clean = self._clean_options(puts, current_price, 'put')
        
        # Use mid prices for more accuracy
        calls_clean['mid'] = (calls_clean['bid'] + calls_clean['ask']) / 2
        calls_clean['mid'] = calls_clean['mid'].fillna(calls_clean['lastPrice'])
        
        puts_clean['mid'] = (puts_clean['bid'] + puts_clean['ask']) / 2
        puts_clean['mid'] = puts_clean['mid'].fillna(puts_clean['lastPrice'])
        
        # Create synthetic prices using put-call parity for better coverage
        # C - P = S - K*e^(-rT) => C = P + S - K*e^(-rT)
        combined = self._combine_with_parity(calls_clean, puts_clean, 
                                              current_price, T)
        
        if len(combined) < 5:
            raise ValueError("Not enough valid options data")
        
        # Define strike range for interpolation
        k_min = combined['strike'].min()
        k_max = combined['strike'].max()
        
        # Extend range slightly
        k_range = k_max - k_min
        k_min = max(k_min - 0.1 * k_range, current_price * 0.5)
        k_max = k_max + 0.1 * k_range
        
        strikes_interp = np.linspace(k_min, k_max, num_points)
        
        # Fit smoothing spline to call prices
        strikes = combined['strike'].values
        prices = combined['call_price'].values
        
        # Sort by strike
        sort_idx = np.argsort(strikes)
        strikes = strikes[sort_idx]
        prices = prices[sort_idx]
        
        # Remove duplicates
        _, unique_idx = np.unique(strikes, return_index=True)
        strikes = strikes[unique_idx]
        prices = prices[unique_idx]
        
        # Fit spline with smoothing
        try:
            # Use UnivariateSpline for controllable smoothing
            spline = UnivariateSpline(strikes, prices, s=smoothing * len(strikes))
        except Exception:
            # Fallback to cubic spline
            spline = CubicSpline(strikes, prices)
        
        # Calculate second derivative (risk-neutral density)
        # PDF(K) = e^(rT) * d²C/dK²
        prices_interp = spline(strikes_interp)
        
        # Numerical second derivative with smoothing
        dk = strikes_interp[1] - strikes_interp[0]
        
        # First derivative
        d1 = np.gradient(prices_interp, dk)
        # Second derivative
        d2 = np.gradient(d1, dk)
        
        # Apply discount factor
        density = d2 / discount
        
        # Apply Gaussian smoothing to reduce noise
        from scipy.ndimage import gaussian_filter1d
        sigma_smooth = max(1, int(num_points * 0.02))
        density = gaussian_filter1d(density, sigma=sigma_smooth)
        
        # Ensure non-negative and normalize
        density = np.maximum(density, 0)
        
        # Normalize to integrate to 1
        total = np.trapz(density, strikes_interp)
        if total > 0:
            density = density / total
        
        # Calculate CDF
        cdf = np.cumsum(density) * dk
        cdf = cdf / cdf[-1]  # Normalize
        
        # Calculate moments
        expected = np.trapz(strikes_interp * density, strikes_interp)
        variance = np.trapz((strikes_interp - expected)**2 * density, strikes_interp)
        std_dev = np.sqrt(max(0, variance))
        
        # Skewness and kurtosis
        if std_dev > 0:
            skewness = np.trapz(((strikes_interp - expected) / std_dev)**3 * density, 
                                strikes_interp)
            kurtosis = np.trapz(((strikes_interp - expected) / std_dev)**4 * density, 
                                strikes_interp) - 3  # Excess kurtosis
        else:
            skewness = 0
            kurtosis = 0
        
        # Get ATM IV
        atm_iv = self._get_atm_iv(calls_clean, puts_clean, current_price)
        
        return ImpliedDistribution(
            strikes=strikes_interp,
            density=density,
            cdf=cdf,
            expected_price=expected,
            std_dev=std_dev,
            skewness=skewness,
            kurtosis=kurtosis,
            atm_iv=atm_iv,
            days_to_exp=days_to_exp
        )
    
    def _clean_options(self, options: pd.DataFrame, current_price: float,
                       option_type: str) -> pd.DataFrame:
        """Clean options data and filter invalid entries"""
        df = options.copy()
        
        # Ensure required columns
        required = ['strike', 'lastPrice', 'impliedVolatility']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Add bid/ask if missing
        if 'bid' not in df.columns:
            df['bid'] = df['lastPrice'] * 0.95
        if 'ask' not in df.columns:
            df['ask'] = df['lastPrice'] * 1.05
        
        # Filter out invalid data
        df = df[df['lastPrice'] > 0]
        df = df[df['impliedVolatility'] > 0]
        df = df[df['impliedVolatility'] < 5]  # Cap at 500% IV
        
        # Filter strikes to reasonable range
        df = df[df['strike'] > current_price * 0.3]
        df = df[df['strike'] < current_price * 2.0]
        
        df['type'] = option_type
        
        return df.sort_values('strike').reset_index(drop=True)
    
    def _combine_with_parity(self, calls: pd.DataFrame, puts: pd.DataFrame,
                             S: float, T: float) -> pd.DataFrame:
        """Combine calls and puts using put-call parity"""
        discount = np.exp(-self.r * T)
        
        # Merge on strike
        merged = pd.merge(
            calls[['strike', 'mid', 'impliedVolatility']].rename(
                columns={'mid': 'call_mid', 'impliedVolatility': 'call_iv'}),
            puts[['strike', 'mid', 'impliedVolatility']].rename(
                columns={'mid': 'put_mid', 'impliedVolatility': 'put_iv'}),
            on='strike',
            how='outer'
        )
        
        # Calculate synthetic prices
        # Where we have puts but not calls: C = P + S - K*e^(-rT)
        # Where we have calls but not puts: P = C - S + K*e^(-rT)
        
        merged['call_price'] = merged['call_mid']
        synthetic_call = merged['put_mid'] + S - merged['strike'] * discount
        merged['call_price'] = merged['call_price'].fillna(synthetic_call)
        
        # Use average where both exist
        has_both = merged['call_mid'].notna() & merged['put_mid'].notna()
        merged.loc[has_both, 'call_price'] = (
            merged.loc[has_both, 'call_mid'] + synthetic_call[has_both]
        ) / 2
        
        # Drop rows without valid price
        merged = merged.dropna(subset=['call_price'])
        merged = merged[merged['call_price'] > 0]
        
        return merged
    
    def _get_atm_iv(self, calls: pd.DataFrame, puts: pd.DataFrame,
                    current_price: float) -> float:
        """Get at-the-money implied volatility"""
        calls['atm_diff'] = abs(calls['strike'] - current_price)
        puts['atm_diff'] = abs(puts['strike'] - current_price)
        
        atm_call_iv = calls.loc[calls['atm_diff'].idxmin(), 'impliedVolatility']
        
        if len(puts) > 0:
            atm_put_iv = puts.loc[puts['atm_diff'].idxmin(), 'impliedVolatility']
            return (atm_call_iv + atm_put_iv) / 2
        
        return atm_call_iv


class OptionsAnalyzer:
    """
    High-level interface for options analysis combining all analytics.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.r = risk_free_rate
        self.bl = BreedenLitzenberger(risk_free_rate)
        self.bs = BlackScholes()
    
    def analyze_ticker(self, ticker: str, expiration_index: int = 0) -> Dict:
        """
        Complete analysis of a ticker's options chain.
        
        Returns dict with:
        - current_price
        - expiration
        - days_to_exp
        - implied_distribution
        - calls_with_greeks
        - puts_with_greeks
        - iv_surface
        - summary_stats
        """
        stock = yf.Ticker(ticker)
        current_price = stock.history(period='1d')['Close'].iloc[-1]
        
        expirations = stock.options
        if len(expirations) == 0:
            raise ValueError(f"No options available for {ticker}")
        
        exp_date = expirations[min(expiration_index, len(expirations) - 1)]
        
        # Calculate days to expiration
        exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_exp = max(1, (exp_datetime - today).days)
        T = days_to_exp / 365.0
        
        # Get options chain
        chain = stock.option_chain(exp_date)
        calls = chain.calls.copy()
        puts = chain.puts.copy()
        
        # Extract implied distribution
        try:
            impl_dist = self.bl.extract_density(calls, puts, current_price, days_to_exp)
        except Exception as e:
            print(f"Warning: Could not extract distribution: {e}")
            impl_dist = None
        
        # Add Greeks to options
        calls = self._add_greeks(calls, current_price, T, 'call')
        puts = self._add_greeks(puts, current_price, T, 'put')
        
        # Calculate IV surface data
        iv_surface = self._extract_iv_surface(calls, puts, current_price)
        
        # Summary statistics
        summary = self._calculate_summary(calls, puts, current_price, impl_dist)
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'expiration': exp_date,
            'days_to_exp': days_to_exp,
            'expirations_available': expirations,
            'implied_distribution': impl_dist,
            'calls': calls,
            'puts': puts,
            'iv_surface': iv_surface,
            'summary': summary
        }
    
    def _add_greeks(self, options: pd.DataFrame, S: float, T: float,
                    option_type: str) -> pd.DataFrame:
        """Add Greeks columns to options dataframe"""
        greeks_list = []
        
        for _, row in options.iterrows():
            K = row['strike']
            sigma = row.get('impliedVolatility', 0.3)
            
            if sigma > 0 and T > 0:
                g = self.bs.greeks(S, K, T, self.r, sigma, option_type)
                greeks_list.append(g.to_dict())
            else:
                greeks_list.append({'delta': 0, 'gamma': 0, 'theta': 0, 
                                    'vega': 0, 'rho': 0})
        
        greeks_df = pd.DataFrame(greeks_list)
        return pd.concat([options.reset_index(drop=True), greeks_df], axis=1)
    
    def _extract_iv_surface(self, calls: pd.DataFrame, puts: pd.DataFrame,
                            current_price: float) -> pd.DataFrame:
        """Extract IV surface data for visualization"""
        # Combine calls and puts
        calls_iv = calls[['strike', 'impliedVolatility']].copy()
        calls_iv['type'] = 'call'
        calls_iv['moneyness'] = calls_iv['strike'] / current_price
        
        puts_iv = puts[['strike', 'impliedVolatility']].copy()
        puts_iv['type'] = 'put'
        puts_iv['moneyness'] = puts_iv['strike'] / current_price
        
        iv_surface = pd.concat([calls_iv, puts_iv], ignore_index=True)
        iv_surface = iv_surface[iv_surface['impliedVolatility'] > 0]
        iv_surface = iv_surface.sort_values('strike')
        
        return iv_surface
    
    def _calculate_summary(self, calls: pd.DataFrame, puts: pd.DataFrame,
                           current_price: float, 
                           impl_dist: Optional[ImpliedDistribution]) -> Dict:
        """Calculate summary statistics"""
        summary = {}
        
        # Put/Call ratio
        call_volume = calls['volume'].sum() if 'volume' in calls else 0
        put_volume = puts['volume'].sum() if 'volume' in puts else 0
        summary['put_call_ratio'] = put_volume / call_volume if call_volume > 0 else 0
        
        # Open interest
        summary['call_oi'] = calls['openInterest'].sum() if 'openInterest' in calls else 0
        summary['put_oi'] = puts['openInterest'].sum() if 'openInterest' in puts else 0
        summary['total_oi'] = summary['call_oi'] + summary['put_oi']
        
        # IV statistics
        all_iv = pd.concat([calls['impliedVolatility'], puts['impliedVolatility']])
        all_iv = all_iv[all_iv > 0]
        summary['iv_mean'] = all_iv.mean() if len(all_iv) > 0 else 0
        summary['iv_median'] = all_iv.median() if len(all_iv) > 0 else 0
        summary['iv_std'] = all_iv.std() if len(all_iv) > 0 else 0
        
        # Distribution stats
        if impl_dist:
            summary['expected_price'] = impl_dist.expected_price
            summary['expected_move'] = impl_dist.std_dev
            summary['expected_move_pct'] = (impl_dist.std_dev / current_price) * 100
            summary['skewness'] = impl_dist.skewness
            summary['kurtosis'] = impl_dist.kurtosis
            summary['atm_iv'] = impl_dist.atm_iv
            
            # Probability ranges
            summary['prob_above_current'] = impl_dist.probability_above(current_price)
            summary['prob_below_current'] = impl_dist.probability_below(current_price)
            
            # Expected move ranges
            lower_1s, upper_1s = impl_dist.expected_move(0.68)
            lower_2s, upper_2s = impl_dist.expected_move(0.95)
            summary['range_1sigma'] = (lower_1s, upper_1s)
            summary['range_2sigma'] = (lower_2s, upper_2s)
        
        return summary


def analyze_options(ticker: str, expiration_index: int = 0) -> Dict:
    """
    Convenience function for quick analysis.
    """
    analyzer = OptionsAnalyzer()
    return analyzer.analyze_ticker(ticker, expiration_index)


if __name__ == "__main__":
    # Example usage
    ticker = input("Enter ticker (default SPY): ").strip().upper() or "SPY"
    
    print(f"\nAnalyzing {ticker}...")
    results = analyze_options(ticker)
    
    print(f"\n{'='*60}")
    print(f"OPTIONS ANALYSIS: {ticker}")
    print(f"{'='*60}")
    print(f"Current Price: ${results['current_price']:.2f}")
    print(f"Expiration: {results['expiration']} ({results['days_to_exp']} days)")
    
    if results['implied_distribution']:
        dist = results['implied_distribution']
        summary = results['summary']
        
        print(f"\n--- Implied Distribution ---")
        print(f"Expected Price: ${dist.expected_price:.2f}")
        print(f"Expected Move: ±${dist.std_dev:.2f} (±{summary['expected_move_pct']:.1f}%)")
        print(f"ATM IV: {dist.atm_iv*100:.1f}%")
        print(f"Skewness: {dist.skewness:.3f}")
        print(f"Excess Kurtosis: {dist.kurtosis:.3f}")
        print(f"\n1σ Range: ${summary['range_1sigma'][0]:.2f} - ${summary['range_1sigma'][1]:.2f}")
        print(f"2σ Range: ${summary['range_2sigma'][0]:.2f} - ${summary['range_2sigma'][1]:.2f}")
        print(f"\nProb above current: {summary['prob_above_current']*100:.1f}%")
        print(f"Prob below current: {summary['prob_below_current']*100:.1f}%")
    
    print(f"\n--- Market Activity ---")
    print(f"Put/Call Ratio: {results['summary']['put_call_ratio']:.2f}")
    print(f"Total Open Interest: {results['summary']['total_oi']:,.0f}")
    print(f"Mean IV: {results['summary']['iv_mean']*100:.1f}%")
