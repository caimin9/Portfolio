"""
Real-time Notification System
Send alerts via email and Discord when unusual options activity is detected.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

from config import (EMAIL_ENABLED, SMTP_SERVER, SMTP_PORT, EMAIL_FROM,
                   EMAIL_PASSWORD, EMAIL_TO, DISCORD_ENABLED, DISCORD_WEBHOOK_URL)
from scanner import ScanResult


@dataclass
class NotificationConfig:
    """Configuration for notification settings"""
    min_alert_score: int = 2  # Minimum alert score to trigger notification
    email_enabled: bool = EMAIL_ENABLED
    discord_enabled: bool = DISCORD_ENABLED
    cooldown_minutes: int = 60  # Minimum time between notifications for same ticker


class NotificationSystem:
    """
    Multi-channel notification system for options alerts.

    Supports:
    - Email (via SMTP)
    - Discord webhooks
    - Cooldown to prevent spam
    """

    def __init__(self, config: NotificationConfig = NotificationConfig()):
        self.config = config
        self.last_notification = {}  # ticker -> timestamp

    def should_notify(self, result: ScanResult) -> bool:
        """Check if we should send notification for this result"""
        # Check alert score threshold
        if result.alert_score < self.config.min_alert_score:
            return False

        # Check cooldown
        ticker = result.ticker
        if ticker in self.last_notification:
            time_since = (datetime.now() - self.last_notification[ticker]).seconds / 60
            if time_since < self.config.cooldown_minutes:
                return False

        return True

    def send_alert(self, result: ScanResult) -> bool:
        """Send alert via all enabled channels"""
        if not self.should_notify(result):
            return False

        success = True

        if self.config.email_enabled:
            email_sent = self.send_email(result)
            success = success and email_sent

        if self.config.discord_enabled:
            discord_sent = self.send_discord(result)
            success = success and discord_sent

        if success:
            self.last_notification[result.ticker] = datetime.now()

        return success

    def send_bulk_alert(self, results: List[ScanResult]) -> int:
        """Send alerts for multiple results, returns count of notifications sent"""
        count = 0
        for result in results:
            if result.has_alerts and self.send_alert(result):
                count += 1
        return count

    def send_email(self, result: ScanResult) -> bool:
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Options Alert: {result.ticker}"
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO

            # Create HTML email
            html = self._create_email_html(result)

            # Attach HTML
            msg.attach(MIMEText(html, 'html'))

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                server.send_message(msg)

            print(f"✉️ Email sent for {result.ticker}")
            return True

        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def send_discord(self, result: ScanResult) -> bool:
        """Send Discord webhook notification"""
        try:
            # Create rich embed
            embed = {
                "title": f"🚨 Options Alert: {result.ticker}",
                "description": f"Detected {len(result.alerts)} alerts",
                "color": 15158332 if result.skewness < 0 else 3066993,  # Red/Green
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "Price",
                        "value": f"${result.current_price:.2f}",
                        "inline": True
                    },
                    {
                        "name": "ATM IV",
                        "value": f"{result.atm_iv*100:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "Expected Move",
                        "value": f"±{result.expected_move_pct:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "Prob Up",
                        "value": f"{result.prob_up*100:.0f}%",
                        "inline": True
                    },
                    {
                        "name": "P/C Ratio",
                        "value": f"{result.put_call_ratio:.2f}",
                        "inline": True
                    },
                    {
                        "name": "Vol/OI",
                        "value": f"{result.volume_oi_ratio:.2f}x",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Options Analytics System"
                }
            }

            # Add alerts as separate field
            if result.alerts:
                alerts_text = "\n".join([f"⚠️ {alert}" for alert in result.alerts[:5]])
                embed["fields"].insert(0, {
                    "name": "Alerts",
                    "value": alerts_text,
                    "inline": False
                })

            # Add IV change if available
            if result.iv_change is not None:
                direction = "📈" if result.iv_change > 0 else "📉"
                embed["fields"].append({
                    "name": "IV Change",
                    "value": f"{direction} {result.iv_change*100:+.1f}%",
                    "inline": True
                })

            payload = {
                "embeds": [embed],
                "username": "Options Scanner"
            }

            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

            if response.status_code == 204:
                print(f"💬 Discord message sent for {result.ticker}")
                return True
            else:
                print(f"❌ Discord error: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Discord error: {e}")
            return False

    def _create_email_html(self, result: ScanResult) -> str:
        """Create HTML email body"""
        alerts_html = "\n".join([
            f"<li style='margin: 5px 0;'>{alert}</li>"
            for alert in result.alerts
        ])

        # Color based on sentiment
        color = "#ff4444" if result.skewness < 0 else "#00ff88"

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #1e1e1e;
                    color: #ffffff;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #2d2d2d;
                    border-radius: 10px;
                    padding: 20px;
                    border-left: 5px solid {color};
                }}
                .header {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    color: {color};
                }}
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .metric {{
                    background-color: #1a1a1a;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .metric-label {{
                    font-size: 12px;
                    color: #888;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 20px;
                    font-weight: bold;
                }}
                .alerts {{
                    background-color: #3a1a1a;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 3px solid #ff4444;
                    margin: 20px 0;
                }}
                .alerts ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #444;
                    font-size: 12px;
                    color: #888;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    🚨 Options Alert: {result.ticker}
                </div>

                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Current Price</div>
                        <div class="metric-value">${result.current_price:.2f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">ATM IV</div>
                        <div class="metric-value">{result.atm_iv*100:.1f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Expected Move</div>
                        <div class="metric-value">±{result.expected_move_pct:.1f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Probability Up</div>
                        <div class="metric-value">{result.prob_up*100:.0f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Put/Call Ratio</div>
                        <div class="metric-value">{result.put_call_ratio:.2f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Vol/OI Ratio</div>
                        <div class="metric-value">{result.volume_oi_ratio:.2f}x</div>
                    </div>
                </div>

                <div class="alerts">
                    <strong>⚠️ Detected Alerts:</strong>
                    <ul>
                        {alerts_html}
                    </ul>
                </div>

                <div class="footer">
                    Options Analytics System • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """

        return html


def test_notifications():
    """Test notification system with sample data"""
    from scanner import ScanResult

    # Create test result
    test_result = ScanResult(
        ticker="SPY",
        timestamp=datetime.now().isoformat(),
        current_price=450.00,
        expected_move_pct=2.5,
        atm_iv=0.15,
        skewness=-0.3,
        prob_up=0.52,
        prob_down=0.48,
        put_call_ratio=1.2,
        total_volume=1000000,
        total_oi=500000,
        volume_oi_ratio=2.0,
        alerts=["UNUSUAL VOLUME: Vol/OI ratio 2.00x", "HIGH IV: 15.0% (85th percentile)"],
        iv_change=0.02
    )

    notifier = NotificationSystem()

    print("Testing notification system...")
    print(f"Email enabled: {notifier.config.email_enabled}")
    print(f"Discord enabled: {notifier.config.discord_enabled}")

    success = notifier.send_alert(test_result)

    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("⚠️ Test notification had issues (check config)")


if __name__ == "__main__":
    test_notifications()
