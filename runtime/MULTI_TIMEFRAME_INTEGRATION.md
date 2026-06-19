# Multi-Timeframe Signal Validator — Integration Guide

## Overview

The `MultiTimeframeValidator` module confirms trading signals across multiple timeframes (5min, 30min, daily) to reduce false signals and improve trade quality.

**Key Features:**
- Fetches technical data (RSI, SMA50, SMA200) for each timeframe
- Generates BUY/SELL signals based on RSI + trend confirmation
- Validates signals across 2+ timeframes before trading
- Calculates confidence score (0-100) for trade quality
- Caches data to reduce API calls

## Installation

```bash
# Ensure dependencies are installed
pip install yfinance requests

# Validator is ready to use
from runtime.multi_timeframe_validator import MultiTimeframeValidator
```

## Quick Start

### 1. Create a Validator Instance

```python
from runtime.multi_timeframe_validator import MultiTimeframeValidator
import asyncio

async def main():
    validator = MultiTimeframeValidator()
    # Now use validator methods...

asyncio.run(main())
```

### 2. Get Signals for All Timeframes

```python
# Fetch RSI, SMA50, SMA200 for 5min, 30min, and daily
analysis = await validator.get_timeframe_signals('AAPL')
print(analysis)

# Output example:
# MultiTimeframeAnalysis(AAPL):
#   TimeframeSignal(5min): Price=150.25, RSI=28.3, SMA50=150.10, SMA200=145.30, Trend=UP
#   TimeframeSignal(30min): Price=150.30, RSI=32.1, SMA50=150.20, SMA200=145.40, Trend=UP
#   TimeframeSignal(day): Price=150.28, RSI=45.5, SMA50=151.00, SMA200=146.00, Trend=UP
#   BUY confirmations: 2, SELL confirmations: 0
```

### 3. Validate a Trading Signal

```python
# Check if BUY signal is valid (needs 2+ timeframe confirmations)
is_valid = await validator.validate_signal('AAPL', 'BUY', min_confirmations=2)

if is_valid:
    print("Trade AAPL BUY - signal confirmed across 2+ timeframes")
else:
    print("Wait - signal needs more confirmation")
```

### 4. Get Confidence Score (0-100)

```python
# Rate signal strength
confidence = await validator.confidence_score('AAPL', 'BUY')

if confidence >= 70:
    print(f"Strong signal: {confidence}% confidence")
elif confidence >= 50:
    print(f"Moderate signal: {confidence}% confidence")
else:
    print(f"Weak signal: {confidence}% confidence - skip or reduce size")
```

### 5. Analyze Multiple Symbols

```python
# Scan multiple tickers in parallel
symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD']
results = await validator.get_all_signals(symbols)

for symbol, analysis in results.items():
    if analysis:
        signal_type, count = analysis.get_strongest_signal()
        confidence = await validator.confidence_score(symbol, signal_type)
        print(f"{symbol}: {signal_type} ({count} confirmations, {confidence}% confidence)")
```

## Signal Generation Rules

### BUY Signal
Generated when:
- **RSI < 30** (oversold) AND
- **SMA50 > SMA200** (uptrend confirmed)

**Interpretation:** Asset is oversold but in uptrend → buying opportunity

### SELL Signal
Generated when:
- **RSI > 70** (overbought) AND
- **SMA50 < SMA200** (downtrend confirmed)

**Interpretation:** Asset is overbought and in downtrend → selling opportunity

### NO SIGNAL
When:
- RSI is neutral (30-70) regardless of trend
- RSI is extreme (< 30 or > 70) but trend is opposite
- Both conditions don't align

## Confidence Scoring (0-100)

Scoring breakdown:

| Condition | Points |
|-----------|--------|
| No confirmations | 0 |
| 1 timeframe confirms | 30 |
| 2 timeframes confirm | 60 |
| 3 timeframes confirm | 90 |
| **Bonuses:** |
| All timeframes aligned | +10 |
| Extreme RSI (< 20 or > 80) | +10 |
| **Maximum** | **100** |

**Examples:**
- 2 confirmations + extreme RSI = 60 + 10 = **70%**
- 3 confirmations + aligned + extreme RSI = 90 + 10 + 10 = **100%** (capped)
- 1 confirmation only = **30%** (low confidence)

## Integration with Trading System

### With PaperTradingSimulator

```python
from runtime.paper_trader_pro import PaperTradingSimulator
from runtime.multi_timeframe_validator import MultiTimeframeValidator

async def trade_with_validation():
    simulator = PaperTradingSimulator()
    validator = MultiTimeframeValidator()

    for symbol in simulator.WATCHLIST:
        # Get signal across timeframes
        is_valid = await validator.validate_signal(
            symbol,
            'BUY',
            min_confirmations=2
        )

        if is_valid:
            # Only trade if 2+ timeframes confirm
            confidence = await validator.confidence_score(symbol, 'BUY')
            
            # Size position based on confidence
            if confidence >= 80:
                position_size = 100  # Full size
            elif confidence >= 60:
                position_size = 66   # 2/3 size
            else:
                position_size = 33   # 1/3 size
            
            # Execute trade
            print(f"BUY {symbol}: {position_size} shares ({confidence}% confidence)")
```

### With TradingSignalAgent

```python
from runtime.agents_specialized import TradingSignalAgent
from runtime.multi_timeframe_validator import MultiTimeframeValidator

class EnhancedTradingSignalAgent(TradingSignalAgent):
    """Extends trading agent with multi-timeframe validation"""

    async def execute(self, task):
        validator = MultiTimeframeValidator()
        
        for symbol in task.get('symbols', []):
            # Get base signal from existing strategies
            base_signal = await self._run_strategies(symbol)
            
            if base_signal:
                # Validate with multi-timeframe check
                is_valid = await validator.validate_signal(
                    symbol,
                    base_signal,
                    min_confirmations=2
                )
                confidence = await validator.confidence_score(symbol, base_signal)
                
                if is_valid and confidence >= 60:
                    # Emit confirmed signal
                    self.signals.append({
                        'symbol': symbol,
                        'signal': base_signal,
                        'confidence': confidence,
                        'timestamp': time.time()
                    })
```

## API Reference

### MultiTimeframeValidator

#### `get_timeframe_signals(symbol, timeframes=['5min','30min','day'])`

Fetch signals across timeframes.

**Args:**
- `symbol` (str): Stock ticker (e.g., 'AAPL')
- `timeframes` (list): Timeframes to analyze (default: all three)

**Returns:**
- `MultiTimeframeAnalysis`: Contains signals for each timeframe

**Example:**
```python
analysis = await validator.get_timeframe_signals('AAPL', timeframes=['5min', '30min'])
```

#### `validate_signal(symbol, base_signal, min_confirmations=2, timeframes=None)`

Validate a trading signal across timeframes.

**Args:**
- `symbol` (str): Stock ticker
- `base_signal` (str): 'BUY' or 'SELL'
- `min_confirmations` (int): Minimum confirming timeframes (default: 2)
- `timeframes` (list): Optional timeframe list

**Returns:**
- `bool`: True if signal valid, False otherwise

**Example:**
```python
is_valid = await validator.validate_signal('AAPL', 'BUY', min_confirmations=2)
```

#### `confidence_score(symbol, base_signal, timeframes=None)`

Calculate signal confidence (0-100).

**Args:**
- `symbol` (str): Stock ticker
- `base_signal` (str): 'BUY' or 'SELL'
- `timeframes` (list): Optional timeframe list

**Returns:**
- `int`: Confidence score 0-100

**Example:**
```python
confidence = await validator.confidence_score('AAPL', 'BUY')
```

#### `get_all_signals(symbols)`

Analyze multiple symbols in parallel.

**Args:**
- `symbols` (list): List of tickers

**Returns:**
- `dict`: Maps symbol → MultiTimeframeAnalysis

**Example:**
```python
results = await validator.get_all_signals(['AAPL', 'MSFT', 'NVDA'])
```

#### `get_last_analysis(symbol)`

Get cached analysis (non-async).

**Args:**
- `symbol` (str): Stock ticker

**Returns:**
- `MultiTimeframeAnalysis` or None

**Example:**
```python
cached = validator.get_last_analysis('AAPL')
```

### MultiTimeframeAnalysis

Methods on result object:

#### `get_confirmation_count(signal_type)`

Count timeframes confirming signal.

**Returns:**
- `int`: 0-3 (number of confirming timeframes)

#### `is_aligned(signal_type)`

Check if all timeframes agree.

**Returns:**
- `bool`: True if all timeframes show same signal

#### `get_strongest_signal()`

Find best signal across timeframes.

**Returns:**
- `tuple`: ('BUY' or 'SELL', count) or None

## Caching Strategy

The validator caches data to minimize API calls:

| Timeframe | Cache Duration |
|-----------|-----------------|
| 5min | 60 seconds |
| 30min | 300 seconds (5 min) |
| daily | 3600 seconds (1 hour) |

Cache is invalidated when TTL expires, automatically fetching fresh data.

**Manual cache reset:**
```python
# Clear all caches
validator.fetcher.cache.clear()

# Clear specific symbol
validator.fetcher.cache.pop('AAPL_5min', None)
```

## Performance Considerations

### Data Fetching

Timeframe data fetching uses yfinance:
- **5min/30min**: Fetches up to 60 days of history
- **daily**: Fetches up to 1 year of history

First fetch may take 1-2 seconds per symbol/timeframe. Subsequent calls use cache.

### Parallel Analysis

Use `get_all_signals()` for multiple symbols:

```python
# Sequential: ~2 seconds per symbol
for symbol in ['AAPL', 'MSFT', 'NVDA']:
    analysis = await validator.get_timeframe_signals(symbol)

# Parallel: ~2 seconds total
results = await validator.get_all_signals(['AAPL', 'MSFT', 'NVDA'])
```

## Error Handling

```python
try:
    analysis = await validator.get_timeframe_signals('INVALID')
except Exception as e:
    print(f"Error: {e}")
    # Falls back to cached analysis if available
    cached = validator.get_last_analysis('INVALID')
```

## Common Patterns

### Pattern 1: Day Trade Filter

```python
# Only take signals on 5min + 30min alignment (avoid daily noise)
is_valid = await validator.validate_signal(
    'AAPL',
    'BUY',
    min_confirmations=2,
    timeframes=['5min', '30min']  # Skip daily
)
```

### Pattern 2: Swing Trade Filter

```python
# Require daily confirmation (stronger trend)
is_valid = await validator.validate_signal(
    'AAPL',
    'BUY',
    min_confirmations=2,
    timeframes=['30min', 'day']  # Skip 5min
)
```

### Pattern 3: Confidence-Based Sizing

```python
confidence = await validator.confidence_score('AAPL', 'BUY')

position_size = {
    90: 100,  # Full size
    80: 75,   # 3/4 size
    70: 50,   # 1/2 size
    60: 25,   # 1/4 size
}.get(confidence // 10 * 10, 0)  # Round to nearest 10%

if position_size > 0:
    print(f"Buy {position_size} shares")
```

### Pattern 4: Pre-Market Scanning

```python
# Scan watchlist at market open
watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD']
results = await validator.get_all_signals(watchlist)

buy_signals = []
for symbol, analysis in results.items():
    if analysis:
        signal = analysis.get_strongest_signal()
        if signal[0] == 'BUY':
            conf = await validator.confidence_score(symbol, 'BUY')
            if conf >= 70:
                buy_signals.append((symbol, conf))

buy_signals.sort(key=lambda x: x[1], reverse=True)
print(f"Buy candidates: {buy_signals}")
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest runtime/test_multi_timeframe_validator.py -v

# Run specific test
pytest runtime/test_multi_timeframe_validator.py::TestTimeframeSignal::test_rsi_oversold_uptrend_generates_buy -v

# Run with output
pytest runtime/test_multi_timeframe_validator.py -v -s
```

Test categories:
- **Unit tests**: Individual component behavior
- **Integration tests**: End-to-end workflows
- **Mock tests**: Validator behavior with simulated data

## Troubleshooting

### Issue: "No data returned for symbol"

**Cause**: yfinance request failed or symbol is invalid

**Solution**:
```python
# Verify symbol is valid
import yfinance as yf
try:
    ticker = yf.Ticker('SYMBOL')
    info = ticker.info
    print(f"Valid: {info.get('longName')}")
except:
    print("Invalid symbol")
```

### Issue: Cache stale data

**Cause**: TTL not expired yet

**Solution**:
```python
# Force refresh
validator.fetcher.cache.clear()
analysis = await validator.get_timeframe_signals('AAPL')
```

### Issue: Slow first analysis

**Cause**: yfinance fetching 50+ bars from API

**Solution**:
```python
# Subsequent calls hit cache - first call slower is normal
# Analyze symbols during pre-market, reuse cached results during market hours
```

## Examples

See `runtime/multi_timeframe_validator.py` for:
- `example_usage()`: Full walkthrough of all features
- Integration with existing trading agents
- Confidence-based position sizing

## Files

- `runtime/multi_timeframe_validator.py` — Main module (700+ lines, fully documented)
- `runtime/test_multi_timeframe_validator.py` — Comprehensive test suite
- `runtime/MULTI_TIMEFRAME_INTEGRATION.md` — This guide

## Next Steps

1. Import validator into your trading strategy
2. Validate signals before executing trades
3. Track performance of validated vs non-validated trades
4. Adjust `min_confirmations` and confidence thresholds based on results
5. Integrate with existing agents in `runtime/agents_specialized.py`
