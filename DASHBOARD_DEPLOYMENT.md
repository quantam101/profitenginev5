# Trading Dashboard Deployment Guide

## Summary

A complete trading dashboard has been created for the ProfitEngine command-center that displays real-time trading metrics and analytics from the clients.db database.

## Files Created

### 1. Frontend Components
- **`app/command-center/TradingDashboard.tsx`** - Main React dashboard component
  - Client-side component with auto-refresh capability
  - Displays 6 key metric cards + 3 leaderboards
  - Responsive grid layout with dark theme
  - 60-second auto-refresh interval

- **`app/command-center/trading/page.tsx`** - Dedicated dashboard page route
  - Access via `/command-center/trading`
  - Uses dynamic rendering for fresh data

### 2. API Endpoint
- **`app/api/command/trading-dashboard/route.ts`** - Backend aggregation API
  - Queries runtime `/api/clients/*` endpoints
  - Aggregates and transforms trading data
  - Returns JSON metrics for frontend consumption
  - Uses `CLIENT_API_KEY` for authentication

### 3. Updated Files
- **`app/command-center/page.tsx`** - Updated with dashboard navigation
  - Added "Trading Dashboard" link in nav
  - Added query parameter support for dashboard view
  - Updated actions list with dashboard note
  - Changed to `force-dynamic` for fresh data

### 4. Documentation
- **`TRADING_DASHBOARD_README.md`** - Comprehensive documentation
  - Architecture overview
  - Data flow diagram
  - Metrics explanations
  - Customization guide
  - Troubleshooting section

## Key Features

### 1. Metrics Displayed

**Summary Cards (4 KPIs):**
- Active Traders Today (count)
- Total Trades Today (count)
- Daily P&L Total (USD)
- Average P&L per Trade (USD)

**Leaderboard Tables:**
1. Top 5 Performers by Win Rate
   - Rank, Trader, Win Rate %, P&L, Trade Count

2. Top 5 Biggest Gainers (P&L %)
   - Rank, Trader, Gain %, Total P&L, Trade Count

3. Upsell Candidates (Premium Ready)
   - Trader, P&L, Win Rate %, Trade Count, Days Active, Urgency

### 2. Data Sources

All data flows through the existing runtime API:
```
clients.db (SQLite)
    ↓
runtime/client_api.py
├── /api/clients/stats
├── /api/clients/leaderboard?metric=...
└── /api/clients/upsell-candidates
    ↓
/api/command/trading-dashboard (Next.js)
    ↓
TradingDashboard (React component)
```

### 3. Real-Time Updates
- Auto-refreshes every 60 seconds
- Manual refresh button available
- Shows last update timestamp
- No caching (Cache-Control: no-store)

## Deployment Steps

### Prerequisites
1. Runtime backend deployed with client_api.py endpoints active
2. clients.db database populated with trading data
3. `RUNTIME_API_URL` environment variable configured

### 1. Configure Environment

Add to Vercel or deployment environment:

```bash
# Required
RUNTIME_API_URL=https://your-runtime-api.com  # or http://runtime:8080 for local
CLIENT_API_KEY=your-actual-api-key

# Optional (if using custom DB path on runtime)
CLIENTS_DB_PATH=/path/to/clients.db
```

### 2. Verify Dependencies

No new npm packages required. Uses existing:
- React 18+
- Next.js 14+
- TypeScript

### 3. Deploy to Vercel

```bash
# If using Vercel CLI
vercel deploy --env RUNTIME_API_URL=<url> --env CLIENT_API_KEY=<key>

# Or via Git push to trigger automatic deployment
git add app/command-center/TradingDashboard.tsx \
        app/command-center/trading/ \
        app/api/command/trading-dashboard/ \
        app/command-center/page.tsx
git commit -m "feat: add real-time trading dashboard"
git push origin main
```

### 4. Verify Deployment

1. **Check Command Center Hub**
   - Navigate to `/command-center`
   - Verify "Trading Dashboard" card appears
   - Click to navigate to dashboard

2. **Test Dashboard**
   - Go to `/command-center/trading`
   - Should show loading state then metrics
   - Click Refresh button - metrics should update
   - Check last update timestamp

3. **Test API Directly**
   ```bash
   curl -X GET "https://your-domain.com/api/command/trading-dashboard" \
     -H "Cache-Control: no-store"
   ```
   Should return JSON with all metrics populated.

## Configuration Options

### Adjust Auto-Refresh Interval

Edit `app/command-center/TradingDashboard.tsx` line 104:

```typescript
// Change from 60000 (60 seconds)
const interval = setInterval(fetchData, 30000); // 30 seconds
```

### Change Leaderboard Size

Edit `app/api/command/trading-dashboard/route.ts` line 54-56:

```typescript
// Change &limit=5 to desired number
runtimeFetch('/api/clients/leaderboard?metric=win_rate&limit=10&days=30'),
```

### Customize Time Window

Edit the same file - change `days=30` parameter:

```typescript
// Options: 7, 14, 30, 60, 90, 365
runtimeFetch('/api/clients/leaderboard?metric=win_rate&limit=5&days=90'),
```

### Theme Customization

Edit color variables in `TradingDashboard.tsx`:

```typescript
// Primary accent (cyan)
'#7dd3fc'
// Positive (green)
'#4ade80'
// Negative (red)
'#f87171'
// Background (dark)
'#080b12'
```

## Integration Points

### With Existing Systems

1. **Command Center**
   - Dashboard is accessible via the main command-center page
   - Maintains consistent styling and navigation

2. **Runtime Backend**
   - Leverages existing client_api.py endpoints
   - No changes needed to runtime code
   - Uses existing authentication system

3. **Database**
   - Queries existing clients.db schema
   - No schema changes required
   - Works with live trading data

### API Contract

The dashboard expects these endpoints on the runtime:

```
GET /api/clients/stats
Headers: Authorization: Bearer <key>
Query: ?days=30
Returns: ClientStats (total_traders, active_traders, avg_win_rate, total_pnl, etc.)

GET /api/clients/leaderboard
Headers: Authorization: Bearer <key>
Query: ?metric=win_rate&limit=5&days=30
Returns: Leaderboard (entries with rank, user_id, metric_value, etc.)

GET /api/clients/upsell-candidates
Headers: Authorization: Bearer <key>
Query: ?days=30
Returns: List of UpsellCandidate objects
```

If these endpoints change signatures, update the data transformation in `route.ts`.

## Monitoring & Maintenance

### Health Checks

Dashboard logs errors to browser console. In production, check:

1. `/api/command/trading-dashboard` returns 200
2. Runtime backend logs for API key authentication
3. clients.db for data freshness (entry_time timestamps)

### Common Issues

**Dashboard shows error:**
- Verify `RUNTIME_API_URL` is accessible
- Check `CLIENT_API_KEY` matches runtime config
- Ensure runtime backend is deployed

**Metrics are zero:**
- Verify clients.db has trade records
- Check that trades have entry_time in ISO format
- Run: `sqlite3 clients.db "SELECT COUNT(*) FROM trades"`

**Slow load time:**
- Consider caching for longer (adjust Cache-Control)
- Add database indexes on frequently queried columns
- Monitor runtime CPU during peak times

## Testing

### Unit Testing (Optional)

Add tests to verify API response shape:

```typescript
// app/api/command/trading-dashboard/__tests__/route.test.ts
describe('Trading Dashboard API', () => {
  it('returns expected metric structure', async () => {
    // Test that response has all required fields
  });
});
```

### E2E Testing (Optional)

Test dashboard loads and displays data:

```typescript
// e2e/trading-dashboard.spec.ts
test('dashboard displays trading metrics', async ({ page }) => {
  await page.goto('/command-center/trading');
  await expect(page.locator('h1')).toContainText('Trading Dashboard');
  // Verify metrics appear
});
```

## Performance Considerations

### Frontend
- Component memoization: Consider wrapping metrics in React.memo()
- Network requests: Limited to 1 per 60 seconds (auto-refresh)
- Bundle size: Minimal impact (no new dependencies)

### Backend
- Query load: One aggregation call per refresh
- Database: Queries scan trades table; consider indexes
- API rate limiting: 100 requests/hour (sufficient for dashboard)

### Optimization Ideas

1. **Caching Layer**
   - Cache metrics for 30 seconds at CDN level
   - Reduce database query frequency

2. **Pagination**
   - For very large trader populations (1000+)
   - Paginate leaderboards

3. **Lazy Loading**
   - Load upsell candidates on-demand (separate tab)
   - Speed up initial dashboard load

## Security Notes

1. **API Key**: Transmitted in Authorization header, only to backend
2. **Data**: No sensitive data exposed (only aggregated metrics)
3. **CORS**: Dashboard API allows all origins (consider restricting in production)
4. **Rate Limiting**: 100 req/hour per identifier (sufficient for UI)

## Rollback

If issues occur, simply remove the new files:

```bash
git revert <commit-hash>
git push origin main
```

The command-center will revert to showing only the status checks without the dashboard.

## Success Criteria

Dashboard is production-ready when:

- [ ] `/command-center/trading` loads and displays metrics
- [ ] Manual refresh button works
- [ ] Auto-refresh updates every 60 seconds
- [ ] All 6 leaderboard entries populate correctly
- [ ] No console errors
- [ ] Responsive on mobile (iOS/Android)
- [ ] Load time < 2 seconds
- [ ] API call succeeds on runtime backend
- [ ] Error handling displays gracefully if runtime unavailable

## Next Steps

1. **Deploy** to Vercel with environment variables
2. **Verify** all metrics display correctly
3. **Monitor** for 24 hours to ensure stability
4. **Gather feedback** from operations team
5. **Consider enhancements** from Future Enhancements section in README

## Support & Questions

Refer to `TRADING_DASHBOARD_README.md` for:
- Detailed architecture
- Metrics explanations
- Troubleshooting guide
- Customization examples

---

**Version**: 1.0.0  
**Date**: 2026-06-18  
**Status**: Ready for Deployment  
**Estimated Setup Time**: 15 minutes
