# ProfitEngine v5 — Premium Tier Structure

**Status**: Production-Ready | **Updated**: 2026-06-20

This document defines a conversion-focused, friction-free premium tier structure that removes the $25K revenue gate and focuses on immediate value delivery.

---

## Tier Overview Matrix

| Dimension | **TIER 1: Free** | **TIER 2: Premium** | **TIER 3: Annual** | **TIER 4: Enterprise** |
|-----------|-----------------|--------------------|--------------------|----------------------|
| **Pricing** | $0 (free trial) | $29/month | $249/year ($20.75/mo) | Custom (negotiate) |
| **Duration** | 30 days | Month-to-month | Prepaid annually | Custom contract |
| **Best For** | Traders testing the platform | Active traders, signal users | Committed traders, institutions | White-label partners, hedge funds |
| **Billing Cycle** | N/A | Recurring monthly | Single annual charge | Custom |
| **Setup Fee** | None | None | None | Custom |
| **Cancellation** | Expires after 30 days | Cancel anytime (no penalty) | Refund if cancelled in first 30 days | Negotiated terms |

---

## TIER 1: Free (30-Day Trial)

### Goal: Conversion to Paid
The free tier exists to prove value, build habits, and remove friction from trial signup. All features are designed to create urgency at day 28 when the trial expires.

### Features

#### Core Access
- **30-day backtesting trial** on up to 5 stocks
- **3 sample strategies** (beginner-friendly)
  - Momentum Breakout (30-day lookback, daily timeframe)
  - Mean Reversion (Bollinger Bands, 20-day period)
  - Volume Surge (unusual volume detection, 14-day average)
- **Historical backtest results** (view-only, no export)
- **Daily email digest** (1 per day, strategy summary only)

#### Trading Features
- **No live trading access** (backtest-only)
- **No API access** (web UI only)
- **No strategy customization** (fixed parameters)
- **No real-time signals** (history only)
- **30-day data retention** (auto-delete after trial ends)

#### Community & Support
- **Discord access** (read-only, #general only)
- **Email support** (48-hour response, non-priority)
- **Onboarding email sequence** (5 emails over 28 days)

#### Conversion Hooks (Built-In)
- **Day 3**: "First winning strategy results" email with ROI math
- **Day 7**: Unlock view of 2nd and 3rd sample strategies
- **Day 14**: Show signal accuracy metrics (vs. S&P 500 baseline)
- **Day 21**: Social proof email (recent member wins, testimonials)
- **Day 28**: "Trial expires in 2 days" upgrade reminder (discount offer: first month 50% off)

### Value Justification for This Tier
- **Zero friction**: No credit card required, instant signup
- **Instant value**: Backtest results visible in < 5 minutes
- **Proof of concept**: See real strategy performance, not marketing claims
- **Habit formation**: Daily email reminder creates engagement loop
- **Natural progression**: Limits (5 stocks, 3 strategies) feel arbitrary → drives upgrade

### Expected Conversion Rate
- **Target**: 15-20% of free users upgrade by day 30
- **Pricing psychology**: $29/mo feels like "test drive" after 30 days at $0
- **FOMO trigger**: "Your trial data expires in 2 days" is powerful

### LTV (Lifetime Value) from Free Tier
- Avg free user → $0 revenue
- Avg converted user → ~$350/year (12 months × $29 + retention bonus)
- Breakeven conversion rate → 3% (lowest viable segment)
- Realistic target → 15-20% conversion from quality free tier

---

## TIER 2: Premium ($29/month)

### Goal: Revenue Generation + User Retention
This is the core revenue tier. Designed for active traders who want all features, live signals, and community access.

### Features

#### Unlimited Trading
- **Unlimited stocks** (all major US equities)
- **All 11 trading strategies** (live & fully customizable)
  1. Momentum Breakout
  2. Mean Reversion
  3. Volume Surge
  4. Trend Following (MA crossover)
  5. RSI Oversold (momentum reversal)
  6. Earnings Momentum (catalyst-based)
  7. Sector Rotation (correlation-based)
  8. Volatility Breakout (market regime detection)
  9. Fibonacci Retracements (technical levels)
  10. MACD Divergence (momentum confirmation)
  11. Ichimoku Cloud (multi-timeframe confluence)

#### Live Signals & Execution
- **Real-time trading signals** (push notification + email)
- **Signal filtering** (by strategy, confidence threshold, sector)
- **Live position monitoring** (entry, stop-loss, target prices)
- **Risk parameter customization**
  - Position size (1-5% of portfolio)
  - Stop-loss distance (2-10% below entry)
  - Target profit (1-20% above entry)
  - Max portfolio risk (1-5% per trade)

#### API Access (Level 1)
- **REST API** (up to 100 requests/day)
- **Signal webhook** (POST to your endpoint when signal fires)
- **Portfolio export** (JSON, CSV, XLS formats)
- **Backtest data export** (unlimited exports)
- **Rate limits**: 100 API calls/day, 10 calls/min

#### Community & Support
- **Discord access** (full channels, #signals, #strategies, #wins)
- **Weekly community analysis** (written + video, market outlook + signal performance)
- **Email support** (24-hour response, priority queue)
- **Monthly office hours** (live Q&A with strategy authors, 4 sessions/month)
- **Strategy discussion threads** (ask authors to explain signal rationale)

#### Insights & Analytics
- **Confidence score breakdown** (why was this signal generated?)
- **Historical win rate** (by strategy, by timeframe, by market condition)
- **Signal accuracy report** (updated weekly)
- **Portfolio performance vs. S&P 500** (benchmark comparison)
- **Monthly performance report** (email summary)

#### Backtest Customization
- **Unlimited backtests** (change any parameter, run historical analysis)
- **Parameter sweeping** (test 10-1000 combinations)
- **Monte Carlo analysis** (stress-test strategy robustness)
- **Out-of-sample testing** (validate on unseen data)
- **Save custom strategies** (up to 10 custom variants)

### Retention Hooks
- **Streak tracking**: "You've backtested 14 days in a row"
- **Community wins**: Weekly testimonial email ("John made $2,347 on the Earnings Momentum signal")
- **Performance milestone**: "Your portfolio beat SPY by 8% this month"
- **Strategy unlocks**: Monthly feature releases (new indicators, smarter parameters)

### Value Justification
- **ROI clarity**: One winning trade (2-5% return) pays for an entire year
- **Time savings**: 15 min/week to review signals vs. 5+ hours analyzing charts
- **Community**: Real traders sharing winning trades + explanations
- **Customization**: Adapt strategies to your risk tolerance, not fixed settings
- **Risk control**: Position sizing + stop-losses eliminate 90% of catastrophic loss risk

### Pricing Psychology
- **$29/month** feels like a coffee subscription
- **"One winning trade pays for a year"** is the core mental model
- **Compared to advisory fees** (1% AUM = $200/month on $20K portfolio), it's a bargain
- **Cancellation anytime** removes commitment anxiety

### Expected Churn Rate
- **Target**: 5-8% monthly churn (92-95% retention)
- **Healthy SaaS baseline**: 5-7% churn is strong
- **Leverage point**: Community engagement + signal accuracy drive retention

### LTV (Lifetime Value) from Premium Tier
- **Avg duration**: 12-24 months (before trader graduates or loses interest)
- **Base LTV** (12 months): $29 × 12 = $348
- **With 20% annual churn**: Avg 10 months = ~$290 LTV
- **Upsell to annual**: 30% move to annual tier, add $30-50 additional LTV
- **Enterprise upsell**: 5-10% move to Enterprise tier, add $200-500 LTV
- **Total realistic LTV**: $300-400 per Premium user

---

## TIER 3: Annual ($249/year = $20.75/month)

### Goal: Revenue Acceleration + Commitment Signal
Annual tier locks in committed users and improves unit economics. Premium features identical to Tier 2, but with commitment discount + early-access benefits.

### Features

#### Identical to Premium
- All Tier 2 features (11 strategies, API, Discord, analytics)
- Same signal quality, same customization, same support

#### + Annual Bonuses
- **29% discount**: $249/year vs. $348/year (monthly billing)
- **Early access** to new strategies (1-2 weeks before general release)
- **Annual strategy report** (personalized analysis of your top 3 strategies)
- **Guaranteed support response**: 12-hour SLA (vs. 24-hour for monthly)
- **Monthly bonus credit**: $10 credit toward upgrade to Enterprise (if desired)

#### Psychological Commitment
- **Prepayment friction**: Signals "I'm serious about trading"
- **Visible savings**: 29% discount is emotionally clear
- **Loss aversion**: "If I upgrade, I'll use it" (sunk cost effect)
- **Lock-in benefit**: Prices may increase next year; annual users grandfathered at $249

### Conversion Path to Annual
1. **Trial → Monthly**: User converts to Premium at end of trial
2. **Month 2-3**: "Thinking about annual billing? Save 29% + get early access"
3. **After 6 months**: "You've made 12 trades on Premium—switch to annual & save $99/year"
4. **At month 11**: "Your annual billing opens next month—lock in current price"

### Value Justification
- **Breakeven timeline**: 8.5 months, then pure savings
- **Price guarantee**: Lock in $249 price (next year may be $299)
- **Early access**: Test new strategies 2 weeks before peers
- **Time value**: Pre-commit to taking trading seriously for 365 days

### Expected Conversion Rate
- **Target**: 30-40% of Premium users upgrade to Annual
- **Leverage point**: Offer upgrade after month 3 (habit formation peak)
- **Packaging**: Bundle with "early access" + "priority support" to justify commitment

### LTV from Annual Tier
- **Base LTV**: $249/year × 1.5 years (avg duration) = $373
- **Upsell to Enterprise**: 8-12% of annual users upgrade, add $250-400 LTV
- **Total realistic LTV**: $400-500 per Annual user

---

## TIER 4: Enterprise (Custom Pricing)

### Goal: High-Touch Revenue + Strategic Partnerships
Enterprise tier serves institutional clients, hedge funds, and white-label partners. No fixed price; negotiate per client.

### Features

#### Everything in Premium + Custom Builds
- All Tier 2-3 features (unlimited strategies, API, community)
- **White-label hosting** (tradingengine.yourcompany.com)
- **Custom strategy development** (author writes strategy to your specs, $5-20K per strategy)
- **Institutional API** (unlimited requests, SLA-backed, 99.9% uptime guarantee)
- **Webhook priority** (signal delivery in < 100ms, vs. 1-3 sec for Standard API)
- **Custom alert channels** (Slack, SMS, phone, Bloomberg Terminal integration)
- **Dedicated account manager** (weekly sync, quarterly business review)
- **Priority feature requests** (your feedback influences product roadmap)
- **Data licensing** (historical signal data, backtest results for research/publishing)

#### Advanced Analytics (Enterprise Only)
- **Portfolio optimization** (mean-variance efficient frontier)
- **Correlation matrix** (across all strategies, all timeframes)
- **Factor attribution** (how much of return is alpha vs. beta?)
- **Drawdown analysis** (max drawdown, recovery time, underwater chart)
- **VAR calculation** (1-day, 5-day, 10-day Value at Risk)
- **Stress testing** (market regime changes, black swan events)

#### Institutional Features
- **Multi-account management** (manage 10+ sub-accounts from dashboard)
- **Team permissions** (trader, supervisor, compliance, analyst roles)
- **Audit logging** (all trades, all API calls, 5-year history)
- **Compliance reporting** (SEC-ready position reports, trade ticket recording)
- **Rate limiting customization** (negotiate higher limits if needed)

#### Support & SLA
- **Dedicated support channel** (Slack or email, you choose)
- **Response SLA**: 1 hour for critical issues, 4 hours for standard
- **Monthly strategy reviews** (discuss performance, optimization ideas)
- **Quarterly roadmap meetings** (influence feature direction)

### Pricing Framework
- **Minimum**: $2,000/month ($24K/year)
- **Typical**: $5,000-10,000/month (small hedge fund, large advisor book)
- **High-end**: $20,000+/month (multi-billion AUM, white-label, data licensing)

Pricing variables:
- **AUM** (Assets Under Management): Higher AUM = higher fee (0.1-0.5% annual)
- **User count**: More traders = higher fee
- **API volume**: Higher request volume = add-ons
- **Custom features**: White-label + custom strategies add $5-20K flat fees
- **Exclusivity**: "Only strategy you use" = premium pricing

### Sales & Conversion Path
1. **Inbound**: Advisor or hedge fund manager discovers Premium tier
2. **Usage**: Uses for 2-3 months, generates real alpha
3. **Inquiry**: Contacts sales asking for higher limits / custom features
4. **Demo**: Account manager presents Enterprise roadmap, use cases
5. **Pilot**: 1-month pilot at discounted rate ($500-1000) with dedicated support
6. **Negotiation**: Monthly contract signed, terms agreed
7. **Launch**: White-label site deployed, teams onboarded, KPIs established

### Value Justification
- **Alpha generation**: If strategies generate even 2-3% excess return, fee pays for itself 10x
- **Cost savings**: vs. hiring 2-3 algorithmic traders ($200-400K/year salary), this is cheap
- **Compliance**: Built-in audit logging + reporting saves 20+ hours/month of manual work
- **Risk**: Stress testing + portfolio optimization reduce tail risk significantly

### Expected LTV from Enterprise Tier
- **Avg contract duration**: 24-36 months (annual renewals)
- **Avg monthly fee**: $6,000 (blended across portfolio)
- **Base LTV**: $6,000 × 30 months = $180,000
- **Upsell**: Custom strategies, data licensing, increased limits = +$20-50K
- **Total realistic LTV**: $200-250K per Enterprise customer

### Enterprise Sales Metrics
- **Target**: 2-4 Enterprise contracts in first 12 months
- **Year 2**: 5-8 active contracts ($300-400K MRR)
- **Year 3**: 10-15 active contracts ($600-900K MRR, sustainable)

---

## Conversion Funnel: Free → Premium → Annual → Enterprise

```
100 Free Users (Month 1)
   ↓
15-20 Upgrade to Premium (Day 30)  [15-20% conversion]
   ↓
30-40 Add to Premium cohort (Months 2-12)
   ↓
40-50 Premium users after Year 1
   ↓
15-20 Upgrade to Annual  [30-40% of Premium]
   ↓
2-4 Qualify for Enterprise
[Demand generation from satisfied Premium users]
```

### Key Conversion Metrics by Tier

| Metric | TIER 1→2 | TIER 2→3 | TIER 3→4 |
|--------|----------|----------|----------|
| **Conversion rate** | 15-20% | 30-40% | 8-12% |
| **Avg time-to-upgrade** | 30 days | 90 days | 180 days |
| **Churn rate** | N/A (expires) | 5-8%/month | 0.5-1%/month |
| **LTV** | $0 | $300-400 | $400-500 |
| **CAC payback** | N/A | 2-3 months | 3-4 months |

---

## Feature Comparison Table

| Feature | Free | Premium | Annual | Enterprise |
|---------|------|---------|--------|------------|
| **Duration** | 30 days | Month-to-month | Annual | Custom |
| **Price** | $0 | $29/mo | $249/yr | Custom |
| **Backtesting** | 5 stocks, 3 strategies | Unlimited | Unlimited | Unlimited + custom |
| **Strategies** | 3 sample | All 11 | All 11 | All 11 + custom |
| **Live signals** | No | Yes | Yes | Yes (priority) |
| **Real-time data** | No | Yes | Yes | Yes (webhooks) |
| **API access** | No | 100 req/day | 100 req/day | Unlimited |
| **Webhook delivery** | No | 1-3 sec | 1-3 sec | <100 ms (SLA) |
| **Parameter customization** | No | Yes | Yes | Yes |
| **Discord** | Read-only #general | Full access | Full access | Private channel |
| **Email support** | 48 hr | 24 hr | 12 hr (SLA) | 1 hr (SLA) |
| **Monthly office hours** | No | Yes (4x) | Yes (4x) | Quarterly + monthly |
| **Account manager** | No | No | No | Yes (dedicated) |
| **White-label** | No | No | No | Yes |
| **Multi-account** | No | No | No | Yes |
| **Compliance reports** | No | No | No | Yes |
| **Data export** | No | Yes | Yes | Yes (licensing) |

---

## Implementation Checklist

- [ ] Remove $25K revenue gate from production code (see CLAUDE.md TIER_UPGRADE notes)
- [ ] Update `app/page.tsx` TIERS section with new structure
- [ ] Create Stripe products for each tier (Free trial, Premium monthly, Annual)
- [ ] Deploy trial signup flow (email collection, 30-day timer)
- [ ] Build onboarding email sequence (Day 3, 7, 14, 21, 28)
- [ ] Implement conversion hooks in dashboard ("Your trial expires in 2 days")
- [ ] Create Discord tier channels (#premium-signals, #enterprise-partners)
- [ ] Document API limits per tier (100/day for Premium, unlimited for Enterprise)
- [ ] Sales deck for Enterprise segment (target hedge funds, advisors)
- [ ] Security audit (remove any $25K gate logic, verify payment flows)

---

## Success Metrics

Track these KPIs monthly:

1. **Acquisition**: Free signups/month
2. **Conversion**: Free→Premium rate (target: 15-20%)
3. **Upgrade**: Premium→Annual rate (target: 30-40%)
4. **Retention**: Monthly churn rate (target: 5-8% Premium, 1-2% Annual)
5. **LTV**: Avg customer lifetime value (target: $300-500)
6. **CAC**: Customer acquisition cost (target: break-even in 2-3 months)
7. **Enterprise**: New contracts/month (target: 2-4 per year)
8. **MRR**: Monthly recurring revenue (track Premium + Annual + Enterprise)
9. **ARR**: Annual recurring revenue (scale of business)
10. **NPS**: Net Promoter Score (Premium users should be 40+)

---

## Notes for Product/Marketing

- **No lock-in required**: Users can cancel Premium anytime (reduces anxiety, improves conversion)
- **Price anchoring**: $29/month feels cheap after 30 days of $0, even if they make zero trades
- **FOMO is real**: "Your trial data expires in 2 days" is more powerful than "Upgrade now"
- **Annual pricing**: 29% discount is large enough to matter ($99/year savings) but small enough to not cannibalize monthly
- **Enterprise**: Should feel premium, white-glove, bespoke. Price accordingly (2-4 contracts = 20-30% of revenue)
- **Signal quality is king**: If signals are profitable, users upgrade. If not, no amount of pricing tricks help.

