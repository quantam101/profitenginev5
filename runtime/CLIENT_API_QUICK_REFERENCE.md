# Client API — Quick Reference

## API Endpoints Summary

All endpoints require `Authorization: Bearer <api-key>` except `/api/health`.

### Base URL
```
http://localhost:8001         (local)
https://runtime.alreadyhere.com  (production)
```

---

## Health Check (No Auth)

```bash
curl http://localhost:8001/api/health
```

**Response:**
```json
{"ok": true, "service": "client-api", "version": "1.0.0"}
```

---

## Aggregate Stats

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8001/api/clients/stats?days=30"
```

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

## Leaderboard

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8001/api/clients/leaderboard?metric=pnl&limit=5&days=30"
```

**Metrics:** `win_rate` | `pnl` | `days_active` | `total_trades`

**Response:**
```json
{
  "metric": "pnl",
  "entries": [
    {
      "rank": 1,
      "user_id": "user_42",
      "username": "john_trader",
      "metric_value": 5450.25,
      "secondary_value": 72.5,
      "days_active": 45,
      "account_age_days": 45
    }
  ],
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

## Upsell Candidates

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8001/api/clients/upsell-candidates?days=30"
```

**Response:**
```json
{
  "count": 3,
  "candidates": [
    {
      "user_id": "user_99",
      "username": "power_trader",
      "current_pnl": 5200.00,
      "win_rate": 68.5,
      "total_trades": 78,
      "days_active": 35,
      "potential_value": 13000.00,
      "urgency": "high"
    }
  ],
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

## Individual Trader Performance

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8001/api/clients/user_42?days=30"
```

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

## Daily Summary

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8001/api/clients/daily-summary?limit=50"
```

**Response:**
```json
{
  "date": "2026-06-18",
  "total_trades": 342,
  "trades_by_user": {
    "user_42": 28,
    "user_18": 15
  },
  "total_pnl": 6850.25,
  "pnl_by_user": {
    "user_42": 1250.00,
    "user_18": 850.50
  },
  "top_symbol": "AAPL",
  "win_rate": 61.4,
  "active_users": 42,
  "recent_trades": [...],
  "timestamp": "2026-06-18T14:30:00Z"
}
```

---

## Error Responses

### 401 Unauthorized
```json
{"error": "Missing authorization header"}
```

### 403 Forbidden
```json
{"error": "Invalid API key"}
```

### 404 Not Found
```json
{"error": "Trader user_xyz not found"}
```

### 429 Rate Limited
```json
{"error": "Rate limit exceeded", "limit": 100, "window": 3600}
```

---

## Query Parameters

| Endpoint | Parameter | Type | Default | Max | Example |
|----------|-----------|------|---------|-----|---------|
| `/api/clients/stats` | `days` | int | 30 | 365 | `?days=90` |
| `/api/clients/leaderboard` | `metric` | string | `win_rate` | - | `?metric=pnl` |
| `/api/clients/leaderboard` | `limit` | int | 10 | 100 | `?limit=5` |
| `/api/clients/leaderboard` | `days` | int | 30 | 365 | `?days=90` |
| `/api/clients/upsell-candidates` | `days` | int | 30 | 365 | `?days=60` |
| `/api/clients/{user_id}` | `days` | int | 30 | 365 | `?days=90` |
| `/api/clients/daily-summary` | `limit` | int | 50 | 500 | `?limit=100` |

---

## Python Client Usage

```python
import httpx

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8001"

async def get_stats():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/clients/stats?days=30",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        return response.json()

# Run
stats = asyncio.run(get_stats())
print(f"Active traders: {stats['active_traders']}")
```

---

## JavaScript/TypeScript Usage

```javascript
const API_KEY = process.env.PROFITENGINE_CLIENT_API_KEY;
const BASE_URL = process.env.PROFITENGINE_CLIENT_API_URL;

async function getStats() {
  const response = await fetch(
    `${BASE_URL}/api/clients/stats?days=30`,
    {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
}

// Use in React
const [stats, setStats] = useState(null);

useEffect(() => {
  getStats().then(setStats);
}, []);
```

---

## Rate Limiting

- **Limit:** 100 requests/hour per API key
- **Identifier:** API key (hashed for privacy)
- **Response:** HTTP 429 when exceeded
- **Reset:** 1 hour sliding window

---

## Environment Variables

```bash
# Required
CLIENT_API_KEY_HASH=<sha256-hash>
CLIENT_API_WEBHOOK_SECRET=<secret>
CLIENTS_DB_PATH=/path/to/clients.db

# Optional
CLIENT_API_HOST=0.0.0.0
CLIENT_API_PORT=8001
ENVIRONMENT=production
DEBUG=false
```

---

## Configuration

Generate API key hash:

```bash
python3 -c "import hashlib; api_key='your-secure-key'; print(hashlib.sha256(api_key.encode()).hexdigest())"
```

---

## Testing

```bash
# Health check
curl http://localhost:8001/api/health

# Get stats (requires valid API key)
API_KEY="your-key"
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8001/api/clients/stats

# Test rate limiting (101+ requests)
for i in {1..105}; do 
  curl -s -H "Authorization: Bearer $API_KEY" \
    http://localhost:8001/api/clients/stats > /dev/null
  echo "Request $i"
done
```

---

## Common Use Cases

### 1. Display Stats on Homepage

```javascript
const stats = await getStats();
return (
  <div>
    <h2>{stats.total_traders} Traders</h2>
    <p>{stats.avg_win_rate}% Avg Win Rate</p>
    <p>${stats.total_pnl} Total P&L</p>
  </div>
);
```

### 2. Auto-Generate Daily Blog Post

```python
summary = await get_daily_summary()
post = f"""
# Trading Report — {summary['date']}
{summary['total_trades']} trades, ${summary['total_pnl']} P&L
{summary['win_rate']}% win rate
"""
```

### 3. Find Premium Upgrade Targets

```python
candidates = await get_upsell_candidates()
high_value = [c for c in candidates['candidates'] 
              if c['urgency'] == 'high']
```

### 4. Show Top Traders Widget

```javascript
const board = await getLeaderboard('pnl', 5);
return (
  <ul>
    {board.entries.map(trader => (
      <li key={trader.user_id}>
        #{trader.rank} {trader.username}: ${trader.metric_value}
      </li>
    ))}
  </ul>
);
```

---

## Support & Troubleshooting

### "Invalid API key"
- Verify key matches `CLIENT_API_KEY_HASH` hash
- Regenerate hash if needed

### "Rate limit exceeded"
- Wait 1 hour or batch requests
- Use caching to reduce calls

### "Trader not found"
- Verify user_id exists in database
- User must have at least one trade

### "Database connection failed"
- Check `CLIENTS_DB_PATH` exists
- Verify file permissions (readable)

### API not responding
- Check systemd status: `systemctl status profitengine-client-api`
- Check firewall: `sudo ufw status`
- Verify port is listening: `netstat -tlnp | grep 8001`

---

## Files Overview

| File | Purpose |
|------|---------|
| `runtime/client_api.py` | Main API implementation |
| `runtime/client_api_integration.py` | Client library + examples |
| `runtime/CLIENT_API_README.md` | Full documentation |
| `runtime/CLIENT_API_DEPLOYMENT.md` | Deployment guide |
| `runtime/client_api_config.example.env` | Config template |
| `tests/test_client_api.py` | Test suite |

---

## License

Proprietary — ProfitEngine v5. All rights reserved.
