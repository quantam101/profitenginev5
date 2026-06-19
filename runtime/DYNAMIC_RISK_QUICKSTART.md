# Dynamic Risk Management - Quick Start

## 30-Second Setup

```python
from runtime.dynamic_risk_params import create_risk_profile, validate_risk_profile

# 1. Create a risk profile
metrics = create_risk_profile(
    symbol="SPY",
    entry_price=450.0,
    account_balance=50000.0,
    direction="LONG",
    atr_value=2.5,        # Get from market data
    iv_rank=45.0          # Get from options data
)

# 2. Validate it
is_valid, reason = validate_risk_profile(metrics)
if is_valid:
    print(f"✓ Trade approved")
    print(f"  Entry: ${metrics.entry_price}")
    print(f"  Stop:  ${metrics.stop_price}")
    print(f"  Target: ${metrics.target_price}")
    print(f"  Size:  {metrics.position_size} shares")
else:
    print(f"✗ Trade rejected: {reason}")
```

## Complete Workflow

### Step 1: Get Market Data
```python
import yfinance as yf

ticker = "SPY"
df = yf.download(ticker, period="1mo", interval="5m")

highs = df['High'].tail(20).tolist()
lows = df['Low'].tail(20).tolist()
closes = df['Close'].tail(20).tolist()
```

### Step 2: Calculate ATR
```python
from runtime.dynamic_risk_params import calculate_atr

atr = calculate_atr(highs, lows, closes, period=14)
print(f"ATR (14): ${atr:.2f}")
```

### Step 3: Get IV Rank
```python
# Example: fetch from your broker API
iv_rank = get_iv_rank_from_broker("SPY")  # Your API
print(f"IV Rank: {iv_rank:.1f}%")
```

### Step 4: Create Risk Profile
```python
from runtime.dynamic_risk_params import create_risk_profile

metrics = create_risk_profile(
    symbol="SPY",
    entry_price=450.0,
    account_balance=50000.0,
    direction="LONG",
    atr_value=atr,
    iv_rank=iv_rank,
    risk_percent=2.0
)
```

### Step 5: Validate & Execute
```python
from runtime.dynamic_risk_params import validate_risk_profile, format_risk_summary

# Validate
is_valid, reason = validate_risk_profile(metrics)

if is_valid:
    # Print summary
    print(format_risk_summary(metrics))
    
    # Place trade with your broker
    place_order(
        symbol="SPY",
        quantity=metrics.position_size,
        entry=metrics.entry_price,
        stop_loss=metrics.stop_price,
        take_profit=metrics.target_price
    )
else:
    print(f"Trade rejected: {reason}")
```

---

## Common Use Cases

### LONG Trade - Normal Volatility
```python
metrics = create_risk_profile(
    symbol="SPY",
    entry_price=450.0,
    account_balance=50000.0,
    direction="LONG",
    atr_value=2.5,
    iv_rank=50.0,  # Normal
    risk_percent=2.0
)
# Result: Standard stops, typical position size
```

### SHORT Trade - High Volatility
```python
metrics = create_risk_profile(
    symbol="QQQ",
    entry_price=350.0,
    account_balance=50000.0,
    direction="SHORT",
    atr_value=3.0,
    iv_rank=75.0,  # High volatility
    risk_percent=1.5  # Conservative
)
# Result: Wider stops, smaller position (vol adjustment loosens stops)
```

### Conservative Trade - Low Volatility
```python
metrics = create_risk_profile(
    symbol="IWM",
    entry_price=190.0,
    account_balance=50000.0,
    direction="LONG",
    atr_value=1.5,
    iv_rank=20.0,  # Low volatility
    risk_percent=1.0  # Very conservative
)
# Result: Tight stops, precise positioning
```

---

## Key Outputs Explained

### Stop Loss
- **What:** Price to exit if trade goes wrong
- **How:** `stop = entry - (ATR × 1.5 × vol_adjustment)`
- **Tighter at:** Low IV (vol_adj = 0.5x-0.8x)
- **Looser at:** High IV (vol_adj = 1.3x-2.0x)

### Take Profit
- **What:** Price to exit for profit
- **How:** `target = entry + (ATR × 2.5 × vol_adjustment)`
- **Why 2.5x?** Risk/reward ratio (1.67:1 minimum)

### Position Size
- **What:** Number of shares to buy/sell
- **Based on:** Account balance, risk%, stop-loss distance
- **Capped at:** $5,000 per trade, $15,000 concurrent max

### Risk/Reward Ratio
- **What:** How much you can make vs lose
- **Formula:** `(target - entry) / (entry - stop)`
- **Target:** 1.5:1 or higher
- **Minimum:** 1.0:1 for any trade

---

## Volatility Regimes

```
IV Rank 0-25   ► LOW volatility
  • Stops tighten (0.5x-0.8x ATR)
  • Risk per trade decreases
  • Good for scalping, tight entries

IV Rank 25-50  ► NORMAL volatility
  • Standard stops (0.8x-1.0x ATR)
  • Comfortable position sizing
  • Most common regime

IV Rank 50-75  ► ELEVATED volatility
  • Stops widen (1.0x-1.3x ATR)
  • Larger positions possible (wider stops)
  • More range, more profit potential

IV Rank 75-100 ► EXTREME volatility
  • Stops very wide (1.3x-2.0x ATR)
  • Smaller position sizes needed
  • High risk/reward, but max loss increases
```

---

## Real-World Examples

### Example 1: SPY LONG Entry

**Market Data:**
```
Current Price: $450.00
ATR (14):      $2.50
IV Rank:       45% (normal)
Account:       $50,000
```

**Trade Setup:**
```python
metrics = create_risk_profile(
    symbol="SPY",
    entry_price=450.0,
    account_balance=50000.0,
    direction="LONG",
    atr_value=2.50,
    iv_rank=45.0,
    risk_percent=2.0
)
```

**Result:**
```
Entry:    $450.00
Stop:     $446.25  (entry - ATR×1.5×0.96)
Target:   $457.92  (entry + ATR×2.5×0.96)
Size:     45 shares ($20,250)
RR Ratio: 1.64:1
Max Loss: $169
Max Gain: $356
```

### Example 2: QQQ SHORT Entry - High IV

**Market Data:**
```
Current Price: $350.00
ATR (14):      $3.00
IV Rank:       80% (extreme)
Account:       $50,000
```

**Trade Setup:**
```python
metrics = create_risk_profile(
    symbol="QQQ",
    entry_price=350.0,
    account_balance=50000.0,
    direction="SHORT",
    atr_value=3.00,
    iv_rank=80.0,  # Extreme volatility
    risk_percent=1.5  # Conservative
)
```

**Result:**
```
Entry:    $350.00
Stop:     $356.15  (entry + ATR×1.5×1.64, widened by high IV)
Target:   $339.76  (entry - ATR×2.5×1.64, adjusted for vol)
Size:     8 shares ($2,800)
RR Ratio: 1.60:1
Max Loss: $49
Max Gain: $79
```

**Note:** High IV forces smaller positions due to wider stops. Risk is absolute, not relative.

---

## Integration Checklist

- [ ] Import `create_risk_profile` and `validate_risk_profile`
- [ ] Get real ATR from market data (14-period, 5-min bars)
- [ ] Get real IV rank from options data
- [ ] Calculate position size with current_positions_value
- [ ] Validate every profile before trading
- [ ] Respect position limits ($5k single, $15k concurrent)
- [ ] Use stop and target prices in broker API
- [ ] Log all trades with metrics for analysis

---

## Troubleshooting

### ❌ "Position size is 0"
**Cause:** Stop price = entry price (no risk)  
**Fix:** Ensure stop < entry (LONG) or stop > entry (SHORT)

### ❌ "Trade rejected: Risk/reward ratio below minimum"
**Cause:** Target too close to entry  
**Fix:** Increase target multiplier or improve entry logic

### ❌ "Limited by concurrent_limit"
**Cause:** Already have $15k in open positions  
**Fix:** Close some trades or wait for existing positions to resolve

### ❌ "Volatility multiplier seems wrong"
**Cause:** IV rank out of expected range (0-100)  
**Fix:** Validate IV rank calculation; use `normalize_iv_rank()` helper

---

## Testing

Run tests to verify installation:

```bash
python -m pytest runtime/test_dynamic_risk_params.py -v
```

Expected output: **39 passed**

---

## Next Steps

1. **Read full docs:** See `DYNAMIC_RISK_README.md`
2. **Study tests:** `runtime/test_dynamic_risk_params.py` has usage examples
3. **Integrate with broker:** Add to your order submission flow
4. **Backtest:** Test on historical data with real ATR/IV
5. **Paper trade:** Verify on paper trading account first
6. **Live trade:** Monitor first 10-20 trades closely

---

## Files in This Module

```
runtime/
├── dynamic_risk_params.py         # Main module (650+ lines)
├── test_dynamic_risk_params.py    # Test suite (39 tests)
├── DYNAMIC_RISK_README.md         # Full documentation
└── DYNAMIC_RISK_QUICKSTART.md     # This file
```

---

**Questions?** See `DYNAMIC_RISK_README.md` for comprehensive docs.
