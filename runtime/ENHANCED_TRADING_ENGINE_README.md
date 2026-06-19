# Enhanced Trading Engine — ProfitEngine v5

## Overview

The **Enhanced Trading Engine** is a production-grade integrated trading system combining multi-timeframe technical analysis, catalyst scoring, symbol management, and dynamic risk management into a unified signal generation and execution framework.

**File**: `enhanced_trading_engine.py`

## Architecture

```
EnhancedTradingEngine
├── MultiTimeframeValidator (multi_timeframe_validator.py)
│   ├── 5-minute signals (short-term trend)
│   ├── 30-minute signals (medium-term momentum)
│   └── Daily signals (long-term trend)
├── CatalystScorer (catalyst_scorer.py)
│   ├── FDA approvals (biotech)
│   ├── Earnings surprises
│   ├── Analyst consensus
│   └── News sentiment
├── SymbolWatchlist (symbol_watchlist.py)
│   ├── Biotech
│   ├── Growth Tech
│   ├── Finance
│   ├── Healthcare
│   └── Energy
└── DynamicRiskManager (dynamic_risk_params.py)
    ├── ATR-based stops
    ├── Volatility adjustment
    └── Position sizing
```

## Signal Generation Pipeline

### Step-by-Step Process

1. **Watchlist Check**: Verify symbol is tradable
2. **Multi-Timeframe Analysis**: Get signals across 5min/30min/daily
3. **Catalyst Scoring**: Detect and score market catalysts
4. **Cross-Timeframe Validation**: Require 2+ timeframe confirmations
5. **Confidence Calculation**: 0-100 score with catalyst boost
6. **Dynamic Risk Calculation**: ATR-based stops/targets with volatility adjustment
7. **Position Sizing**: Risk-based sizing respecting limits
8. **Limit Checks**: Validate concurrent positions and exposure

### Result: TradeSignal

```python
signal = {
    'action': 'BUY',              # BUY / SELL / NONE
    'symbol': 'NVDA',
    'confidence': 85,              # 0-100
    'entry_price': 125.50,
    'stop_price': 123.20,
    'target_price': 128.75,
    'position_size': 32,           # shares
    'position_value': 4016.00,     # $
    'risk_reward_ratio': 2.50,     # target/stop
    'timeframe_confirmations': 3,  # number of TF confirming
    'catalyst_score': 75.0,        # 0-100
    'volatility_regime': 'elevated'
}
```

## Usage

### Basic Signal Generation

```python
import asyncio
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction

async def main():
    # Initialize engine with $50k account
    engine = EnhancedTradingEngine(account_balance=50000.0)

    # Generate signal for a symbol
    signal = await engine.generate_trade_signal('NVDA')

    if signal and signal.action != SignalAction.NONE:
        print(f"Signal: {signal.action.value}")
        print(f"Confidence: {signal.confidence}%")
        print(f"Entry: ${signal.entry_price:.2f}")
        print(f"Stop: ${signal.stop_price:.2f}")
        print(f"Target: ${signal.target_price:.2f}")
        print(f"Position: {signal.position_size} shares @ ${signal.entry_price:.2f}")

asyncio.run(main())
```

### Execute Signal

```python
async def execute():
    engine = EnhancedTradingEngine(
        alpaca_client=alpaca_client,  # Real broker
        account_balance=50000.0
    )

    signal = await engine.generate_trade_signal('NVDA')

    if signal and signal.confidence >= 50:
        result = await engine.execute_signal(signal)

        print(f"Status: {result.status}")
        print(f"Order ID: {result.order_id}")
        print(f"Entry: ${result.entry_price:.2f}")
        print(f"Stop: ${result.stop_loss:.2f}")
        print(f"Target: ${result.take_profit:.2f}")

asyncio.run(execute())
```

### Monitor Positions

```python
async def monitor():
    engine = EnhancedTradingEngine(alpaca_client=alpaca_client)

    # Monitor single position
    position = await engine.monitor_position(
        order_id='NVDA_1702000000000',
        current_price=126.50
    )

    print(f"Current Price: ${position.current_price:.2f}")
    print(f"P&L: ${position.unrealized_pnl:+.2f}")
    print(f"P&L %: {position.unrealized_pnl_percent:+.1f}%")
    print(f"Status: {position.status}")  # OPEN / AT_STOP / AT_TARGET

    # Monitor all positions
    all_positions = await engine.monitor_all_positions()
    for order_id, pos in all_positions.items():
        print(f"{pos.symbol}: {pos.unrealized_pnl_percent:+.1f}%")

asyncio.run(monitor())
```

### Portfolio Analytics

```python
async def analytics():
    engine = EnhancedTradingEngine(account_balance=50000.0)

    # After executing several signals...
    metrics = engine.get_portfolio_metrics()

    print(f"Account Balance: ${metrics['account_balance']:.2f}")
    print(f"Open Positions: {metrics['open_positions']}")
    print(f"Total Exposure: ${metrics['total_exposure']:.2f}")
    print(f"Unrealized P&L: ${metrics['unrealized_pnl']:+.2f}")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")

    # Export for analysis
    engine.export_signals('signals_log.json')
    engine.export_positions('positions_log.json')

asyncio.run(analytics())
```

## Signal Confidence Scoring

Confidence is calculated as follows:

```
Base Score = 30 × num_confirming_timeframes
    (1 TF = 30%, 2 TF = 60%, 3 TF = 90%)

Alignment Bonus = +10 (if all 3 timeframes align)

RSI Extreme Bonus = +10 (if RSI < 20 for BUY or > 80 for SELL)

Catalyst Boost = +20 × (catalyst_score / 100)
    (up to +20% boost from catalyst strength)

Final Confidence = min(Base + Bonuses, 100)
```

Example:
- 2 TF confirmations: 60 base
- All aligned: +10
- Strong FDA catalyst (90/100): +18
- **Total: 88%**

## Risk Management

### Position Sizing

Position size is calculated as:

```
Risk per share = |entry_price - stop_price|
Position size = (account × 2%) / risk_per_share

Constraints:
- Max single position: $5,000
- Max concurrent exposure: $15,000
- Max concurrent trades: 5
- Min position: 1 share
```

### Stop Loss & Take Profit

Calculated using ATR (Average True Range):

```
Stop Loss (LONG)  = entry - (ATR × 1.5 × volatility_mult)
Stop Loss (SHORT) = entry + (ATR × 1.5 × volatility_mult)

Take Profit (LONG)  = entry + (ATR × 2.5 × volatility_mult)
Take Profit (SHORT) = entry - (ATR × 2.5 × volatility_mult)

Volatility Multiplier:
- IV Rank < 25: 0.5-0.8x (tight stops in low vol)
- IV Rank 25-50: 0.8-1.0x (normal)
- IV Rank 50-75: 1.0-1.3x (wider in elevated vol)
- IV Rank > 75: 1.3-2.0x (wide stops in crisis)
```

## Risk Constraints

| Constraint | Value | Purpose |
|---|---|---|
| MAX_SINGLE_POSITION | $5,000 | Limit single trade risk |
| MAX_CONCURRENT_POSITIONS | $15,000 | Limit total portfolio exposure |
| MAX_CONCURRENT_TRADES | 5 | Max open orders |
| DEFAULT_RISK_PER_TRADE | 2% | Risk per trade as % of account |
| MIN_CONFIDENCE_FOR_EXECUTION | 50% | Minimum signal confidence |
| STRONG_SIGNAL_THRESHOLD | 75% | High confidence threshold |

## Symbol Watchlist Categories

### BIOTECH
- High catalyst activity (FDA approvals, trials)
- High volatility (65% annualized)
- Examples: CRSP, EDIT, BEAM, FATE

### GROWTH_TECH
- Product launches, earnings surprises
- Medium volatility (55% annualized)
- Examples: NVDA, TSLA, COIN, UPST

### FINANCE
- Macro events, regulatory announcements
- Lower volatility (35% annualized)
- Examples: JPM, BAC, GS, MS

### HEALTHCARE
- Earnings, M&A activity
- Medium volatility (38% annualized)
- Examples: UNH, JNJ, PFE, ABBV

### ENERGY
- Geopolitical events, oil prices
- Medium volatility (42% annualized)
- Examples: XOM, CVX, COP, MPC

## Catalyst Types & Weights

| Catalyst | Weight | Trigger |
|---|---|---|
| FDA Approval | 100 | Biotech drug approval |
| Earnings Surprise | 75 | Beat earnings > 5% |
| Analyst Upgrade | 50 | Positive consensus shift |
| News Sentiment | 30 | Positive news articles |
| Sector Momentum | 20 | Sector outperforming |
| Short Squeeze | 15 | High short interest |
| Earnings Beat | 60 | Beat EPS expectations |
| Revenue Beat | 50 | Beat revenue expectations |
| Guidance Raise | 55 | Raised FY guidance |
| Product Launch | 65 | New product announcement |
| Partnership | 45 | Strategic partnership |
| Insider Buying | 40 | CEO/Director buying stock |

## Data Structures

### TradeSignal

```python
@dataclass
class TradeSignal:
    action: SignalAction              # BUY / SELL / NONE
    symbol: str
    confidence: int                   # 0-100
    reason: str                       # Human-readable explanation
    entry_price: float
    stop_price: float
    target_price: float
    position_size: int                # number of shares
    position_value: float             # $ value
    risk_reward_ratio: float
    timeframe_confirmations: int      # 1-3
    catalyst_score: float             # 0-100
    volatility_regime: str            # 'low', 'normal', 'elevated', 'extreme'
    timestamp: str                    # ISO 8601
    metadata: Dict[str, Any]          # catalyst details, ATR, etc.
```

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    status: str                       # SUCCESS / FAILED / PENDING
    order_id: str
    symbol: str
    action: str                       # BUY / SELL
    entry_price: float
    position_size: int
    position_value: float
    stop_loss: float
    take_profit: float
    error_message: Optional[str]
    timestamp: str
```

### PositionStatus

```python
@dataclass
class PositionStatus:
    order_id: str
    symbol: str
    action: str                       # BUY / SELL
    entry_price: float
    current_price: float
    position_size: int
    entry_value: float
    current_value: float
    unrealized_pnl: float             # $ P&L
    unrealized_pnl_percent: float     # % P&L
    stop_loss: float
    take_profit: float
    status: str                       # OPEN / CLOSED / AT_STOP / AT_TARGET
    timestamp: str
```

## Integration with Brokers

### Alpaca Integration

```python
from alpaca.trading.client import TradingClient

alpaca_client = TradingClient(api_key, secret_key)

engine = EnhancedTradingEngine(
    alpaca_client=alpaca_client,
    account_balance=50000.0
)

signal = await engine.generate_trade_signal('NVDA')
result = await engine.execute_signal(signal)
```

### Robinhood Integration

```python
from robin_stocks.robinhood import login, orders

engine = EnhancedTradingEngine(
    robinhood_client=robinhood_client,
    account_balance=50000.0
)

signal = await engine.generate_trade_signal('NVDA')
result = await engine.execute_signal(signal)
```

## Logging & Monitoring

Engine logs all signals and trades:

```python
# Access signal log
for entry in engine.signal_log:
    print(f"{entry['timestamp']}: {entry['action']} "
          f"{entry['symbol']} @ {entry['confidence']}%")

# Access trade history
for trade in engine.trade_history:
    print(f"{trade['order_id']}: {trade['action']} "
          f"{trade['position_size']} @ ${trade['entry_price']:.2f}")

# Export logs
engine.export_signals('signals.json')
engine.export_positions('positions.json')
```

## Error Handling

```python
import logging

logging.basicConfig(level=logging.DEBUG)

engine = EnhancedTradingEngine(account_balance=50000.0)

signal = await engine.generate_trade_signal('NVDA')

if signal is None:
    print("Signal generation failed (check logs)")
elif signal.action == SignalAction.NONE:
    print("No actionable signal generated")
else:
    result = await engine.execute_signal(signal)
    if result.status == "FAILED":
        print(f"Execution error: {result.error_message}")
```

## Performance Considerations

### Async/Concurrent Execution

```python
# Generate signals for multiple symbols concurrently
symbols = ['NVDA', 'TSLA', 'MSFT', 'AMZN', 'AAPL']
tasks = [engine.generate_trade_signal(sym) for sym in symbols]
signals = await asyncio.gather(*tasks)

# Execute all signals in parallel
exec_tasks = [engine.execute_signal(sig) for sig in signals if sig]
results = await asyncio.gather(*exec_tasks)
```

### Caching

- Multi-timeframe validator caches OHLCV data per timeframe
- Symbol metrics cached locally
- Last 100 signals cached in memory

### Scalability

- Designed for 5-50 concurrent positions
- Supports 100+ symbols in watchlist
- ~100ms signal generation per symbol
- ~50ms execution latency

## Testing

```python
import pytest
from enhanced_trading_engine import EnhancedTradingEngine

@pytest.mark.asyncio
async def test_signal_generation():
    engine = EnhancedTradingEngine(account_balance=50000.0)
    signal = await engine.generate_trade_signal('NVDA')
    assert signal is not None
    assert signal.confidence >= 0
    assert signal.confidence <= 100

@pytest.mark.asyncio
async def test_position_sizing():
    engine = EnhancedTradingEngine(account_balance=50000.0)
    size = engine._calculate_position_size(
        symbol='NVDA',
        entry_price=125.50,
        stop_price=123.20,
        direction='LONG'
    )
    assert size > 0
    assert (size * 125.50) <= engine.MAX_SINGLE_POSITION
```

## Deployment

### Production Checklist

- [ ] API keys configured in environment variables
- [ ] Broker credentials validated
- [ ] Account balance verified
- [ ] Risk limits reviewed and approved
- [ ] Stop loss and take profit logic tested
- [ ] Position monitoring enabled
- [ ] Logging configured to persistent storage
- [ ] Error notifications configured
- [ ] Paper trading mode enabled first
- [ ] Live trading with minimal position size
- [ ] Daily P&L reconciliation
- [ ] Weekly backtest validation

## Limitations & Future Work

### Current Limitations
- No multi-leg options strategies
- Limited to US equities (9:30-16:00 ET)
- Single symbol at a time (async friendly)
- No portfolio optimization
- IV data requires Finnhub/Alpaca API

### Planned Enhancements
- Multi-symbol portfolio optimization
- Options strategies (spreads, iron condors)
- Extended hours trading (pre/post market)
- Backtesting framework
- Machine learning signal enhancement
- Portfolio rebalancing automation

## References

- **MultiTimeframeValidator**: Validates signals across 5min, 30min, daily timeframes
- **CatalystScorer**: Scores market catalysts (FDA, earnings, analyst)
- **SymbolWatchlist**: 40+ symbols across 5 market categories
- **DynamicRiskManager**: ATR-based position sizing with volatility adjustment

## Support

For issues or feature requests, see:
- `ENHANCED_TRADING_ENGINE_QUICKREF.md` - Quick reference
- `ENHANCED_TRADING_ENGINE_INTEGRATION.md` - Integration guide
- Test suite: `test_enhanced_trading_engine.py`

---

**Version**: 5.0.0  
**Last Updated**: 2024-12-20  
**Status**: Production Ready
