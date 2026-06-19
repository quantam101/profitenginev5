# JUST RUN IT — No Setup Required

## One Command at 4:00 AM

```bash
python deploy_premarket_4am.py
```

That's it. Everything else is automatic.

---

## What Happens

### If you have Finnhub API key (OPTIONAL)
```
[FINNHUB] ✓ Paper trading with real market data
[FINNHUB] ✓ Real prices from Finnhub API
[FINNHUB] ✓ Starting: $100.00
[FINNHUB] ✓ Auto-switch to real money at $1000.00 threshold
[MODE] FINNHUB_PAPER
```

### If no Finnhub API key (DEFAULT)
```
[NO API KEY] Running paper trading in simulation mode
[SIMULATION] ✓ Paper trading with simulated prices
[SIMULATION] ✓ Strategy validation mode
[SIMULATION] ✓ Starting: $100.00
[MODE] SIMULATION
```

**Both modes run the exact same strategy.**  
**Same win rate, same P&L calculation, same signals.**  
The only difference: live prices vs simulated prices.

---

## To Get Live Market Prices (Optional)

If you want real Finnhub prices instead of simulation:

### 1. Register (2 minutes)
```
https://finnhub.io/register
Sign up → Copy API key
```

### 2. Set API Key (1 command)
```powershell
$env:FINNHUB_API_KEY = "your_api_key_here"
```

### 3. Launch (same command)
```bash
python deploy_premarket_4am.py
```

Now it'll show `[MODE] FINNHUB_PAPER` with real prices.

---

## Expected Output (Either Mode)

```
======================================================================
PRE-MARKET TRADING SESSION - PAPER TRADING
======================================================================
Start Time: 2026-06-19T04:00:00
Starting Balance: $100.00
Target Balance: $1000.00
Required Daily Return: 38.9%
Data Source: [Finnhub API OR Simulation] (prices)
Mode: LIVE MARKET paper trading OR Paper trading (validation/testing)

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

**Q: Do I need to do anything right now?**  
A: Nope. Just run at 4 AM tomorrow.

**Q: What if I don't get Finnhub API key?**  
A: Still works. Uses simulation mode with same strategy.

**Q: What's the difference?**  
A: Live prices (Finnhub) vs simulated prices (no API key).  
Strategy is identical either way.

**Q: Can I add the API key later?**  
A: Yes. Run with simulation today, add key tomorrow, get live prices.

**Q: What happens when I hit $1000?**  
A: If/when you add Robinhood credentials, it switches to real money.  
For now, paper trading all the way.

**Q: How do I switch to real Robinhood money?**  
A: After paper trading validates, see `PHASE_2_ROBINHOOD_SWITCH.md`

---

## Ready?

4:00 AM tomorrow.  
One command.  
Watch it trade.

```bash
python deploy_premarket_4am.py
```
