# AGGRESSIVE DEPLOYMENT GUIDE

**Status**: LIVE - AGGRESSIVE MODE ACTIVE  
**Launch**: June 26, 2026 @ 4:00 AM MST  
**Position Size**: $200-500 per trade (was $50-100)  
**Daily Loss Limit**: $200 (was $50)  
**Target Win Rate**: 85%+ (higher bar)  
**Risk Level**: MEDIUM-HIGH

---

## KEY CHANGES FROM MICRO TO AGGRESSIVE

### Position Sizing

| Metric | Micro | Aggressive | Change |
|--------|-------|-----------|--------|
| Min trade | $50 | $200 | +300% |
| Max trade | $100 | $500 | +400% |
| Base allocation | 75% | 90% | +15% |
| Kelly fraction | 0.25 (25%) | 0.50 (50%) | +25% |

**Example: $754 account**
- Micro mode: Risk max $100/trade
- Aggressive mode: Risk max $500/trade
- **5x more capital deployed per trade**

### Risk Limits

| Limit | Micro | Aggressive | Impact |
|-------|-------|-----------|--------|
| Daily max loss | $50 | $200 | Account can lose 26.5% in one day |
| Weekly max loss | $200 | $500 | Account can lose 66% in one week |
| Max open positions | 2 | 5 | 5 concurrent trades |
| Max trades/day | 3 | 8 | More trading opportunities |

**⚠️ WARNING**: Daily loss of $200 = 26.5% account drawdown in single day

### Signal Sensitivity

| Parameter | Micro | Aggressive | Effect |
|-----------|-------|-----------|--------|
| RSI threshold | 30/70 | 35/65 | More trades triggered |
| Confidence req | 55% | 50% | Lower bar for entry |
| Vote threshold | 0.3 | 0.2 | More trade signals |
| High vol action | SKIP | TRADE 50% | Trade volatile markets |

**Result**: 2-3x more trade signals daily

### Stop Loss & Exits

| Setting | Micro | Aggressive | Impact |
|---------|-------|-----------|--------|
| ATR multiplier | 2.0x | 1.5x | Tighter stops, faster exits |
| Exit partial 1 | +5% | +3% | Lock profit earlier |
| Exit partial 2 | +10% | +6% | Gradual taking of profits |
| Exits | 2-tier | 3-tier | More exit opportunities |
| Max hold | 4 hours | 3 hours | Close positions faster |

**Result**: Faster in, faster out (1-3 hour trades vs 4 hour)

---

## AGGRESSIVE EXECUTION FLOW

### 4:00 AM MST — Trigger

**New aggressive config loads**:
```yaml
position_size: $200-500 (was $50-100)
daily_loss_limit: $200 (was $50)
trades_per_day: 8 (was 3)
signal_confidence: 50% (was 55%)
```

### 4:00-4:15 AM — Signal Generation

**More trades generated**:
```
Micro mode: ~2-3 signals
Aggressive mode: ~6-8 signals

Reason: Wider RSI bands (35/65 vs 30/70)
        Lower confidence threshold (50% vs 55%)
        Higher vol tolerance
```

### 4:15-4:30 AM — Execution

**Larger positions placed**:
```
Example Trade 1: EHGO $500 (was $100)
Entry: $4.63
Stop: $4.50 (tighter: 1.5x ATR)
Target 1: $4.76 (+3%, sell 33%)
Target 2: $4.90 (+6%, sell 33%)
Target 3: $5.11 (+10%, sell 33%)

Profit potential: $185 (at target 3)
Loss potential: $65 (at stop loss)
Risk/reward: 1:2.85
```

### 4:30 AM - 12:00 PM — Active Management

**More frequent exits**:
- Partial exits at +3%, +6%, +10%
- Tighter stops (1.5x ATR vs 2x)
- Close faster (3 hours vs 4 hours)
- May exit multiple times per position

### 12:00-3:50 PM — Flatten

**All remaining positions closed by 3:50 PM ET**

---

## DAILY P&L SCENARIOS

### Scenario 1: Good Day (Above Average)

```
8 trades generated
6 executed (confidence > 50%)
5 winners, 1 loser

Avg winner: +$50 × 5 = +$250
Avg loser: -$40 × 1 = -$40
Daily P&L: +$210

Win rate: 83%
Account growth: +27.8% (from $754)
Trades to go: 4 (before hitting $200 daily limit)
```

### Scenario 2: Average Day

```
6 trades generated
5 executed
3 winners, 2 losers

Avg winner: +$40 × 3 = +$120
Avg loser: -$30 × 2 = -$60
Daily P&L: +$60

Win rate: 60%
Account growth: +7.9%
Status: PROFITABLE, below limit
```

### Scenario 3: Below Average (Loss Day)

```
5 trades generated
5 executed
2 winners, 3 losers

Avg winner: +$50 × 2 = +$100
Avg loser: -$70 × 3 = -$210
Daily P&L: -$110

Win rate: 40%
Account drawdown: -14.6%
Status: LOSS but within limits
```

### Scenario 4: Worst Case (Limit Hit)

```
6 trades generated
6 executed
1 winner, 5 losers

Avg winner: +$80 × 1 = +$80
Avg loser: -$56 × 5 = -$280
Daily P&L: -$200

Win rate: 17% (DISASTER)
Account drawdown: -26.5%
Status: DAILY LIMIT HIT - TRADING STOPPED
```

---

## DAILY TARGETS (AGGRESSIVE MODE)

### Daily
```
Trades: 4-8
Win rate: 65%+ (higher than micro's 60%)
Avg profit/win: $40-80
Avg loss/loss: $30-60
Daily target: +$50-150
```

### Weekly
```
Trades: 20-40 (aggressive hunting)
Win rate: 65%+
Weekly target: +$300-750
```

### Scaling Triggers

**Tier 2** (When account hits $1,500):
```
Position size: $500-1,000 (was $200-500)
Daily loss limit: $300 (was $200)
Daily target: +$100-300
```

**Tier 3** (When account hits $5,000):
```
Position size: $1,000-2,000
Daily loss limit: $500
Daily target: +$300-600
```

---

## RISK MANAGEMENT DIFFERENCES

### Micro Mode (Conservative)
```
✅ Proof of concept
✅ Low stress
✅ Slow growth
❌ Takes weeks to scale
```

### Aggressive Mode (Capital Growth)
```
✅ Fast account growth
✅ More trading opportunities
✅ Prove system at scale
❌ Daily swings of ±26%
❌ Stress & sleepless nights
❌ Ruin risk if system fails
```

---

## WARNING SIGNS TO WATCH

### ⚠️ Red Flags (Stop & Review)

1. **2 consecutive days losing $100+**
   - Action: Review signal quality
   - May need to revert to micro

2. **Win rate drops below 55%**
   - Action: Check regime detection
   - May need tighter filters

3. **Average loss exceeds $100/trade**
   - Action: Stops too wide
   - Tighten ATR multiplier

4. **Can't find 4+ trades/day**
   - Action: Market too quiet
   - Lower thresholds too much

### 🔴 Hard Stop (Automatic)

- Daily loss hits -$200 → All trading halted
- Weekly loss hits -$500 → 2-day pause
- Account drops below $500 → Scale back to micro

---

## FIRST WEEK AGGRESSIVE TARGETS

| Day | Goal | Status |
|-----|------|--------|
| Thu 4/26 | Prove aggressive works | +$50-100 |
| Fri 4/27 | Validate consistency | +$50-100 |
| Mon 4/30 | Hit $1,000+ (32% growth) | +$200-250 |

**By Friday**: If 60%+ win rate → proceed to Tier 2  
**By Monday**: If $1,000+ account → scale to $500-1,000 positions

---

## PSYCHOLOGICAL IMPACT

### Daily Swings (Aggressive Mode)

```
Good day:   +$200 = +26.5% (feels amazing)
Bad day:    -$200 = -26.5% (feels terrible)
Average:    ±$50-100 daily swings

Your stress level will increase significantly.
```

### Account Value Timeline (Projected)

```
Day 1: $754 (start)
Day 2: $850 (+12.7%)
Day 3: $950 (+25.9%)
Day 4: $1,000 (+32.6%) ← Tier 2 trigger
Day 5: $1,150 (+52.5%)
```

**If 2% daily ROI sustained**: $754 → $10,000 in 5-6 weeks

---

## WHEN TO REVERT TO MICRO

❌ If win rate drops below 50%  
❌ If losing $100+ per day for 3+ days  
❌ If signal quality seems degraded  
❌ If psychological stress overwhelming  
❌ If account drops below $500  

**Revert process**:
1. Switch config back to micro-trading.yaml
2. Reduce position size to $50-100
3. Daily loss limit back to $50
4. Run 20 trades to rebuild confidence
5. Retry aggressive when comfortable

---

## EXECUTION CHECKLIST

**Before 4:00 AM MST Tomorrow**:

- ✅ Aggressive config deployed (`aggressive-trading.yaml`)
- ✅ Automation updated (8 trades/day target)
- ✅ Risk limits understood ($200 daily max)
- ✅ Position sizing confirmed ($200-500)
- ✅ Stop losses tighter (1.5x ATR)
- ✅ Daily targets realistic (+$50-150)
- ✅ Revert plan ready (if needed)

**Mental preparation**:
- ✅ Ready for ±$200 daily swings
- ✅ Understand 5x capital deployed
- ✅ Accept 26% single-day drawdown possible
- ✅ Committed to hard loss limits

---

## LIVE METRICS (Tomorrow)

**4:00 AM MST**: System launches with aggressive config  
**4:15 AM**: First trades executed ($200-500 sizes)  
**4:15 PM**: Daily summary with results  

**Slack alert**:
```
🚀 AGGRESSIVE MODE ACTIVE
📊 Trades: 6
💰 Daily P&L: +$95
📈 Account: $849 (+12.6%)
⏰ Next execution: Tomorrow 4:00 AM
```

---

**AGGRESSIVE MODE DEPLOYED & LIVE**  
**Position size**: 5x increase ($200-500)  
**Risk**: 4x increase ($200 daily max)  
**Reward potential**: 5x+ if 70%+ win rate  
**First execution**: Tomorrow @ 4:00 AM MST

Ready to scale fast. 🚀

