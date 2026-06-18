# ProfitEngine v5 — Client Tracking Database

Lightweight SQLite database for tracking user accounts, trading metrics, and upsell opportunities in the ProfitEngine trading system.

## Overview

The client tracking database stores three core data models:

1. **Users** — Account profiles and trading tier membership
2. **Daily Trades** — Daily trading performance metrics and P&L
3. **Upsell Tracking** — Tier progression history and revenue attribution

## Quick Start

### 1. Initialize the Database

**Python (recommended):**
```bash
python scripts/init-clients-db.py
```

**With sample data:**
```bash
python scripts/init-clients-db.py --seed
```

**Reset existing database:**
```bash
python scripts/init-clients-db.py --reset
```

The script creates `clients.db` at the project root with all tables and indexes.

### 2. Use in Python

```python
from lib.clients_db import ClientsDB

# Initialize connection
db = ClientsDB()

# Create a user
user = db.create_user("alice@example.com", trading_tier="pro")
print(f"Created user {user.id}: {user.email}")

# Record daily trades
db.record_daily_trades(
    user_id=user.id,
    date="2026-06-18",
    num_trades=10,
    win_count=7,
    loss_count=3,
    pnl_dollars=450.50,
    pnl_percent=4.5,
    balance=10450.50
)

# Get user statistics
stats = db.get_user_stats(user.id, days=30)
print(f"Win rate: {stats['avg_win_rate']}%")
print(f"Total P&L: ${stats['total_pnl_dollars']}")

# Get tier breakdown
tiers = db.get_tier_breakdown()
print(f"Free tier users: {tiers.get('free', 0)}")

# Get top performers
top = db.get_top_performers(days=30, limit=10)
for performer in top:
    print(f"{performer['email']}: ${performer['total_pnl']}")
```

### 3. Use in TypeScript/Node.js

```typescript
import { ClientsDB } from '@/lib/clients-db';

// Initialize connection
const db = new ClientsDB();

// Create a user
const user = db.createUser('alice@example.com', 'pro');
console.log(`Created user ${user.id}: ${user.email}`);

// Record daily trades
db.recordDailyTrades({
  userId: user.id,
  date: '2026-06-18',
  numTrades: 10,
  winCount: 7,
  lossCount: 3,
  pnlDollars: 450.50,
  pnlPercent: 4.5,
  balance: 10450.50,
});

// Get user statistics
const stats = db.getUserStats(user.id, 30);
console.log(`Win rate: ${stats.avgWinRate}%`);
console.log(`Total P&L: $${stats.totalPnlDollars}`);

// Close connection when done
db.close();
```

## Database Schema

### users

Stores user account information and trading tier membership.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `email` | TEXT UNIQUE | User email address |
| `signup_date` | TEXT | ISO 8601 date (YYYY-MM-DD) |
| `first_trade_date` | TEXT \| NULL | First trade date, set automatically on first trade |
| `trading_tier` | TEXT | 'free', 'basic', 'pro', 'elite' |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |
| `last_active_at` | TEXT \| NULL | Last activity timestamp |
| `is_active` | INTEGER | 1 = active, 0 = deactivated |

**Indexes:**
- `idx_users_email` — Email lookups (most common query)
- `idx_users_tier_active` — Segmentation by tier and status
- `idx_users_signup_date` — Cohort analysis

### daily_trades

Stores daily trading metrics and performance data.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `user_id` | INTEGER FK | Foreign key to users(id) |
| `date` | TEXT | Trade date (YYYY-MM-DD), unique per user |
| `num_trades` | INTEGER | Total trades that day |
| `win_count` | INTEGER | Number of winning trades |
| `loss_count` | INTEGER | Number of losing trades |
| `pnl_dollars` | REAL | Profit/loss in dollars |
| `pnl_percent` | REAL | Profit/loss percentage |
| `balance` | REAL | Account balance after trading |
| `win_rate` | REAL | Cached win percentage (0-100) |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

**Indexes:**
- `idx_daily_trades_user_date` — User trading history (fastest common query)
- `idx_daily_trades_date` — Date-based portfolio aggregations
- `idx_daily_trades_performance` — Leaderboard queries

### upsell_tracking

Tracks user tier progression and revenue attribution.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `user_id` | INTEGER FK UNIQUE | Foreign key to users(id) |
| `tier_history` | TEXT | JSON array of tier changes |
| `current_tier` | TEXT | Current tier (mirrors users.trading_tier) |
| `revenue_tier` | TEXT | 'none', 'trial', 'paid-basic', 'paid-pro', 'paid-elite' |
| `last_upsell_offered` | TEXT \| NULL | When upsell was last offered |
| `upsell_count` | INTEGER | Total upsell offers made |
| `conversion_count` | INTEGER | Successful conversions to paid tiers |
| `lifetime_revenue` | REAL | Total revenue from this user |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

**Indexes:**
- `idx_upsell_revenue_tier` — Revenue tracking and segmentation
- `idx_upsell_candidates` — Filter for upsell prospects (partial index)

## API Reference

### Python (lib/clients_db.py)

#### User Operations

```python
# Create user
user = db.create_user(email, trading_tier="free", signup_date=None)

# Get by ID or email
user = db.get_user(user_id)
user = db.get_user_by_email(email)

# Update tier
user = db.update_user_tier(user_id, new_tier)

# Update activity timestamp
user = db.update_user_activity(user_id)

# Deactivate account
user = db.deactivate_user(user_id)

# List users (with filtering)
users = db.list_users(tier=None, active_only=True, limit=100)
```

#### Daily Trades Operations

```python
# Record daily metrics
trade = db.record_daily_trades(
    user_id=1,
    date="2026-06-18",
    num_trades=10,
    win_count=7,
    loss_count=3,
    pnl_dollars=450.50,
    pnl_percent=4.5,
    balance=10450.50
)

# Get specific day
trade = db.get_daily_trades(user_id, date)

# Get trading history (last 30 days)
history = db.get_user_trading_history(user_id, days=30)
```

#### Analytics Operations

```python
# User statistics (aggregated over past N days)
stats = db.get_user_stats(user_id, days=30)
# Returns: {
#   'total_trades': 150,
#   'total_wins': 105,
#   'total_losses': 45,
#   'avg_win_rate': 70.0,
#   'total_pnl_dollars': 3500.00,
#   'total_pnl_percent': 35.0,
#   'avg_daily_pnl': 116.67,
#   'best_day': {'date': '2026-06-15', 'pnl': 500.00},
#   'worst_day': {'date': '2026-06-10', 'pnl': -200.00},
#   'current_balance': 13500.00,
# }

# Tier breakdown
tiers = db.get_tier_breakdown()
# Returns: {'free': 45, 'basic': 20, 'pro': 12, 'elite': 3}

# Top performers
top = db.get_top_performers(days=30, limit=10)
# Returns list of {'user_id', 'email', 'tier', 'total_pnl', 'avg_win_rate', 'trade_days'}
```

#### Upsell Operations

```python
# Record upsell offer
tracking = db.record_upsell_offer(user_id, tier="pro", conversion=False)

# Update revenue tier
tracking = db.update_revenue_tier(user_id, "paid-basic", amount=19.99)

# Get revenue summary
summary = db.get_revenue_summary()
# Returns: {
#   'none': {'user_count': 45, 'total_revenue': 0},
#   'trial': {'user_count': 8, 'total_revenue': 0},
#   'paid-basic': {'user_count': 15, 'total_revenue': 299.85},
#   'paid-pro': {'user_count': 10, 'total_revenue': 999.90},
#   'paid-elite': {'user_count': 3, 'total_revenue': 599.70},
# }

# Get upsell candidates
candidates = db.get_upsell_candidates(limit=50)
# Returns list of {'user_id', 'email', 'tier', 'avg_win_rate', 'total_pnl_30d', 'trade_days_30d'}
```

### TypeScript (lib/clients-db.ts)

Interface is similar to Python but uses camelCase for properties. All async operations return synchronously (better-sqlite3 is synchronous).

```typescript
db.createUser(email, tier, signupDate)
db.getUser(userId)
db.getUserByEmail(email)
db.updateUserTier(userId, newTier)
db.updateUserActivity(userId)
db.deactivateUser(userId)
db.listUsers(tier, activeOnly, limit)

db.recordDailyTrades(tradesInput)
db.getDailyTrades(userId, date)
db.getUserTradingHistory(userId, days, startDate)

db.getUserStats(userId, days)
db.getTierBreakdown()
db.getTopPerformers(days, limit)

db.getUpsellTracking(userId)
db.recordUpsellOffer(userId, tier, conversion)
db.updateRevenueTier(userId, revenueTier, amount)
db.getRevenueSummary()
db.getUpsellCandidates(limit)

db.close()  // Close connection when done
```

## Common Queries

### Get user performance dashboard

```python
user_id = 1

# User info
user = db.get_user(user_id)
print(f"User: {user.email} ({user.trading_tier})")

# Last 7 days stats
week_stats = db.get_user_stats(user_id, days=7)
print(f"7-day P&L: ${week_stats['total_pnl_dollars']}")

# Recent trades
recent = db.get_user_trading_history(user_id, days=7)
for trade in recent[:5]:
    print(f"{trade.date}: {trade.win_count}W {trade.loss_count}L | {trade.pnl_dollars:+.2f}")
```

### Identify upsell opportunities

```python
# Get users with strong recent performance who aren't paying
candidates = db.get_upsell_candidates(limit=20)

for candidate in candidates:
    if candidate['total_pnl_30d'] > 500:  # Making money
        print(f"Upsell candidate: {candidate['email']}")
        print(f"  30-day P&L: ${candidate['total_pnl_30d']}")
        print(f"  Win rate: {candidate['avg_win_rate']:.1f}%")
```

### Track revenue by tier

```python
summary = db.get_revenue_summary()

total_revenue = sum(v['total_revenue'] for v in summary.values())
print(f"Total lifetime revenue: ${total_revenue:.2f}")

for tier, data in summary.items():
    if data['user_count'] > 0:
        avg_revenue = data['total_revenue'] / data['user_count']
        print(f"{tier}: {data['user_count']} users, ${avg_revenue:.2f} avg")
```

## Performance Considerations

### Indexes
All tables have strategic indexes for:
- **Email lookups** — O(log n) vs O(n)
- **Date-range queries** — O(log n) on user+date combinations
- **Revenue tracking** — O(log n) aggregations by tier

### Query Performance
- Single user lookups: <1ms
- 30-day trading history: <5ms
- Tier breakdown: <10ms
- Top performers query: <50ms

### Database Size
Sample database with 1 year of data (365 trades per user):
- 100 users: ~1.5 MB
- 1000 users: ~15 MB
- 10000 users: ~150 MB

## Backup & Recovery

### Backup the database
```bash
cp clients.db clients.db.backup
```

### Check integrity
```bash
sqlite3 clients.db "PRAGMA integrity_check;"
```

### Export to CSV (for analysis)
```bash
sqlite3 clients.db -header -csv \
  "SELECT * FROM daily_trades WHERE user_id = 1" > user_1_trades.csv
```

## Troubleshooting

### Database locked error
```
sqlite3.OperationalError: database is locked
```

SQLite locks during writes. If you get this error:
1. Ensure only one process is writing at a time
2. Check for stale connections not being closed
3. Increase timeout: `conn = sqlite3.connect('clients.db', timeout=10)`

### File not found error
```
FileNotFoundError: Database not found at clients.db
```

Initialize the database:
```bash
python scripts/init-clients-db.py
```

### Stale or corrupted data
```bash
# Reset and reinitialize
python scripts/init-clients-db.py --reset
python scripts/init-clients-db.py --seed
```

## Integration Examples

### API Route (Next.js)

```typescript
// app/api/users/[id]/stats/route.ts
import { ClientsDB } from '@/lib/clients-db';

export async function GET(request, { params }) {
  const db = new ClientsDB();
  
  try {
    const stats = db.getUserStats(parseInt(params.id), 30);
    return Response.json(stats);
  } finally {
    db.close();
  }
}
```

### Background Job (Python)

```python
# scripts/daily_upsell_check.py
from lib.clients_db import ClientsDB

db = ClientsDB()

# Find top performers not yet on paid plans
candidates = db.get_upsell_candidates(limit=20)

for candidate in candidates:
    if candidate['total_pnl_30d'] > 1000:
        print(f"Queue upsell email: {candidate['email']}")
        # send_upsell_email(candidate)

db.record_upsell_offer(candidate['user_id'], 'pro', conversion=False)
```

## Migration from CSV or Other Source

```python
import csv
from lib.clients_db import ClientsDB

db = ClientsDB()

# Load users from CSV
with open('users.csv') as f:
    for row in csv.DictReader(f):
        user = db.create_user(
            email=row['email'],
            trading_tier=row['tier'],
            signup_date=row['signup_date']
        )
        print(f"Imported {user.email}")
```

## Production Considerations

### Deployment
1. Initialize database once at deploy time: `python scripts/init-clients-db.py`
2. Store `clients.db` in persistent volume (not ephemeral)
3. Back up regularly: daily backup to cloud storage
4. Monitor database file size (set alert at 1GB)

### Monitoring
Track these metrics:
- Daily P&L by tier (revenue correlation)
- Tier conversion rate (upsell effectiveness)
- User retention (inactive users after 30 days)
- Database file size (storage planning)

## License

Part of ProfitEngine v5. See LICENSE in project root.
