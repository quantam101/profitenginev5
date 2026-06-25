# Revenue Metrics Reference Guide

Complete reference for all metrics, formulas, and tracking methods across all 8 revenue streams.

---

## 1. GUMROAD METRICS

### Core Metrics
| Metric | Formula | Unit | Frequency | API Endpoint |
|--------|---------|------|-----------|--------------|
| Revenue | Total income from sales | USD | Hourly | `/v2/products` |
| Sales | Number of transactions | Count | Hourly | `/v2/products` |
| Customers | Unique buyers | Count | Daily | Dashboard |
| Page Views | Visits to Gumroad page | Count | Daily | Dashboard |
| Conversion Rate | (Sales / Views) × 100 | % | Daily | Calculated |
| Avg Order Value | Revenue / Sales | USD | Daily | Calculated |
| Refunds | Refunded transactions | Count | Daily | `/v2/refunds` |
| Refund Rate | (Refunds / Sales) × 100 | % | Daily | Calculated |

### Product-Level Metrics
```
Per Product:
- Name
- Sales (24h)
- Revenue (24h)
- Conversion rate
- Customer reviews/rating
- Top referring source
```

### Gumroad API Examples
```bash
# List all products
curl -H "Authorization: Bearer TOKEN" \
  https://api.gumroad.com/v2/products

# Get sales for product
curl -H "Authorization: Bearer TOKEN" \
  https://api.gumroad.com/v2/products/ID/sales

# Get customer list
curl -H "Authorization: Bearer TOKEN" \
  https://api.gumroad.com/v2/customers
```

---

## 2. EMAIL METRICS

### List Health
| Metric | Benchmark | Formula | Risk Indicator |
|--------|-----------|---------|-----------------|
| Total Subscribers | Growing | Previous + New - Unsubscribes | Baseline |
| Growth Rate (24h) | > 0.5% | (New Subs / Total) × 100 | < 0% = churn |
| Unsubscribe Rate | < 0.5% | (Unsubscribes / Sent) × 100 | > 1% = problem |
| Bounce Rate | < 2% | (Bounces / Sent) × 100 | > 5% = list quality issue |
| Complaint Rate | < 0.1% | (Complaints / Sent) × 100 | Any spike = urgent |

### Campaign Metrics
| Metric | Good | Benchmark | Formula |
|--------|------|-----------|---------|
| Open Rate | 20-40% | 15-25% | (Opens / Sent) × 100 |
| Click Rate | 2-5% | 1-3% | (Clicks / Sent) × 100 |
| Click-to-Open Rate | 10-20% | 5-15% | (Clicks / Opens) × 100 |
| Conversion Rate | 1-3% | 0.5-2% | (Conversions / Clicks) × 100 |
| Unsubscribe Rate | < 0.5% | < 1% | (Unsubscribes / Sent) × 100 |
| Complaint Rate | < 0.1% | < 0.5% | (Complaints / Sent) × 100 |

### Revenue Attribution
```
Email Revenue = Email Links Clicked × Conversion Rate × Avg Order Value

Example:
1,000 clicks × 5% conversion × $50 AOV = $2,500 revenue
```

### Email Platform API Examples (Mailchimp v3)
```bash
# Get list growth
curl -s -X GET "https://us1.api.mailchimp.com/3.0/lists/LIST_ID" \
  -u "user:$API_KEY" | jq '.stats'

# Get campaign performance
curl -s -X GET "https://us1.api.mailchimp.com/3.0/campaigns/ID/reports" \
  -u "user:$API_KEY"

# Get recent activity
curl -s -X GET "https://us1.api.mailchimp.com/3.0/reports" \
  -u "user:$API_KEY"
```

---

## 3. SOCIAL MEDIA METRICS

### Universal Metrics (All Platforms)
| Metric | Formula | Importance | Tracking Method |
|--------|---------|------------|-----------------|
| **Followers** | Cumulative accounts following | Baseline | Platform native |
| **New Followers (24h)** | Followers today - Followers yesterday | Growth | Platform native |
| **Impressions** | Reach (unique users seeing content) | Top of funnel | Platform analytics |
| **Engagement** | Likes + Comments + Shares + Saves | Mid funnel | Platform analytics |
| **Engagement Rate** | (Engagement / Impressions) × 100 | Quality metric | Calculated |
| **Reach** | Unique accounts seeing content | Paid effectiveness | Platform analytics |
| **CTR** | (Clicks / Impressions) × 100 | Bottom of funnel | Calculated |

### Platform-Specific Metrics

#### YouTube
```
Views:            Page views of video
Watch Time:       Total hours watched
Avg View Duration: Avg. time per viewer (retention)
Subscribers Gained: New channel subscriptions
CTR:             (Clicks on thumbnail / Impressions) × 100
Engagement:       Likes + Comments + Shares + Subscribers
Revenue (if monetized):
  - AdSense Revenue (CPM × Impressions / 1000)
  - Channel Memberships
  - Super Chat/Thanks
  - YouTube Shorts Bonus
```

#### TikTok
```
Views:            Video plays
Completion Rate:  % who watch to end
Likes:            Heart reactions
Comments:         User comments
Shares:           Shares to other accounts
Bookmarks:        Saves for later
Engagement Rate:  (Engagement / Views) × 100
Click-Through:    Clicks on bio link
```

#### Instagram
```
Impressions:      # of times content is shown
Reach:            # of unique accounts seeing content
Engagement:       Likes + Comments + Saves + Shares
Engagement Rate:  (Engagement / Impressions) × 100
Profile Visits:   Visits to profile (24h)
Website Clicks:   Clicks to external link
Video Views:      # of video plays
Story Views:      Unique story viewers
Follower Action:  Follows from content (24h)
```

#### X (Twitter)
```
Impressions:      # of times tweet shown
Likes:            Like reactions
Retweets:         Retweets / shares
Replies:          Comment replies
Quote Tweets:     Quoted retweets
Engagement Rate:  (Engagement / Impressions) × 100
Click Rate:       (Clicks / Impressions) × 100
Link Clicks:      Clicks to external URLs
```

### Social Revenue Attribution
```
Social Revenue = Social Clicks × Conversion Rate × Avg Order Value

Example:
YouTube link clicks: 500
Email subscribers from YouTube: 100
Email conversion rate: 5%
Avg order value: $50
Revenue = 100 × 5% × $50 = $250
```

---

## 4. AFFILIATE METRICS

### Per-Program Tracking
| Metric | Formula | Importance | Example |
|--------|---------|------------|---------|
| **Clicks** | Links clicked from your content | Traffic indicator | 100 clicks |
| **Conversions** | Clicks → purchases | Sales quality | 5 conversions |
| **Conversion Rate** | (Conversions / Clicks) × 100 | Effectiveness | 5% |
| **Avg Commission** | Revenue / Conversions | Deal quality | $25/sale |
| **Revenue** | Conversions × Avg Commission | Bottom line | $125 |
| **Commission Rate** | % of sale price to affiliate | Deal terms | 10% |
| **Pending Payout** | Earned but not yet paid | Cash flow | $500 |
| **Payout Schedule** | Days until payment received | Timing | 45 days |

### Network-by-Network Performance
```
Amazon Associates:
  - Tracking: 24-hour cookie window
  - Commission: 3-10% depending on category
  - Revenue (24h): $X from clicks

ShareASale:
  - Tracking: 30-60 day window (varies)
  - Commission: 5-25% by program
  - Revenue (24h): $X from clicks

CJ Affiliate:
  - Tracking: 30-90 day window
  - Commission: Custom per program
  - Revenue (24h): $X from clicks
```

### Affiliate Revenue Attribution
```
Total Affiliate Revenue = Sum of (Conversions × Commission Rate) per program

Example (24h):
- Amazon: 10 conversions × $5 avg = $50
- ShareASale: 3 conversions × $15 avg = $45
- CJ: 2 conversions × $30 avg = $60
TOTAL = $155
```

### Affiliate Network API Examples
```bash
# ShareASale - Get last month stats
curl -X GET "https://api.shareasale.com/x/api/stats" \
  -H "Authorization: Bearer TOKEN" \
  -d "token=TOKEN&action=lastMonth"

# Impact - Get conversions
curl -X GET "https://api.impact.com/reporting/conversions" \
  -H "Authorization: Bearer API_KEY" \
  -d "start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"
```

---

## 5. SPONSORSHIP METRICS

### Deal Tracking
| Metric | Formula | Type | Example |
|--------|---------|------|---------|
| Deal Value | Contract amount | Baseline | $5,000 |
| Impressions Delivered | # views/impressions | KPI | 50,000 |
| Clicks to Sponsor | Link clicks | Performance | 250 |
| Conversions | Clicks → sponsor signup/sale | Performance | 12 |
| ROI Multiple | Revenue / Ad Spend | Quality | 3x |
| Renewal Likelihood | Sponsor satisfaction score | Retention | High |
| Revenue Recognition | Flat fee or performance-based | Timing | Monthly |

### Sponsorship Types & Tracking
```
1. FLAT FEE
   - Invoice: $X per month
   - Deliverable: Mention in email, social posts
   - Tracking: Simple — one payment per period

2. PERFORMANCE-BASED
   - Base fee: $X
   - Bonus per conversion: $Y
   - Tracking: Complex — measure click-through
   - Example: $1,000 + $50 per conversion

3. HYBRID
   - Flat fee: $X (guaranteed)
   - Upside: +$Y per conversion if target met
   - Tracking: Hybrid — base + performance
```

### Sponsorship Revenue
```
Monthly Sponsorship Revenue = 
  (# of deals) × (Flat fees) + (# of conversions) × (Performance bonus)

Example:
- Deal 1: $2,000 flat
- Deal 2: $500 flat + $20 per conversion (5 conversions)
- Deal 3: $100 per conversion (8 conversions)

Total = $2,000 + $500 + $100 + ($20 × 5) + ($100 × 8)
      = $2,600 + $100 + $800 = $3,500
```

---

## 6. CONSULTING METRICS

### Service Types & Pricing
| Service | Duration | Rate | Annual (1x/month) | Annual (2x/month) |
|---------|----------|------|-------------------|-------------------|
| 1-on-1 Coaching | 60 min | $200/h | $2,400 | $4,800 |
| Strategy Session | 90 min | $500 | $6,000 | $12,000 |
| Full Project | Variable | $2,000+ | Variable | Variable |
| Monthly Retainer | 4h/month | $200/h | $9,600 | $19,200 |

### Monthly Revenue Calculation
```
Consulting Revenue = 
  (Billable Hours × Hourly Rate) + (Project Fees)

Example Month:
- Coaching: 4 sessions × 1 hr × $200 = $800
- Strategy: 2 sessions × 1.5 hrs × $500 = $1,500
- Project: 1 project × $3,000 = $3,000
- Retainers: 2 clients × $800 = $1,600
TOTAL = $6,900/month
```

### Pipeline Metrics
| Metric | Formula | Target | Benchmark |
|--------|---------|--------|-----------|
| **Sales Pipeline Value** | Sum of active proposals | 3-5x monthly target | $20,000+ |
| **Win Rate** | (Closed deals / Proposals) × 100 | > 30% | 20-40% |
| **Sales Cycle** | Average days from inquiry to close | < 30 days | 15-45 days |
| **Proposal-to-Close** | % of proposals that close | > 25% | 20-30% |
| **Avg Deal Size** | Total revenue / # of deals | Trending up | Varies |

### Revenue Forecasting
```
Next Month Revenue Forecast =
  (Confirmed bookings) + (Proposals × Win Rate) + (Recurring retainers)

Example:
- Confirmed: $2,000
- Proposals: $5,000 × 40% win rate = $2,000
- Retainers: $1,600
FORECAST = $5,600
```

---

## 7. YOUTUBE MONETIZATION METRICS

### Monetization Requirements
- ✅ Channel has 1,000+ subscribers
- ✅ 4,000+ watch hours in last 12 months
- ✅ YouTube Partner Program enabled
- ✅ Google AdSense account linked

### Revenue Streams

#### AdSense Revenue
```
Revenue = (Impressions / 1,000) × CPM

CPM = Cost per 1,000 impressions
Typical range: $2 - $10 depending on:
- Content category (finance > general)
- Audience location (US/UK > others)
- Season (Q4 > Q1)
```

#### Channel Members
```
Revenue = # of new members × membership fee
YouTube takes 30%, creator gets 70%

Example:
- 10 new members × $5/month × 70% = $35/month
```

#### Super Chat & Tips
```
Revenue = $ super chats / tips sent by viewers
YouTube takes 30%, creator gets 70%

Typical: $1 - $500 per super chat
```

#### YouTube Shorts Bonus
```
Revenue = Monthly bonus fund (varies)
Requires 1,000 subscribers + 100M Shorts views/month
Monthly bonus: $100 - $10,000 depending on performance
```

### YouTube Analytics API Metrics
```bash
# Get revenue metrics (requires OAuth)
curl -s "https://youtubeanalytics.googleapis.com/v2/reports" \
  -H "Authorization: Bearer TOKEN" \
  -d "ids=channel==CHANNEL_ID" \
  -d "metrics=estimatedRevenue,views,subscribersGained" \
  -d "start-date=2026-06-01&end-date=2026-06-30"
```

---

## 8. TRADING METRICS

### Daily Metrics
| Metric | Formula | Importance | Example |
|--------|---------|------------|---------|
| **Portfolio Value** | Current market value of holdings | Baseline | $50,000 |
| **Daily P&L** | Portfolio value change | Daily performance | +$500 |
| **Daily P&L %** | (Daily P&L / Portfolio) × 100 | Return | +1% |
| **Open Positions** | # of active trades | Risk | 5 |
| **Closed Trades** | # of trades exited | Activity | 3 |
| **Win Rate** | (Wins / Total) × 100 | Quality | 60% |
| **Profit Factor** | (Gross profit / Gross loss) | Consistency | 2.5x |

### Trade-Level Metrics
```
Per Trade:
- Entry time/price
- Exit time/price
- Quantity
- Fee
- P&L = (Exit price - Entry price) × Quantity - Fees
- P&L % = P&L / (Entry price × Quantity) × 100
- Duration = Exit time - Entry time
```

### Performance Metrics
| Period | Win Rate | Profit Factor | Avg Win | Avg Loss | Best Trade | Worst Trade |
|--------|----------|---------------|---------|----------|-----------|------------|
| 24h | 0% | - | $0 | $0 | $0 | $0 |
| 7d | 0% | - | $0 | $0 | $0 | $0 |
| 30d | 0% | - | $0 | $0 | $0 | $0 |

### Risk Management Metrics
```
Risk/Reward Ratio = Avg Win / Avg Loss
  Good: > 2:1
  Excellent: > 3:1

Maximum Drawdown = Lowest point - Peak
  Acceptable: < 20%
  Conservative: < 10%

Win Rate Target = > 40% for profitable trading
Profit Factor Target = > 1.5x for consistent profit
```

---

## CONSOLIDATED METRICS

### Daily Revenue Calculation
```
Total Daily Revenue = 
  Gumroad Revenue +
  Stripe Payments +
  Email Revenue +
  Social/YouTube Revenue +
  Affiliate Commissions +
  Sponsorship Revenue +
  Consulting Revenue +
  Trading P&L

Example:
$150 (Gumroad) +
$200 (Stripe) +
$50 (Email) +
$100 (YouTube AdSense) +
$75 (Affiliates) +
$500 (Sponsorship) +
$0 (Consulting) +
+$250 (Trading) =
$1,325 TOTAL
```

### Revenue Growth Metrics
```
Day-over-Day (DoD) = (Today - Yesterday) / Yesterday × 100
Week-over-Week (WoW) = (This Week - Last Week) / Last Week × 100
Month-over-Month (MoM) = (This Month - Last Month) / Last Month × 100
Year-over-Year (YoY) = (This Year - Last Year) / Last Year × 100
```

### Revenue Stream Stability
```
Per Stream Coefficient of Variation = Std Dev / Mean
- < 0.5: Stable revenue stream
- 0.5 - 1.0: Moderate volatility
- > 1.0: Highly volatile (depends on one-time events)

Diversification = # of active streams (target: 6+)
Concentration = Largest stream / Total × 100 (target: < 30%)
```

---

## HEALTH CHECKS

### Critical Metrics Dashboard
```
✓ All APIs connected
✓ Data freshness (< 24h)
✓ No errors in last 24h
✓ Revenue positive
✓ All payment processors active
✓ Affiliate accounts authorized
```

### Alert Thresholds
| Issue | Threshold | Action |
|-------|-----------|--------|
| API Down | > 1 hour | Manual check, test alternative |
| Revenue Drop | > 50% vs. avg | Review recent changes |
| High Bounce Rate (email) | > 5% | Check list quality |
| Low Engagement | < 50% of avg | Review content strategy |
| Trading Loss | > 10% of portfolio | Review risk management |

---

## GLOSSARY

- **CPM** = Cost per 1,000 impressions
- **RPM** = Revenue per 1,000 impressions (creator perspective)
- **CTR** = Click-through rate = (Clicks / Impressions) × 100
- **Conversion Rate** = (Conversions / Clicks) × 100
- **AOV** = Average order value = Revenue / Orders
- **LTV** = Lifetime value = (Avg Order Value) × (Purchase Frequency) × (Customer Lifespan)
- **CAC** = Customer acquisition cost = Marketing Spend / New Customers
- **ROAS** = Return on ad spend = Revenue / Ad Spend
- **MRR** = Monthly recurring revenue (subscriptions)
- **Churn Rate** = (Cancelled / Total customers) × 100
- **Engagement Rate** = (Likes + Comments + Shares / Followers) × 100
- **Win Rate** = (Profitable trades / Total trades) × 100
- **Profit Factor** = Gross profit / Gross loss

---

**Last Updated:** 2026-06-25  
**Reference Version:** 1.0  
**Status:** Complete
