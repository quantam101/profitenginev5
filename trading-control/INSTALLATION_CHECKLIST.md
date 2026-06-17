# Performance Attribution Engine — Installation Checklist

## Pre-Flight Check

```bash
# 1. Verify all files exist
ls -lh trading-control/performance_attribution.py
ls -lh trading-control/attribution_integration_example.py
ls -lh trading-control/test_performance_attribution.py
ls -lh trading-control/PERFORMANCE_ATTRIBUTION_GUIDE.md
```

## File Validation

```bash
# 2. Verify Python syntax
python -m py_compile trading-control/performance_attribution.py
python -m py_compile trading-control/attribution_integration_example.py
python -m py_compile trading-control/test_performance_attribution.py

# Expected output: No errors
```

## Quick Test

```bash
# 3. Run basic import test
cd trading-control
python -c "from performance_attribution import PerformanceAttributionEngine; print('✅ Import successful')"
```

## Optional: Full Test Suite

```bash
# 4. Run comprehensive tests (requires pytest)
cd trading-control
pytest test_performance_attribution.py -v

# Expected: 50+ tests passing
```

## Integration Steps

### Step 1: Add Imports to launch_complete_system.py

```python
from performance_attribution import PerformanceAttributionEngine
from attribution_integration_example import TradingSystemWithAttribution
```

### Step 2: Initialize Attribution System in CompleteSystem

```python
class CompleteSystem:
    def __init__(self):
        self.trading_os = TradingControlOS()
        self.news_monitor = NewsMonitor24_7(...)
        self.attribution_system = TradingSystemWithAttribution()  # ADD THIS
        self.start_time = datetime.now()
```

### Step 3: Record Each Trade's Attribution

After trade execution:

```python
# After each trade completes
self.attribution_system.record_trade_with_attribution(
    trade_outcome={
        'trade_id': execution_result.order_id,
        'symbol': proposal.symbol,
        'direction': proposal.direction,
        'entry_price': str(proposal.entry_price),
        'exit_price': str(execution_result.fill_price),
        'realized_pnl': str(execution_result.realized_pnl),
        'return_pct': float(execution_result.realized_pnl / proposal.position_size_usd),
        'regime': str(proposal.regime_signal.regime),
        'duration_minutes': (exit_time - entry_time).total_seconds() / 60,
        'timestamp': datetime.now().isoformat()
    },
    proposal_signals={
        'technical': {
            'confidence': proposal.technical_signal.confidence,
            'strength': proposal.technical_signal.pattern_score
        },
        'microstructure': {
            'confidence': proposal.microstructure_signal.confidence,
            'strength': proposal.microstructure_signal.liquidity_score
        },
        'regime': {
            'confidence': proposal.regime_signal.regime_confidence,
            'strength': 0.8 if proposal.regime_signal.approved_to_trade else 0.2
        },
        'portfolio': {
            'confidence': 0.8,
            'strength': proposal.portfolio_signal.risk_budget_remaining / 1000.0
        }
    }
)
```

### Step 4: Generate Reports in print_final_report()

```python
def print_final_report(self):
    """Print final system report."""
    # ... existing code ...
    
    # ADD: Attribution reports
    logger.info("\n" + "="*80)
    logger.info("PERFORMANCE ATTRIBUTION ANALYSIS")
    logger.info("="*80 + "\n")
    
    self.attribution_system.print_agent_performance_summary()
    self.attribution_system.print_regime_performance_summary()
    
    self.attribution_system.generate_daily_report()
    self.attribution_system.generate_weekly_report()
    self.attribution_system.generate_monthly_report()
```

### Step 5: Cleanup in Shutdown

```python
async def run_system(self):
    """Run complete system: trading + news monitoring."""
    try:
        await asyncio.gather(
            self.news_monitor.run_forever(),
            return_exceptions=True
        )
    except KeyboardInterrupt:
        logger.info("\n\nSystem shutting down...")
        self.print_final_report()
        self.attribution_system.shutdown()  # ADD THIS
```

## Verify Installation

After integration:

```bash
# 1. Check for import errors
python -c "from launch_complete_system import CompleteSystem; print('✅ Integration OK')"

# 2. Run sample trades
python launch_complete_system.py
# ... run for a few minutes, then Ctrl+C ...

# 3. Check reports were generated
ls -la ./logs/attribution_*.json
# Expected: Files exist with today's date
```

## Report Verification

```bash
# 1. Verify daily report exists
cat ./logs/attribution_daily_*.json | python -m json.tool | head -50

# 2. Check report structure
python -c "
import json
with open('./logs/attribution_daily_*.json') as f:
    report = json.load(f)
    assert 'summary' in report
    assert 'agent_statistics' in report
    assert 'regime_breakdown' in report
    print('✅ Report structure valid')
"
```

## Performance Check

```bash
# Monitor CPU/memory during operation
watch -n 1 'ps aux | grep launch_complete_system | grep -v grep'

# Expected: No significant increase over baseline
```

## Troubleshooting

### Issue: ImportError on PerformanceAttributionEngine

**Solution**: Verify file exists
```bash
ls -la trading-control/performance_attribution.py
```

### Issue: JSON export failing

**Solution**: Check logs directory writable
```bash
mkdir -p ./trading-control/logs
chmod 755 ./trading-control/logs
```

### Issue: No reports generated

**Solution**: Verify trades are being executed
```bash
# Check audit log for recent trades
sqlite3 trading-control/audit.db "SELECT COUNT(*) FROM orders WHERE created_at > datetime('now', '-1 hour')"
```

### Issue: Reports have missing data

**Solution**: Verify proposal_signals dict has all 4 agents
```python
required_agents = ['technical', 'microstructure', 'regime', 'portfolio']
assert all(agent in proposal_signals for agent in required_agents)
```

## Rollback

If issues occur, you can safely remove attribution system:

```bash
# 1. Remove integration lines from launch_complete_system.py
# 2. Delete attribution files:
rm trading-control/performance_attribution.py
rm trading-control/attribution_integration_example.py
rm trading-control/test_performance_attribution.py

# 3. System continues operating normally
```

## Success Criteria

✅ All files copied to trading-control/  
✅ Python syntax validation passes  
✅ Import test succeeds  
✅ Tests pass (optional)  
✅ Integration code added to launch_complete_system.py  
✅ System runs without errors  
✅ Reports generate to ./logs/attribution_*.json  
✅ Reports contain valid JSON with expected structure  

## Support

For questions or issues:
1. Check PERFORMANCE_ATTRIBUTION_GUIDE.md
2. Review test cases in test_performance_attribution.py
3. Check integration example in attribution_integration_example.py

## Deployment Confirmation

When all steps are complete:

```bash
echo "✅ Performance Attribution Engine - Deployment Complete"
date
```

---

**Installation Time**: ~10 minutes  
**Integration Time**: ~5 minutes  
**Testing Time**: ~2 minutes  
**Total**: ~17 minutes

---

Created: 2026-06-17  
Status: PRODUCTION READY ✅
