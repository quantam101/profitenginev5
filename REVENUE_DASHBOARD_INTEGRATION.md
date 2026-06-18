# Revenue Dashboard Integration Guide

## What's New

A complete revenue and business metrics dashboard for Already Here LLC has been implemented to track ProfitEngine v5 profitability. The dashboard displays real-time MRR, ARR, LTV, churn rate, COGS, and net profit margin.

## Files Created

### 1. API Endpoint
**Path:** `/app/api/command/revenue/route.ts`

Calculates and returns all revenue metrics from `clients.db`. 

Key features:
- Real data from customer balances and tiers
- Tier pricing: Hybrid (0.5% AUM), White-Label (1.0%), Enterprise (1.5%)
- COGS calculation including payment fees, API costs, and fixed hosting
- Top 10 customer leaderboard
- Monthly trend data
- Health check information

### 2. Dashboard Component
**Path:** `/app/command-center/RevenueDashboard.tsx`

Client-side React component displaying all metrics with:
- 6 KPI metric cards (MRR, ARR, LTV, Churn, COGS, Margin)
- 5 customer metric cards
- 2 pie charts (customer distribution, revenue by tier)
- 1 bar chart (MRR trend)
- Top 10 customers leaderboard table
- CSV export functionality
- Auto-refresh every 5 minutes
- Color-coded health indicators (green=positive, red=negative, yellow=warning)

### 3. Dashboard Page
**Path:** `/app/command-center/revenue/page.tsx`

Next.js page route serving the dashboard at `/command-center/revenue`

### 4. Documentation
**Path:** `/docs/REVENUE_DASHBOARD.md`

Comprehensive reference including:
- KPI definitions and formulas
- Tier breakdown strategy
- API specification
- Data sources and schema
- Calculation details
- Export functionality
- Troubleshooting guide
- Future enhancements

## How to Use

### Access the Dashboard

1. **URL:** `https://<your-domain>/command-center/revenue`
2. **From Command Center:** Click "Revenue Dashboard" link
3. **From Navigation:** Updated nav menu includes revenue dashboard link

### Key Metrics Explained

**MRR (Monthly Recurring Revenue):**
- Sum of all customer subscription fees
- Hybrid customers pay 0.5% of their balance per month
- Example: 10 customers × $50k avg balance × 0.5% = $2,500 MRR

**ARR (Annual Recurring Revenue):**
- MRR × 12 for annual projection
- Used for investor reporting and forecasting

**LTV (Customer Lifetime Value):**
- Average monthly revenue × 24-month assumed lifetime
- Shows long-term value of acquiring a customer

**Churn Rate:**
- % of customers inactive in last 30 days
- Healthy target: <5%

**COGS (Cost of Goods Sold):**
- Payment processing: 3% of MRR
- API costs: Scaled with AUM ($50 per $100k)
- Fixed hosting: $500/month

**Net Profit Margin:**
- (MRR - COGS) / MRR × 100%
- Target: >70% (typical SaaS benchmark)

### Features

#### Auto-Refresh
- Dashboard refreshes every 5 minutes
- Manual refresh button available
- Shows last update timestamp

#### CSV Export
- Button exports all metrics to CSV
- Includes KPIs, tier breakdown, top customers
- Filename: `revenue-metrics-YYYY-MM-DD.csv`
- Use for accounting, board presentations, investor updates

#### Tier Analysis
- Pie chart shows customer distribution by tier
- Separate chart shows revenue impact per tier
- Free tier = growth funnel, paid tiers = revenue sources

#### Top Customers
- Leaderboard of high-value accounts
- Shows User ID, email, tier, balance, monthly revenue, LTV
- Use for account management focus

## Data Requirements

### Database Setup
The dashboard requires `clients.db` with the following tables:

**users table:**
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL,
  signup_date TEXT,
  trading_tier TEXT DEFAULT 'free',
  last_active_at TEXT,
  is_active INTEGER DEFAULT 1
)
```

**daily_trades table:**
```sql
CREATE TABLE daily_trades (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  date TEXT,
  balance REAL,
  -- ... other columns
)
```

### Verify Database
```bash
# Check if database exists and has data
sqlite3 clients.db "SELECT COUNT(*) FROM users;"
sqlite3 clients.db "SELECT trading_tier, COUNT(*) FROM users GROUP BY trading_tier;"
```

## Integration Points

### Command Center Navigation
Updated `/app/command-center/page.tsx` to include:
- Revenue Dashboard link in navigation menu
- Revenue Dashboard card in checks section

### API Integration
All revenue calculations pull from:
- **Source:** `clients.db` (SQLite)
- **Lookup:** User balances from `daily_trades` latest entries
- **Tiers:** From `users.trading_tier` column

### Next.js Configuration
- Dynamic rendering: `force-dynamic` (no caching)
- Revalidation: 0 (always fresh)
- Auto-refresh: Client-side 5-minute interval

## Customization

### Adjust Tier Pricing
Edit `/app/api/command/revenue/route.ts`:
```typescript
const TIER_PRICING = {
  free: 0.0,
  hybrid: 0.005,    // Change here (0.5%)
  whiteLable: 0.01, // Change here (1.0%)
  enterprise: 0.015 // Change here (1.5%)
};
```

### Adjust Fixed Costs
```typescript
const MONTHLY_FIXED_COSTS = 500; // Change here
```

### Change Refresh Interval
Edit `/app/command-center/RevenueDashboard.tsx`:
```typescript
// Currently: 5 * 60 * 1000 = 5 minutes
const interval = setInterval(fetchMetrics, 5 * 60 * 1000);
```

### Update Color Scheme
Modify color variables in `RevenueDashboard.tsx`:
```typescript
const colorMap = {
  positive: '#4ade80',  // Green
  negative: '#f87171',  // Red
  neutral: '#7dd3fc',   // Blue
  warning: '#facc15',   // Yellow
};
```

## Testing

### Test the API Directly
```bash
curl https://<your-domain>/api/command/revenue | jq .
```

### Test Data Validation
```bash
# Check for users with balances
sqlite3 clients.db \
  "SELECT u.id, u.email, u.trading_tier, MAX(d.balance) as balance 
   FROM users u 
   LEFT JOIN daily_trades d ON u.id = d.user_id 
   GROUP BY u.id 
   LIMIT 5;"
```

### Manual Test Checklist
- [ ] Dashboard loads at `/command-center/revenue`
- [ ] Metrics display (not zero/null)
- [ ] Charts render properly
- [ ] Refresh button works
- [ ] CSV export downloads
- [ ] Top 10 customers populate
- [ ] Auto-refresh triggers every 5 minutes

## Production Checklist

Before deploying to production:

- [ ] Database contains real customer data with balances
- [ ] Tier pricing matches actual pricing model
- [ ] COGS calculations validated against actuals
- [ ] Top customers verified manually
- [ ] Churn rate calculation reviewed
- [ ] CSV export tested
- [ ] Navigation links updated
- [ ] Performance tested with full customer dataset
- [ ] Error handling verified (API timeout, DB connection fail)
- [ ] Mobile responsiveness checked
- [ ] Browser compatibility tested (Chrome, Safari, Edge)

## Troubleshooting

### Dashboard Shows No Data
**Cause:** No customers in database or no balances recorded
**Action:** 
```bash
npm run db:init:seed  # Populates test data
# Or manually add users and daily_trades records
```

### API Returns 500 Error
**Cause:** Database not found or connection error
**Check:**
```bash
ls -la clients.db  # File exists?
npm run db:test    # Connection works?
```

### Charts Don't Display
**Cause:** SVG rendering issue in browser
**Action:** Clear cache, try different browser, check console logs

### Metrics Look Wrong
**Cause:** COGS formula or tier pricing misconfigured
**Action:** 
1. Verify tier assignments: `SELECT trading_tier, COUNT(*) FROM users GROUP BY trading_tier;`
2. Verify balances: `SELECT MAX(balance) FROM daily_trades;`
3. Check formulas in `/app/api/command/revenue/route.ts`

## Performance Optimization

### For Large Customer Bases (>5000 users)

1. **Add database indexes:**
```sql
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_daily_trades_user_id ON daily_trades(user_id);
CREATE INDEX idx_daily_trades_date ON daily_trades(date);
```

2. **Implement pagination:**
- Top 10 customers already paginated
- Add date range filters for monthly trends

3. **Cache top-level metrics:**
- Store daily MRR snapshots for trending
- Query last 30 days instead of full history

## Monitoring & Alerts

### Key Metrics to Monitor
- **Churn Rate >5%:** Trigger retention outreach
- **Margin <60%:** Investigate COGS increase
- **MRR Decline >5% MoM:** Alert sales team
- **Data Freshness >30 min:** Alert ops team

### Integration with Monitoring
Export metrics to monitoring tool:
```bash
# Example: Send to monitoring API
curl -X POST https://monitoring.example.com/metrics \
  -H "Content-Type: application/json" \
  -d @/tmp/revenue-metrics.json
```

## Future Enhancements

1. **Historical Tracking** - Store daily snapshots for 12-month trends
2. **Cohort Analysis** - Track customers by signup cohort
3. **Predictive Analytics** - Forecast MRR based on growth rate
4. **Alerts & Notifications** - Churn spike, margin alerts
5. **Drill-down Reports** - Click tier to see individual customers
6. **Custom Date Ranges** - Month-over-month comparisons
7. **Integration APIs** - Sync to Stripe, QuickBooks
8. **Role-based Access** - Owner/CFO/Sales different views

## Support

For issues or questions:
1. See `/docs/REVENUE_DASHBOARD.md` for detailed reference
2. Check browser console for errors: F12 → Console tab
3. Verify API response: Check `/api/command/revenue` directly
4. Review database health: Run db:test command

---

**Version:** 1.0  
**Last Updated:** 2026-06-18  
**Status:** Production Ready
