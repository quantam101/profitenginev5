# Dynamic Risk Adjustment - Quick Reference

## How It Works

The system now adjusts trading risk limits dynamically based on market volatility:

```
Market Volatility ↑  →  Risk Parameters ↓  →  Tighter Stop-Loss  →  Smaller Positions
Market Volatility ↓  →  Risk Parameters ↑  →  Looser Stop-Loss   →  Larger Positions
```

## Key Methods

### In `app.py`

```python
# 1. Calculate volatility scalar (affects position sizing)
volatility_scalar = self.risk_adjuster.calculate_volatility_scalar(symbol)
# Returns: 0.1 (very high vol) to 1.5 (very low vol)
# Meaning: < 1.0 = reduce size, > 1.0 = increase size

# 2. Adjust daily loss limit (affects stop-loss tightness)
adjusted_limit, utilization_pct = self.risk_adjuster.adjust_daily_loss_limit(realized_loss)
# Returns: (adjusted_limit_usd, utilization_percentage)
# Tightens as losses approach limit
```

### In `risk_kernel.py`

```python
# GATE 3 now checks against dynamic limit instead of hardcoded $200
if account_state.daily_pnl <= -self.max_daily_loss:
    rejections.append(RejectionReason.DAILY_LOSS_HIT)
```

## Configuration Parameters

In `config.yaml` under `risk.dynamic_risk`:

```yaml
baseline_volatility: 0.02              # Reference: 2% annualized volatility
kelly_base_fraction: 0.05              # Base Kelly: 5% before adjustments
volatility_lookback_periods: 20        # Rolling window: 20 periods
regime_switch_threshold: 0.95          # Confidence: 95% for regime change
```

## Market Regimes & Limits

| Regime | Volatility | Kelly | Loss Scalar | Loss Limit |
|--------|-----------|-------|-------------|-----------|
| Low | < 1.5% | 0.08 | 1.3x | $260 |
| Normal | 1.5-3% | 0.05 | 1.0x | $200 |
| High | 3-6% | 0.02 | 0.7x | $140 |
| Crisis | > 6% | 0.005 | 0.3x | $60 |

## Progressive Loss Tightening

As daily losses increase toward the limit:

| Loss Utilization | Loss Limit Adjustment | New Limit |
|-----|--------|---------|
| 0-50% | None | Base limit |
| 50-75% | -10% | 90% of base |
| 75-90% | -25% | 75% of base |
| 90%+ | -50% | 50% of base (stop new trades) |

**Example:** With $200 baseline in NORMAL regime and 80% loss utilization:
- Loss so far: $160
- Adjusted limit: $200 × 0.75 = $150
- Can't take more trades until loss drops below $150

## Volatility Scalar Effects

```
Formula: scalar = reference_volatility / current_volatility
Reference: 2% (from config)

Examples:
- Current Vol 1%  → scalar = 2.0/1.0 = 2.0 (capped at 1.5) → 50% larger positions
- Current Vol 2%  → scalar = 2.0/2.0 = 1.0 → baseline sizing
- Current Vol 4%  → scalar = 2.0/4.0 = 0.5 → 50% smaller positions
- Current Vol 5%  → scalar = 2.0/5.0 = 0.4 → 60% smaller positions
```

## Logging Output

When enabled, you'll see:

```
[AAPL] Volatility scalar: 0.856  # High vol = reduce size
[AAPL] Loss limit: $140.00 (utilization: 75.3%)  # Near limit = tighten
```

## Integration Points

| Where | What | Why |
|-------|------|-----|
| `process_market_snapshot()` line 90-96 | Calculate volatility scalar | Adjust position sizes |
| `process_market_snapshot()` line 116-119 | Adjust loss limit | Tighten stops dynamically |
| `risk_kernel.evaluate()` parameter | Pass adjusted limit | Apply stricter gates near loss limit |

## Testing Scenario

**Setup:** $200 daily loss limit, NORMAL regime

**Trade 1:** Lose $80, Vol = 2%
- Loss utilization: 40% → No adjustment
- Scalar: 1.0 → Normal sizing

**Trade 2:** Lose $60 more ($140 total), Vol spikes to 4%
- Loss utilization: 70% → Limit tightens to $150
- Scalar: 0.5 → Positions 50% smaller

**Trade 3:** Attempt another trade with $140 loss cumulative
- REJECTED: Daily loss ($140) > adjusted limit ($150)
- Must let losses recover before new trades

## Common Questions

**Q: What if price history is missing?**
A: Volatility scalar defaults to 1.0 (no adjustment)

**Q: What if realized losses haven't updated yet?**
A: Adjusted limit still applies based on last known loss

**Q: Can I disable dynamic adjustment?**
A: Not directly, but set `regime_switch_threshold: 0.0` to lock in NORMAL regime

**Q: Does this affect Kelly fraction calculation?**
A: Kelly is calculated but not yet applied to position sizing (future feature)

## Files to Review

1. `dynamic_risk_adjustment.py` - Core logic (348 lines)
2. `app.py` - Integration points (lines 29, 44-52, 90-96, 116-119, 132)
3. `risk_kernel.py` - Gate application (lines 17-26, 29-48, 60)
4. `config.yaml` - Parameters (lines 37-40)

## Performance Metrics to Watch

- **Regime Hit Rate:** How often do regimes change? (Expected: Daily)
- **Loss Limit Adjustments:** How often triggered? (Expected: ~30% of trades)
- **Volatility Scalar Range:** Min-max values observed (Expected: 0.15-1.5)
- **False Positives:** Trades rejected by tightened limits that would've won (Monitor)

---

**Last Updated:** 2026-06-17 | **Status:** Production Ready
