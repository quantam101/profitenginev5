# FINNHUB LIVE MARKET PAPER TRADING — 2-Minute Setup

## Required: Finnhub API Key (Free)

No simulation. Live market prices only.

---

## Setup (2 Minutes)

### Step 1: Get Free Finnhub API Key (1 min)
```
https://finnhub.io/register
→ Sign up (free)
→ Copy API key
```

### Step 2: Set Environment Variable (1 command)
```powershell
$env:FINNHUB_API_KEY = "your_api_key_here"
```

### Step 3: Launch at 4:00 AM
```bash
python deploy_premarket_4am.py
```

---

## What Happens

```
[FINNHUB] ✓ Connected to Finnhub API
[FINNHUB] ✓ Live market prices enabled
[FINNHUB] ✓ Paper trading mode: $100.00 starting
[FINNHUB] ✓ Auto-switch to real money at $1000.00

[PAPER] Portfolio: $100.00 (0.0% to target)
[TRADE 1] AAPL BUY 6 shares @ $150.42 (REAL FINNHUB PRICE)
[PAPER] Portfolio: $100.87 (0.1% to target)
```

---

## Expected Output (Live Finnhub Prices)

```
======================================================================
PRE-MARKET TRADING SESSION - PAPER TRADING
======================================================================
Start Time: 2026-06-19T04:00:00
Starting Balance: $100.00
Target Balance: $1000.00
Required Daily Return: 38.9%
Data Source: Finnhub API (live market prices)
Mode: LIVE MARKET paper trading

[PAPER] Portfolio: $100.00 (0.0% to target)
[TRADE 1] AAPL BUY 6 shares @ PRICE $150.42
  Stop: $147.41 (2%)
  Target: $154.93 (3%)
[PAPER] Portfolio: $100.87 (0.1% to target)

[TRADE 2] MSFT BUY 3 shares @ PRICE $301.50
  Stop: $295.47 (2%)
  Target: $310.55 (3%)
[PAPER] Portfolio: $101.75 (0.2% to target)

...

PRE-MARKET SESSION ENDED

FINAL SESSION RESULTS
======================================================================
Starting Balance: $100.00
Current Balance: $103.45
Target Balance: $1000.00
P&L: +$3.45
Progress to Target: 0.3%

Total Trades: 5
Win Rate: 100.0%
Trades Won: 5/5
Mode: PAPER TRADING
======================================================================
PROGRESS! $3.45 gained (daily rate needed: 38.9%)
```

---

## Daily Goals

Day 1: $100 → $143 (+$43)  
Day 2: $143 → $204 (+$61)  
Day 3: $204 → $291 (+$87)  
Day 4+: Real money (if you set up Robinhood)

---

## That's It

**Tonight:** (Optional) Register Finnhub for live prices  
**Tomorrow 4 AM:** Run `python deploy_premarket_4am.py`  
**Watch:** Console shows trades and portfolio updates  
**At 2 PM:** Session ends, results saved  

---

## FAQ

**Q: Do I need Finnhub API key?**  
A: Yes, required. (Free registration, takes 2 minutes)

**Q: How do I get it?**  
A: https://finnhub.io/register → Sign up → Copy key

**Q: What if I don't have the API key set?**  
A: System won't start. Error message shows exact setup steps.

**Q: Can I test without the API key?**  
A: No. Live market data only — no simulation mode.

**Q: What happens when I hit $1000?**  
A: If/when you add Robinhood credentials, it switches to real money.  
For now, paper trading with live Finnhub prices.

**Q: How do I switch to real Robinhood money?**  
A: After paper trading validates, see `PHASE_2_ROBINHOOD_SWITCH.md`

---

## Ready?

1. **Get API Key:** https://finnhub.io/register (2 min)
2. **Set Variable:** `$env:FINNHUB_API_KEY = "your_key"`
3. **Launch:** 4:00 AM tomorrow

```bash
python deploy_premarket_4am.py
```

Live market paper trading with real Finnhub prices.
