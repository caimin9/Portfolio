"""
Configuration file for Options Analytics System
"""

import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories
for dir_path in [PLOTS_DIR, DATA_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Portfolio file
PORTFOLIO_FILE = os.path.join(DATA_DIR, 'portfolio.json')
WATCHLIST_FILE = os.path.join(DATA_DIR, 'watchlist.json')
ALERTS_LOG = os.path.join(LOGS_DIR, 'alerts.log')

# Default parameters
DEFAULT_RISK_FREE_RATE = 0.05  # 5% annual
DEFAULT_HISTORY_PERIOD = '1y'

# Alert thresholds
UNUSUAL_VOLUME_THRESHOLD = 2.0  # Volume > 2x average
IV_PERCENTILE_ALERT = 80  # Alert when IV above 80th percentile
PUT_CALL_RATIO_THRESHOLD = 1.5  # Alert when P/C ratio > 1.5

# Dashboard settings
DASHBOARD_REFRESH_SECONDS = 60

# Notification settings
# Email (SMTP)
EMAIL_ENABLED = False  # Set to True to enable email notifications
SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP server (or your provider)
SMTP_PORT = 587
EMAIL_FROM = "your_email@gmail.com"  # Your email
EMAIL_PASSWORD = ""  # App password for Gmail (NOT your regular password)
EMAIL_TO = "alerts@example.com"  # Where to send alerts

# Discord webhook
DISCORD_ENABLED = False  # Set to True to enable Discord notifications
DISCORD_WEBHOOK_URL = ""  # Your Discord webhook URL

# Notification preferences
MIN_ALERT_SCORE = 2  # Minimum alert severity to trigger notification
NOTIFICATION_COOLDOWN_MINUTES = 60  # Min time between notifications for same ticker
