# Live Paper Trading Verification — ProfitEngine v5

## Overview

The Live Trading Verification system runs the EnhancedTradingEngine against simulated live market data to validate trading performance before production deployment.

**Status:** Phase 4 Validation  
**Target Metrics:**
- Win rate: 85%+
- Profit factor: 3.0+
- Symbols traded: 10+
- Trades executed: 100+

---

## Quick Start

### 1. Prerequisites

```bash
cd runtime
pip install -r requirements.txt  # Ensure all dependencies installed
```

### 2. Run Verification

```bash
# From project root
python live_trading_verification.py
```

**Configuration Options:**

Edit `live_trading_verification.py` lines 455-462:

```python
ACCOUNT_BALANCE = 10000.0          # Starting capital
MAX_DURATION_HOURS = 24.0          # Run for up to 24 hours
MIN_TRADES = 100                   # Target 100+ trades
TRADES_PER_SYMBOL = 3              # Max 3 trades per symbol (1-5)
```

### 3. Monitor Progress

The system logs in real-time to both console and `live_trading_verification.log`:

```
[Iteration 1] Trading NVDA...
[NVDA] Trade #1: BUY 25 @ $125.50 (confidence: 85%, RR: 2.50:1)
[NVDA] Position hit take profit @ $128.75
[NVDA] Trade closed: P&L: +$80.00 (+2.52%)
```

---

## Execution Flow

### Phase 1: Initialization
- Load EnhancedTradingEngine with starting balance
- Load symbol watchlist (40 symbols across 5 categories)
- Initialize tracking structures

### Phase 2: Main Trading Loop
1. **Symbol Selection** — Pick next symbol with fewest attempts
2. **Signal Generation** — Run full multi-timeframe analysis
3. **Validation** — Check confidence, risk limits, position constraints
4. **Execution** — Record trade with entry price, stop, target
5. **Monitoring** — Simulate price movement (Monte Carlo)
6. **Exit** — Close on stop loss, take profit, or trailing stop

### Phase 3: Termination Conditions
- 24-hour time limit reached
- 100+ trades executed
- No more symbols available

### Phase 4: Reporting
- Calculate metrics (win rate, profit factor, P&L)
- Export detailed trade log
- Generate JSON results file
- Compare to Phase 4 targets

---

## Output Files

### 1. Live Log
```
File: live_trading_verification.log
Format: Real-time log of all trades, signals, and metrics
Useful for: Monitoring progress, debugging issues
```

### 2. JSON Export
```
File: live_trading_results.json
Contains:
  - metrics: Summary statistics
  - trades: Detailed trade records
  - metadata: System info and timestamp
```

### 3. Console Summary
```
Printed after completion:
  - Trade statistics (count, symbols, win rate)
  - P&L metrics (gross profit, loss, net P&L)
  - Performance vs Phase 4 targets
  - Detailed trade log
```

---

## Key Features

### 1. Realistic Signal Generation
- Multi-timeframe validation (5min, 30min, daily)
- Catalyst scoring (FDA, earnings, analyst)
- Dynamic risk parameters (ATR-based stops/targets)
- Confidence scoring (0-100%)

### 2. Risk Management
- Max position size: $5,000
- Max concurrent exposure: $15,000
- Max concurrent trades: 5
- Position sizing: 2% account risk per trade

### 3. Trade Monitoring
- Entry price and time tracking
- Exit price and reason (stop, target, market close)
- Real-time P&L calculation
- Position status (OPEN, CLOSED_PROFIT, CLOSED_LOSS)

### 4. Performance Analytics
- Win rate calculation
- Profit factor (gross profit / gross loss)
- Average win / average loss
- Largest win / largest loss
- Account return percentage

---

## Metrics Explained

### Win Rate
- Definition: (Winning Trades / Total Closed Trades) × 100
- Target: 85%+
- Interpretation: Percentage of trades that make money

### Profit Factor
- Definition: Gross Profit / |Gross Loss|
- Target: 3.0+ (3:1 ratio)
- Interpretation: For every $1 lost, you make $3 in profit

### P&L (Profit and Loss)
- Gross Profit: Sum of all winning trades
- Gross Loss: Sum of all losing trades (absolute value)
- Net P&L: Gross Profit - Gross Loss
- Return %: (Net P&L / Initial Balance) × 100

### Risk/Reward Ratio
- Per trade: (Target - Entry) / (Entry - Stop)
- Target: 2.0+ (2:1 minimum)
- Higher ratios = better risk management

---

## Watchlist Symbols (40 Total)

### Biotech (8)
CRSP, EDIT, BEAM, FATE, ARQT, VERV, PACB, RXDX

### Growth Tech (8)
NVDA, TSLA, COIN, UPST, DDOG, NFLX, ROKU, MSTR

### Finance (8)
JPM, BAC, GS, MS, WFC, C, BLK, SCHW

### Healthcare (8)
UNH, JNJ, PFE, ABBV, MRK, ELV, CNC, HCA

### Energy (8)
XOM, CVX, COP, MPC, SLB, EOG, PXD, OKE

---

## Troubleshooting

### Issue: "No valid signal generated"
**Cause:** Market data unavailable or low confidence  
**Solution:** Check API connectivity, wait for market hours

### Issue: "Position limit exceeded"
**Cause:** Too many open positions or high exposure  
**Solution:** Close positions manually, reduce position size

### Issue: "ImportError: Failed to import components"
**Cause:** Missing module files  
**Solution:** Ensure all runtime/*.py files are present

### Issue: Low win rate (< 50%)
**Cause:** Volatile market, weak signal quality  
**Solution:** Adjust confidence threshold, review catalyst scoring

---

## Advanced Configuration

### Adjust Risk Parameters
Edit `enhanced_trading_engine.py`:
```python
MAX_SINGLE_POSITION = 5000.00      # Max per trade
MAX_CONCURRENT_POSITIONS = 15000.00 # Total exposure
MAX_CONCURRENT_TRADES = 5           # Open positions
DEFAULT_RISK_PER_TRADE = 0.02       # 2% per trade
```

### Adjust Signal Thresholds
Edit `enhanced_trading_engine.py`:
```python
MIN_CONFIDENCE_FOR_EXECUTION = 50   # Minimum to trade
STRONG_SIGNAL_THRESHOLD = 75        # High confidence
```

### Add Symbols to Watchlist
Edit `runtime/symbol_watchlist.py`:
```python
WATCHLIST_DB = {
    "GROWTH_TECH": ["NVDA", "TSLA", "NEW_SYMBOL", ...]
}
```

---

## Performance Benchmarks

### Target Metrics (Phase 4)
| Metric | Target | Status |
|--------|--------|--------|
| Win Rate | 85%+ | TBD |
| Profit Factor | 3.0+ | TBD |
| Symbols Traded | 10+ | TBD |
| Trades Executed | 100+ | TBD |

### Historical Baselines
- Previous version: 62% win rate, 1.8 profit factor
- Expected improvement: 85% win rate, 3.0 profit factor
- Reason: Enhanced catalyst scoring + dynamic risk

---

## Integration with Production

Once metrics targets are met:

1. **Deploy Runtime** → Docker container to OCI
2. **Deploy API** → Next.js backend to Vercel
3. **Enable Trading** → Toggle `trading_enabled=true`
4. **Monitor Live** → Real trades with position limits
5. **Scale Gradually** → Increase position sizes progressively

---

## Support & Documentation

### Related Files
- `runtime/enhanced_trading_engine.py` — Core trading engine
- `runtime/multi_timeframe_validator.py` — Signal validation
- `runtime/catalyst_scorer.py` — Catalyst analysis
- `runtime/dynamic_risk_params.py` — Risk management

### Logs & Exports
- `live_trading_verification.log` — Real-time log
- `live_trading_results.json` — Structured results
- `autonomous_trading.log` — Production trading log

---

## Next Steps

1. **Run verification** → `python live_trading_verification.py`
2. **Monitor progress** → Watch log file in real-time
3. **Review results** → Check JSON export and summary
4. **Compare metrics** → Verify Phase 4 targets are met
5. **Plan deployment** → If targets passed, move to production

---

**Last Updated:** 2026-06-18  
**ProfitEngine v5.0.0**
