# Strategy Deep-Dive Template

**Purpose**: Reusable structure for explaining trading strategies on Threads/Instagram/LinkedIn  
**Reading Time**: 8 minutes  
**Post Count**: 6-8 part Threads thread  

---

## TEMPLATE STRUCTURE

### PART 1: HOOK (The First 280 Characters)

**Formula**: Claim + Stat + Consequence

```
[STRATEGY NAME] has a ___% win rate on paper.
But [PERCENTAGE]% of traders who trade it lose money.
Here's what they're missing.
```

**Examples**:

```
"Mean reversion has 65% win rate on paper.
92% of traders who implement it lose money.
Here's the secret that separates winners from losers."
```

```
"Momentum strategies make money every year since 1926.
Yet 95% of retail traders can't profit from them.
This is why (and how to fix it)."
```

```
"Volatility mean reversion made 40% last year.
It's also blown up 1,000+ retail accounts.
Here's how to get the returns without the risk."
```

**Rules**:
- ✅ Use specific numbers (not "most" or "many")
- ✅ Create contrast (works on paper ≠ works in practice)
- ✅ Hint at a secret/insight
- ❌ Don't ask questions
- ❌ Don't use vague language
- ❌ Don't oversell

---

### PART 2: THE HISTORY (Why This Strategy Exists)

**Purpose**: Build credibility, explain where the edge comes from

**Structure**:
- Academic research or historical evidence
- Time period the strategy was profitable
- Who it works for (large funds? small caps? specific markets?)
- Why it's still relevant

**Example 1 (Mean Reversion)**:

```
"PART 2: Mean reversion was first documented in 1826.
It's been studied by academics for 100+ years.
It works because:

1. Markets overshoot (prices go too far too fast)
2. Humans anchor to recent prices (bias)
3. Fundamental value pulls price back (gravity)

But here's the catch: mean reversion ONLY works in range-bound markets.
In trends, it destroys accounts."
```

**Example 2 (Momentum)**:

```
"PART 2: Momentum returns were first measured by Jegadeesh & Titman (1993).
40+ years of research confirm it works.

The reason? Behavioral finance:
- Underreaction: Market slow to price in information
- Herding: Traders follow each other
- Anchoring: Traders price based on recent history, not fundamentals

These biases don't disappear because everyone knows about them.
They persist because fighting them requires discipline."
```

---

### PART 3: THE BACKTEST (Proof It Works)

**Purpose**: Show quantified results, make it specific

**Structure**:
- Strategy rules (3-5 bullet points max)
- Backtest period
- Key metrics (win rate, Sharpe, max drawdown, profit factor)
- Screenshot or chart (if possible)

**Example (Mean Reversion)**:

```
"PART 3: Tested mean reversion on SPY (2015-2026).

Rules:
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Hold max 20 bars
- Risk 1% per trade

Results:
- Win rate: 65%
- Sharpe ratio: 1.3
- Max drawdown: -18%
- Annual return: 21%

Looks great, right?
But this is where it falls apart in reality..."
```

**Rules**:
- ✅ Include 5-10 years of data minimum
- ✅ Show realistic costs (slippage, commissions)
- ✅ Include both win rate AND Sharpe (profit factor if possible)
- ✅ Mention max drawdown (shows risk)
- ❌ Don't cherry-pick favorable periods
- ❌ Don't show hypothetical returns (past ≠ future)
- ❌ Don't hide drawdown (it's critical)

---

### PART 4: THE FAILURE POINT (Why It Breaks)

**Purpose**: Show the real-world failure mode, build empathy, position solution

**Structure**:
- How the strategy fails in live trading
- Why the failure is inevitable (market regime, hidden assumption, execution problem)
- Quantified impact (how much money is lost)

**Example 1 (Mean Reversion in Trends)**:

```
"PART 4: Mean reversion fails in one specific condition: trends.

Look at 2024:
- SPY had 3 strong momentum phases (Jan-Mar, Jun-Aug, Oct-Nov)
- During trends, mean reversion = buying falling knives
- Traders using that RSI strategy lost 40% during Q2 2024

Why? The regime changed from mean-reverting to trending.
Mean reversion strategies have 0 Sharpe ratio in trend regimes.
They lose money every day."
```

**Example 2 (Momentum in Reversals)**:

```
"PART 4: Momentum fails at market inflection points.

The pattern:
- Momentum builds (say, Tesla rallies 20%)
- Retail traders pile in (FOMO kicks in)
- Hedge funds realize it's overextended
- They start shorting
- The move reverses hard (20% reversal in 2 days)

Momentum traders bought at the top of the momentum.
They lose 8-12% right as the trade reverses.

Why? Momentum works on herding psychology.
When the herd realizes the move is overdone, herding reverses.
The fastest way to lose momentum is to actually catch the inflection."
```

**Rules**:
- ✅ Be specific (what condition breaks it?)
- ✅ Show the loss (quantify the pain)
- ✅ Explain the mechanism (why does it break?)
- ✅ Build empathy (this happened to me / most traders)
- ❌ Don't be vague ("market conditions change")
- ❌ Don't claim total failure ("never works")
- ❌ Don't skip the mechanism (readers need to understand why)

---

### PART 5: THE REGIME FILTER (The Secret)

**Purpose**: Show how professionals handle the failure point

**Structure**:
- What additional data detects the regime shift
- How to automatically adapt the strategy
- Why this turns losers into winners

**Example 1 (Mean Reversion + Regime Detection)**:

```
"PART 5: Professionals add one filter: regime detection.

They use the ADX indicator (Average Directional Index):
- ADX < 20: Range-bound market (use mean reversion)
- ADX > 20: Trending market (skip mean reversion)
- ADX > 30: Strong trend (do the opposite: buy momentum)

With this one addition:
- Before: 65% win rate, 1.3 Sharpe, 40% loss in trends
- After: 73% win rate, 1.8 Sharpe, -2% loss in trends

One filter. Completely different results."
```

**Example 2 (Momentum + Regime Detection)**:

```
"PART 5: The professionals use this trick: check market breadth.

Before taking momentum trades, check:
- Percentage of stocks above 50-day moving average
- If >70%: Market is extended (skip momentum, wait for pullback)
- If 50-70%: Market is healthy (take momentum trades)
- If <50%: Market is in downtrend (don't take momentum)

This one filter prevents 80% of momentum reversals.
It cuts your win rate by 5%, but prevents the 40% losses that wipe accounts."
```

**Rules**:
- ✅ Use standard indicators (ADX, breadth, VIX, yield curve)
- ✅ Show the before/after metrics
- ✅ Explain why the filter works (market mechanism, not magic)
- ✅ Acknowledge the trade-off (sometimes miss winning trades to avoid big losses)
- ❌ Don't use obscure indicators
- ❌ Don't claim the filter fixes everything
- ❌ Don't skip the mechanism

---

### PART 6: THE VALIDATION (Multiple Signals)

**Purpose**: Show how to avoid false signals

**Structure**:
- One primary signal (the strategy core)
- 2-3 confirmation signals (only trade when all align)
- Real example showing why this matters

**Example (Mean Reversion with Validation)**:

```
"PART 6: But here's the trap: even with regime detection, false signals still exist.

The solution? Require multiple confirmations before trading:

Signal 1 (Primary): RSI < 30 (the mean reversion signal)
Signal 2 (Trend filter): ADX < 20 (range-bound market)
Signal 3 (Support): Price within 2% of moving average
Signal 4 (Volume): Volume spike on oversold candle (institutional interest)

Trade only when ALL 4 align.

Results:
- Win rate drops: 73% → 52%
- Sharpe ratio stays similar: 1.8 → 1.75 (less trades = less drag)
- Max drawdown: -18% → -7% (false signals eliminated)

You trade less. You win less often. But the losers are smaller."
```

**Rules**:
- ✅ Use 2-4 additional signals (not more—overcomplicates)
- ✅ Choose signals from different categories (trend, support, volume, volatility)
- ✅ Show the trade-off (fewer trades but better quality)
- ✅ Specific examples (which candles, which levels?)
- ❌ Don't pile on 10 signals ("paralysis by analysis")
- ❌ Don't use correlated signals (moving average + exponential moving average = redundant)
- ❌ Don't claim 100% accuracy

---

### PART 7: THE EXECUTION (How to Actually Trade It)

**Purpose**: Bridge the gap between backtest and live

**Structure**:
- Entry rules (specific, mechanical)
- Exit rules (specific, mechanical)
- Position sizing (how much risk?)
- Realistic assumptions (slippage, commissions, taxes)

**Example**:

```
"PART 7: Here's exactly how to trade mean reversion with regime filter:

ENTRY:
1. ADX < 20 (check daily chart)
2. RSI < 30 on 4-hour chart
3. Price tested support (2-day moving average)
4. Volume spike on entry candle
5. Entry order: limit order at previous low (not market order)

EXIT - PROFIT:
- RSI > 70 (take profit at mean reversion point)
- Or: Price hits previous high (profit target 3x risk)

EXIT - LOSS:
- ADX > 30 (regime shift, exit immediately)
- Or: Price breaks below support by 2% (hard stop loss)

POSITION SIZE:
- Risk 1% of account per trade
- If account = $50,000, risk $500 per trade
- If setup: -$500 loss at stop, position size = $50,000 / $500 = 100 shares

REALISTIC COSTS:
- Slippage: assume 2% on entry/exit
- Commissions: $5 per round trip
- Annual taxes: assume 15% of profits

Example math:
- Backtest shows: $10,000 profit/year
- Minus slippage: -$1,500 (15% of 100 trades × 2% × $50K)
- Minus taxes: -$1,275 (15% tax on $8,500)
- Real profit: ~$7,000/year (vs. backtest $10,000)
- But realistic, not fantasy."
```

**Rules**:
- ✅ Be mechanical (no judgment calls)
- ✅ Include entry, exit-win, exit-loss
- ✅ Include position sizing (critical for risk management)
- ✅ Include realistic costs (75% of traders ignore this)
- ❌ Don't leave ambiguity ("trade when it feels right")
- ❌ Don't ignore costs
- ❌ Don't assume perfect fills

---

### PART 8: THE CALL-TO-ACTION (Engagement)

**Purpose**: Get readers to engage, validate against their experience

**Structure**:
- Ask about their experience
- Create vulnerability (share your mistakes)
- Invite them to try it
- Reference ProfitEngine (soft mention only)

**Example**:

```
"PART 8: Here's my challenge to you:

Have you traded mean reversion?
If so: Did you use a regime filter?
If not: What stopped you (too complex? didn't know?)

I traded mean reversion for 2 years without regime detection.
Lost $8,000 in 2023 on false signals in the trending market.
Didn't realize the problem until I backtracked with regime filters.

If you want to test this framework live,
ProfitEngine has this structure built in (automated regime detection, multi-signal validation).

But even without automation: take the framework above and test it.
What's your result?"
```

**Rules**:
- ✅ Ask a specific question (gets replies)
- ✅ Share a personal failure (builds trust)
- ✅ Mention ProfitEngine naturally (not "buy now")
- ✅ Invite testing/verification
- ❌ Don't sell hard ("this is the only way")
- ❌ Don't ask vague questions ("what do you think?")
- ❌ Don't assume everyone agrees with you

---

## FORMATTING FOR THREADS/INSTAGRAM/LINKEDIN

### Threads Format (Multi-Part)

```
PART 1 (Hook) — Standalone post, 280 chars max
[Thread indicator emoji or text]

PART 2 (History) — Reply to Part 1
PART 3 (Backtest) — Reply to Part 2
[Include screenshot if possible]

PART 4 (Failure Point) — Reply to Part 3
PART 5 (Regime Filter) — Reply to Part 4
PART 6 (Validation) — Reply to Part 5
PART 7 (Execution) — Reply to Part 6
PART 8 (CTA) — Reply to Part 7
```

### Instagram Carousel Format

Condense to 5-7 slides:
1. Hook graphic
2. History/context
3. Backtest results (screenshot)
4. Failure point
5. Regime filter explanation
6. Execution rules
7. CTA

### LinkedIn Article Format

Combine into 2,000-2,500 word article:
- Hook paragraph
- History section
- Backtest section with images
- Failure analysis
- Filter explanation
- Execution guide
- Conclusion + CTA

---

## TIMING & ENGAGEMENT TIPS

**Best times to publish**:
- Threads: 9 AM ET (US traders waking up)
- Instagram: 6-8 PM ET (evening browsing)
- LinkedIn: 8-10 AM ET (morning professional browsing)

**Engagement obligations**:
- Threads: Reply to 100% of comments in first 2 hours
- Threads: Reply to 70% of comments in hours 2-12
- Instagram: Reply within 24 hours (carousel/reel)
- LinkedIn: Reply within 24 hours (article)

**Follow-up**:
- Day 2: Share carousel version with "See full strategy breakdown"
- Day 3: Share Instagram reel with "Quick visual guide"
- Day 7: Share LinkedIn article with "Long-form deep dive"
- Week 2: Reference the strategy in next post ("As I outlined in the mean reversion post...")

---

## CUSTOMIZATION CHECKLIST

For each strategy deep-dive, personalize:

```
□ Strategy name: ________________________
□ Win rate on paper: _________%
□ Percentage of traders who fail: _________%
□ Historical evidence (study, researcher, year): ________________
□ Backtest period: _________ to _________
□ Key metrics (Sharpe/Max Drawdown/Annual Return): _________
□ Primary failure point: ________________________
□ Regime detection method: ________________________
□ Primary signal: ________________________
□ Confirmation signals (2-3): ________________________
□ Position sizing rule: ________________________
□ Expected slippage cost: ________%
□ Your personal experience: ________________________
□ Your biggest mistake with this strategy: ________________________
□ Current ProfitEngine feature that automates this: ________________________
```

Once filled out, the full post writes itself.

