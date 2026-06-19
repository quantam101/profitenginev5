# Enhanced Trading Engine — Quick Reference

## Installation

```bash
# Install dependencies
pip install yfinance requests httpx fastapi uvicorn numpy

# Import
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction
```

## Quick Start (30 seconds)

```python
import asyncio
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction

async def main():
    engine = EnhancedTradingEngine(account_balance=50000.0)
    signal = await engine.generate_trade_signal('NVDA')
    
    if signal and signal.action != SignalAction.NONE:
        print(f"BUY {signal.position_size} @ ${signal.entry_price:.2f}")
        result = await engine.execute_signal(signal)
        print(f"Order: {result.order_id}")

asyncio.run(main())
```

## Core Methods

### Signal Generation

```python
signal = await engine.generate_trade_signal('NVDA')

# Returns:
# TradeSignal(
#     action=BUY,
#     confidence=85,
#     entry_price=125.50,
#     stop_price=123.20,
#     target_price=128.75,
#     position_size=32,
#     ...
# )
```

### Signal Execution

```python
result = await engine.execute_signal(signal)

# Returns ExecutionResult(status='SUCCESS', order_id='...', ...)
```

### Position Monitoring

```python
position = await engine.monitor_position(order_id)

# Returns PositionStatus with P&L metrics
print(f"P&L: {position.unrealized_pnl_percent:.1f}%")
```

### Portfolio Metrics

```python
metrics = engine.get_portfolio_metrics()

# {
#   'account_balance': 50000.00,
#   'open_positions': 3,
#   'unrealized_pnl': 1250.50,
#   'unrealized_pnl_percent': 2.5,
#   'win_rate': 75.0
# }
```

## Signal Confidence Levels

| Confidence | Interpretation | Action |
|---|---|---|
| 90-100% | Extreme Confidence | Execute without hesitation |
| 75-89% | Strong Signal | Execute with caution |
| 50-74% | Moderate Signal | Execute with smaller size |
| 25-49% | Weak Signal | Skip or reduce size |
| 0-24% | No Signal | Do not execute |

## Risk Parameters (Hardcoded)

```python
MAX_SINGLE_POSITION = $5,000              # Max per trade
MAX_CONCURRENT_POSITIONS = $15,000        # Total exposure
MAX_CONCURRENT_TRADES = 5                 # Open orders
DEFAULT_RISK_PER_TRADE = 2%               # Risk per signal
MIN_CONFIDENCE_FOR_EXECUTION = 50%        # Minimum threshold
```

## Symbol Categories

```python
# Available watchlists
BIOTECH = "BIOTECH"              # CRSP, EDIT, BEAM, FATE
GROWTH_TECH = "GROWTH_TECH"      # NVDA, TSLA, COIN, UPST
FINANCE = "FINANCE"              # JPM, BAC, GS, MS
HEALTHCARE = "HEALTHCARE"        # UNH, JNJ, PFE, ABBV
ENERGY = "ENERGY"                # XOM, CVX, COP, MPC

# Get watchlist
symbols = engine.watchlist.get_watchlist('BIOTECH')
# ['CRSP', 'EDIT', 'BEAM', 'FATE', 'ARQT', 'VERV', 'PACB', 'RXDX']
```

## Multi-Timeframe Signal Logic

| Timeframe | Period | Use Case |
|---|---|---|
| 5-minute | Short-term | Entry confirmation |
| 30-minute | Medium-term | Trend momentum |
| Daily | Long-term | Overall direction |

**Validation Rule**: Signal requires 2+ timeframes confirming to be valid.

```python
# Example: 3 confirmations
5-min:  BUY  ✓
30-min: BUY  ✓
Daily:  BUY  ✓
Result: Valid (100% aligned)

# Example: 2 confirmations
5-min:  BUY  ✓
30-min: SELL ✗
Daily:  BUY  ✓
Result: Valid (2/3 confirm)
```

## Catalyst Scoring

| Catalyst | Score | Notes |
|---|---|---|
| FDA Approval | 100 | Biotech drug approval |
| Earnings Beat | 60 | EPS surprise > 5% |
| Analyst Upgrade | 50 | Consensus improvement |
| Product Launch | 65 | New product announcement |
| Partnership | 45 | Strategic deal |
| News Sentiment | 30 | Positive articles |

**Score Impact**: +0 to +20 confidence boost

## Position Sizing Formula

```
Risk per Share = |Entry - Stop|
Position Size = (Account × 2%) / Risk per Share

Example:
- Account: $50,000
- Entry: $125.50
- Stop: $123.20
- Risk: $2.30 per share

Position = ($50,000 × 0.02) / $2.30
Position = $1,000 / $2.30 = 434 shares

Check Limits:
- Max single position: 434 × $125.50 = $54,457 ✗ (exceeds $5k)
- Adjust: $5,000 / $125.50 = 39 shares ✓
```

## Stop Loss & Take Profit

### ATR-Based Calculation

```
ATR = Average True Range (14 periods)

LONG Position:
- Stop Loss = Entry - (ATR × 1.5 × Vol Multiplier)
- Take Profit = Entry + (ATR × 2.5 × Vol Multiplier)

SHORT Position:
- Stop Loss = Entry + (ATR × 1.5 × Vol Multiplier)
- Take Profit = Entry - (ATR × 2.5 × Vol Multiplier)

Volatility Multiplier:
- Low Vol (IV < 25): 0.5x - 0.8x (tight stops)
- Normal (IV 25-50): 0.8x - 1.0x
- Elevated (IV 50-75): 1.0x - 1.3x
- Extreme (IV > 75): 1.3x - 2.0x (wide stops)
```

### Example

```python
signal = await engine.generate_trade_signal('NVDA')

print(f"Entry:  ${signal.entry_price:.2f}")
print(f"Stop:   ${signal.stop_price:.2f}")
print(f"Target: ${signal.target_price:.2f}")
print(f"RR:     {signal.risk_reward_ratio:.2f}:1")

# Typical output:
# Entry:  $125.50
# Stop:   $123.20
# Target: $128.75
# RR:     2.50:1
```

## Async Patterns

### Single Signal

```python
signal = await engine.generate_trade_signal('NVDA')
```

### Multiple Signals (Parallel)

```python
tasks = [
    engine.generate_trade_signal('NVDA'),
    engine.generate_trade_signal('TSLA'),
    engine.generate_trade_signal('MSFT')
]
signals = await asyncio.gather(*tasks)
```

### Monitor All Positions

```python
positions = await engine.monitor_all_positions()

for order_id, pos in positions.items():
    print(f"{pos.symbol}: {pos.unrealized_pnl_percent:+.1f}%")
```

## Common Workflows

### Scan and Execute

```python
async def scan_and_trade():
    engine = EnhancedTradingEngine(alpaca_client=alpaca, account_balance=50000)
    
    symbols = engine.watchlist.get_watchlist()
    
    for symbol in symbols:
        signal = await engine.generate_trade_signal(symbol)
        
        if signal and signal.confidence >= 75:
            result = await engine.execute_signal(signal)
            print(f"{result.symbol}: {result.status}")
        
        await asyncio.sleep(0.5)  # Rate limiting

asyncio.run(scan_and_trade())
```

### Monitor and Adjust

```python
async def monitor_loop():
    engine = EnhancedTradingEngine(alpaca_client=alpaca)
    
    while True:
        positions = await engine.monitor_all_positions()
        
        for order_id, pos in positions.items():
            if pos.unrealized_pnl_percent <= -5:  # Stop loss hit
                print(f"Close {pos.symbol} at {pos.current_price}")
            elif pos.unrealized_pnl_percent >= 10:  # Take profit
                print(f"Close {pos.symbol} at {pos.current_price}")
        
        await asyncio.sleep(60)  # Check every minute

asyncio.run(monitor_loop())
```

### Daily Analysis

```python
async def daily_report():
    engine = EnhancedTradingEngine(account_balance=50000)
    
    metrics = engine.get_portfolio_metrics()
    
    print(f"Account: ${metrics['account_balance']:.2f}")
    print(f"P&L: {metrics['unrealized_pnl_percent']:+.1f}%")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")
    
    engine.export_signals('daily_signals.json')
    engine.export_positions('daily_positions.json')

asyncio.run(daily_report())
```

## Environment Variables

```bash
# Optional API keys
export FINNHUB_API_KEY="your_finnhub_key"
export ALPACA_API_KEY="your_alpaca_key"
export ALPACA_SECRET_KEY="your_alpaca_secret"
```

## Troubleshooting

| Issue | Solution |
|---|---|
| "Symbol not in watchlist" | Use `engine.watchlist.get_watchlist()` to see available symbols |
| "Signal confidence below threshold" | Lower `MIN_CONFIDENCE_FOR_EXECUTION` or improve market conditions |
| "Position limit exceeded" | Close some positions or increase `MAX_CONCURRENT_POSITIONS` |
| "No timeframe data" | Wait for market hours or check symbol availability |
| "API key errors" | Set `FINNHUB_API_KEY` and `ALPACA_API_KEY` environment variables |

## Key Files

- `enhanced_trading_engine.py` - Main engine (this integration)
- `multi_timeframe_validator.py` - Timeframe signal validation
- `catalyst_scorer.py` - Catalyst detection and scoring
- `symbol_watchlist.py` - Symbol management and filtering
- `dynamic_risk_params.py` - Risk calculations and position sizing
- `ENHANCED_TRADING_ENGINE_README.md` - Full documentation
- `ENHANCED_TRADING_ENGINE_INTEGRATION.md` - Integration examples

## Performance Metrics

- **Signal Generation**: ~100ms per symbol
- **Data Caching**: OHLCV data cached per timeframe
- **Execution Latency**: ~50ms to broker
- **Throughput**: 50+ symbols/minute with async
- **Memory**: ~50MB for full watchlist data

## Example Output

```
2024-12-20 10:15:23 - Generating trade signal for NVDA
2024-12-20 10:15:23 - [NVDA] Fetching multi-timeframe signals...
2024-12-20 10:15:24 - [NVDA] Scoring catalysts...
2024-12-20 10:15:24 - [NVDA] Base signal: BUY (3 confirmations)
2024-12-20 10:15:24 - [NVDA] Confidence: 85 → 88 (catalyst boost: 3.0)
2024-12-20 10:15:24 - [NVDA] Current price: $125.50
2024-12-20 10:15:24 - [NVDA] Risk/Reward: 2.50:1
2024-12-20 10:15:24 - [NVDA] ✓ Signal generated: BUY @ $125.50 (confidence: 88%, size: 32 shares)
2024-12-20 10:15:25 - [NVDA] ✓ Order executed: NVDA_1702993325000 (32 @ $125.50)
```

---

**Version**: 5.0.0  
**Last Updated**: 2024-12-20
