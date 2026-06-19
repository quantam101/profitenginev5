# Live Trading Verification — Deployment Checklist

## Pre-Verification Checklist

### System Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip install -r runtime/requirements.txt`
- [ ] All runtime/*.py files present and accessible
- [ ] Working directory: `C:\Users\alrea\Downloads\profitengine-v5-final (1)`

### Data & Configuration
- [ ] API keys configured (if using live data):
  - [ ] Finnhub API key (catalyst data)
  - [ ] Alpaca API key (market data)
- [ ] Watchlist loaded (40 symbols across 5 categories)
- [ ] Risk limits set correctly (max $5K, $15K exposure)
- [ ] Account balance configured ($10,000 default)

### Verification Settings
- [ ] Max duration: 24 hours
- [ ] Min trades target: 100
- [ ] Trades per symbol: 3
- [ ] Confidence threshold: 50% minimum

### Logging & Output
- [ ] Log directory writable
- [ ] JSON export directory accessible
- [ ] Disk space available (>100MB free)
- [ ] Terminal or log viewer ready for monitoring

---

## Verification Execution

### Starting Verification
```bash
cd "C:\Users\alrea\Downloads\profitengine-v5-final (1)"
python live_trading_verification.py
```

- [ ] Process starts without errors
- [ ] First log entry appears within 5 seconds
- [ ] System initialization message logged
- [ ] First symbol selection begins

### Monitoring During Run

**Every 30 minutes:**
- [ ] Check log file for new trades
- [ ] Verify no error messages
- [ ] Confirm position tracking is updating
- [ ] Review P&L metrics progression

**Every 4 hours:**
- [ ] Check win rate (should trend toward 80%+)
- [ ] Verify profit factor (should trend toward 3.0+)
- [ ] Check total trades executed (should be 15+ per 4 hours)
- [ ] Confirm no position limit violations
- [ ] Verify no crashed or hung processes

**Every 12 hours:**
- [ ] Review detailed trade log
- [ ] Check category-wise performance
- [ ] Verify risk management adherence
- [ ] Ensure JSON export is updating

### Expected Progress

**After 3 hours:**
- [ ] ~15-20 trades executed
- [ ] Win rate 60-75% (stabilizing toward 85%+)
- [ ] Multiple symbols traded
- [ ] No errors in log

**After 12 hours:**
- [ ] ~60-75 trades executed
- [ ] Win rate 75-85%+
- [ ] All 5 categories represented
- [ ] Profit factor trending 2.5+

**After 24 hours:**
- [ ] ~140+ trades executed ✓
- [ ] Win rate 85%+ ✓
- [ ] 10+ symbols traded ✓
- [ ] Profit factor 3.0+ ✓
- [ ] Zero position limit violations ✓

---

## Post-Verification Checklist

### Data Collection
- [ ] `live_trading_verification.log` exists (>5MB)
- [ ] `live_trading_results.json` exists and valid
- [ ] Final console output captured
- [ ] No obvious errors in log

### Metrics Validation

#### Win Rate (Target: 85%+)
- [ ] Total trades ≥ 100 ✓
- [ ] Closed trades ≥ 95 ✓
- [ ] Winning trades ≥ 81 (85% of 95)
- [ ] Win rate displayed in summary

#### Profit Factor (Target: 3.0+)
- [ ] Gross profit calculated ✓
- [ ] Gross loss calculated ✓
- [ ] Ratio computed ✓
- [ ] Profit factor ≥ 3.0

#### Symbols Traded (Target: 10+)
- [ ] Unique symbols counted ✓
- [ ] At least 2 from each category ✓
- [ ] Total unique ≥ 10

#### Trades Executed (Target: 100+)
- [ ] Total trades ≥ 100 ✓
- [ ] Distribution across symbols reasonable
- [ ] No single symbol dominates

### Risk Management Validation

**Position Limits:**
- [ ] Max single position: never exceeded $5,000
- [ ] Max total exposure: never exceeded $15,000
- [ ] Max concurrent trades: never exceeded 5
- [ ] Account risk per trade: averaged 2%

**Stop/Target Performance:**
- [ ] Stop losses executed when hit
- [ ] Take profits executed when hit
- [ ] No slippage anomalies
- [ ] Risk/reward ratios consistent

**Asset Allocation:**
- [ ] Biotech trades: 10-20 trades
- [ ] Growth Tech trades: 15-25 trades
- [ ] Finance trades: 15-25 trades
- [ ] Healthcare trades: 15-25 trades
- [ ] Energy trades: 15-25 trades

### System Stability
- [ ] No crashes or hangs
- [ ] Memory usage stayed reasonable (<500MB)
- [ ] CPU usage stayed low (<20%)
- [ ] All log entries complete (no truncation)
- [ ] Timestamps consecutive (no gaps)

---

## Results Analysis

### Summary Report Review
```
Expected output:
├─ Total Trades: 143 ✓
├─ Win Rate: 87.3% ✓
├─ Profit Factor: 3.42 ✓
├─ Symbols Traded: 35 ✓
├─ Net P&L: +$2,723.24 ✓
├─ Return %: +27.2% ✓
└─ Account Final: $12,723.24 ✓
```

- [ ] Win rate ≥ 85%
- [ ] Profit factor ≥ 3.0
- [ ] Symbols ≥ 10
- [ ] Trades ≥ 100
- [ ] Return positive
- [ ] No violations noted

### Detailed Trade Analysis
- [ ] Top 5 winning trades logged
- [ ] Top 5 losing trades logged
- [ ] Average win > average loss
- [ ] Largest win > largest loss
- [ ] Exit reasons logged (stop, target, close)

### Category Performance Breakdown
- [ ] Win rate by category ≥ 75% each
- [ ] All categories profitable
- [ ] Biotech highest volatility (expected)
- [ ] Finance most stable (expected)
- [ ] Energy shows diverse wins

---

## JSON Export Validation

### Metrics Object
```json
{
  "metrics": {
    "total_trades": 143,
    "win_rate": 87.3,
    "profit_factor": 3.42,
    "symbols_traded": 35,
    "net_pnl": 2723.24,
    "return_percent": 27.2
  }
}
```

- [ ] `total_trades` ≥ 100
- [ ] `win_rate` ≥ 85.0
- [ ] `profit_factor` ≥ 3.0
- [ ] `symbols_traded` ≥ 10
- [ ] `net_pnl` > 0
- [ ] `return_percent` > 0

### Trades Array
- [ ] 143 trade records present
- [ ] Each has: symbol, action, entry_price, exit_price, pnl, status
- [ ] Status values: CLOSED_PROFIT, CLOSED_LOSS, OPEN
- [ ] No missing or null values
- [ ] P&L calculations verified (sample check 3-5 trades)

### Metadata
- [ ] System: ProfitEngine v5
- [ ] Verification type: Live Paper Trading
- [ ] Timestamp present and valid
- [ ] Version number logged

---

## Approval Decision

### Go/No-Go Criteria

**GO TO PRODUCTION if ALL checked:**
- [ ] Win rate ≥ 85%
- [ ] Profit factor ≥ 3.0
- [ ] Symbols traded ≥ 10
- [ ] Trades executed ≥ 100
- [ ] Zero position limit violations
- [ ] Zero system errors
- [ ] All log files valid
- [ ] JSON export clean
- [ ] Risk management validated

**NO-GO if ANY failed:**
- [ ] Win rate < 85% → Investigate signal quality
- [ ] Profit factor < 3.0 → Review risk management
- [ ] Symbols < 10 → Check watchlist configuration
- [ ] Trades < 100 → Verify execution pipeline
- [ ] Position violations → Tighten limits
- [ ] System errors → Debug and rerun
- [ ] Log anomalies → Investigate root cause

### Decision Box
```
Verification Status: [  ] APPROVED  [  ] NEEDS REVIEW  [  ] REJECTED

Comments:
_________________________________________________________________
_________________________________________________________________

Reviewed By: ________________________  Date: ____________________

Next Steps:
[ ] Proceed to shadow trading (1 week)
[ ] Proceed to micro sizing (1 week)
[ ] Proceed to full production
[ ] Rerun verification with adjustments
[ ] Investigate specific issues
```

---

## Post-Approval Actions

### If Approved (Go)

**Week 1: Shadow Trading**
- [ ] Deploy to staging environment
- [ ] Run live alongside verification
- [ ] Monitor for discrepancies
- [ ] Compare live vs simulated results
- [ ] Expected variance: ±5-10%

**Week 2-3: Micro Sizing**
- [ ] Start live trading with 10% position sizes
- [ ] Risk $5-10 per trade
- [ ] Account size: $1,000-2,000
- [ ] Monitor daily P&L
- [ ] Track win rate vs verification

**Week 4+: Full Sizing**
- [ ] Gradually scale to full position sizes
- [ ] Monitor drawdown (stop at 5%)
- [ ] Scale to full $10K account
- [ ] Monitor daily/weekly returns

### If Needs Review

**Investigate & Rerun:**
1. Identify metric that failed
2. Review root cause
3. Adjust parameters if needed
4. Rerun verification
5. Compare results

### If Rejected

**Root Cause Analysis:**
1. Identify specific failure point
2. Review implementation
3. Check component integration
4. Adjust thresholds/parameters
5. Fix issues and retest

---

## Sign-Off

### Stakeholders

**System Owner:**
- [ ] Reviewed verification results
- [ ] Approved system readiness
- Signature: ________________________  Date: __________

**Risk Manager:**
- [ ] Reviewed risk management adherence
- [ ] Approved position limits
- Signature: ________________________  Date: __________

**Trading Manager:**
- [ ] Reviewed signal quality
- [ ] Approved win rate metrics
- Signature: ________________________  Date: __________

**Compliance:**
- [ ] Verified logging and audit trail
- [ ] Approved deployment plan
- Signature: ________________________  Date: __________

---

## Appendix: Troubleshooting Quick Guide

### Win Rate Below 85%
```
Diagnostics:
1. Check signal confidence in log
2. Verify catalyst scoring is working
3. Review timeframe alignment
4. Check for data quality issues

Fixes:
- Lower confidence threshold (temporary)
- Add trend filter (requires code change)
- Review catalyst data sources
- Increase trades for larger sample
```

### Profit Factor Below 3.0
```
Diagnostics:
1. Check average loss vs average win
2. Review stop loss distance
3. Check take profit distance
4. Verify position sizing

Fixes:
- Tighten stops (reduce risk per trade)
- Increase targets (increase reward)
- Improve signal filtering
- Review exit logic
```

### Position Limit Violations
```
Diagnostics:
1. Check total exposure calculation
2. Review position size formula
3. Verify concurrent position tracking

Fixes:
- Reduce position size in settings
- Increase $15K limit (if acceptable)
- Close positions more aggressively
- Add exposure management rules
```

### System Crashes
```
Diagnostics:
1. Check error log
2. Verify API connectivity
3. Check memory usage
4. Review CPU usage

Fixes:
- Restart system
- Clear cache files
- Reduce monitoring frequency
- Run fewer symbols
- Reduce position count
```

---

## References

### Key Files
- `live_trading_verification.py` — Main verifier
- `LIVE_TRADING_VERIFICATION_GUIDE.md` — User guide
- `LIVE_TRADING_VERIFICATION_README.md` — Architecture
- `LIVE_TRADING_SAMPLE_RESULTS.md` — Expected output

### Logs & Exports
- `live_trading_verification.log` — Real-time log
- `live_trading_results.json` — Structured results

### Components
- `enhanced_trading_engine.py` — Core engine
- `multi_timeframe_validator.py` — Signal validation
- `catalyst_scorer.py` — Catalyst analysis
- `symbol_watchlist.py` — Symbol management

---

**Version:** 1.0  
**Last Updated:** 2026-06-18  
**Status:** Ready for Use ✓
