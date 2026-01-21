"""
Watchlist Scanner Module
Monitors a list of tickers for unusual options activity and distribution changes.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import yfinance as yf

from config import (WATCHLIST_FILE, DATA_DIR, UNUSUAL_VOLUME_THRESHOLD,
                   IV_PERCENTILE_ALERT, PUT_CALL_RATIO_THRESHOLD)
from analytics import OptionsAnalyzer, ImpliedDistribution


@dataclass
class ScanResult:
    """Result from scanning a ticker"""
    ticker: str
    timestamp: str
    current_price: float
    
    # Distribution metrics
    expected_move_pct: float
    atm_iv: float
    skewness: float
    prob_up: float
    prob_down: float
    
    # Flow metrics
    put_call_ratio: float
    total_volume: int
    total_oi: int
    volume_oi_ratio: float
    
    # Alerts
    alerts: List[str]
    
    # Change from previous scan
    iv_change: Optional[float] = None
    skew_change: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def has_alerts(self) -> bool:
        return len(self.alerts) > 0
    
    @property
    def alert_score(self) -> int:
        """Score based on number and type of alerts"""
        score = 0
        for alert in self.alerts:
            if 'UNUSUAL' in alert.upper():
                score += 3
            elif 'HIGH' in alert.upper():
                score += 2
            else:
                score += 1
        return score


class Watchlist:
    """Manages a watchlist of tickers to monitor"""
    
    def __init__(self, watchlist_file: str = WATCHLIST_FILE):
        self.watchlist_file = watchlist_file
        self.tickers: List[str] = []
        self.scan_history: Dict[str, List[ScanResult]] = {}
        self.load()
    
    def load(self):
        """Load watchlist from file"""
        if os.path.exists(self.watchlist_file):
            try:
                with open(self.watchlist_file, 'r') as f:
                    data = json.load(f)
                    self.tickers = data.get('tickers', [])
            except (json.JSONDecodeError, KeyError):
                self.tickers = []
        else:
            # Default watchlist
            self.tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META']
            self.save()
    
    def save(self):
        """Save watchlist to file"""
        os.makedirs(os.path.dirname(self.watchlist_file), exist_ok=True)
        data = {
            'tickers': self.tickers,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.watchlist_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add(self, ticker: str):
        """Add ticker to watchlist"""
        ticker = ticker.upper()
        if ticker not in self.tickers:
            self.tickers.append(ticker)
            self.save()
    
    def remove(self, ticker: str):
        """Remove ticker from watchlist"""
        ticker = ticker.upper()
        if ticker in self.tickers:
            self.tickers.remove(ticker)
            self.save()
    
    def clear(self):
        """Clear watchlist"""
        self.tickers = []
        self.save()


class OptionsScanner:
    """
    Scans options for unusual activity and distribution changes.
    
    Detects:
    1. Unusual volume (volume >> open interest)
    2. High IV percentile
    3. Put/Call ratio extremes
    4. Distribution skew changes
    5. Large expected move changes
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.analyzer = OptionsAnalyzer(risk_free_rate)
        self.scan_history: Dict[str, List[ScanResult]] = {}
        self.iv_history: Dict[str, List[Tuple[datetime, float]]] = {}
    
    def scan_ticker(self, ticker: str, expiration_index: int = 0) -> Optional[ScanResult]:
        """
        Scan a single ticker for options activity.
        
        Returns ScanResult with metrics and any alerts.
        """
        try:
            results = self.analyzer.analyze_ticker(ticker, expiration_index)
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            return None
        
        alerts = []
        
        # Extract metrics
        current_price = results['current_price']
        calls = results['calls']
        puts = results['puts']
        impl_dist = results['implied_distribution']
        summary = results['summary']
        
        # Volume analysis
        call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
        put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
        total_volume = call_volume + put_volume
        
        call_oi = calls['openInterest'].sum() if 'openInterest' in calls.columns else 0
        put_oi = puts['openInterest'].sum() if 'openInterest' in puts.columns else 0
        total_oi = call_oi + put_oi
        
        volume_oi_ratio = total_volume / total_oi if total_oi > 0 else 0
        
        # Check for unusual volume
        if volume_oi_ratio > UNUSUAL_VOLUME_THRESHOLD:
            alerts.append(f"UNUSUAL VOLUME: Vol/OI ratio {volume_oi_ratio:.2f}x")
        
        # Put/Call ratio
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        if put_call_ratio > PUT_CALL_RATIO_THRESHOLD:
            alerts.append(f"HIGH PUT/CALL: {put_call_ratio:.2f}")
        elif put_call_ratio < (1 / PUT_CALL_RATIO_THRESHOLD):
            alerts.append(f"HIGH CALL ACTIVITY: P/C {put_call_ratio:.2f}")
        
        # IV analysis
        atm_iv = impl_dist.atm_iv if impl_dist else summary.get('atm_iv', 0)
        
        # Track IV history for percentile
        self._update_iv_history(ticker, atm_iv)
        iv_percentile = self._get_iv_percentile(ticker, atm_iv)
        
        if iv_percentile > IV_PERCENTILE_ALERT:
            alerts.append(f"HIGH IV: {atm_iv*100:.1f}% ({iv_percentile:.0f}th percentile)")
        
        # Distribution metrics
        if impl_dist:
            expected_move_pct = (impl_dist.std_dev / current_price) * 100
            skewness = impl_dist.skewness
            prob_up = impl_dist.probability_above(current_price)
            prob_down = impl_dist.probability_below(current_price)
            
            # Check for significant skew (bearish or bullish bias)
            if skewness < -0.5:
                alerts.append(f"BEARISH SKEW: {skewness:.2f}")
            elif skewness > 0.3:
                alerts.append(f"BULLISH SKEW: {skewness:.2f}")
            
            # Check probability imbalance
            if prob_up > 0.6:
                alerts.append(f"BULLISH BIAS: {prob_up*100:.0f}% prob up")
            elif prob_down > 0.6:
                alerts.append(f"BEARISH BIAS: {prob_down*100:.0f}% prob down")
        else:
            expected_move_pct = 0
            skewness = 0
            prob_up = 0.5
            prob_down = 0.5
        
        # Calculate changes from previous scan
        iv_change, skew_change = self._calculate_changes(ticker, atm_iv, skewness)
        
        if iv_change is not None and abs(iv_change) > 0.05:  # 5% IV change
            direction = "UP" if iv_change > 0 else "DOWN"
            alerts.append(f"IV CHANGE {direction}: {iv_change*100:+.1f}%")
        
        result = ScanResult(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            expected_move_pct=expected_move_pct,
            atm_iv=atm_iv,
            skewness=skewness,
            prob_up=prob_up,
            prob_down=prob_down,
            put_call_ratio=put_call_ratio,
            total_volume=int(total_volume),
            total_oi=int(total_oi),
            volume_oi_ratio=volume_oi_ratio,
            alerts=alerts,
            iv_change=iv_change,
            skew_change=skew_change
        )
        
        # Store in history
        if ticker not in self.scan_history:
            self.scan_history[ticker] = []
        self.scan_history[ticker].append(result)
        
        # Keep only last 100 scans per ticker
        self.scan_history[ticker] = self.scan_history[ticker][-100:]
        
        return result
    
    def scan_watchlist(self, watchlist: Watchlist,
                       expiration_index: int = 0,
                       send_notifications: bool = False) -> List[ScanResult]:
        """
        Scan all tickers in watchlist.

        Parameters:
        -----------
        watchlist : Watchlist
            Watchlist object with tickers to scan
        expiration_index : int
            Which expiration to use (0 = nearest)
        send_notifications : bool
            If True, send alerts via email/Discord for significant results

        Returns:
        --------
        List of ScanResult objects, sorted by alert score
        """
        results = []

        for ticker in watchlist.tickers:
            print(f"Scanning {ticker}...", end=" ")
            result = self.scan_ticker(ticker, expiration_index)
            if result:
                results.append(result)
                if result.has_alerts:
                    print(f"⚠️ {len(result.alerts)} alerts")
                else:
                    print("✓")
            else:
                print("✗ failed")

        # Sort by alert score
        results.sort(key=lambda x: x.alert_score, reverse=True)

        # Send notifications if enabled
        if send_notifications:
            self._send_notifications(results)

        return results

    def _send_notifications(self, results: List[ScanResult]):
        """Send notifications for significant scan results"""
        try:
            from notifications import NotificationSystem

            notifier = NotificationSystem()
            count = notifier.send_bulk_alert(results)

            if count > 0:
                print(f"\n📨 Sent {count} notification(s)")
        except ImportError:
            print("\n⚠️ Notifications module not available")
        except Exception as e:
            print(f"\n⚠️ Error sending notifications: {e}")
    
    def _update_iv_history(self, ticker: str, iv: float):
        """Update IV history for a ticker"""
        if ticker not in self.iv_history:
            self.iv_history[ticker] = []
        
        self.iv_history[ticker].append((datetime.now(), iv))
        
        # Keep only last 30 days of data
        cutoff = datetime.now() - timedelta(days=30)
        self.iv_history[ticker] = [
            (dt, val) for dt, val in self.iv_history[ticker] 
            if dt > cutoff
        ]
    
    def _get_iv_percentile(self, ticker: str, current_iv: float) -> float:
        """Get percentile rank of current IV"""
        if ticker not in self.iv_history or len(self.iv_history[ticker]) < 5:
            return 50.0  # Default to median
        
        ivs = [val for _, val in self.iv_history[ticker]]
        percentile = (np.sum(np.array(ivs) < current_iv) / len(ivs)) * 100
        return percentile
    
    def _calculate_changes(self, ticker: str, current_iv: float,
                           current_skew: float) -> Tuple[Optional[float], Optional[float]]:
        """Calculate changes from previous scan"""
        if ticker not in self.scan_history or len(self.scan_history[ticker]) < 2:
            return None, None
        
        prev = self.scan_history[ticker][-2]
        iv_change = current_iv - prev.atm_iv
        skew_change = current_skew - prev.skewness
        
        return iv_change, skew_change
    
    def get_top_movers(self, results: List[ScanResult], n: int = 5) -> Dict:
        """Get top movers by various metrics"""
        if not results:
            return {}
        
        df = pd.DataFrame([r.to_dict() for r in results])
        
        return {
            'highest_iv': df.nlargest(n, 'atm_iv')[['ticker', 'atm_iv']].to_dict('records'),
            'highest_volume': df.nlargest(n, 'total_volume')[['ticker', 'total_volume']].to_dict('records'),
            'most_bullish': df.nlargest(n, 'prob_up')[['ticker', 'prob_up', 'skewness']].to_dict('records'),
            'most_bearish': df.nsmallest(n, 'skewness')[['ticker', 'skewness', 'prob_down']].to_dict('records'),
            'unusual_activity': df.nlargest(n, 'volume_oi_ratio')[['ticker', 'volume_oi_ratio']].to_dict('records')
        }
    
    def generate_report(self, results: List[ScanResult]) -> str:
        """Generate a text report of scan results"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"OPTIONS SCANNER REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        
        # Summary
        total = len(results)
        with_alerts = sum(1 for r in results if r.has_alerts)
        lines.append(f"\nScanned {total} tickers, {with_alerts} with alerts\n")
        
        # Tickers with alerts
        if with_alerts > 0:
            lines.append("-" * 50)
            lines.append("ALERTS:")
            lines.append("-" * 50)
            
            for result in results:
                if result.has_alerts:
                    lines.append(f"\n{result.ticker} @ ${result.current_price:.2f}")
                    for alert in result.alerts:
                        lines.append(f"  ⚠️ {alert}")
        
        # Top movers
        movers = self.get_top_movers(results)
        
        lines.append("\n" + "-" * 50)
        lines.append("HIGHEST IV:")
        for item in movers.get('highest_iv', []):
            lines.append(f"  {item['ticker']}: {item['atm_iv']*100:.1f}%")
        
        lines.append("\n" + "-" * 50)
        lines.append("MOST BULLISH DISTRIBUTIONS:")
        for item in movers.get('most_bullish', []):
            lines.append(f"  {item['ticker']}: {item['prob_up']*100:.0f}% up probability")
        
        lines.append("\n" + "-" * 50)
        lines.append("UNUSUAL ACTIVITY (Vol/OI):")
        for item in movers.get('unusual_activity', []):
            lines.append(f"  {item['ticker']}: {item['volume_oi_ratio']:.2f}x")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


def scan_market(tickers: List[str] = None) -> List[ScanResult]:
    """Quick function to scan tickers"""
    watchlist = Watchlist()
    
    if tickers:
        for t in tickers:
            watchlist.add(t)
    
    scanner = OptionsScanner()
    results = scanner.scan_watchlist(watchlist)
    
    print("\n" + scanner.generate_report(results))
    
    return results


if __name__ == "__main__":
    # Demo scan
    print("Starting market scan...")
    results = scan_market()
