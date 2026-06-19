# Landing Page Generator — Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                               │
│  (Mobile, Tablet, Desktop)                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Landing Page (Next.js Rendered)                              │ │
│  │  http://localhost:3000/landing                                │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  <LiveMetricsHero /> Component                           │ │ │
│  │  │  • Fetches /api/landing-metrics every 5 min              │ │ │
│  │  │  • Renders metrics, social proof, dashboard, pricing     │ │ │
│  │  │  • Tracks conversions with /api/conversions              │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌────────────────────┐      ┌──────────────────┐
        │ GET /api/landing   │      │ POST /api/conv   │
        │ -metrics           │      │ ersions          │
        │ (5-min cache)      │      │ (conversion      │
        │                    │      │  tracking)       │
        └─────────┬──────────┘      └────────┬─────────┘
                  │                          │
        ┌─────────▼──────────────────────────▼─────────┐
        │        NEXT.JS SERVER (api/route.ts)         │
        │                                               │
        │  /api/landing-metrics/route.ts               │
        │  ├─ Check 5-min cache                        │
        │  ├─ Spawn Python process if cache expired    │
        │  └─ Return JSON + cache headers              │
        │                                               │
        │  /api/conversions/route.ts                   │
        │  ├─ POST: Store conversion event             │
        │  ├─ GET /metrics: Aggregated by section      │
        │  └─ GET /sections: All section metrics       │
        └──────────┬──────────────────────────┬────────┘
                   │                          │
          ┌────────▼────────┐        ┌───────▼──────────┐
          │  Spawn Python3  │        │ In-Memory Store  │
          │  Process        │        │ (EventHistory)   │
          └────────┬────────┘        └──────────────────┘
                   │
        ┌──────────▼───────────────────┐
        │ landing_page_generator.py     │
        │                               │
        │ ┌─────────────────────────┐  │
        │ │ get_current_win_rate()  │  │
        │ │ get_total_users()       │  │
        │ │ get_weekly_pnl()        │  │
        │ │ get_top_performers()    │  │
        │ │ get_seven_day_history() │  │
        │ │ get_tier_breakdown()    │  │
        │ │ get_total_pnl_all_time()│  │
        │ └────────┬────────────────┘  │
        │          │ (SQL queries)      │
        └──────────┼──────────────────┘
                   │
        ┌──────────▼────────────────┐
        │   SQLite: clients.db       │
        │                            │
        │  Tables:                   │
        │  ├─ users                  │
        │  │  ├─ id (PK)             │
        │  │  ├─ email               │
        │  │  ├─ trading_tier        │
        │  │  └─ is_active           │
        │  │                          │
        │  ├─ daily_trades           │
        │  │  ├─ id (PK)             │
        │  │  ├─ user_id (FK)        │
        │  │  ├─ date                │
        │  │  ├─ num_trades          │
        │  │  ├─ win_count           │
        │  │  ├─ pnl_dollars         │
        │  │  ├─ win_rate            │
        │  │  └─ balance             │
        │  │                          │
        │  └─ upsell_tracking        │
        │     ├─ user_id (FK)        │
        │     ├─ lifetime_revenue    │
        │     └─ revenue_tier        │
        │                            │
        └────────────────────────────┘
```

## Data Flow - Metrics Update (5-minute cycle)

```
┌─ 5 MINUTE TIMER ─┐
│                  │
▼                  │
Browser sends request to /api/landing-metrics
                  │
▼                 │
API checks 5-min cache
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
      CACHED           NOT CACHED
       (return)        (fetch new)
         │                 │
         │        ┌────────▼────────┐
         │        │                 │
         │        │ Spawn Python    │
         │        │ Process         │
         │        │                 │
         │        └────────┬────────┘
         │                 │
         │        ┌────────▼────────────────┐
         │        │ Query clients.db        │
         │        │ • Current win rate      │
         │        │ • Active users          │
         │        │ • Weekly P&L            │
         │        │ • Top performers        │
         │        │ • 7-day history         │
         │        │ • Tier breakdown        │
         │        │ • Trust signals         │
         │        └────────┬────────────────┘
         │                 │
         │        ┌────────▼────────────────┐
         │        │ Export as JSON          │
         │        │ (generate_metrics_json) │
         │        └────────┬────────────────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
           Cache result (5 min TTL)
                  │
                  ▼
           Return to client as JSON
                  │
                  ▼
           React component updates display
                  │
                  ▼
           User sees fresh metrics
```

## Data Flow - Conversion Tracking

```
User interacts with landing page
        │
        ├─ Clicks CTA button
        │     │
        │     └─ trackCtaClick('hero', 'Get Started')
        │
        ├─ Expands FAQ
        │     │
        │     └─ trackFaqOpen('question text')
        │
        ├─ Views social proof
        │     │
        │     └─ trackPerformerView(1, 'elite')
        │
        └─ Submits signup form
              │
              └─ trackSignup('pricing', 'user@example.com')

                       │
                       ▼
         Create ConversionEvent object
         {
           timestamp: ISO timestamp
           section: 'hero' | 'pricing' | etc
           action: 'cta_click' | 'signup' | etc
           sessionId: unique session ID
           metadata: additional data
         }
                       │
                       ▼
         POST /api/conversions
                       │
                       ├─ Validate event
                       ├─ Store in memory
                       ├─ Log to console
                       └─ Return success

Later, view aggregated analytics:
                       │
         GET /api/conversions/metrics
              GET /api/conversions/sections
                       │
                       ▼
         Aggregate events by section:
         {
           section: 'hero',
           total_views: 245,
           total_clicks: 18,
           total_conversions: 3,
           click_through_rate: 7.35%,
           conversion_rate: 16.67%
         }
```

## Component Architecture

```
Landing Page (Next.js)
│
├─ Header/Navbar
│  └─ Links to sections
│
├─ LiveMetricsHero (React Component)
│  │
│  ├─ useEffect: Fetch /api/landing-metrics
│  │
│  ├─ MetricCard (Hero Section)
│  │  ├─ Win Rate: 85.3%
│  │  ├─ Users: 42
│  │  ├─ Weekly P&L: $12,345
│  │  └─ Trades: 1,238
│  │
│  ├─ TopPerformerCard (Social Proof)
│  │  ├─ #1 Performer: Elite, 92.5%, $5,500
│  │  ├─ #2 Performer: Pro, 88%, $3,200
│  │  └─ #3 Performer: Pro, 85%, $2,750
│  │
│  ├─ PerformanceChart (Dashboard)
│  │  ├─ 7-day P&L bars
│  │  └─ Key metrics display
│  │
│  ├─ PricingCard (Pricing)
│  │  ├─ Free: 15 customers
│  │  ├─ Pro: 22 customers (popular)
│  │  └─ Elite: 5 customers
│  │
│  └─ TrustSignal (Trust Section)
│     ├─ 42 Active Traders
│     ├─ $123,456 Total P&L
│     ├─ 99.8% Uptime
│     └─ 12 Profitable Days
│
├─ FAQ Section
│  ├─ FAQ Item (expandable)
│  │  ├─ Question
│  │  └─ Answer (using real metrics)
│  └─ Multiple FAQ items
│
├─ CTA Section
│  └─ Call-to-action buttons
│
└─ Footer
   └─ Links + update timestamp
```

## Database Schema

```sql
-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    signup_date TEXT NOT NULL,
    first_trade_date TEXT,
    trading_tier TEXT DEFAULT 'free',
    is_active BOOLEAN DEFAULT 1
);

-- Daily Trades Table
CREATE TABLE daily_trades (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    num_trades INTEGER NOT NULL,
    win_count INTEGER NOT NULL,
    loss_count INTEGER NOT NULL,
    pnl_dollars REAL NOT NULL,
    pnl_percent REAL NOT NULL,
    balance REAL NOT NULL,
    win_rate REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Upsell Tracking Table
CREATE TABLE upsell_tracking (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tier_history TEXT,  -- JSON array
    current_tier TEXT,
    revenue_tier TEXT,
    last_upsell_offered TEXT,
    upsell_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    lifetime_revenue REAL DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Indices for performance
CREATE INDEX idx_daily_trades_date ON daily_trades(date DESC);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_tier ON users(trading_tier);
```

## Metrics Collection Pipeline

```
┌─ Python Backend (landing_page_generator.py) ─┐
│                                                │
│  LandingPageGenerator                          │
│  │                                              │
│  ├─ Connection Pool                            │
│  │  └─ SQLite connection handling              │
│  │                                              │
│  ├─ Hero Metrics                               │
│  │  ├─ get_current_win_rate()                  │
│  │  │  └─ SELECT AVG(win_rate) FROM trades    │
│  │  ├─ get_total_users()                       │
│  │  │  └─ COUNT(*) FROM users WHERE active    │
│  │  ├─ get_weekly_pnl()                        │
│  │  │  └─ SUM(pnl_dollars) FROM trades        │
│  │  └─ get_weekly_trade_count()                │
│  │     └─ SUM(num_trades) FROM trades         │
│  │                                              │
│  ├─ Social Proof Metrics                       │
│  │  └─ get_top_performers()                    │
│  │     └─ JOINs users + trades, ORDER by PnL │
│  │                                              │
│  ├─ Dashboard Metrics                          │
│  │  └─ get_seven_day_history()                 │
│  │     └─ GROUP BY date for 7 days             │
│  │                                              │
│  ├─ Pricing Metrics                            │
│  │  ├─ get_tier_breakdown()                    │
│  │  ├─ get_avg_revenue_by_tier()               │
│  │  └─ get_total_revenue()                     │
│  │                                              │
│  ├─ Trust Metrics                              │
│  │  ├─ get_profitable_days_count()             │
│  │  ├─ get_total_pnl_all_time()                │
│  │  └─ get_uptime_percent()                    │
│  │                                              │
│  └─ Export                                      │
│     └─ generate_metrics_json()                 │
│        └─ Output: JSON with all metrics        │
│                                                │
└────────────────────────────────────────────────┘
```

## Caching Strategy

```
Cache Layers (from fastest to slowest):

Level 1: Browser Cache
├─ Response Headers: Cache-Control: max-age=300
├─ TTL: 5 minutes
└─ Auto-refreshes on /landing page visit

Level 2: API Cache (Next.js)
├─ Location: Memory in Next.js process
├─ TTL: 5 minutes (s-maxage)
├─ Stale-while-revalidate: 10 minutes
└─ Prevents database hammering

Level 3: Database Query
├─ SQL queries executed on cache miss
├─ Max duration: 2 seconds (timeout)
└─ Returns fresh metrics

Level 4: Fallback
├─ Last successful metrics returned
├─ If database unavailable
└─ TTL: 1 minute

Timeline:
t=0min: User visits page, cache hit, instant load
t=2min: User refreshes, still cached, instant
t=5min: Cache expires, Python subprocess executes
t=5.5min: New metrics fetched from database
t=5.6min: New metrics cached in memory
t=5.7min: User sees updated metrics
```

## Performance Characteristics

```
┌─ Metric Response Time Distribution ─┐
│                                      │
│  Cached (95% of requests)            │
│  ├─ Network: 100-200ms               │
│  ├─ Parsing: 50ms                    │
│  └─ Render: 500-800ms                │
│  └─> Total: <1.5 seconds ✅         │
│                                      │
│  Cache miss (5% of requests)         │
│  ├─ Network: 100-200ms               │
│  ├─ Python startup: 300-500ms        │
│  ├─ DB query: 200-500ms              │
│  ├─ JSON generation: 50-100ms        │
│  ├─ Network response: 100-200ms      │
│  └─> Total: 1.5-2 seconds ✅        │
│                                      │
└──────────────────────────────────────┘

Lighthouse Scores (Expected):
├─ Performance: 85-90
├─ Accessibility: 95+
├─ Best Practices: 90+
└─ SEO: 95+
```

## Error Handling Flow

```
Request to /api/landing-metrics
        │
        ▼
    Try/Catch wrapper
        │
    ┌───┴────┐
    │        │
    ▼        ▼
SUCCESS    ERROR
    │        │
    │        ├─ Log error
    │        ├─ Return cached (if available)
    │        ├─ Else return fallback zeros
    │        └─ Status 200 (to prevent breaks)
    │
    └─────────┐
              │
              ▼
         Return JSON with
         Cache-Control header
              │
              ▼
         Client receives metrics
         (real or fallback)
              │
              ▼
         Component renders
         (no visual errors)
```

---

This architecture ensures:
- ✅ Real-time metrics (5-min refresh)
- ✅ Fast loading (<2 seconds)
- ✅ No database hammering (5-min cache)
- ✅ Graceful degradation (fallback metrics)
- ✅ Privacy (no personal data exposed)
- ✅ Scalability (stateless API)
