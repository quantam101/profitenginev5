# Trading Dashboard — Quick Start (15 min deployment)

## What Was Built

A real-time trading dashboard that displays:
- Today's active traders
- Top 5 performers by win rate
- Top 5 biggest gainers (P&L %)
- Average daily P&L
- Upsell candidates (premium tier upgrade prospects)

All data flows from `clients.db` via the runtime API.

**Location:** `/command-center/trading` (or `/command-center?view=trading`)

---

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `app/command-center/TradingDashboard.tsx` | React dashboard component | 355 |
| `app/api/command/trading-dashboard/route.ts` | Backend aggregation API | 149 |
| `app/command-center/trading/page.tsx` | Page route | 8 |
| `TRADING_DASHBOARD_README.md` | Full documentation | 331 |
| `DASHBOARD_DEPLOYMENT.md` | Deployment guide | 365 |
| `IMPLEMENTATION_SUMMARY.md` | Complete overview | 451 |
| `dashboard-api-schema.json` | API schema reference | - |
| `dashboard-test-commands.sh` | Test commands | - |

---

## Deployment (3 steps, 15 minutes)

### Step 1: Set Environment Variables

In Vercel project settings, add:

```bash
RUNTIME_API_URL=https://your-runtime-domain.com
CLIENT_API_KEY=your-actual-api-key-from-runtime
```

**Example (OCI):**
```bash
RUNTIME_API_URL=https://runtime.alreadyhere.com  # or http://129.146.167.73:8080
CLIENT_API_KEY=<your-production-key>
```

### Step 2: Deploy

```bash
git add app/command-center/ app/api/command/
git commit -m "feat: add real-time trading dashboard"
git push origin main
```

Vercel auto-deploys on push to main.

### Step 3: Verify

Navigate to: `https://your-domain.com/command-center/trading`

You should see:
- 4 metric cards (active traders, total trades, daily P&L, avg P&L)
- 3 leaderboard tables (win rate, gainers, upsell candidates)
- "Last updated" timestamp and Refresh button
- Auto-refresh every 60 seconds

---

## Testing

### Quick Manual Test

```bash
# 1. Check API endpoint
curl -X GET "https://your-domain.com/api/command/trading-dashboard"

# 2. Open dashboard
https://your-domain.com/command-center/trading

# 3. Click Refresh button - should see new "Updated" timestamp

# 4. Wait 60 seconds - should auto-refresh with new data
```

### Test with Sample Script

```bash
bash dashboard-test-commands.sh
```

Requires `curl` and optionally `jq` for pretty JSON output.

---

## Common Issues & Fixes

### Dashboard shows "Failed to load dashboard"

**Cause:** Environment variables not set or runtime not accessible

**Fix:**
1. Verify `RUNTIME_API_URL` in Vercel settings
2. Test manually: `curl https://your-runtime-url/api/clients/stats`
3. Verify `CLIENT_API_KEY` matches runtime config

### Metrics show as zero/null

**Cause:** No trading data in clients.db yet

**Fix:**
1. Ensure trades have been executed today
2. Verify entry_time is in ISO format: `2026-06-18T14:23:45Z`
3. Check: `sqlite3 clients.db "SELECT COUNT(*) FROM trades WHERE DATE(entry_time) = DATE('now')"`

### Slow page load (> 2 seconds)

**Cause:** API is slow or database query heavy

**Fix:**
1. Check runtime logs for slow queries
2. Add indexes: `CREATE INDEX idx_trades_user_id ON trades(user_id)`
3. Verify database size: `ls -lh clients.db`

---

## Key Features

| Feature | Benefit |
|---------|---------|
| **Auto-refresh (60s)** | Always up-to-date metrics |
| **Manual refresh** | Instant updates on demand |
| **Dark theme** | Matches command-center aesthetics |
| **Responsive** | Works on mobile, tablet, desktop |
| **Error handling** | Shows user-friendly messages |
| **No caching** | Real-time data (Cache-Control: no-store) |

---

## Data Refresh

- **Auto-refresh:** Every 60 seconds (configurable)
- **Manual refresh:** Click "Refresh" button
- **Cache policy:** `no-store` (always fresh)
- **API timeout:** 5 seconds (fail gracefully)

---

## Customization

### Change refresh interval from 60s to 30s:

Edit `app/command-center/TradingDashboard.tsx` line 104:
```typescript
const interval = setInterval(fetchData, 30000); // was 60000
```

### Change leaderboard size from 5 to 10:

Edit `app/api/command/trading-dashboard/route.ts` lines 54-56:
```typescript
runtimeFetch('/api/clients/leaderboard?metric=win_rate&limit=10&days=30'),
```

### Change lookback window from 30 days to 90 days:

Same file, change `days=30` to `days=90` in leaderboard queries.

---

## Monitoring Dashboard

The dashboard is self-explanatory for operations:

- **Active Traders:** Should be > 0 during trading hours
- **Total P&L:** Positive = growing platform profitability
- **Win Rate:** 50%+ is healthy
- **Upsell Candidates:** Prioritize "High" urgency for sales outreach

---

## Next Steps

1. ✓ Deploy with environment variables
2. ✓ Navigate to `/command-center/trading`
3. ✓ Verify metrics display
4. Monitor for 24 hours
5. Share access with operations team
6. Use upsell candidates for sales targeting

---

## Documentation

For more details, see:
- **Full Guide:** `TRADING_DASHBOARD_README.md`
- **Deployment:** `DASHBOARD_DEPLOYMENT.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`
- **API Schema:** `dashboard-api-schema.json`

---

## Support

If dashboard won't load:
1. Check environment variables are set
2. Verify runtime backend is accessible
3. Check browser console for errors
4. Review runtime logs for API key issues
5. See troubleshooting in `TRADING_DASHBOARD_README.md`

---

**Status:** Ready to deploy  
**Setup Time:** 15 minutes  
**Maintenance:** Zero (auto-refresh built-in)  
**Cost:** None (uses existing infrastructure)
