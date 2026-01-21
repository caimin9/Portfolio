# Terminal Dashboard Guide

## Overview

**Single-page professional terminal** - Bloomberg-style layout with all key analytics visible at once.

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  📊 OPTIONS ANALYTICS TERMINAL              🕐 19:45:32     │
├─────────────────────────────────────────────────────────────┤
│  Value    P&L    Beta   Vol   Corr   Positions             │
│  $50K   +$2.5K   1.2   15%   0.45       5                   │
├─────────────────────────────────────────────────────────────┤
│  ⚠️ Alerts (if any)                                         │
├─────────────────────────────────────────────────────────────┤
│  ⚙️ Controls (collapsible)                                  │
│  Lookback: 60 days   [🔄 Refresh]  [➕ Manage]             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Cumulative P&L              │  Rolling Beta                │
│  [Line chart]                │  [Multi-line chart]          │
│                              │                               │
├──────────────────────────────┼──────────────────────────────┤
│                              │                               │
│  Correlation Matrix          │  Price Forecast              │
│  [Heatmap]                   │  [Distribution bars]         │
│                              │                               │
├─────────────────────────────────────────────────────────────┤
│  Additional Analytics (tabs)                                 │
│  Greeks | Positions | Risk Metrics                          │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Top Header (Always Visible)
- **6 Key Metrics** in one row
- Real-time updates
- Color-coded deltas

### 2×2 Live Chart Grid

**Top Left: Cumulative P&L**
- Time series of portfolio P&L
- Filled area chart
- Current P&L annotation
- Adjustable lookback period

**Top Right: Rolling Beta**
- Top 3 positions by weight
- Separate line for each
- Market beta reference line
- Shows position weights

**Bottom Left: Correlation Matrix**
- Heatmap of all positions
- Color scale: -1 (red) to +1 (green)
- Average correlation displayed
- Updates with lookback period

**Bottom Right: Price Forecast**
- Implied distribution (largest position)
- Current vs expected price
- 68% confidence range
- Days to expiration

### Controls (Collapsible)
- **Lookback Period**: 30d, 60d, 90d, 120d, 180d, 252d
- **Refresh Button**: Force data reload
- **Manage Positions**: Quick link to sidebar

### Additional Tabs
- **Greeks**: Delta, Gamma, Theta, Vega
- **Positions**: Full table with P&L
- **Risk Metrics**: VaR, Expected Move, Diversification

### Sidebar (Collapsed)
- Position management
- Quick add functionality
- Remove positions

## Usage

### Launch
```bash
streamlit run dashboard_terminal.py
```

### Add Positions
1. Click "➕ Manage Positions" OR
2. Open sidebar (arrow in top-left)
3. Enter ticker, quantity, price
4. Click "Add Stock"

### Adjust Lookback
1. Click "⚙️ Controls"
2. Select period (30-252 days)
3. Charts update automatically

### Refresh Data
- Click "🔄 Refresh Data" in controls
- Or just refresh browser page

## What Each Chart Shows

### Cumulative P&L
**What:** Portfolio profit/loss over time
**How:** Current value - cost basis, calculated daily
**Good:** Steady upward trend
**Bad:** Large drawdowns, high volatility

### Rolling Beta
**What:** Systematic risk (market sensitivity)
**How:** Regression of returns vs SPY
**β = 1.0:** Moves with market
**β > 1.0:** More volatile (amplified swings)
**β < 1.0:** Less volatile (defensive)

### Correlation Matrix
**What:** How positions move together
**How:** Correlation of daily returns
**Green (positive):** Move together
**Red (negative):** Move opposite
**Want:** Low correlation (< 0.5) for diversification

### Price Forecast
**What:** Market-implied distribution
**How:** Breeden-Litzenberger from options
**Shows:** Where price likely to be by expiration
**Use:** Probability of targets, expected moves

## Quick Tips

### For Day Trading
- Use 30-day lookback
- Watch P&L chart for trends
- Monitor beta for volatility

### For Position Trading
- Use 90-180 day lookback
- Focus on correlations
- Check forecast distributions

### For Risk Management
- Watch correlation matrix (> 0.7 = clustered)
- Check beta (> 1.5 = high risk)
- Monitor VaR in risk metrics tab

## Keyboard Shortcuts

- `R` - Refresh app
- `C` - Clear cache
- `?` - Keyboard shortcuts

## Comparison to Multi-Page

| Multi-Page | Terminal |
|------------|----------|
| Click through 6 pages | ✅ Everything visible |
| Metrics scattered | ✅ All in header |
| Separate charts | ✅ 2×2 grid |
| Hard to compare | ✅ Side-by-side |
| Slow navigation | ✅ Instant view |

## When to Use

**Terminal Dashboard:**
- Active monitoring
- Quick decisions
- All-in-one view
- Professional trading

**Multi-Page Dashboard:**
- Deep dive analysis
- Detailed exploration
- Step-by-step workflow
- Learning/research

## Performance

**Load Time:**
- Empty portfolio: < 1 second
- 1-5 positions: 3-5 seconds
- 6-10 positions: 5-10 seconds

**Refresh:**
- Cached: Instant
- Full recalc: 5-15 seconds

## Color Guide

- **Purple (#6366f1)**: Primary accent, buttons
- **Green (#10b981)**: Positive, profit, good
- **Red (#ef4444)**: Negative, loss, warning
- **Orange (#f59e0b)**: Warning, moderate
- **Cyan (#3b82f6)**: Info, neutral
- **Gray (#9090a8)**: Labels, secondary text

## Pro Tips

1. **Keep it Clean**: 5-10 positions max for best visibility
2. **Set Lookback**: Match your trading timeframe
3. **Watch Correlations**: High = adjust portfolio
4. **Monitor Beta**: Keep below 1.5 for moderate risk
5. **Use Alerts**: They catch issues automatically

## Summary

**One screen. All data. Professional terminal.**

No clicking through pages. No hunting for metrics. Everything you need visible at once.

Perfect for active traders and portfolio managers.
