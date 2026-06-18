# ProfitEngine Trading Dashboard

Real-time trading analytics and performance metrics from the clients.db database, integrated into the command-center.

## Overview

The trading dashboard provides operator visibility into:

1. **Today's Active Traders** - Count of traders with activity today
2. **Top Performers by Win Rate** - Top 5 traders ranked by win percentage
3. **Biggest Gainers** - Top 5 traders by P&L percentage gains
4. **New Sign-ups Today** - Tracked separately (placeholder for future expansion)
5. **Average Daily P&L** - Mean profitability across all trades
6. **Upsell Candidates** - Consistent winners ready for premium tier upgrade

## Architecture

### Components

#### 1. **API Endpoint: `/api/command/trading-dashboard`**
- **File**: `app/api/command/trading-dashboard/route.ts`
- **Method**: GET
- **Authentication**: Bearer token (uses `CLIENT_API_KEY` from environment)
- **Response**: JSON with aggregated trading metrics

**Response Schema:**
```typescript
{
  active_traders_today: number;
  top_performers_by_win_rate: Array<{
    rank: number;
    user_id: string;
    username: string;
    win_rate: number;
    total_pnl: number;
    total_trades: number;
  }>;
  biggest_gainers: Array<{
    rank: number;
    user_id: string;
    username: string;
    pnl_percent: number;
    total_pnl: number;
    total_trades: number;
  }>;
  new_signups_today: number;
  avg_daily_pnl: number;
  upsell_candidates: Array<{
    user_id: string;
    username: string;
    current_pnl: number;
    win_rate: number;
    total_trades: number;
    days_active: number;
    urgency: string;  // "low", "medium", "high"
  }>;
  timestamp: string;
  summary: {
    total_trades_today: number;
    total_pnl_today: number;
    total_active_traders: number;
  };
}
```

#### 2. **React Component: `TradingDashboard.tsx`**
- **File**: `app/command-center/TradingDashboard.tsx`
- **Type**: Client component (`'use client'`)
- **Features**:
  - Auto-refresh every 60 seconds
  - Manual refresh button
  - Last update timestamp
  - Responsive grid layout
  - Color-coded metrics (positive/negative/neutral)
  - Tabular leaderboards

#### 3. **Pages**
- **Command Center Hub**: `/command-center` (main page with navigation)
- **Trading Dashboard**: `/command-center/trading` (dedicated dashboard page)
- **Query Parameter Alternative**: `/command-center?view=trading`

## Data Flow

```
clients.db (SQLite)
    ↓
runtime/client_api.py (FastAPI endpoints)
    ├── /api/clients/stats
    ├── /api/clients/leaderboard
    └── /api/clients/upsell-candidates
    ↓
Next.js API: /api/command/trading-dashboard
    ↓
TradingDashboard Component
    ↓
Browser UI
```

## Environment Variables

Required for the API endpoint to function:

```bash
# Runtime API endpoint
RUNTIME_API_URL=http://runtime:8080  # or your deployed runtime URL

# Client API authentication
CLIENT_API_KEY=your-api-key-here

# Optional: Database path (defaults to clients.db)
CLIENTS_DB_PATH=/path/to/clients.db
```

## Usage

### Access the Dashboard

1. **Via Command Center Hub**
   ```
   https://your-domain.com/command-center → Click "Trading Dashboard"
   ```

2. **Direct URL**
   ```
   https://your-domain.com/command-center/trading
   ```

3. **Query Parameter**
   ```
   https://your-domain.com/command-center?view=trading
   ```

### API Direct Access

For programmatic access to the metrics:

```bash
curl -X GET "https://your-domain.com/api/command/trading-dashboard" \
  -H "Cache-Control: no-store"
```

The dashboard auto-refreshes every 60 seconds, and users can manually trigger updates via the Refresh button.

## Metrics Explained

### Active Traders Today
- Count of unique traders with at least one trade entry today
- Real-time indicator of daily platform activity

### Top 5 Performers (Win Rate)
- Ranked by winning trade percentage
- Secondary sort: total P&L value
- Time window: Last 30 days (configurable)
- Identifies consistent winners

### Top 5 Biggest Gainers (P&L %)
- Ranked by percentage gain relative to capital
- Shows explosive growth potential
- Identifies high-risk/high-reward traders
- Useful for testimonials and marketing

### Average Daily P&L
- Mean profitability per trade across all traders
- Indicator of overall platform health
- Positive = growing trader base profit

### Upsell Candidates
- Criteria:
  - On free or standard tier
  - 10+ trades in lookback period
  - Composite score > 0.5 from:
    - PnL score (normalized to $1000)
    - Win rate score (% / 100)
    - Trade count score (/ 100)
    - Days active (consistency)
- Urgency levels:
  - **High** (score > 0.75): Close immediately
  - **Medium** (0.5-0.75): Follow up in 7 days
  - **Low** (< 0.5): Educational nurture path

## Customization

### Modify Refresh Interval

In `TradingDashboard.tsx`, change the interval:

```typescript
// Line: const interval = setInterval(fetchData, 60000);
const interval = setInterval(fetchData, 30000); // 30 seconds
```

### Change Leaderboard Size

In `api/command/trading-dashboard/route.ts`:

```typescript
// Change &limit=5 in any fetch call
runtimeFetch('/api/clients/leaderboard?metric=win_rate&limit=10&days=30'),
```

### Adjust Upsell Scoring

In `runtime/client_api.py`, modify the upsell candidate scoring logic (lines 569-576).

### Styling

All styles are inline CSS with CSS variables:
- Primary accent: `#7dd3fc`
- Positive indicator: `#4ade80`
- Negative indicator: `#f87171`
- Background: `#080b12`
- Text: `#e5f7ff`

Edit the style objects in `TradingDashboard.tsx` to customize appearance.

## Deployment Notes

### Vercel Frontend
- Dashboard is fully static-compatible but configured for `force-dynamic` to get fresh data
- Cache-Control headers set to `no-store` for live updates
- No additional build configuration needed

### Runtime Backend
- Ensure `/api/clients/stats`, `/api/clients/leaderboard`, and `/api/clients/upsell-candidates` are deployed
- `CLIENT_API_KEY` must match the key used by the frontend
- Database path must be accessible from the runtime container

### Database Access
- The dashboard queries the SQLite clients.db via the runtime API
- No direct database access from frontend (security best practice)
- All aggregation and calculations happen in the Python backend

## Monitoring & Alerts

The dashboard itself is a monitoring tool. Watch for:

1. **No Active Traders**: May indicate platform issue or off-peak hours
2. **Zero P&L**: Check if trades are being recorded
3. **High Error Rate**: Verify runtime backend is accessible
4. **Stale Timestamp**: Refresh button will retry the connection

## Troubleshooting

### Dashboard Shows "Failed to load dashboard"
- Check that `RUNTIME_API_URL` is set correctly
- Verify `CLIENT_API_KEY` matches the runtime configuration
- Ensure runtime backend is deployed and responding to `/api/clients/stats`

### Metrics Are Null/Zero
- Check clients.db has data with today's date
- Verify trades have `entry_time` in ISO format
- Run: `sqlite3 clients.db "SELECT COUNT(*) FROM trades WHERE DATE(entry_time) = DATE('now')"`

### Slow Refresh
- Leaderboard queries scan all clients; large datasets may be slow
- Consider adding database indexes on `user_id` and `entry_time`
- Adjust refresh interval to reduce load

### CORS Issues
- Dashboard API sets `allow_origins=["*"]` in runtime
- If issues persist, check that frontend domain is not blocked by CSP headers

## Database Schema Reference

The underlying clients.db tables:

```sql
-- Clients table
CREATE TABLE clients (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    email TEXT UNIQUE,
    account_created TEXT NOT NULL,
    account_status TEXT DEFAULT 'active',
    tier TEXT DEFAULT 'free'
);

-- Trades table
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    shares INTEGER NOT NULL,
    pnl REAL NOT NULL,
    pnl_percent REAL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    status TEXT DEFAULT 'closed',
    FOREIGN KEY (user_id) REFERENCES clients(user_id)
);

-- Performance cache
CREATE TABLE trader_stats (
    user_id TEXT PRIMARY KEY,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_pnl REAL,
    win_rate REAL,
    days_active INTEGER,
    last_updated TEXT
);
```

## Future Enhancements

1. **New Sign-ups Tracking**: Add `account_created` tracking for daily cohorts
2. **Win Rate Filtering**: Add filters by time period, symbol, or account tier
3. **Export Functionality**: Add CSV/JSON export of leaderboards
4. **Churn Detection**: Identify traders with declining activity
5. **Revenue Projection**: Estimate LTV based on trading patterns
6. **Drill-Down Views**: Click trader name to see detailed performance history
7. **Alerts**: Push notifications when upsell candidates reach urgency threshold
8. **Comparison Charts**: Compare period-over-period performance

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all environment variables are set
3. Review runtime logs for API errors
4. Check clients.db directly for data presence

---

**Last Updated**: 2026-06-18
**Dashboard Version**: 1.0.0
**Status**: Production Ready
