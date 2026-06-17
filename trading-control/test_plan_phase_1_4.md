# Already Here - Complete Phase Test Plan
## Tomorrow 4am-8pm (Market Open to Close)

**Date:** 2026-06-17  
**Duration:** 16 hours continuous  
**Objective:** Validate all 4 phases end-to-end with real market conditions  

---

## ⏰ **Phase Timeline**

### **PHASE 1: Paper Trading** (4:00am - 7:00am)
**Goal:** Validate signal generation with live market data

```
Time:     4:00 AM - 7:00 AM (3 hours, pre-market + early trading)
Mode:     paper (simulated execution)
Capital:  $0 (no real risk)
Assets:   AAPL, MSFT, TSLA, AMZN, GOOGL (large cap focus)
Target:   30 proposals, analyze win rate
```

**Success Criteria:**
- ✅ 30+ proposals generated
- ✅ Win rate ≥ 40%
- ✅ All 4 agents functioning
- ✅ Risk kernel gates working (< 50% rejection rate)
- ✅ Audit ledger logging all trades

**If PASS:** → Proceed to Phase 2  
**If FAIL:** → Debug, iterate, retry Phase 1

---

### **PHASE 2: Shadow Trading** (7:00am - 11:00am)
**Goal:** Validate slippage model with real orderbooks

```
Time:     7:00 AM - 11:00 AM (4 hours, market hours)
Mode:     shadow (real quotes, simulated fills)
Capital:  $0 (no execution)
Assets:   Same as Phase 1
Target:   20+ shadow proposals, measure slippage accuracy
```

**Success Criteria:**
- ✅ Actual fills within ±15% of predicted slippage
- ✅ Liquidity model accurate
- ✅ Orderbook analysis working
- ✅ No stale quote errors
- ✅ All 4 agents still functional

**If PASS:** → Proceed to Phase 3  
**If FAIL:** → Recalibrate slippage model, retry Phase 2

---

### **PHASE 3: Preview Mode** (11:00am - 3:00pm)
**Goal:** Validate Robinhood connection with real quotes, fake fills

```
Time:     11:00 AM - 3:00 PM (4 hours, peak trading)
Mode:     preview (real Robinhood, sandbox execution)
Capital:  $50 max per trade ($0 real risk)
Assets:   AAPL, MSFT (high liquidity focus)
Target:   4 trades, validate Robinhood connection
```

**Success Criteria:**
- ✅ 4 orders submitted to Robinhood preview endpoint
- ✅ All orders acknowledged by Robinhood
- ✅ Fill prices logged correctly
- ✅ Broker reconciliation matches local ledger
- ✅ Account state queryable
- ✅ No authentication errors

**If PASS:** → Proceed to Phase 4  
**If FAIL:** → Check OAuth token, retry Phase 3

---

### **PHASE 4: Restricted Automation** (3:00pm - 8:00pm)
**Goal:** Full autonomous execution with hard limits enforced

```
Time:     3:00 PM - 8:00 PM (5 hours, late trading to close)
Mode:     live (real execution, real capital)
Capital:  $250 max per trade
Assets:   AAPL, MSFT, TSLA (liquid, established)
Target:   Unlimited trades, full profitability test
```

**Success Criteria:**
- ✅ Orders execute on real Robinhood account
- ✅ Fills recorded and P&L calculated
- ✅ Daily loss limit enforced ($200 hard stop)
- ✅ All 13 risk gates functioning
- ✅ Kill switch responsive
- ✅ End-of-day reconciliation passes

**If PROFITABLE:** → Promote to unrestricted  
**If LOSS ≤ $200:** → Shutdown, analyze, iterate  
**If LOSS > $200:** → Kill switch auto-triggers

---

## 📊 **Metrics to Track (All Phases)**

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| Proposals Generated | ✓ | ✓ | ✓ | ✓ |
| Win Rate | ✓ | ✓ | ✓ | ✓ |
| Rejections / Reasons | ✓ | ✓ | ✓ | ✓ |
| Slippage vs Model | - | ✓ | ✓ | ✓ |
| Fill Rate | Simulated | Simulated | Preview | Real |
| Broker Reconciliation | N/A | N/A | ✓ | ✓ |
| Account Equity | Simulated | Simulated | $50 | Real |
| Daily P&L | Simulated | Simulated | $0 | Real |
| Max Drawdown | Tracked | Tracked | Tracked | Tracked |

---

## 🔍 **Live Monitoring (Tomorrow 4am)**

### **Real-Time Dashboard**
```bash
# Terminal 1: Run trading system
cd trading-control
python app.py --mode paper --duration 12h --log verbose

# Terminal 2: Monitor audit ledger (refresh every 5 min)
watch -n 300 'sqlite3 audit.db "SELECT COUNT(*), SUM(realized_pnl) FROM outcomes;"'

# Terminal 3: System health check
watch -n 60 'python -c "from audit_ledger import AuditLedger; l = AuditLedger(\"audit.db\"); print(l.get_stats())"'
```

### **Checkpoints (Every Hour)**
```
4:00 AM - Phase 1 start (paper trading begins)
5:00 AM - Phase 1 checkpoint (10 trades, win rate?)
6:00 AM - Phase 1 checkpoint (20 trades, confidence high?)
7:00 AM - Phase 1 complete → Phase 2 start (shadow trading)
8:00 AM - Phase 2 checkpoint (slippage accurate?)
9:00 AM - Phase 2 checkpoint (rejection rates normal?)
11:00 AM - Phase 2 complete → Phase 3 start (preview mode)
12:00 PM - Phase 3 checkpoint (Robinhood connected?)
1:00 PM - Phase 3 checkpoint (fills matching?)
3:00 PM - Phase 3 complete → Phase 4 start (LIVE)
4:00 PM - Phase 4 checkpoint (real P&L?)
5:00 PM - Phase 4 checkpoint (stop loss working?)
6:00 PM - Phase 4 checkpoint (daily loss OK?)
8:00 PM - Phase 4 complete (market close)
```

---

## 📋 **Pass/Fail Criteria**

### **Phase 1 PASS:**
- ✅ 30+ proposals
- ✅ Win rate ≥ 40%
- ✅ < 40% rejection rate
- ✅ All 4 agents operating

### **Phase 2 PASS:**
- ✅ Slippage ±15% accurate
- ✅ No "DATA_STALE" errors
- ✅ Liquidity predictions correct
- ✅ Zero proposal errors

### **Phase 3 PASS:**
- ✅ 4+ real Robinhood orders
- ✅ Broker reconciliation 100%
- ✅ OAuth authentication stable
- ✅ No network timeouts

### **Phase 4 PASS:**
- ✅ Real fills executed
- ✅ P&L calculated correctly
- ✅ Daily loss limit enforced
- ✅ End-of-day close clean

---

## ⚠️ **Kill Switch Triggers (Phase 4)**

Auto-shutdown if:
- Daily loss ≥ $200 (hard limit)
- Broker connection lost
- Data freshness > 5 seconds
- Risk kernel gate failure
- Account reconciliation mismatch

---

## 📁 **Output & Logging**

All results saved to:
```
audit.db                           # SQLite ledger
logs/phase_1_4am-7am.log          # Phase 1 logs
logs/phase_2_7am-11am.log         # Phase 2 logs
logs/phase_3_11am-3pm.log         # Phase 3 logs
logs/phase_4_3pm-8pm.log          # Phase 4 logs

proof_of_work/
├── phase_1_report.md             # Win rate, stats
├── phase_2_slippage_analysis.md  # Accuracy check
├── phase_3_broker_validation.md  # Robinhood test
└── phase_4_trading_results.md    # Real P&L, final stats
```

---

## 🎯 **Success = Promotion Path**

**If all 4 phases PASS:**
- ✅ Paper → Shadow → Preview → Live validated
- ✅ Ready for **unrestricted automation**
- ✅ Can scale capital allocation
- ✅ Full profitability testing begins

**If any phase FAILS:**
- 🔄 Debug, iterate, retry
- 📊 Generate root cause analysis
- 🔧 Recalibrate agents/config
- ♻️ Return to failing phase

---

## 📞 **Pre-Test Checklist (Tonight)**

Before 4am tomorrow:
- [ ] Robinhood OAuth token active
- [ ] trading-control/ directory ready
- [ ] config.yaml configured
- [ ] audit.db schema initialized
- [ ] Logs directory created
- [ ] 3 terminal windows open (monitoring setup)
- [ ] Coffee/energy drink prepared ☕

---

**Ready for 4am tomorrow?** 🚀
