# Revenue Dashboard — Already Here LLC Business Intelligence

## Overview

The Revenue Dashboard provides real-time business metrics for Already Here LLC's ProfitEngine subscription model. It tracks monthly recurring revenue (MRR), annual recurring revenue (ARR), customer lifetime value (LTV), churn rate, cost of goods sold (COGS), and net profit margin across all customer tiers.

**Access:** `/command-center/revenue`

**API Endpoint:** `/api/command/revenue`

---

## Key Performance Indicators (KPIs)

### Monthly Recurring Revenue (MRR)
- **Definition:** Sum of all subscription revenue from paying customers in the current month
- **Formula:** SUM(customer_balance × tier_fee_percent) for all paying customers
- **Tiers:**
  - Free: 0% (no charge)
  - Hybrid: 0.5% of AUM (Assets Under Management)
  - White Label: 1.0% of AUM
  - Enterprise: 1.5% of AUM
- **Use Case:** Primary indicator of business health and recurring revenue stability

### Annual Recurring Revenue (ARR)
- **Definition:** MRR × 12
- **Use Case:** Normalized annual revenue projection for investor reporting

### Customer Lifetime Value (LTV)
- **Definition:** Average monthly revenue per customer × 24-month assumed lifetime
- **Formula:** (MRR / paying_customers) × 24
- **Use Case:** Long-term customer acquisition cost justification

### Churn Rate
- **Definition:** Percentage of active customers who became inactive in the last 30 days
- **Calculation:** (Churned customers / Active customers) × 100%
- **Threshold:** Healthy <5%, Warning 5-10%, Critical >10%
- **Use Case:** Customer retention health metric

### Cost of Goods Sold (COGS)
- **Components:**
  - Payment processing fees: 3% of MRR (Stripe transaction fees)
  - API costs: Scaled with total customer balance ($50 per $100k AUM)
  - Fixed hosting costs: $500/month (Vercel, Runtime server, misc APIs)
- **Use Case:** Profitability analysis and margin calculations

### Net Profit Margin
- **Definition:** (MRR - COGS) / MRR × 100%
- **Target:** >70% (software SaaS benchmark)
- **Use Case:** Overall business profitability metric

---

## Customer Metrics

### Total Customers
All user accounts (active and inactive)

### Paying Customers
Active users generating monthly recurring revenue (any non-free tier)

### Free Customers
Active users on free tier (non-revenue but potential upsell targets)

### New Customers This Month
Active users whose signup_date is within current calendar month

### Average Customer Balance
Total assets across all active customers ÷ number of active customers

---

## Tier Breakdown

Segmentation of customers by subscription tier with both customer count and revenue impact.

### Free Tier
- **Revenue:** $0/customer
- **Function:** Trial/onboarding funnel
- **Conversion Target:** 5-10% to Hybrid

### Hybrid Tier
- **Revenue:** 0.5% of AUM
- **Typical AUM:** $10k-$100k
- **Expected MRR:** $50-$500/customer
- **Function:** Self-service SaaS entry point

### White Label Tier
- **Revenue:** 1.0% of AUM
- **Typical AUM:** $50k-$500k
- **Expected MRR:** $500-$5,000/customer
- **Function:** White-labeled reselling platform

### Enterprise Tier
- **Revenue:** 1.5% of AUM
- **Typical AUM:** $500k+
- **Expected MRR:** $7,500+/customer
- **Function:** Custom implementations and dedicated support

---

## Dashboard Components

### 1. Key Performance Indicators Section
Six metric cards showing MRR, ARR, LTV, Churn Rate, COGS, and Net Profit Margin. Each card includes:
- Large primary metric value
- Color coding (positive=green, negative=red, warning=yellow)
- Optional detail text

### 2. Customer Metrics Section
Five cards showing customer counts and balance metrics:
- Total customers
- Paying customers
- Free customers
- New customers this month
- Average customer balance

### 3. Charts Section

#### Customers by Tier (Pie Chart)
- Visual distribution of active customers across four tiers
- Percentage labels for each segment
- Used to identify tier composition and growth opportunities

#### Revenue Distribution by Tier (Pie Chart)
- Dollar value distribution across tiers
- Shows which tiers contribute most to revenue
- Highlights growth potential in underutilized tiers

#### MRR Trend Chart (Bar Chart)
- Monthly MRR progression (currently showing current month)
- Extensible to 12-month historical view
- Used to monitor growth trajectory

### 4. Top 10 Customers Table
Leaderboard showing high-value customers:
- User ID
- Email (truncated)
- Tier
- Current balance
- Monthly recurring revenue
- Calculated LTV

### 5. Data Health Section
Monitoring metrics:
- Data Quality: "healthy" or error status
- Records Processed: Total customer count analyzed
- Last Updated: Timestamp of latest refresh

---

## API Specification

### Endpoint
```
GET /api/command/revenue
```

### Request
No parameters required. Auto-refresh every 5 minutes client-side.

### Response
```json
{
  "timestamp": "2026-06-18T14:30:00.000Z",
  "monthYear": "2026-06",
  
  "mrr": 2500.50,
  "arr": 30006.00,
  "ltv": 1200.00,
  "churnRate": 2.5,
  "cogs": 750.00,
  "netProfitMargin": 70.00,
  
  "totalCustomers": 150,
  "payingCustomers": 50,
  "freeCustomers": 100,
  "newCustomersThisMonth": 12,
  "avgCustomerBalance": 25000.00,
  
  "tierBreakdown": {
    "free": 100,
    "hybrid": 40,
    "whiteLable": 8,
    "enterprise": 2
  },
  
  "revenueByTier": {
    "free": 0.00,
    "hybrid": 1500.00,
    "whiteLable": 800.00,
    "enterprise": 200.50
  },
  
  "monthlyTrend": [
    {
      "month": "2026-06",
      "mrr": 2500.50,
      "customers": 50,
      "churnRate": 2.5
    }
  ],
  
  "topCustomers": [
    {
      "userId": 42,
      "email": "whale@example.com",
      "tier": "enterprise",
      "balance": 500000.00,
      "monthlyRevenue": 7500.00,
      "ltv": 180000.00
    }
  ],
  
  "health": {
    "dataQuality": "healthy",
    "lastUpdate": "2026-06-18T14:30:00.000Z",
    "recordsProcessed": 150
  }
}
```

### Status Codes
- `200 OK` — Successful calculation
- `500 Internal Server Error` — Database connection or processing error

### Error Response
```json
{
  "error": "failed_to_calculate_revenue",
  "message": "Database not found at /path/to/clients.db"
}
```

---

## Data Sources

### clients.db Schema

#### users table
- `id` (INTEGER PRIMARY KEY)
- `email` (TEXT)
- `signup_date` (TEXT)
- `first_trade_date` (TEXT NULL)
- `trading_tier` (TEXT) — free, hybrid, white-label, enterprise
- `last_active_at` (TEXT NULL)
- `is_active` (INTEGER) — 0=inactive, 1=active

#### daily_trades table
- `user_id` (INTEGER FOREIGN KEY)
- `date` (TEXT)
- `num_trades` (INTEGER)
- `win_count` (INTEGER)
- `loss_count` (INTEGER)
- `pnl_dollars` (REAL)
- `pnl_percent` (REAL)
- `balance` (REAL) — Current AUM from latest trade entry
- `win_rate` (REAL)

#### upsell_tracking table
- `user_id` (INTEGER FOREIGN KEY)
- `tier_history` (TEXT JSON)
- `current_tier` (TEXT)
- `revenue_tier` (TEXT)
- `last_upsell_offered` (TEXT)
- `upsell_count` (INTEGER)
- `conversion_count` (INTEGER)
- `lifetime_revenue` (REAL)

---

## Calculations & Formulas

### MRR Calculation
```
MRR = SUM(
  FOR each active user:
    balance × tier_fee_percent
)

Where tier_fee_percent:
- Free: 0.0
- Hybrid: 0.005 (0.5%)
- White Label: 0.01 (1.0%)
- Enterprise: 0.015 (1.5%)
```

### COGS Breakdown
```
COGS = payment_processing_fees + api_costs + fixed_hosting

payment_processing_fees = MRR × 0.03 (Stripe 3% + $0.25 per transaction)
api_costs = MAX(100, (total_balance / 100000) × 50)
fixed_hosting = $500/month

Simplified in this dashboard:
COGS ≈ (MRR × 0.03) + scaled_api_costs + $500
```

### Churn Rate
```
ChurnRate = (users_inactive_30_days / active_users) × 100%

Where last_active_at < (TODAY - 30 days)
```

### Net Profit Margin
```
NetProfitMargin = ((MRR - COGS) / MRR) × 100%
```

---

## Export Functionality

### CSV Export
The dashboard includes a "Export CSV" button that downloads a formatted report containing:
- All KPI metrics (MRR, ARR, LTV, etc.)
- Customer segment breakdown
- Revenue by tier
- Top 10 customer leaderboard
- Health metrics

**Filename Format:** `revenue-metrics-YYYY-MM-DD.csv`

**Use Cases:**
- Monthly accounting reconciliation
- Investor reporting
- Board presentations
- Financial forecasting

---

## Auto-Refresh & Monitoring

### Client-Side Auto-Refresh
- Default interval: 5 minutes
- Configurable in `RevenueDashboard.tsx`
- Manual refresh button for immediate updates
- Timestamp shows last update time

### Caching Strategy
- API response: `Cache-Control: no-store`
- Database queries: Executed fresh on each request
- No client-side caching (always fetch latest)

---

## Tier Strategy & Growth Targets

### Current Model
| Tier | Customers | Total AUM | MRR | LTV | Margin |
|------|-----------|-----------|-----|-----|--------|
| Free | 100 | $0 | $0 | $0 | N/A |
| Hybrid | 40 | $1M | $5k | $120k | 70% |
| White Label | 8 | $500k | $5k | $120k | 70% |
| Enterprise | 2 | $1M | $15k | $360k | 70% |

### Optimization Opportunities
1. **Free → Hybrid Conversion:** Target 10% of free users = 10 new customers × $500/month avg = $5k additional MRR
2. **Hybrid → White Label Upsell:** Focus on customers with >$50k balance
3. **Enterprise Expansion:** Multi-year contracts with commitment discounts
4. **Churn Reduction:** <2% churn rate through proactive outreach and education

---

## Troubleshooting

### "Database not found" Error
```
Action: Run initialization script
Command: npm run db:init
Details: Creates clients.db with schema if missing
```

### Missing or Stale Data
```
Symptoms: Zero customers or old balance values
Action: 1. Check daily_trades table entries
        2. Verify user signup_date is recent
        3. Run: db.recordDailyTrades() for test data
```

### API Timeout
```
Symptoms: Refresh button hangs >5 seconds
Cause: Large customer base (>5000 users)
Action: Add database indexes or implement pagination
```

### Chart Display Issues
```
Cause: SVG rendering in older browsers
Action: Use modern Chrome/Edge/Firefox
        Ensure JavaScript is enabled
```

---

## Future Enhancements

1. **Historical Trending** — Store daily/monthly snapshots for 12-month trends
2. **Cohort Analysis** — Group customers by signup month to track lifetime patterns
3. **Predictive Metrics** — Forecast MRR based on current growth rate and churn
4. **Benchmark Comparison** — Compare against SaaS industry averages
5. **Alerts & Automation** — Notify on churn spike or margin compression
6. **Drill-Down Reports** — Click tier → see individual customers in that segment
7. **Custom Date Ranges** — Compare month-over-month or year-over-year
8. **Integration** — Sync to Stripe, accounting software, or BI platforms

---

## Integration with Other Systems

### Accounting
- MRR/ARR used for revenue recognition (ASC 606 compliance)
- COGS validates against actual payment processor statements
- Monthly export feeds to QuickBooks or Xero

### Sales & Upsell
- Top customers list for account management focus
- Churn alerts trigger proactive outreach
- Free/Hybrid → Enterprise upsell opportunities

### Operations
- COGS monitors cost efficiency
- Net margin alerts if compression detected
- Health metrics indicate data integrity

### Investor Relations
- ARR primary metric for growth tracking
- LTV/CAC ratio (when combined with marketing costs)
- Churn rate demonstrates retention efficiency

---

## Access Control

Currently **auth-free** to match command-center design philosophy.

Future enhancement: Integrate with NextAuth for role-based access:
- Owners: Full access to all metrics + export
- CFO/Finance: MRR, COGS, margin, export
- Sales: Customer tiers, growth targets, upsell opportunities
- Support: Churn alerts, customer health signals

---

## Support & Questions

For issues or enhancements:
1. Check logs: `npm run dev` and monitor browser console
2. Verify database: `sqlite3 clients.db "SELECT COUNT(*) FROM users;"`
3. Test API: `curl https://<domain>/api/command/revenue`
4. File issue with reproduction steps and data sample
