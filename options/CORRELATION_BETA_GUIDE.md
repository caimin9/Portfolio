# Rolling Correlations & Beta Analysis Guide

## Overview

The correlation and beta analysis module helps you understand:
- **Diversification** - Are your assets moving together or independently?
- **Systematic Risk** - How sensitive is your asset to market movements?
- **Regime Changes** - When do relationships between assets break down?
- **Hedge Effectiveness** - Is your hedge actually protecting you?

---

## Key Concepts

### 1. Correlation

**What it is:** Measures how two assets move together (-1 to +1)

**Interpretation:**
- **+1.0**: Perfect positive correlation (move together)
- **+0.7 to +1.0**: Strong positive (usually move together)
- **+0.3 to +0.7**: Moderate positive (often move together)
- **-0.3 to +0.3**: Low/neutral (move independently) - **BEST for diversification**
- **-0.7 to -0.3**: Moderate negative (often move opposite)
- **-1.0 to -0.7**: Strong negative (usually move opposite)
- **-1.0**: Perfect negative correlation (mirror opposites)

**Example:**
```python
from correlation_analysis import quick_correlation

# How correlated are Apple and Microsoft?
corr = quick_correlation('AAPL', 'MSFT', window=60, period='2y')
# Result: 0.75 = Strong positive correlation
# Interpretation: Limited diversification benefit
```

### 2. Beta

**What it is:** Measures systematic risk - how much an asset moves relative to the market

**Interpretation:**
- **β = 1.0**: Moves exactly with the market (SPY has β = 1.0)
- **β > 1.0**: More volatile than market (amplified swings)
  - β = 1.5: If market moves ±1%, asset moves ±1.5%
- **β < 1.0**: Less volatile than market (dampened swings)
  - β = 0.5: If market moves ±1%, asset moves ±0.5%
- **β ≈ 0**: Market-neutral (moves independently)
- **β < 0**: Inverse to market (rare - some inverse ETFs)

**Example:**
```python
from correlation_analysis import quick_beta

# How risky is Tesla relative to S&P 500?
beta = quick_beta('TSLA', 'SPY', window=60, period='2y')
# Result: β = 2.1
# Interpretation: 2x market volatility - HIGH systematic risk
```

### 3. Alpha

**What it is:** Excess return above what beta predicts (skill vs luck)

**Interpretation:**
- **α > 0**: Outperforming expected return (positive excess return)
- **α = 0**: Performing exactly as expected based on beta
- **α < 0**: Underperforming expected return

**Example:**
- Stock has β = 1.2, market returns 10%
- Expected return = 1.2 × 10% = 12%
- Actual return = 15%
- Alpha = 15% - 12% = +3% (outperformance)

### 4. R² (R-Squared)

**What it is:** How much of price movement is explained by the market

**Interpretation:**
- **R² = 1.0**: 100% explained by market (pure systematic risk)
- **R² = 0.7**: 70% explained by market
- **R² = 0.5**: 50% explained by market, 50% idiosyncratic
- **R² = 0.0**: 0% explained by market (pure company-specific risk)

**Example:**
- AAPL: R² = 0.65 → 65% market-driven, 35% company-specific
- Diversified index fund: R² = 0.95+ → almost entirely market-driven

---

## Use Cases

### 1. Portfolio Diversification

**Goal:** Build a portfolio where assets don't all crash together

**Method:**
```python
from correlation_analysis import analyze_portfolio_correlations

# Analyze your portfolio
tickers = ['SPY', 'TLT', 'GLD', 'VNQ', 'EEM']
corr_matrix = analyze_portfolio_correlations(tickers, window=60)

# Look for:
# - Low average correlation (< 0.5 is good)
# - No high correlation pairs (> 0.7)
# - Diversification score > 1.2
```

**Ideal Portfolio Correlation:**
- Stocks (SPY) + Bonds (TLT): Low/negative correlation
- US Stocks (SPY) + Gold (GLD): Low correlation
- US (SPY) + International (EEM): Moderate correlation
- Stocks (SPY) + Real Estate (VNQ): Moderate correlation

**Red Flags:**
- Tech stocks all > 0.8 correlation (e.g., AAPL, MSFT, GOOGL)
- Energy stocks > 0.9 correlation (e.g., XOM, CVX, COP)
- Small cap ETFs > 0.95 correlation (e.g., IJR, VB, IWM)

### 2. Risk Management

**Goal:** Understand and control portfolio risk

**Method:**
```python
# Check beta for each position
from correlation_analysis import quick_beta

for ticker in portfolio:
    beta = quick_beta(ticker, 'SPY')

    if beta.current_beta > 1.5:
        print(f"⚠️ {ticker}: HIGH risk (β = {beta.current_beta:.2f})")
    elif beta.current_beta < 0.5:
        print(f"✓ {ticker}: LOW risk (β = {beta.current_beta:.2f})")
```

**Portfolio Beta:**
- Average your position betas weighted by position size
- Portfolio β = 1.0: Market risk
- Portfolio β = 1.3: 30% more volatile than market
- Portfolio β = 0.7: 30% less volatile (more defensive)

### 3. Hedge Effectiveness

**Goal:** Verify your hedge is actually working

**Method:**
```python
# Check if SPY put options hedge your long SPY position
from correlation_analysis import quick_correlation

corr = quick_correlation('SPY', 'SH', window=60)  # SH = inverse SPY

# Want strong NEGATIVE correlation (< -0.7)
if corr.iloc[-1] < -0.7:
    print("✓ Good hedge - inverse relationship strong")
else:
    print("⚠️ Poor hedge - consider alternatives")
```

**Good Hedges:**
- SPY long + SPY puts: Very negative correlation
- Tech stocks + inverse tech ETF: Strong negative
- Stocks + VIX calls: Negative (VIX spikes when stocks crash)

**Poor Hedges:**
- Tech stocks + different tech stocks: Still positive correlation
- US stocks + international stocks: Moderate positive (crash together)

### 4. Regime Change Detection

**Goal:** Know when market relationships break down

**Method:**
```python
from correlation_analysis import CorrelationAnalyzer

analyzer = CorrelationAnalyzer()
changes = analyzer.detect_correlation_regime_change(
    'SPY', 'TLT', period='2y', threshold=0.3
)

# Look for major shifts
for change in changes:
    if change['regime'] == 'breakdown':
        print(f"⚠️ {change['date']}: Diversification broke down")
        print(f"   Correlation went from {change['from_corr']:.2f} to {change['to_corr']:.2f}")
```

**Important Regime Changes:**
- **Stock-Bond correlation** turning positive (normally negative)
  - Happens during stagflation or liquidity crises
  - Diversification fails when you need it most
- **Tech correlation spike** (all tech stocks moving together)
  - Sector rotation, increased systematic risk
  - Harder to find stock-specific alpha
- **Gold correlation** with stocks increasing
  - Fear trade weakening
  - Gold losing safe-haven status

### 5. Sector Rotation

**Goal:** Identify which sectors are leading/lagging

**Method:**
```python
# Compare sector ETFs
sectors = ['XLK', 'XLF', 'XLE', 'XLV', 'XLY', 'XLP']

corr_matrix = analyze_portfolio_correlations(sectors)

# Low correlation = independent movement = rotation opportunity
# High correlation = sector correlation = market-wide trend
```

**Rotation Signals:**
- Defensive sectors (XLP, XLU) leading → Market topping
- Cyclical sectors (XLE, XLB) leading → Market strengthening
- Tech (XLK) decoupling → Flight to growth or sector bubble

### 6. Position Sizing

**Goal:** Size positions based on contribution to portfolio risk

**Method:**
```python
# High beta → Smaller position (more volatile)
# Low beta → Larger position (less volatile)

for ticker in portfolio:
    beta = quick_beta(ticker, 'SPY')

    # Risk-adjust position size
    base_size = 10000  # $10k base
    adjusted_size = base_size / beta.current_beta

    print(f"{ticker}: ${adjusted_size:.0f} (β = {beta.current_beta:.2f})")
```

**Example:**
- NVDA (β = 2.0) → $5,000 position (high vol, smaller size)
- KO (β = 0.6) → $16,600 position (low vol, larger size)
- Result: Equal risk contribution despite different volatilities

---

## Common Patterns

### Pattern 1: Crisis Correlation Spike
**What happens:** All correlations go to +1.0 during market crashes

**Why:** Indiscriminate selling - everything drops together

**Action:**
- Monitor correlation trends (rising = danger)
- Diversify across TRUE uncorrelated assets (bonds, gold, cash)
- Don't rely on stock-stock diversification in crashes

### Pattern 2: Low Volatility, High Correlation
**What happens:** VIX is low but stocks moving together

**Why:** Complacency, passive investing, ETF flows

**Action:**
- Stock picking won't work (all boats rise/fall together)
- Focus on market timing or broad beta exposure
- Look for uncorrelated opportunities (commodities, crypto, etc.)

### Pattern 3: Beta Decay
**What happens:** Growth stock beta drops as it matures

**Why:** Company becomes less risky, more predictable

**Action:**
- AAPL: Used to be β = 1.5, now β = 1.1
- Adjust expectations for returns
- May need to rotate to higher beta for growth

### Pattern 4: Correlation Mean Reversion
**What happens:** Extreme correlations don't last

**Why:** Market relationships are somewhat stable long-term

**Action:**
- Very high correlation (> 0.9) → Likely to decrease
- Very low correlation (< 0.1) → Likely to increase
- Don't assume current correlation persists

---

## Dashboard Usage

### Rolling Correlation Tab

1. Enter two tickers
2. Set window (60 days = ~3 months is good default)
3. Click "Calculate"
4. Analyze:
   - Current correlation
   - Is it above/below mean?
   - Trending up or down?
   - High volatility in correlation = unstable relationship

### Rolling Beta Tab

1. Enter asset and benchmark (usually SPY)
2. Set window
3. Click "Calculate"
4. Analyze:
   - Current beta vs historical average
   - Is it in HIGH/LOW/NORMAL regime?
   - Alpha (outperformance/underperformance)
   - R² (how much is market vs company-specific)

### Portfolio Correlations Tab

1. Enter multiple tickers (one per line)
2. Click "Calculate Matrix"
3. Analyze:
   - Heatmap colors (red = high correlation = clustering)
   - Average correlation (want < 0.5)
   - High correlation pairs (> 0.7) → reduce overlap
   - Diversification score

---

## Pro Tips

### 1. Window Selection

**Short windows (20-30 days):**
- ✓ Responsive to recent changes
- ✗ Noisy, many false signals
- Use for: Active trading, regime change detection

**Medium windows (60-90 days):**
- ✓ Balance of responsiveness and stability
- ✗ May lag major shifts slightly
- Use for: General analysis, portfolio review

**Long windows (180-252 days):**
- ✓ Smooth, stable estimates
- ✗ Slow to react to changes
- Use for: Strategic allocation, long-term planning

**Recommendation:** Use 60-day window as default, but check multiple windows

### 2. Multiple Benchmarks

Don't just use SPY for beta:
- **Tech stocks:** Use QQQ (Nasdaq)
- **Small caps:** Use IWM (Russell 2000)
- **Value stocks:** Use VTV (Value index)
- **International:** Use EFA (EAFE)
- **Sector-specific:** Use sector ETF (XLF for banks, etc.)

### 3. Correlation Stability

Check correlation over multiple periods:
```python
# Is correlation stable or changing?
corr_60d = quick_correlation('A', 'B', window=60)
corr_120d = quick_correlation('A', 'B', window=120)
corr_252d = quick_correlation('A', 'B', window=252)

# Stable if all similar (within 0.2)
# Unstable if large differences (> 0.3)
```

### 4. Crisis Stress Test

Check correlations during past crises:
```python
# Manually filter to crisis periods
# March 2020 (COVID crash)
# Q4 2018 (rate fears)
# 2008 (financial crisis)

# Do correlations spike? By how much?
# Does your diversification hold up?
```

---

## Advanced Concepts

### Conditional Correlation

Correlation changes based on market conditions:
- **Bull market:** Lower correlations (dispersion)
- **Bear market:** Higher correlations (everything falls)
- **High VIX:** Correlations spike
- **Low VIX:** Correlations disperse

**Implication:** Diversification works best when you need it least

### Dynamic Correlation

Use EWMA (exponentially weighted) for adaptive correlation:
- Recent data weighted more heavily
- Faster response to regime changes
- Reduces lag compared to simple rolling windows

### Tail Correlation

Regular correlation measures typical conditions. Tail correlation measures extremes:
- Assets might have low normal correlation
- But high correlation during crashes (left tail)
- Important for risk management

### Copulas

Beyond linear correlation:
- Model joint distributions
- Capture non-linear relationships
- Better for tail risk analysis

---

## Troubleshooting

### "No data fetched for any ticker"
- Check ticker symbols are correct
- Ensure internet connection
- Try longer period ('5y' instead of '2y')
- Some tickers may be delisted or have gaps

### "Not enough valid options data"
- Different issue - this is for correlations, not options
- Ensure tickers have sufficient history
- Need at least min_periods (default 30 days) of overlap

### Correlation = NaN
- Not enough overlapping data
- Different trading hours (US vs international)
- One asset has data gaps
- Try longer period or different window

### Beta seems wrong
- Check you're using correct benchmark
- Verify period has sufficient data
- Look at R² - low R² means beta less meaningful
- Compare to published betas (e.g., Yahoo Finance)

---

## Summary

**Key Takeaways:**

1. **Correlation tells you about diversification**
   - Want low (< 0.5) for different assets
   - Watch for regime changes (spikes = danger)

2. **Beta tells you about systematic risk**
   - β > 1: More volatile than market
   - β < 1: Less volatile (defensive)
   - Use for position sizing and risk budgeting

3. **Alpha tells you about skill/luck**
   - Positive alpha = good (but hard to sustain)
   - Focus on risk-adjusted returns, not just alpha

4. **R² tells you about diversification potential**
   - Low R²: More company-specific risk/return
   - High R²: Mostly market-driven

5. **Monitor rolling metrics, not just current**
   - Relationships change over time
   - Regime changes matter
   - Past doesn't predict future perfectly

**Best Practices:**
- Check correlations monthly for portfolio review
- Monitor beta for position sizing
- Watch for correlation regime changes
- Stress test during past crises
- Don't assume relationships are stable

**Remember:** Correlation ≠ Causation. Just because two assets move together doesn't mean one causes the other to move!
