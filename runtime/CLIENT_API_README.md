# ProfitEngine Client API

REST API for querying client trading data from `clients.db`. Enables other repos (profitengine-tau, content, etc.) to access real-time trading statistics, leaderboards, performance metrics, and upsell opportunities.

## Features

- **Aggregate Stats** — Total traders, active traders, average win rate, total P&L
- **Leaderboards** — Top traders by win rate, P&L, days active, or trade count
- **Upsell Candidates** — Identify clients ready for premium tier upgrade
- **Individual Performance** — Detailed metrics per trader (trades, P&L, streaks, etc.)
- **Daily Summary** — Today's trading activity aggregated by user and symbol
- **Rate Limiting** — 100 requests/hour per API key
- **CORS Enabled** — Works across repos (profitengine-tau, content, etc.)
- **Authentication** — Bearer token validation with HMAC

## Quick Start

### 1. Environment Setup

```bash
# In your .env file (backend or OCI server)

# API Key (store hash in production)
CLIENT_API_KEY_HASH=<sha256-hash-of-your-api-key>

# Webhook Secret (for signature verification)
CLIENT_API_WEBHOOK_SECRET=<random-secure-string>

# Database path
CLIENTS_DB_PATH=/path/to/clients.db

# (Optional) Seed API key for local development
PROFITENGINE_CLIENT_API_KEY=dev-key-change-in-production
```

### 2. Generate API Key Hash

```python
import hashlib

# Your actual API key (share with client repos)
api_key = "your-secure-random-key"

# Hash to store in backend .env
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
print(f"CLIENT_API_KEY_HASH={key_hash}")
```

### 3. Start the API Server

```bash
# Option A: Run as FastAPI app directly
python -m runtime.client_api

# Option B: Start with uvicorn
uvicorn runtime.client_api:app --host 0.0.0.0 --port 8001

# Option C: Include in existing backend server
# In backend/server.py:
# from runtime.client_api import app as client_api_app
# app.include_router(client_api_app.router)
```

### 4. Verify Health Check (no auth)

```bash
curl http://localhost:8001/api/health
```

Response:
```json
{
  "ok": true,
  "service": "client-api",
  "version": "1.0.0",
  "timestamp": "2026-06-18T14:30:00Z",
  "db_ready": true
}
```

## API Endpoints

All endpoints (except `/api/health`) require Bearer token authentication.

### Headers

```
Authorization: Bearer <api-key>
Content-Type: application/json
```

### Rate Limiting

- **Limit:** 100 requests/hour per API key
- **Response on limit exceeded:** HTTP 429
- **Header:** `X-RateLimit-Remaining`

---

## Endpoints

### 1. Health Check (No Auth)

```
GET /api/health
```

Check API readiness and database status.

**Response:**
```json
{
  "ok": true,
  "service": "client-api",
  "version": "1.0.0",
  "timestamp": "2026-06-18T14:30:00Z",
  "db_ready": true
}
```

---

### 2. Aggregate Stats

```
GET /api/clients/stats?days=30
```

Get system-wide trading statistics.

**Query Parameters:**
- `days` (int, 1-365): Rolling window days (default: 30)

**Response:**
```json
{
  "total_traders": 245,
  "active_traders": 187,
  "avg_win_rate": 54.3,
  "total_pnl": 12450.50,
  "total_trades": 3421,
  "avg_trades_per_trader": 14.0,
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

### 3. Leaderboard

```
GET /api/clients/leaderboard?metric=win_rate&limit=10&days=30
```

Get ranked traders by specified metric.

**Query Parameters:**
- `metric` (string): `win_rate` | `pnl` | `days_active` | `total_trades` (default: `win_rate`)
- `limit` (int, 1-100): Number of top traders to return (default: 10)
- `days` (int, 1-365): Rolling window days (default: 30)

**Response:**
```json
{
  "metric": "win_rate",
  "entries": [
    {
      "rank": 1,
      "user_id": "user_42",
      "username": "john_trader",
      "metric_value": 72.5,
      "secondary_value": 3450.25,
      "days_active": 45,
      "account_age_days": 45
    },
    {
      "rank": 2,
      "user_id": "user_18",
      "username": "jane_pro",
      "metric_value": 68.3,
      "secondary_value": 2890.75,
      "days_active": 60,
      "account_age_days": 60
    }
  ],
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

### 4. Upsell Candidates

```
GET /api/clients/upsell-candidates?days=30
```

Identify high-performing traders ready for premium tier upgrade.

**Query Parameters:**
- `days` (int, 1-365): Rolling window days (default: 30)

**Response:**
```json
{
  "count": 5,
  "candidates": [
    {
      "user_id": "user_99",
      "username": "power_trader",
      "current_pnl": 5200.00,
      "win_rate": 68.5,
      "total_trades": 78,
      "days_active": 35,
      "recommendation": "Ready for premium: 78 trades, 68.5% win rate",
      "potential_value": 13000.00,
      "urgency": "high"
    },
    {
      "user_id": "user_67",
      "username": "steady_earner",
      "current_pnl": 2100.00,
      "win_rate": 62.0,
      "total_trades": 42,
      "days_active": 28,
      "recommendation": "Ready for premium: 42 trades, 62.0% win rate",
      "potential_value": 5250.00,
      "urgency": "medium"
    }
  ],
  "timestamp": "2026-06-18T14:30:00Z"
}
```

**Urgency Levels:**
- `high`: Score > 0.75 (very qualified)
- `medium`: Score 0.5-0.75 (qualified)
- `low`: Score < 0.5 (developing)

---

### 5. Individual Trader Performance

```
GET /api/clients/{user_id}?days=30
```

Get detailed performance metrics for a single trader.

**Path Parameters:**
- `user_id` (string): Trader ID

**Query Parameters:**
- `days` (int, 1-365): Rolling window days (default: 30)

**Response:**
```json
{
  "user_id": "user_42",
  "username": "john_trader",
  "total_trades": 125,
  "winning_trades": 87,
  "losing_trades": 38,
  "win_rate": 69.6,
  "total_pnl": 4250.50,
  "avg_win": 65.30,
  "avg_loss": -45.20,
  "largest_win": 450.00,
  "largest_loss": -200.00,
  "consecutive_wins": 5,
  "consecutive_losses": 0,
  "days_active": 45,
  "account_created": "2026-05-04T10:30:00Z",
  "last_trade": "2026-06-18T14:15:00Z",
  "current_streak": "winning",
  "account_status": "active"
}
```

---

### 6. Daily Summary

```
GET /api/clients/daily-summary?limit=50
```

Get today's aggregated trading activity.

**Query Parameters:**
- `limit` (int, 1-500): Max recent trades to include (default: 50)

**Response:**
```json
{
  "date": "2026-06-18",
  "total_trades": 342,
  "trades_by_user": {
    "user_42": 28,
    "user_18": 15,
    "user_99": 22,
    ...
  },
  "total_pnl": 6850.25,
  "pnl_by_user": {
    "user_42": 1250.00,
    "user_18": 850.50,
    "user_99": 2100.75,
    ...
  },
  "top_symbol": "AAPL",
  "win_rate": 61.4,
  "active_users": 42,
  "recent_trades": [
    {
      "trade_id": "trade_abc123",
      "user_id": "user_42",
      "symbol": "AAPL",
      "side": "BUY",
      "entry_price": 192.50,
      "exit_price": 195.75,
      "shares": 10,
      "pnl": 325.00,
      "pnl_percent": 1.69,
      "entry_time": "2026-06-18T09:30:00Z",
      "exit_time": "2026-06-18T14:15:00Z",
      "status": "closed"
    }
  ],
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

## Error Handling

All error responses include timestamp and status code.

**401 Unauthorized:**
```json
{
  "error": "Missing authorization header",
  "status_code": 401,
  "timestamp": "2026-06-18T14:30:00Z"
}
```

**403 Forbidden:**
```json
{
  "error": "Invalid API key",
  "status_code": 403,
  "timestamp": "2026-06-18T14:30:00Z"
}
```

**404 Not Found:**
```json
{
  "error": "Trader user_xyz not found",
  "status_code": 404,
  "timestamp": "2026-06-18T14:30:00Z"
}
```

**429 Rate Limit:**
```json
{
  "error": "Rate limit exceeded",
  "limit": 100,
  "window": 3600,
  "status_code": 429,
  "timestamp": "2026-06-18T14:30:00Z"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "detail": "Connection to database failed",
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

## Integration Examples

### profitengine-tau (Frontend)

```javascript
// In Next.js API route or component

const getStats = async () => {
  const response = await fetch(
    'https://your-runtime-api.com/api/clients/stats?days=30',
    {
      headers: {
        'Authorization': `Bearer ${process.env.CLIENT_API_KEY}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return response.json();
};

export default async function StatsDisplay() {
  const stats = await getStats();
  return (
    <div>
      <h2>Community Stats</h2>
      <p>Active Traders: {stats.active_traders}</p>
      <p>Avg Win Rate: {stats.avg_win_rate}%</p>
      <p>Total P&L: ${stats.total_pnl.toLocaleString()}</p>
    </div>
  );
}
```

### Content Blog (Daily Post Auto-Generation)

```python
# In content repo CI/CD workflow

import httpx

async def generate_daily_post():
    # Fetch data
    response = await httpx.get(
        'https://your-runtime-api.com/api/clients/daily-summary',
        headers={'Authorization': f'Bearer {API_KEY}'},
    )
    summary = response.json()
    
    # Generate markdown
    post = f"""
# Daily Trading Report — {summary['date']}

{summary['total_trades']} trades executed
${summary['total_pnl']:,.2f} total P&L
{summary['win_rate']}% win rate
    """
    
    # Publish to GitHub content repo
    ...
```

### Sales Engine (Upsell Automation)

```python
# Identify candidates for premium sales outreach

import httpx

async def get_sales_targets():
    response = await httpx.get(
        'https://your-runtime-api.com/api/clients/upsell-candidates?days=30',
        headers={'Authorization': f'Bearer {API_KEY}'},
    )
    candidates = response.json()['candidates']
    
    # Filter high-urgency only
    high_urgency = [c for c in candidates if c['urgency'] == 'high']
    
    # Send to CRM
    for candidate in high_urgency:
        send_to_crm(candidate['user_id'], candidate['potential_value'])
```

---

## Database Schema

The API queries SQLite tables:

### `clients` table

```sql
CREATE TABLE clients (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    email TEXT UNIQUE,
    account_created TEXT NOT NULL,
    account_status TEXT DEFAULT 'active',
    tier TEXT DEFAULT 'free'
);
```

### `trades` table

```sql
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
```

### `trader_stats` table (cache)

```sql
CREATE TABLE trader_stats (
    user_id TEXT PRIMARY KEY,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_pnl REAL,
    win_rate REAL,
    days_active INTEGER,
    last_updated TEXT,
    FOREIGN KEY (user_id) REFERENCES clients(user_id)
);
```

---

## Performance Notes

- Leaderboards with `limit > 50` may take 1-2 seconds
- Daily summary on high-volume days (1000+ trades) may take 2-3 seconds
- Use caching in calling services (5-minute cache for stats/leaderboards recommended)
- Rate limit is 100 requests/hour per key — plan batch requests accordingly

---

## Deployment Checklist

- [ ] Generate secure API key and hash
- [ ] Set `CLIENT_API_KEY_HASH` in backend `.env`
- [ ] Set `CLIENT_API_WEBHOOK_SECRET` for webhook verification
- [ ] Seed database with client and trade data
- [ ] Test `/api/health` endpoint
- [ ] Verify rate limiting works (test with 101+ rapid requests)
- [ ] Configure CORS origins if restricting access
- [ ] Add API key to profitengine-tau `.env`
- [ ] Add API key to content repo secrets
- [ ] Monitor API logs for errors and performance
- [ ] Set up alerting if endpoint response time > 5s

---

## Troubleshooting

**"Missing authorization header"**
- Ensure all requests include: `Authorization: Bearer <key>`

**"Invalid API key"**
- Verify API key hash matches `CLIENT_API_KEY_HASH` env var
- Regenerate hash: `hashlib.sha256(api_key.encode()).hexdigest()`

**"Rate limit exceeded"**
- Wait 1 hour or upgrade rate limit in `client_api.py`
- Batch multiple requests into single calls when possible

**"Database connection failed"**
- Verify `CLIENTS_DB_PATH` is correct and database file exists
- Check file permissions (should be readable by API process)

**"Trader not found"**
- Verify user_id exists in `clients` table
- Check that user has at least one trade in `trades` table

---

## License

Proprietary — ProfitEngine v5
