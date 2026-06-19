# FINNHUB PAPER TRADING SETUP — $100 to $1000

## Quick Summary

- **Starting Balance:** $100 (paper trading)
- **Real Market Data:** Finnhub API (live stock prices)
- **Auto-Switch:** Automatically activates real money at $1000
- **No Risk:** Paper trading until goal is reached

---

## STEP 1: Get Free Finnhub API Key (2 minutes)

### Option A: Free Tier (Recommended)
1. Go to: https://finnhub.io/register
2. Sign up with email
3. Choose **Free Plan**
4. Get your API key from dashboard
5. Copy the key

### Option B: Get API Key from Dashboard
- Login at https://finnhub.io
- Go to Dashboard → API keys
- Copy your free API key

---

## STEP 2: Set Environment Variable

### Windows Command Prompt
```cmd
set FINNHUB_API_KEY=your_api_key_here
```

### Windows PowerShell
```powershell
$env:FINNHUB_API_KEY = "your_api_key_here"
```

### Linux/Mac
```bash
export FINNHUB_API_KEY="your_api_key_here"
```

### Permanent (add to .env file)
Create file `.env` in project root:
```
FINNHUB_API_KEY=your_api_key_here
```

---

## STEP 3: Verify Setup

Run verification:
```bash
python verify_system_ready.py
```

Should show:
```
[CHECK 1] Testing module imports...
  ✓ All module imports successful
```

---

## STEP 4: Launch at 4 AM

```bash
python deploy_premarket_4am.py
```

### Expected Output
```
======================================================================
PRE-MARKET TRADING SESSION - PAPER TRADING
======================================================================
Start Time: 2026-06-19T04:00:00
Starting Balance: $100.00
Target Balance: $1000.00
Data Source: Finnhub API (real-time prices)
Mode: Paper trading until $1000.00

[FINNHUB] Paper trading initialized with $100.00
[FINNHUB] Auto-switch to real money at $1000.00 threshold

[PAPER] Portfolio: $100.00 (0.0% to target)
[TRADE 1] AAPL BUY 1 shares @ REAL PRICE $150.42
  Stop: $147.41 (2%)
  Target: $154.93 (3%)
```

---

## WHAT HAPPENS AUTOMATICALLY

### During Paper Trading ($100 - $999)
- All trades are **simulated** (no real money spent)
- Prices are **real** from Finnhub API
- Portfolio value tracks actual market movements
- Win/loss calculations are realistic

### At $1000 Threshold
- System automatically detects: Portfolio = $1000+
- Logs: `[FinnhubClient] SWITCHING TO REAL MONEY TRADING`
- Real money trading activates
- All future trades use actual account funds

### During Real Money Trading ($1000+)
- Same signal generation strategy
- Real broker execution (if integrated)
- Real profit/loss
- Actual portfolio growth

---

## EXAMPLE TRADING SESSION

### Start (4:00 AM)
```
Portfolio: $100.00
Paper Trading Mode: ON
```

### First Trade
```
[TRADE 1] AAPL BUY 6 shares @ $150.42 (Finnhub real price)
Entry: $150.42
Stop: $147.41 (2% loss = -$18.25)
Target: $154.93 (3% profit = +$27.06)
```

### After 3 Profitable Trades
```
[PAPER] Portfolio: $103.45 (+3.45%)
Progress: 0.3% to $1000 target
```

### After 10 Profitable Trades (2% avg per trade)
```
[PAPER] Portfolio: $122.00 (+22%)
Progress: 2.2% to $1000 target
```

### After Reaching $500
```
[PAPER] Portfolio: $500.00
Progress: 50.0% to $1000 target
```

### At $1000 Milestone
```
[REAL MONEY] Portfolio: $1000.01
[FinnhubClient] SWITCHING TO REAL MONEY TRADING
Mode: Paper trading until $1000.00 → COMPLETE
Mode: Real money trading activated
```

---

## FINNHUB API LIMITS

### Free Plan
- **Requests:** 60 per minute
- **Data:** Delayed by 15 minutes
- **Symbols:** All US stocks supported
- **Cost:** Free

### For Real-Time (1 min or less delay)
- Premium plans available
- Not required for paper trading
- Free plan sufficient for testing

---

## MONITORING PAPER TRADING

### Real-Time Log
```bash
tail -f premarket_trading_4am.log
```

### Check Portfolio Every Hour
Look for lines like:
```
[PAPER] Portfolio: $103.45 (0.3% to target)
[PAPER] Portfolio: $150.23 (5.0% to target)
[PAPER] Portfolio: $267.50 (16.7% to target)
[PAPER] Portfolio: $523.00 (52.3% to target)
[REAL MONEY] Portfolio: $1000.50 (100.0% to target)
```

### Results File
```bash
cat premarket_trading_summary.json
```

Shows:
- `is_real_money`: false (paper) or true (real)
- `portfolio_value`: current account value
- `pnl_dollars`: profit/loss in dollars
- `progress_percent`: % toward $1000

---

## TROUBLESHOOTING

### "No API key provided - using simulation mode"
**Problem:** Finnhub API key not set  
**Solution:** 
```powershell
$env:FINNHUB_API_KEY = "your_key_here"
python deploy_premarket_4am.py
```

### "Cannot get price for AAPL"
**Problem:** API call failed  
**Solution:**
- Check internet connection
- Verify API key is valid
- Wait 60 seconds (rate limit)
- Check Finnhub status: https://status.finnhub.io

### "Insufficient buying power"
**Problem:** Portfolio value too low for position size  
**Solution:**
- Position sizing automatic: 10% of portfolio
- As portfolio grows, position sizes grow
- Start small, scale up with profits

### "No position to close"
**Problem:** Tried to close position that doesn't exist  
**Solution:**
- System skips invalid closes automatically
- Check log for warnings
- Normal operation

---

## DAILY TARGETS

For $100 → $1000 in 7 days:

| Day | Start | Target | Needed |
|-----|-------|--------|--------|
| 1 | $100 | $143 | +$43 |
| 2 | $143 | $204 | +$61 |
| 3 | $204 | $291 | +$87 |
| 4 | $291 | $416 | +$125 |
| 5 | $416 | $595 | +$179 |
| 6 | $595 | $851 | +$256 |
| 7 | $851 | $1216 | +$365 |

**Daily return needed: ~43% compounded**

With 2-3% profit per trade × 5 trades = 10-15% per day  
**Need:** 3-4x more profitability OR more trades per day

---

## AFTER PAPER TRADING ($1000+)

### What Switches to Real Money?
- Order execution (trades become real)
- Buying power (your actual account funds)
- P&L (real profit/loss)
- Portfolio value (real account balance)

### What Stays the Same?
- Signal generation (same algorithm)
- Risk management (same stops/targets)
- Position sizing (same percentage-based)
- Compliance monitoring (same rules)

### First Real Money Trade
When portfolio hits $1000:
- Next signal generated
- Order sent to actual broker
- Real money executed
- Real profit/loss recorded

---

## SAFETY FEATURES

### Paper Trading Protection
- No real money at risk before $1000
- All positions fully backed by cash
- No leverage or margin
- Perfect for testing strategy

### Automatic Safeguards
- Auto-switch only at $1000+ (not below)
- Position limits enforced (max 5 open)
- Compliance checks before every trade
- Stop-loss and take-profit on every position

### Emergency Stop
```bash
# Press Ctrl+C to stop at any time
# All positions closed, session ends cleanly
```

---

## NEXT STEPS

1. **Get API Key:**
   - Visit https://finnhub.io/register
   - Copy API key

2. **Set Environment:**
   ```powershell
   $env:FINNHUB_API_KEY = "your_key_here"
   ```

3. **Verify System:**
   ```bash
   python verify_system_ready.py
   ```

4. **Launch at 4 AM:**
   ```bash
   python deploy_premarket_4am.py
   ```

5. **Monitor:**
   - Watch console for portfolio updates
   - Target: +$43 profit on Day 1

6. **After $1000:**
   - System switches to real money automatically
   - Real trading begins
   - Continue same strategy Days 2-7

---

## QUESTIONS?

**Finnhub Documentation:** https://finnhub.io/docs/api/  
**Finnhub Status:** https://status.finnhub.io/  
**API Key Issues:** Check dashboard at https://finnhub.io

---

**Ready?** Get your API key, set the env var, launch at 4 AM.  
**Target:** $100 → $1000 in one week on paper, then real money.
