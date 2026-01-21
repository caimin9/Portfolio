# Notification Setup Guide

This guide explains how to set up real-time notifications for your options scanner.

## Overview

The notification system can alert you via:
- **Email** (using SMTP, works with Gmail, Outlook, etc.)
- **Discord** (using webhooks)

Alerts are sent when the scanner detects unusual options activity, high IV, put/call imbalances, or distribution changes.

---

## Email Setup (Gmail)

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security**
3. Enable **2-Step Verification**

### Step 2: Create App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select **Mail** and **Windows Computer** (or other device)
3. Click **Generate**
4. Copy the 16-character password (you'll need this)

### Step 3: Configure `config.py`
Edit `options/config.py`:

```python
# Email settings
EMAIL_ENABLED = True  # Enable email notifications
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "your_email@gmail.com"  # Your Gmail address
EMAIL_PASSWORD = "your_app_password_here"  # The 16-char app password from Step 2
EMAIL_TO = "recipient@example.com"  # Where to receive alerts
```

### For Other Email Providers:

**Outlook/Hotmail:**
```python
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
```

**Yahoo:**
```python
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 587
```

**Custom SMTP:**
Check your email provider's documentation for SMTP settings.

---

## Discord Setup

### Step 1: Create Discord Webhook
1. Open Discord and go to your server
2. Go to **Server Settings** > **Integrations** > **Webhooks**
3. Click **New Webhook**
4. Name it (e.g., "Options Scanner")
5. Select the channel where you want alerts
6. Click **Copy Webhook URL**

### Step 2: Configure `config.py`
Edit `options/config.py`:

```python
# Discord settings
DISCORD_ENABLED = True  # Enable Discord notifications
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

---

## Notification Preferences

You can customize when notifications are sent:

```python
# In config.py

# Minimum alert severity (1-10, higher = more severe)
# Only send notifications for alerts scoring at least this value
MIN_ALERT_SCORE = 2  # Default: 2

# Cooldown period in minutes
# Prevents spam by limiting notifications for the same ticker
NOTIFICATION_COOLDOWN_MINUTES = 60  # Default: 60 (1 hour)
```

### Alert Score System:
- **UNUSUAL** alerts (volume spikes): +3 points
- **HIGH** alerts (IV extremes, P/C ratio): +2 points
- Other alerts: +1 point

Example: A ticker with "UNUSUAL VOLUME" + "HIGH IV" = 5 points

---

## Usage

### Manual Scan with Notifications
```python
from scanner import scan_market

# Scan watchlist and send notifications
results = scan_market(send_notifications=True)
```

### In Your Code
```python
from scanner import OptionsScanner, Watchlist

watchlist = Watchlist()
scanner = OptionsScanner()

# Scan with notifications enabled
results = scanner.scan_watchlist(watchlist, send_notifications=True)
```

### Test Notifications
```python
# Test your notification setup
python notifications.py
```

This will send a test alert to verify your configuration.

---

## Dashboard Integration

The Streamlit dashboard automatically supports notifications. Just configure `config.py` and notifications will be sent when you click "Scan Watchlist".

To enable auto-notifications in dashboard:
1. Enable notifications in `config.py`
2. Run scanner from dashboard
3. Alerts will be sent automatically for significant findings

---

## Troubleshooting

### Email Issues

**"Authentication failed"**
- Make sure you're using an **app password**, not your regular Gmail password
- Verify 2-Factor Authentication is enabled
- Check EMAIL_FROM and EMAIL_PASSWORD are correct

**"Connection refused"**
- Verify SMTP_SERVER and SMTP_PORT are correct
- Check firewall settings
- Try port 465 with SSL instead:
  ```python
  SMTP_PORT = 465
  # Update notifications.py to use SMTP_SSL instead of SMTP
  ```

### Discord Issues

**"Invalid webhook URL"**
- Verify you copied the complete webhook URL
- Make sure Discord webhook is not deleted
- Check webhook has permissions to post in the channel

**No messages appearing**
- Check the webhook is assigned to the correct channel
- Verify the webhook is not disabled
- Test with: `python notifications.py`

### General Issues

**"Module not found" errors**
- Install required packages:
  ```bash
  pip install requests
  ```

**Notifications not sending**
1. Check `EMAIL_ENABLED` or `DISCORD_ENABLED` is `True`
2. Run test: `python notifications.py`
3. Check alert score threshold (`MIN_ALERT_SCORE`)
4. Verify cooldown hasn't prevented notification

---

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `config.py` to `.gitignore`
   - Use environment variables for production

2. **Use app passwords, not main passwords**

3. **Limit webhook permissions**
   - Create a dedicated Discord channel for alerts
   - Don't share webhook URLs publicly

4. **Rotate credentials periodically**

---

## Example Configuration

Here's a complete example `config.py` setup:

```python
# Enable both email and Discord
EMAIL_ENABLED = True
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "mytrading@gmail.com"
EMAIL_PASSWORD = "abcd efgh ijkl mnop"  # App password
EMAIL_TO = "myphone@gmail.com"  # Send to phone for instant alerts

DISCORD_ENABLED = True
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/abcdef..."

# Strict alerts only (score >= 3)
MIN_ALERT_SCORE = 3

# Allow notifications every 30 minutes per ticker
NOTIFICATION_COOLDOWN_MINUTES = 30
```

---

## Advanced: Scheduled Auto-Scanning

To automatically scan your watchlist every N minutes:

```python
# Create scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from scanner import OptionsScanner, Watchlist

def auto_scan():
    print("Running scheduled scan...")
    watchlist = Watchlist()
    scanner = OptionsScanner()
    results = scanner.scan_watchlist(watchlist, send_notifications=True)
    print(f"Scan complete. Found {len([r for r in results if r.has_alerts])} alerts.")

scheduler = BlockingScheduler()
scheduler.add_job(auto_scan, 'interval', minutes=15)  # Scan every 15 minutes

print("Scheduler started. Press Ctrl+C to stop.")
scheduler.start()
```

Install scheduler:
```bash
pip install apscheduler
```

Run continuously:
```bash
python scheduler.py
```

---

## What Gets Alerted?

Notifications are sent for:

1. **Unusual Volume**: Volume > 2x Open Interest
2. **High IV**: IV above 80th percentile (historical)
3. **Put/Call Ratio Extremes**: P/C > 1.5 or < 0.67
4. **Distribution Skew**: Skewness < -0.5 (bearish) or > 0.3 (bullish)
5. **Probability Imbalance**: >60% probability in one direction
6. **IV Changes**: >5% IV increase/decrease since last scan

---

## Support

If you encounter issues:
1. Run the test: `python notifications.py`
2. Check the error messages carefully
3. Verify all credentials in `config.py`
4. Make sure required packages are installed

For Gmail specifically, ensure:
- 2FA is enabled
- App password is created
- "Less secure app access" is NOT needed (app passwords are more secure)
