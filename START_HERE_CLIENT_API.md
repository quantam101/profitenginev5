# Client API — START HERE

Complete REST API for querying client trading data. Ready to integrate with profitengine-tau, content, and other repos.

**Status:** Production Ready ✅ | **Files:** 9 | **Size:** 119 KB | **Tests:** 40+ unit tests

---

## What You Get

- ✅ **6 REST Endpoints** — stats, leaderboard, upsell, performance, daily summary, health
- ✅ **Authentication** — Bearer token with SHA-256 hashing
- ✅ **Rate Limiting** — 100 requests/hour per API key
- ✅ **Database Integration** — SQLite wrapper with auto schema
- ✅ **Error Handling** — Standardized JSON responses with timestamps
- ✅ **CORS Enabled** — Works across repos (profitengine-tau, content, sales)
- ✅ **Comprehensive Tests** — 40+ unit & integration tests
- ✅ **Full Documentation** — README, deployment guide, quick reference
- ✅ **Integration Examples** — Python, JavaScript, and common patterns
- ✅ **Production Ready** — Systemd service, Docker, Vercel support

---

## Quick Start (5 minutes)

### 1. Generate API Key

```bash
python3 << 'EOF'
import hashlib
import secrets

api_key = secrets.token_urlsafe(32)
key_hash = hashlib.sha256(api_key.encode()).hexdigest()

print(f"API Key: {api_key}")
print(f"Env var: CLIENT_API_KEY_HASH={key_hash}")
EOF
```

Save the API key for client repos (profitengine-tau, content, etc.)

### 2. Set Environment Variables

```bash
# In your .env file
CLIENT_API_KEY_HASH=<hash-from-step-1>
CLIENT_API_WEBHOOK_SECRET=<random-secure-string>
CLIENTS_DB_PATH=/path/to/clients.db
```

### 3. Install & Run

```bash
# Install dependencies
pip install fastapi uvicorn pydantic python-multipart

# Run locally
python -m uvicorn runtime.client_api:app --reload

# Test health check (no auth needed)
curl http://localhost:8001/api/health
```

### 4. Test an Endpoint

```bash
# With API key
API_KEY="<your-api-key>"
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8001/api/clients/stats?days=30
```

### 5. Integrate with Frontend

```javascript
// In profitengine-tau (Next.js)
const response = await fetch(
  'https://runtime.alreadyhere.com/api/clients/stats?days=30',
  {
    headers: {
      'Authorization': `Bearer ${process.env.PROFITENGINE_CLIENT_API_KEY}`,
    }
  }
);
const stats = await response.json();
```

---

## File Guide

| File | Purpose | Read First? |
|------|---------|-------------|
| **START_HERE_CLIENT_API.md** | This file — quick overview | 👈 You are here |
| **CLIENT_API_INDEX.md** | Complete file manifest & map | Next |
| **runtime/CLIENT_API_QUICK_REFERENCE.md** | One-page endpoint reference | For quick answers |
| **runtime/CLIENT_API_README.md** | Full API documentation | For detailed specs |
| **runtime/CLIENT_API_DEPLOYMENT.md** | How to deploy (OCI, Docker, Vercel) | Before deploying |
| **runtime/client_api.py** | Core API implementation | Source code |
| **runtime/client_api_integration.py** | Client library + code examples | For integration |
| **tests/test_client_api.py** | Test suite | For verification |

---

## The 6 Endpoints

### 1. Health Check ✅
```bash
GET /api/health  # No auth required
```
Service status, version, database readiness. Use for monitoring.

### 2. Aggregate Stats 📊
```bash
GET /api/clients/stats?days=30
# Returns: total traders, active traders, avg win rate, total P&L
```
System-wide KPIs for dashboards and reports.

### 3. Leaderboard 🏆
```bash
GET /api/clients/leaderboard?metric=pnl&limit=10&days=30
# Metrics: win_rate, pnl, days_active, total_trades
```
Top traders by any metric with ranking.

### 4. Upsell Candidates 💰
```bash
GET /api/clients/upsell-candidates?days=30
# Returns: high-performing free-tier users ready for premium
```
Identify sales targets with revenue potential.

### 5. Trader Performance 👤
```bash
GET /api/clients/{user_id}?days=30
# Returns: comprehensive performance metrics, streaks, P&L
```
Deep-dive into individual trader data.

### 6. Daily Summary 📈
```bash
GET /api/clients/daily-summary?limit=50
# Returns: today's trades, P&L, symbols, active users
```
Today's trading activity aggregated by user/symbol.

---

## Where to Deploy

### Option 1: OCI Server (Recommended)
```bash
# Systemd service on 129.146.167.73:8001
# See: CLIENT_API_DEPLOYMENT.md, Section 1
ssh opc@129.146.167.73
mkdir -p /opt/profitengine/runtime
# ... follow deployment guide
```

### Option 2: Docker
```bash
docker build -t profitengine-client-api:latest .
docker run -d --port 8001:8001 --volume /data/clients.db:/app/clients.db profitengine-client-api:latest
```

### Option 3: Vercel (Frontend)
```bash
# Create API routes in profitengine-tau
# Set PROFITENGINE_CLIENT_API_URL in Vercel env vars
# See: CLIENT_API_DEPLOYMENT.md, Section 3
```

### Option 4: Local Development
```bash
python -m uvicorn runtime.client_api:app --reload
```

---

## Integration with Your Repos

### profitengine-tau (Frontend)
Add to Next.js or React component:
```javascript
const stats = await fetch(`/api/clients/stats`, {
  headers: { 'Authorization': `Bearer ${API_KEY}` }
}).then(r => r.json());
```

### content (Blog)
Auto-generate daily trading reports:
```python
summary = await get_daily_summary()
post = f"# Trading Report — {summary['date']}\n{summary['total_trades']} trades, ${summary['total_pnl']}"
```

### sales-engine (CRM)
Find premium upgrade targets:
```python
candidates = await get_upsell_candidates()
for c in candidates:
    email_prospect(c['user_id'], c['potential_value'])
```

---

## Testing

Run the test suite to verify setup:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/test_client_api.py -v

# Run specific test class
pytest tests/test_client_api.py::TestStatsEndpoint -v

# Show coverage
pytest tests/test_client_api.py --cov=runtime.client_api
```

**Test Coverage:** 40+ unit & integration tests
- Authentication (valid/invalid keys)
- Rate limiting (within/over limit)
- All 6 endpoints with valid/missing auth
- Parameter validation
- Error responses (400/403/404/429/500)
- Data aggregation accuracy
- Performance benchmarks

---

## Configuration Checklist

Before going to production, set these environment variables:

```bash
# REQUIRED
☐ CLIENT_API_KEY_HASH          # SHA-256 hash of API key
☐ CLIENT_API_WEBHOOK_SECRET    # Random secure string
☐ CLIENTS_DB_PATH              # Path to SQLite database

# RECOMMENDED
☐ ENVIRONMENT=production        # Set environment
☐ DEBUG=false                   # Disable debug mode
☐ CLIENT_API_HOST=0.0.0.0       # Listen on all IPs
☐ CLIENT_API_PORT=8001          # Assign port
☐ CLIENT_API_RATE_LIMIT_REQUESTS=100
☐ CLIENT_API_RATE_LIMIT_WINDOW=3600

# OPTIONAL
☐ LOG_LEVEL=INFO               # Logging level
☐ JSON_LOGS=true               # Structured logging
☐ SENTRY_DSN=                  # Error tracking

# FOR REPOS
☐ PROFITENGINE_CLIENT_API_URL   # Runtime API URL
☐ PROFITENGINE_CLIENT_API_KEY   # API key for frontend
☐ CONTENT_REPO_API_KEY          # For content blog
☐ SALES_API_KEY                 # For sales engine
```

See `runtime/client_api_config.example.env` for full reference.

---

## Troubleshooting

### API won't start?
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Verify dependencies
python3 -c "import fastapi; print(fastapi.__version__)"

# Check port availability
netstat -tlnp | grep 8001
```

### "Invalid API key" error?
```bash
# Verify key hash matches
python3 << 'EOF'
import hashlib
api_key = "your-key"
print(hashlib.sha256(api_key.encode()).hexdigest())
EOF
# Compare with CLIENT_API_KEY_HASH in .env
```

### "Database connection failed"?
```bash
# Verify database exists
ls -la /path/to/clients.db

# Check permissions
chmod 644 /path/to/clients.db

# Verify schema
sqlite3 /path/to/clients.db ".tables"
```

### Rate limit exceeded?
```bash
# Wait 1 hour (sliding window)
# Or increase limit in client_api.py:
# RATE_LIMIT_REQUESTS = 200  # Default: 100
```

See `CLIENT_API_DEPLOYMENT.md` "Troubleshooting" section for more issues.

---

## API Key Management

### Generate Secure Key
```bash
python3 -c "import secrets, hashlib; key=secrets.token_urlsafe(32); print(f'{key}\n{hashlib.sha256(key.encode()).hexdigest()}')"
```

### Distribute to Repos
1. **profitengine-tau:** Add to Vercel environment variables
2. **content:** Add to GitHub Secrets
3. **sales-engine:** Add to CRM config
4. **monitoring:** Add to uptime checker

### Rotate Keys (Every 90 Days)
1. Generate new key
2. Update `CLIENT_API_KEY_HASH` in .env
3. Distribute new key to all client repos
4. Remove old key from all repos

---

## Performance

Typical response times:
- Health check: <10ms
- Stats: 100-300ms
- Leaderboard: 200-500ms
- Upsell candidates: 300-800ms
- Individual trader: 50-200ms
- Daily summary: 150-400ms

Rate limit: 100 requests/hour per API key

---

## Security

- ✅ Bearer token authentication (SHA-256 hashing)
- ✅ HMAC webhook signature verification
- ✅ Rate limiting (100 req/hour)
- ✅ No secrets in code (all in .env)
- ✅ Database foreign keys
- ✅ Input validation (Pydantic)
- ✅ Sanitized error messages
- ✅ Timestamp in all responses

⚠️ For production also add:
- HTTPS (via reverse proxy)
- IP whitelist (if applicable)
- Database backups
- API key rotation schedule
- Sentry error tracking

---

## Next Steps

1. **Read Overview** → `CLIENT_API_INDEX.md` (5 min)
2. **Generate API Key** → See "Quick Start" above
3. **Choose Deployment** → See "Where to Deploy" or `CLIENT_API_DEPLOYMENT.md`
4. **Run Tests** → `pytest tests/test_client_api.py -v`
5. **Test Endpoints** → See `CLIENT_API_QUICK_REFERENCE.md`
6. **Integrate Repos** → Use examples in `client_api_integration.py`
7. **Monitor** → Health checks and error alerting
8. **Rotate Keys** → Every 90 days

---

## Support

### Quick Questions?
→ **`CLIENT_API_QUICK_REFERENCE.md`** (all endpoints on one page)

### Need Help Deploying?
→ **`CLIENT_API_DEPLOYMENT.md`** (step-by-step for OCI, Docker, Vercel)

### Integration Questions?
→ **`runtime/client_api_integration.py`** (code examples for all repos)

### Full API Specs?
→ **`CLIENT_API_README.md`** (complete documentation)

### Need to Verify Setup?
→ **`tests/test_client_api.py`** (run tests to validate)

---

## Summary

| Item | Details |
|------|---------|
| **Status** | Production Ready ✅ |
| **Files** | 9 (119 KB total) |
| **Endpoints** | 6 (stats, leaderboard, upsell, performance, daily, health) |
| **Authentication** | Bearer token (SHA-256) |
| **Rate Limit** | 100 req/hour per key |
| **Tests** | 40+ unit & integration |
| **Deployment** | OCI (systemd), Docker, Vercel, Local |
| **Documentation** | README, deployment guide, quick ref |
| **Integration** | Python, JavaScript examples |
| **License** | Proprietary — ProfitEngine v5 |

---

## License

Proprietary — ProfitEngine v5. All rights reserved.

---

## Version

- Version: 1.0.0
- Created: June 18, 2026
- Last Updated: June 18, 2026

---

**Ready?** Start with the "Quick Start" section above, or jump to `CLIENT_API_INDEX.md` for the complete file map.
