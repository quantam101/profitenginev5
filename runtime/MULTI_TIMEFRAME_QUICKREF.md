# Multi-Timeframe Signal Validator — Quick Reference

## One-Minute Summary

Validates trading signals across 5min, 30min, and daily timeframes to reduce false signals. Requires 2+ timeframes to confirm before trading.

## Installation

```bash
pip install yfinance requests
```

## Basic Usage

```python
from runtime.multi_timeframe_validator import MultiTimeframeValidator
import asyncio

async def main():
    validator = MultiTimeframeValidator()
    
    # Get signals for all timeframes
    analysis = await validator.get_timeframe_signals('AAPL')
    
    # Check if BUY is valid (needs 2+ confirmations)
    is_valid = await validator.validate_signal('AAPL', 'BUY')
    
    # Get confidence score (0-100)
    confidence = await validator.confidence_score('AAPL', 'BUY')
    
    print(f"Valid: {is_valid}, Confidence: {confidence}%")

asyncio.run(main())
```

## Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_timeframe_signals(symbol)` | Fetch RSI, SMA, trend for all TF | MultiTimeframeAnalysis |
| `validate_signal(symbol, 'BUY'/'SELL')` | Check if signal valid | bool |
| `confidence_score(symbol, 'BUY'/'SELL')` | Rate signal 0-100 | int |
| `get_all_signals(symbols)` | Analyze multiple symbols | dict |

## Signal Rules

**BUY**: RSI < 30 (oversold) + SMA50 > SMA200 (uptrend)
**SELL**: RSI > 70 (overbought) + SMA50 < SMA200 (downtrend)

## Confidence Scoring

- 1 confirmation = 30%
- 2 confirmations = 60%
- 3 confirmations = 90%
- All aligned = +10%
- Extreme RSI (< 20 or > 80) = +10%
- **Maximum = 100%**

## Validation Example

```python
# Require 2+ timeframes to confirm
is_valid = await validator.validate_signal('AAPL', 'BUY', min_confirmations=2)

if is_valid:
    confidence = await validator.confidence_score('AAPL', 'BUY')
    print(f"Trade AAPL BUY ({confidence}% confidence)")
```

## Position Sizing by Confidence

```python
confidence = await validator.confidence_score('AAPL', 'BUY')

if confidence >= 80:
    shares = 100  # Full
elif confidence >= 60:
    shares = 67   # 2/3
else:
    shares = 33   # 1/3
```

## Scan Watchlist

```python
symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA']
results = await validator.get_all_signals(symbols)

for symbol, analysis in results.items():
    if analysis:
        signal = analysis.get_strongest_signal()
        if signal:
            print(f"{symbol}: {signal[0]} ({signal[1]} confirmations)")
```

## Multi-Timeframe Analysis Methods

```python
analysis = await validator.get_timeframe_signals('AAPL')

# Count how many TF confirm signal
buy_count = analysis.get_confirmation_count('BUY')

# Check if all TF aligned
is_aligned = analysis.is_aligned('BUY')

# Get strongest signal across TF
signal_type, confirmations = analysis.get_strongest_signal()
```

## Caching

Automatic caching by timeframe:
- 5min: 60 seconds
- 30min: 300 seconds
- daily: 3600 seconds

Clear cache if needed:
```python
validator.fetcher.cache.clear()
```

## Common Patterns

### Day Trade (5min + 30min only)
```python
is_valid = await validator.validate_signal(
    'AAPL', 'BUY',
    timeframes=['5min', '30min']
)
```

### Swing Trade (30min + daily)
```python
is_valid = await validator.validate_signal(
    'AAPL', 'BUY',
    timeframes=['30min', 'day']
)
```

### Pre-Market Scan
```python
results = await validator.get_all_signals(['AAPL', 'MSFT', 'NVDA'])
buys = {s: a for s, a in results.items() if a and a.get_strongest_signal()[0] == 'BUY'}
```

## Example Integration

```python
from runtime.multi_timeframe_validator import MultiTimeframeValidator
from runtime.example_multi_timeframe_trading import ValidatedTradingExecutor

async def trade():
    executor = ValidatedTradingExecutor(
        min_confirmations=2,
        min_confidence=65,
        position_size_base=100
    )
    
    result = await executor.execute_trade('AAPL', 'BUY', 150.25)
    
    if result['executed']:
        print(f"Bought {result['position_size']} @ ${result['current_price']}")
    else:
        print(f"Rejected: {result['reason']}")
```

## Testing

```bash
# Run tests
pytest runtime/test_multi_timeframe_validator.py -v

# Run specific test
pytest runtime/test_multi_timeframe_validator.py::TestTimeframeSignal -v
```

## Troubleshooting

**No data for symbol?**
- Symbol may be invalid
- yfinance outage
- Clear cache: `validator.fetcher.cache.clear()`

**Slow first call?**
- Normal - yfinance fetching 200 bars
- Subsequent calls hit cache
- First call: 1-2 sec, cached calls: <100ms

**Stale data?**
- Cache hasn't expired yet
- Clear manually: `validator.fetcher.cache.clear()`

## Files

- `runtime/multi_timeframe_validator.py` — Main module (700+ lines)
- `runtime/test_multi_timeframe_validator.py` — Tests (300+ lines)
- `runtime/example_multi_timeframe_trading.py` — Trading examples
- `runtime/MULTI_TIMEFRAME_INTEGRATION.md` — Full documentation

## Performance

- **Parallel analysis**: Use `get_all_signals()` for multiple symbols
- **Caching**: Automatic per-timeframe caching reduces API calls
- **Typical times**:
  - First fetch: 1-2 seconds per symbol
  - Cached fetch: <100ms
  - Parallel (3 symbols): ~2 seconds (vs 6 sequential)

## Next Steps

1. Import into your trading strategy
2. Validate signals before trades
3. Track performance of validated trades
4. Adjust confidence thresholds based on results
5. Use position sizing by confidence

See `MULTI_TIMEFRAME_INTEGRATION.md` for full documentation.
