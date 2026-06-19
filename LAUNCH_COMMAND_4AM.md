# 4 AM LAUNCH — QUICK START

## ONE-LINE LAUNCH
```bash
python deploy_premarket_4am.py
```

## WHAT TO EXPECT

### Console Output (Real-Time)
```
======================================================================
PRE-MARKET TRADING SESSION - $1000 TARGET
======================================================================
Start Time: 2026-06-19T04:00:00
Starting Balance: $100.00
Target Balance: $1000.00
Required Daily Return: 128.0%
Broker Connected: True

[BROKER CONNECTED] Account: mock_account
[BROKER CONNECTED] Portfolio: $100.00

======================================================================
[TRADE 1] AAPL BUY 6 shares
  Entry: $150.00
  Stop: $147.00
  Target: $154.50
  Reason: MultiFrame(3/3) + Catalyst(85%) + Compliance OK
  Current Portfolio: $100.00

[PORTFOLIO] $100.50 (0.5% to target)

[TRADE 2] MSFT BUY 3 shares
  Entry: $151.00
  Stop: $148.98
  Target: $155.53
  Current Portfolio: $101.50

...

======================================================================
PRE-MARKET SESSION ENDED
======================================================================

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
Compliance Blocks: 0
======================================================================
PROGRESS! $3.45 gained (daily rate needed: 128.0%)
Results saved to premarket_trading_summary.json
```

## MONITORING DURING SESSION

### Check Progress Every Hour
1. **Look at console output** for portfolio updates
2. **Current Portfolio line** shows real-time account value
3. **Progress to Target** percentage shows how close to $1000

### If Something Goes Wrong
1. **Trades not executing?** Check Robinhood connection in console
2. **Compliance blocks appearing?** Check FINRA SHO list for blocked symbols
3. **Error messages?** Check `premarket_trading_4am.log` file
4. **Need to stop?** Press `Ctrl+C`

## AFTER SESSION ENDS (2:00 PM)

Check results file:
```bash
cat premarket_trading_summary.json
```

Key metrics to review:
- `pnl_dollars` — actual profit/loss
- `progress_percent` — % toward $1000 target  
- `win_rate_percent` — accuracy of signal generation
- `total_trades` — activity level

## DAY 1 GOAL

**Minimum:** At least $43 profit (to stay on pace for $1000)  
**Target:** 100% win rate on 5+ trades  
**Ideal:** $50+ profit to exceed pace

## NEXT STEPS (Day 2-7)

If Day 1 P&L >= $43:
- [ ] Keep same strategy
- [ ] Run again at 4 AM Day 2
- [ ] Aim for consistent $43+ daily

If Day 1 P&L < $43:
- [ ] Increase position sizing (currently 10% per position)
- [ ] Loosen confidence threshold (currently 85 minimum)
- [ ] Increase max trades per day (currently 10 max)
- [ ] Run analysis: which symbols were profitable?

## ENV SETUP (Optional - For Real Robinhood Trading)

If you have a Robinhood account:

```bash
# Set these environment variables
export ROBINHOOD_USERNAME="your.email@example.com"
export ROBINHOOD_PASSWORD="your-password"
export ROBINHOOD_MFA="123456"  # If MFA enabled
```

Without these, system will run in **simulation mode** (useful for testing).

---

**Ready?** Set alarm for 3:45 AM. Review DEPLOYMENT_4AM_$1000_CHECKLIST.md. Execute at 4:00 AM MST.

**Target:** $1000 from $100 in 7 days.  
**Day 1 Goal:** +$43 profit.  
**Let's go.**
