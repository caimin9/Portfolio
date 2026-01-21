# Added: Breeden-Litzenberger Implied Distribution

## What's New

✅ **Implied Distribution from Options Chain** - Now showing Breeden-Litzenberger distribution
- Uses options chain data to derive market's implied probability distribution
- Shows where the market thinks the stock price will be at expiration
- Current price marked with green dashed line

## Grid Layout Now

**2×3 Grid on Stock Detail Page:**

**Row 1:**
- Price History (1Y) | Rolling Beta vs SPY

**Row 2:**
- Rolling Correlation with SPY | Analyst Ratings

**Row 3:**
- **Implied Distribution (NEW!)** | Fundamentals

## How to Apply

**Quick Restart:**
1. Stop both processes (`Ctrl+C`)
2. Restart backend: `cd options && python api.py`
3. Restart frontend: `cd terminal-app && npm run dev`
4. Go to http://localhost:3000

## What the Distribution Shows

**The Area Chart:**
- **X-axis:** Strike prices
- **Y-axis:** Probability density
- **Green line:** Current stock price
- **Blue area:** Probability distribution

**Metrics Below Chart:**
- **Std Dev:** Expected move (dollar amount)
- **Skew:** Distribution asymmetry
  - Negative = bearish tilt
  - Positive = bullish tilt
- **Current:** Current stock price

**ATM IV in Title:**
- Shows at-the-money implied volatility percentage
- Higher IV = market expects bigger moves

## Use Cases

**1. Expected Range**
- Look at where the distribution is widest
- That's where the market expects price to be

**2. Skew Analysis**
- Negative skew = market pricing in downside protection
- Positive skew = market pricing in upside potential

**3. Compare to Analyst Target**
- See if analyst targets fall within the distribution
- High probability = consensus view
- Low probability = contrarian view

## Example Interpretation

```
AAPL @ $150
Implied Distribution shows:
- Peak around $148-152 (most likely range)
- Std Dev: $8.50 (±5.7% move expected)
- Skew: -0.3 (slight bearish bias)
- ATM IV: 28% (moderate volatility)

Interpretation: Market expects AAPL to stay near current price,
with slight downside bias and moderate volatility.
```

## Troubleshooting

**"No options data available"**
- Stock may not have active options
- Or options data temporarily unavailable
- Try major stocks (AAPL, MSFT, TSLA, SPY)

**Distribution looks weird?**
- Wide strikes = low liquidity
- Narrow distribution = low IV / near expiration
- Multiple peaks = unusual options activity

**Calculation failed?**
Check backend logs for:
```
Distribution calculation failed for TICKER: [error]
```

## Technical Details

**Method:** Breeden-Litzenberger formula
- Derives risk-neutral probability distribution from options prices
- Uses second derivative of call prices with respect to strike

**Data Source:** yfinance options chain
- Nearest expiration by default
- Uses both calls and puts
- Smoothed with cubic spline

**Window:** Current expiration cycle
- Updates when you load the page
- Not historical (uses current options prices)

Enjoy the new distribution analysis! 📊
