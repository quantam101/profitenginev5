# Landing Page Generator — Integration Guide

Complete guide to deploying and using the auto-updating landing page with real metrics.

## What You Get

### Files Created

```
app/
├── landing_page_generator.py       # Backend: Metrics collection
├── landing/
│   └── page.tsx                    # Landing page (Next.js)
├── components/
│   └── LiveMetricsHero.tsx         # React component (metrics display)
├── api/
│   ├── landing-metrics/
│   │   └── route.ts                # API endpoint (metrics JSON)
│   └── conversions/
│       └── route.ts                # Conversion tracking API
├── landing.css                     # Responsive dark theme
├── lib/
│   └── conversion_tracker.ts       # Client-side tracking utils
└── LANDING_PAGE_GENERATOR_README.md # Full documentation
```

### Key Features

✓ Real-time metrics (updates every 5 minutes)
✓ Social proof (top 3 performers anonymized)
✓ Performance dashboard (7-day P&L chart)
✓ Transparent pricing (actual tier breakdown)
✓ Trust signals (customer count, profitability, uptime)
✓ FAQ with real answers (dynamically populated)
✓ Conversion tracking (per section)
✓ Mobile responsive (works on all devices)
✓ Fast loading (<2 seconds)
✓ No fake metrics (100% real data from clients.db)

## Quick Setup (5 minutes)

### 1. Verify Files Exist

```bash
# Check all files created
ls -la app/landing_page_generator.py
ls -la app/landing/page.tsx
ls -la app/components/LiveMetricsHero.tsx
ls -la app/api/landing-metrics/route.ts
ls -la app/api/conversions/route.ts
```

### 2. Install Python Dependencies (if needed)

The generator uses only Python stdlib (sqlite3, json, datetime).

### 3. Test the API

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Test API endpoint
curl http://localhost:3000/api/landing-metrics | jq

# Check conversion API
curl -X POST http://localhost:3000/api/conversions \
  -H "Content-Type: application/json" \
  -d '{
    "section": "hero",
    "action": "cta_click",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "metadata": {"cta_text": "Get Started"}
  }'
```

### 4. View Landing Page

```
http://localhost:3000/landing
```

You should see:
- Live metrics from your database
- Top 3 performers
- 7-day performance chart
- Pricing tiers with real customer counts
- FAQ with real answers
- Trust signals

## How to Use

### Add to Your Site

#### Option A: Standalone Landing Page

Use `/landing` as your primary landing page:

```
profitengine-tau.vercel.app/landing
```

#### Option B: Embed Metrics Component

Import into another page:

```tsx
import LiveMetricsHero from '@/app/components/LiveMetricsHero';

export default function HomePage() {
  return (
    <>
      <header>Welcome to ProfitEngine</header>
      <LiveMetricsHero />
      <footer>© 2024</footer>
    </>
  );
}
```

### Track Conversions

#### In React Components

```tsx
import { trackCtaClick, trackSignup, trackTierSelected } from '@/app/lib/conversion_tracker';

export function SignupButton() {
  const handleClick = () => {
    trackCtaClick('hero', 'Get Started');
    // Then redirect to signup
    window.location.href = '/signup';
  };

  return <button onClick={handleClick}>Get Started</button>;
}

export function SignupForm() {
  const handleSubmit = async (email: string) => {
    // Sign up user...
    await createUser(email);
    // Track conversion
    trackSignup('hero', email);
  };
}

export function PricingTiers() {
  const selectTier = (tier: string, price: number) => {
    trackTierSelected(tier, price);
  };
}
```

#### Track Page Events

```tsx
import { initializeTracking } from '@/app/lib/conversion_tracker';

export default function LandingPage() {
  useEffect(() => {
    // Initialize page-level tracking
    initializeTracking();
  }, []);

  return <main>{/* page content */}</main>;
}
```

### Monitor Conversions

#### Real-time Dashboard

```bash
# Poll conversion metrics
watch -n 5 'curl -s http://localhost:3000/api/conversions/sections | jq'
```

#### Expected Output

```json
[
  {
    "section": "hero",
    "total_views": 245,
    "total_clicks": 18,
    "total_conversions": 3,
    "click_through_rate": 7.35,
    "conversion_rate": 16.67
  },
  {
    "section": "pricing",
    "total_views": 180,
    "total_clicks": 24,
    "total_conversions": 8,
    "click_through_rate": 13.33,
    "conversion_rate": 33.33
  }
]
```

## Customization

### Change Metrics Displayed

Edit `landing_page_generator.py`:

```python
class LandingPageGenerator:
    def get_custom_metric(self) -> float:
        """Add your custom metric"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ... ")
            return result
        finally:
            conn.close()
```

### Change Update Frequency

Edit `app/api/landing-metrics/route.ts`:

```typescript
const CACHE_DURATION = 10 * 60 * 1000; // 10 minutes instead of 5
```

And update component refresh:

```tsx
// In LiveMetricsHero.tsx
const interval = setInterval(fetchMetrics, 10 * 60 * 1000);
```

### Customize Styling

Edit `app/landing.css`:

```css
:root {
  --primary: #00ff00;    /* Change to your brand color */
  --accent: #ff6b00;
  --bg: #0a0a0a;
  --text: #ffffff;
}
```

### Add Custom Sections

1. **Add method to generator**:

```python
def get_featured_trades(self) -> List[Dict]:
    """Get recent winning trades"""
    conn = self._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, pnl_dollars, date
            FROM daily_trades
            WHERE pnl_dollars > 0
            ORDER BY date DESC
            LIMIT 5
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
```

2. **Export in JSON**:

```python
def generate_metrics_json(self, metrics: LandingPageMetrics) -> str:
    return json.dumps({
        ...
        "featured_trades": self.get_featured_trades()
    }, indent=2, default=str)
```

3. **Add component**:

```tsx
export function FeaturedTrades({ trades }) {
  return (
    <section>
      {trades.map(trade => (
        <div key={trade.id}>
          <div>${trade.pnl_dollars}</div>
          <div>{trade.date}</div>
        </div>
      ))}
    </section>
  );
}
```

## Deployment

### To Vercel (Recommended)

```bash
# 1. Commit changes
git add app/landing*
git add app/components/LiveMetricsHero.tsx
git add app/api/landing-metrics/
git add app/api/conversions/
git add app/lib/conversion_tracker.ts
git commit -m "feat: add real-time landing page generator"

# 2. Push to main (auto-deploys)
git push origin main

# 3. Access at
# https://profitengine-tau.vercel.app/landing
```

### To OCI Server (Self-Hosted)

```bash
# 1. SSH to server
ssh opc@129.146.167.73

# 2. Pull latest code
cd /var/www/profitengine
git pull origin main

# 3. Install dependencies (if needed)
npm install

# 4. Build
npm run build

# 5. Restart server
pm2 restart profitengine

# 6. Verify
curl https://your-domain.com/landing
curl https://your-domain.com/api/landing-metrics
```

## Monitoring & Analytics

### View Real-time Metrics

```bash
# Terminal 1: Watch landing metrics
watch -n 5 'curl -s http://localhost:3000/api/landing-metrics | jq ".hero"'

# Terminal 2: Watch conversions
watch -n 5 'curl -s http://localhost:3000/api/conversions/sections | jq'
```

### Check Database

```bash
# View sample trades
sqlite3 clients.db "SELECT * FROM daily_trades ORDER BY date DESC LIMIT 5;"

# View users by tier
sqlite3 clients.db "SELECT trading_tier, COUNT(*) FROM users WHERE is_active=1 GROUP BY trading_tier;"

# View top performers
sqlite3 clients.db "
  SELECT u.id, u.trading_tier, SUM(d.pnl_dollars) as total_pnl, AVG(d.win_rate) as win_rate
  FROM users u
  LEFT JOIN daily_trades d ON u.id = d.user_id
  WHERE u.is_active = 1 AND d.date >= date('now', '-30 days')
  GROUP BY u.id
  ORDER BY total_pnl DESC
  LIMIT 3;
"
```

### Generate Reports

```python
from app.landing_page_generator import LandingPageGenerator

gen = LandingPageGenerator()
metrics = gen.get_current_metrics()

# Print report
print(f"""
LANDING PAGE METRICS REPORT
===========================
Generated: {metrics.last_updated}

HERO METRICS
-----------
Win Rate: {metrics.current_win_rate:.1f}%
Active Users: {metrics.total_users}
Weekly P&L: ${metrics.weekly_pnl:,.0f}
Trades/Week: {metrics.total_trades_week}

TOP PERFORMERS
--------------
""")

for p in metrics.top_performers:
    print(f"#{p.rank} {p.tier}: ${p.pnl_30d:,.0f} ({p.win_rate:.1f}% win rate)")

print(f"""
TRUST SIGNALS
-------------
Days Profitable: {metrics.days_profitable}
Total P&L: ${metrics.total_pnl_generated:,.0f}
Uptime: {metrics.uptime_percent:.1f}%
Customers: {metrics.customer_count}
""")
```

## Troubleshooting

### Landing Page Shows No Data

**Problem**: Metrics display as 0

**Solution**:
1. Check database has data: `sqlite3 clients.db "SELECT COUNT(*) FROM daily_trades;"`
2. Check API endpoint: `curl http://localhost:3000/api/landing-metrics`
3. Check Python path in route.ts matches actual location
4. Check clients.db is in project root

### API Returns Error

**Problem**: `/api/landing-metrics` gives 500 error

**Solution**:
1. Check Python is installed: `python3 --version`
2. Check database file exists: `ls -la clients.db`
3. Check logs: `tail -f .next/server.log`
4. Try running Python directly:
   ```bash
   cd /path/to/project
   python3 -c "from app.landing_page_generator import LandingPageGenerator; print(LandingPageGenerator().get_current_metrics())"
   ```

### Metrics Not Updating

**Problem**: Page shows stale data

**Solution**:
1. Check cache timeout: `curl -i http://localhost:3000/api/landing-metrics | grep Cache-Control`
2. Force refresh: Press Ctrl+Shift+R (hard refresh)
3. Clear browser cache
4. Wait 5 minutes for cache to expire

### Performance Issues

**Problem**: Page loads slowly

**Solution**:
1. Add database indexes:
   ```sql
   CREATE INDEX idx_daily_trades_date ON daily_trades(date DESC);
   CREATE INDEX idx_daily_trades_user ON daily_trades(user_id);
   CREATE INDEX idx_users_active ON users(is_active);
   ```

2. Reduce metrics collection:
   - Edit `get_seven_day_history()` to fetch fewer days
   - Reduce `get_top_performers()` limit
   - Cache results longer (change `CACHE_DURATION`)

## Best Practices

### 1. Keep Metrics Accurate

- Run tests regularly: `npm test`
- Monitor database integrity
- Update metrics every 5 minutes (but not more frequently)

### 2. Protect User Privacy

- Anonymize performer data (no emails shown)
- Don't expose user IDs publicly
- Use aggregated metrics only

### 3. Set Realistic Expectations

- Show actual win rates (not best-case scenarios)
- Include losing days in charts
- Don't hide negative results

### 4. Track Conversions Properly

- Tag every CTA with source section
- Track signup completion
- Monitor which sections convert best

### 5. Test Before Deploying

```bash
# Run locally first
npm run dev

# Check all sections load
# Test mobile responsiveness
# Verify API responds correctly
# Check conversion tracking works

# Then deploy
git push origin main
```

## FAQ

**Q: Can I show customer names?**
A: Not recommended. Current implementation anonymizes for privacy. If you want to show names, get explicit consent first.

**Q: What if a customer's data is wrong?**
A: Edit clients.db directly or through admin panel, then wait 5 minutes for cache refresh.

**Q: How do I export metrics?**
A: Use the API endpoint or add CSV export: `GET /api/landing-metrics?format=csv`

**Q: Can I use this for multiple products?**
A: Yes. Create separate landing pages by copying and modifying the component.

**Q: What happens if database goes down?**
A: API returns cached metrics (up to 1 minute old) or fallback zeros with error flag.

## Next Steps

1. ✅ Deploy to production
2. ✅ Monitor conversions for 1 week
3. ✅ A/B test different layouts
4. ✅ Optimize based on conversion data
5. ✅ Add customer testimonial section
6. ✅ Integrate with email marketing

## Support

- **Documentation**: See LANDING_PAGE_GENERATOR_README.md
- **Issues**: Check logs in .next/server.log
- **API Testing**: Use provided curl commands
- **Metrics Debug**: Run landing_page_generator.py directly

---

**Status**: Production Ready
**Last Updated**: 2024-06-18
**Version**: 1.0
