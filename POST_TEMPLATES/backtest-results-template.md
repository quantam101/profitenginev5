# Backtest Results Template

**Purpose**: Weekly/monthly post showcasing backtest results  
**Post Type**: Threads (3-4 parts) + Instagram (carousel) + LinkedIn (article)  
**Frequency**: Weekly  
**Best For**: Proof of concept, social proof, engagement via technical discussion  

---

## TEMPLATE STRUCTURE

### PART 1: HOOK (Eye-Catching Result)

**Formula**: Unexpected number + market condition + implication

```
"[STRATEGY] just made [PERCENTAGE]% in [TIMEFRAME]
while the market [UP/DOWN/FLAT].
Here's what worked (and what almost failed)."
```

**Examples**:

```
"Mean reversion made 12% last week while SPY was down 2%.
Here's what this strategy sees that other traders miss."
```

```
"Sector rotation portfolio up 31% YTD.
I tested it on 2020 (crashed 40%), 2022 (crashed 35%), 2008 (crashed 55%).
Here's why it still works despite those disasters."
```

```
"Built a new backtest on small-cap momentum.
56% win rate. 1.8 Sharpe. Passed stress tests.
But before I trade it live, here are the biggest risks I found."
```

**Rules**:
- ✅ Use specific numbers (not "great returns")
- ✅ Create contrast (works well when market works poorly)
- ✅ Hint at insight ("what this strategy sees...")
- ✅ Include the caveat ("here's what could break it")
- ❌ Don't cherry-pick results
- ❌ Don't ignore losses (be balanced)
- ❌ Don't claim it's "never lost money"

---

### PART 2: THE RESULTS (Screenshot + Narrative)

**Purpose**: Show exact backtest metrics with context

**Structure**:
- Strategy name and rules (1-2 sentences)
- Backtest period
- Key metrics (in priority order):
  - Annual return
  - Sharpe ratio
  - Max drawdown
  - Win rate
  - Profit factor
  - Number of trades
- Chart/screenshot of equity curve
- Current live performance (if applicable)

**Example 1 (Monthly Update)**:

```
"PART 2: Sector rotation backtest results (2015-2026, 11 years)

STRATEGY:
- Allocate 60% to best-performing sector last 3 months
- Hold 30% in runner-up sector
- Hold 10% cash
- Rebalance monthly

RESULTS:
- Annual return: 18.2%
- Sharpe ratio: 1.4
- Max drawdown: -22% (Feb 2020)
- Win rate: 68% (monthly months positive)
- Profit factor: 2.1 (win avg $10K, loss avg $4.8K)
- Total trades: 132 (11 years × 12 months)

[EQUITY CURVE SCREENSHOT]

Beats S&P 500 (10% annual) by 8 percentage points.
Acceptable drawdown for that outperformance."
```

**Example 2 (New Strategy)**:

```
"PART 2: Small-cap momentum backtest (2018-2026, 8 years)

STRATEGY:
- Rank small caps (market cap $300M-$2B) by 20-day returns
- Buy top 10 performers
- Sell bottom 10 (short or just avoid)
- Hold 1 month
- Equal weight, 1% risk per trade
- Rebalance monthly

RESULTS:
- Annual return: 24.8%
- Sharpe ratio: 1.6
- Max drawdown: -18% (March 2020)
- Win rate: 56% (but risk/reward makes money)
- Profit factor: 2.3 (win $12K avg, lose $5.2K avg)
- Total trades: 96 (8 years × 12 months)

[EQUITY CURVE SCREENSHOT]

But wait: let's test it on crashes..."
```

**Rules for Metrics**:
- ✅ Always include: Annual return, Sharpe, Max drawdown, Win rate
- ✅ Add context: How does it compare to SPY? To other strategies?
- ✅ Be honest: If Sharpe is low, say so and explain why you still like it
- ✅ Include trades count: More trades = more realistic slippage impact
- ❌ Don't cherry-pick only good metrics
- ❌ Don't show Sharpe without max drawdown
- ❌ Don't claim "perfect" (everything has drawdowns)

---

### PART 3: THE STRESS TEST (Proof It Survives Crashes)

**Purpose**: Show the strategy survives bad market conditions

**Structure**:
- Test the strategy on 2-3 major crashes
- Show the max loss during each crash
- Show recovery time
- Conclude: If it survives crashes, it probably works

**Example (Mean Reversion Stress Test)**:

```
"PART 3: But does this strategy survive crashes?

Tested mean reversion on 3 worst markets:

2008 FINANCIAL CRISIS:
- Max drawdown: -32% (vs. -57% for S&P 500)
- Recovery time: 8 months
- Win rate during crisis: 62% (mean reversion still works)

2020 MARCH COVID CRASH:
- Max drawdown: -28% (vs. -34% for S&P 500)
- Recovery time: 3 months
- Win rate during crisis: 51% (below avg, but positive)

2022 TECH BEAR MARKET:
- Max drawdown: -14% (vs. -33% for Nasdaq)
- Recovery time: 2 months
- Win rate during crisis: 65% (better than average)

Takeaway: Mean reversion WORKS in crashes.
When everyone panics, mean reversion finds the oversold bounces.
That's when the strategy makes money while others bleed."
```

**Example (Momentum Stress Test)**:

```
"PART 3: Now the hard part—does momentum survive crashes?

2008 FINANCIAL CRISIS:
- Max drawdown: -65% (ouch—worse than S&P 500)
- Why? Momentum strategies ride trends into crashes
- Recovery time: 18 months (really long)

2020 MARCH COVID:
- Max drawdown: -45% (vs. -34% market)
- Why? Momentum reversed hard
- Recovery time: 6 months

2022 TECH BEAR:
- Max drawdown: -38% (vs. -33% market)
- Why? Tech momentum leaders crashed hardest
- Recovery time: 4 months

HONEST TAKE:
Momentum is a high-win strategy but high-risk in crashes.
You get bigger losses when crashes happen.
This is the trade-off. If you can't tolerate that, don't trade momentum."
```

**Rules**:
- ✅ Test on 2+ major crashes (proves it's not luck)
- ✅ Include max drawdown AND recovery time
- ✅ Compare to market drawdown (shows relative risk)
- ✅ Be honest about failures (some strategies blow up in crashes)
- ✅ Explain why (mechanism understanding is key)
- ❌ Don't hide crash results
- ❌ Don't claim strategies that "never lose in crashes" (they don't exist)
- ❌ Don't ignore recovery time (months matter)

---

### PART 4: THE TRADE-OFFS (What You're Giving Up)

**Purpose**: Show you've thought through the strategy critically

**Structure**:
- What this strategy does well
- What it does poorly
- Who should/shouldn't trade it
- Your personal decision

**Example**:

```
"PART 4: The trade-offs of mean reversion:

WHAT IT DOES WELL:
✓ Makes money 65%+ of the time (high win rate = psychological comfort)
✓ Works in crashes (mean reversion bounces when others panic)
✓ Requires minimal capital (can trade small positions)
✓ Simple rules (easy to execute, hard to second-guess)

WHAT IT DOES POORLY:
✗ Gets crushed in trends (loses money 70%+ of days in trending markets)
✗ Requires regime detection (adds complexity)
✗ Needs tighter stop losses (forces exits on noise)
✗ Requires strict position sizing (can't scale easily)

WHO SHOULD TRADE IT:
→ Traders who tolerate 40%+ drawdowns between profitable periods
→ Traders with patience (mean reversion can take weeks)
→ Traders with discipline (regime filters stop you from trading trends)

WHO SHOULDN'T TRADE IT:
← Trend-following traders (opposite philosophy)
← Day traders (mean reversion plays on daily/weekly timeframes)
← Emotional traders (drawdowns test your nerve)

MY DECISION:
I'm building this into ProfitEngine because it works.
But I'm adding a regime detector so traders don't take it live in trending markets.
The biggest risk isn't the strategy—it's the trader trading it at the wrong time."
```

**Rules**:
- ✅ Balance pros and cons (equal length)
- ✅ Include who should/shouldn't trade it (self-awareness)
- ✅ Share your personal decision (build trust)
- ✅ Acknowledge the biggest risk (usually the trader, not the strategy)
- ❌ Don't make it sound perfect
- ❌ Don't oversell your decision
- ❌ Don't hide the downsides

---

### PART 5: LIVE PERFORMANCE (If You're Trading It)

**Purpose**: Bridge backtest to reality (only include if you're actually trading it)

**Structure**:
- Time period trading live
- Live performance vs. backtest expectations
- Adjustments you've made (slippage assumptions, position sizing, etc.)
- What surprised you (good and bad)

**Example**:

```
"PART 5: Real-world performance (last 6 months live):

SETUP:
- Started trading in January 2026
- $50,000 starting capital
- 1% risk per trade

RESULTS:
- Live return: 8.2% (vs. 18.2% backtest annual)
- Slippage impact: -2.4% (larger than backtest assumption)
- Drawdown: -7% (within expectations)
- Win rate: 65% (matches backtest)

SURPRISES:
✓ Slippage better than expected in large caps
✗ Liquidity worse than expected in small-cap plays
✓ Regime filter worked perfectly (saved me 3 bad trades)
✗ Emotional discipline harder than expected (wanted to ignore filter)

ADJUSTMENTS:
1. Using larger positions (liquidity allows it)
2. Avoiding 3pm-4pm EST (lowest volume period)
3. Strict 1% risk rule (no exceptions)
4. Regime filter stops overrides (non-negotiable)

NEXT MONTH:
- Scaling from $50K to $100K
- Adding second strategy (want multiple edges)
- Tracking slippage per hour of day"
```

**Rules** (for live performance):
- ✅ Show honest numbers (including underperformance)
- ✅ Explain gaps between backtest and live (slippage, emotion, liquidity)
- ✅ Document adjustments (shows learning)
- ✅ Include surprises (good and bad)
- ✅ Only include if you're actually trading it (don't fake it)
- ❌ Don't hide losses
- ❌ Don't exaggerate gains
- ❌ Don't ignore failures (regime filter didn't work, be honest)
- ❌ Don't claim live results that differ drastically without explanation

---

### PART 6: THE NEXT TEST (What You're Researching)

**Purpose**: Show you're continually improving, invite engagement

**Structure**:
- Planned tests (what you want to validate next)
- Open questions (what you don't know yet)
- Invitation to readers (what would they test?)

**Example**:

```
"PART 6: What I'm testing next:

PLANNED TESTS:
1. Does this strategy work on crypto? (Backtest BTH, ETH)
2. Can I combine it with momentum? (Better risk/reward?)
3. What's the optimal holding period? (1 month, 2 months?)
4. Does volatility filtering help? (Skip high-vol periods?)

OPEN QUESTIONS:
? Why does it work better in Q3-Q4? (Seasonality?)
? Does sector matter? (Tech mean reversion different from Energy?)
? What's the optimal regime threshold? (ADX 20 vs. 25?)
? Can retail traders actually execute it? (Liquidity constraints?)

TO YOU:
What would YOU test?
- Different timeframes?
- Different entry signals?
- Different position sizing?
- Different markets?

Let's collaborate. I'll test what you suggest."
```

**Rules**:
- ✅ Show you're still learning (builds credibility)
- ✅ Ask for help/collaboration (community-building)
- ✅ Document what you don't know (humility)
- ✅ Invite engagement (readers suggest tests)
- ❌ Don't claim you know everything
- ❌ Don't ask vague questions
- ❌ Don't ignore reader suggestions (follow up next month)

---

## INSTAGRAM CAROUSEL FORMAT (5 Slides)

**Slide 1: Hook**
```
BACKTEST RESULTS

[Strategy Name]
[Timeframe]
[Key Metric]

"[Percentage]% annual returns while market [did X]"
```

**Slide 2: Results Summary**
```
KEY METRICS

Annual Return: [X]%
Sharpe Ratio: [X.X]
Max Drawdown: [X]%
Win Rate: [X]%
Profit Factor: [X.X]

vs. S&P 500 baseline
```

**Slide 3: Equity Curve**
```
[Screenshot of backtest equity curve]

"11 years of results, including 2 crashes"
```

**Slide 4: Stress Test**
```
TESTED ON CRASHES

2008: -32% (vs. -57% market)
2020: -28% (vs. -34% market)
2022: -14% (vs. -33% market)

"Survives downturns"
```

**Slide 5: Call to Action**
```
FULL BREAKDOWN

Link in bio
See the detailed analysis:
- Rules
- Trade-offs
- Live performance
- Next tests

@ProfitEngine
```

---

## LINKEDIN ARTICLE FORMAT (1,500-2,000 Words)

**Headline**:
```
"I Backtested [Strategy] on 11 Years of Data. 
Here's Why It Works (And When It Breaks)."
```

**Opening**:
- The hook (surprising result)
- Why you tested it (personal experience, problem you're solving)
- What you found (teaser)

**Section 1: The Strategy**
- Simple explanation (rules, timeframe, market)
- Why it exists (academic research, historical evidence)
- Backtest setup (period, assumptions, costs)

**Section 2: The Results**
- Key metrics with context
- Equity curve screenshot
- Comparison to S&P 500
- Why these results matter

**Section 3: Crash Testing**
- Three major crashes tested
- How strategy performed in each
- Why it survived (or didn't)
- Implication for traders

**Section 4: Trade-offs**
- What it does well
- What it doesn't
- Who should/shouldn't trade it
- Your recommendation

**Section 5: Live Performance** (if applicable)
- Months trading live
- Actual vs. backtest results
- Adjustments made
- Surprises discovered

**Section 6: Future Research**
- What you're testing next
- Open questions
- Invitation to readers

**Closing**:
- Key takeaway
- CTA (free trial, join community, etc.)

---

## ENGAGEMENT STRATEGY

**For Threads**:
- Post Part 1 as main thread hook
- Parts 2-6 as replies
- First 2 hours: Reply to EVERY comment
- Engagement goals: 30-50 replies, 500-800 impressions

**For Instagram**:
- Post carousel (morning)
- Post reel showing equity curve + metrics (afternoon)
- Caption references Threads post
- Link in bio to full backtest details
- Engagement goals: 200-400 likes, 30-50 saves

**For LinkedIn**:
- Publish article
- Share link with context (why you backtested this)
- Tag relevant traders/funds
- Respond to all comments within 24 hours
- Engagement goals: 50-100 shares, 10-20 comments

---

## WEEKLY POSTING RHYTHM

**Every week, publish one backtest result:**

| Week | Strategy | Focus |
|------|----------|-------|
| 1 | Mean reversion | Crash-proof strategies |
| 2 | Momentum | Higher returns, higher risk |
| 3 | Sector rotation | Systematic asset allocation |
| 4 | Volatility | Advanced strategies |
| 5 | Combination strategy | Multiple edges = robustness |

**Repeat the cycle monthly** (backtest improvements, new data, new tests)

---

## CUSTOMIZATION CHECKLIST

```
□ Strategy name: _________________
□ Backtest start year: _________, end year: _________
□ Annual return: _________%
□ Sharpe ratio: _________
□ Max drawdown: _________%
□ Win rate: _________%
□ Profit factor: _________
□ Number of trades: _________
□ Comparison to S&P 500: _________%

STRESS TESTS:
□ Crash 1 (year): _________, drawdown: _________%
□ Crash 2 (year): _________, drawdown: _________%
□ Crash 3 (year): _________, drawdown: _________%

LIVE PERFORMANCE (if applicable):
□ Trading since: _________________
□ Live return: _________%
□ Slippage impact: _________
□ Emotional adjustments: _________________

NEXT TESTS:
□ Test 1: _________________________
□ Test 2: _________________________
□ Test 3: _________________________

OPEN QUESTIONS:
? _________________________________
? _________________________________
? _________________________________
```

Fill this out, and your backtest post writes itself.

