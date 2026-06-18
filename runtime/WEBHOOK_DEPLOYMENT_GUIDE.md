# Robinhood Webhook Handler — Production Deployment Guide

## Quick Start

### 1. Copy & Configure

```bash
cd runtime/

# Copy webhook handler
cp robinhood_webhook_handler.py runtime/

# Create environment file
cp robinhood_webhook.example.env .env
# Edit .env and fill in ROBINHOOD_WEBHOOK_SECRET
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn pydantic
```

### 3. Run Webhook Handler

**Option A: Standalone (testing)**

```bash
uvicorn robinhood_webhook_handler:app --host 127.0.0.1 --port 8001
```

**Option B: Production (with main API)**

In `runtime/api.py`:

```python
from robinhood_webhook_handler import app as webhook_app

# Mount at /webhooks
app.include_router(webhook_app.router, prefix="/webhooks")
```

Then start main API as usual — webhook endpoints available at `http://localhost:8000/webhooks/...`

### 4. Register with Robinhood

Contact Robinhood API support and provide:

```
Webhook URL: https://yourdomain.com/webhooks/webhook/robinhood
Webhook Secret: [from ROBINHOOD_WEBHOOK_SECRET env var]
Events: order_filled, order_partially_filled, position_closed, account_balance_changed, margin_call
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       ROBINHOOD API                             │
│                 (Trade Execution Engine)                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ POST /webhook
                          │ (trade executed, position closed)
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│            WEBHOOK HANDLER (FastAPI on Port 8001)               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. RECEIVE REQUEST                                        │  │
│  │    ├─ Get X-Robinhood-Signature header                   │  │
│  │    ├─ Get X-Robinhood-Timestamp header                   │  │
│  │    └─ Read raw JSON payload                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 2. VALIDATE SECURITY                                      │  │
│  │    ├─ Verify HMAC-SHA256 signature ✓                     │  │
│  │    ├─ Check timestamp freshness (replay attack) ✓         │  │
│  │    └─ Verify event_id not already processed ✓            │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 3. ROUTE EVENT (by event_type)                            │  │
│  │    ├─ order_filled → _handle_order_filled()              │  │
│  │    ├─ position_closed → _handle_position_closed()        │  │
│  │    ├─ account_balance_changed → _handle_balance_changed()│  │
│  │    ├─ margin_call_warning → _handle_margin_warning()     │  │
│  │    └─ margin_call → _handle_margin_call()                │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 4. UPDATE DATABASE (transactional)                         │  │
│  │    ├─ Record in webhook_events (idempotency log)         │  │
│  │    ├─ Update trade_log with P&L                          │  │
│  │    ├─ Record balance_history                             │  │
│  │    └─ Create alerts (if thresholds crossed)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 5. TRIGGER ALERTS                                         │  │
│  │    ├─ Daily loss > $100 → CIRCUIT BREAKER                │  │
│  │    ├─ Daily gain > $500 → LOCK PROFITS                   │  │
│  │    ├─ Win rate drop < 45% → WARNING                      │  │
│  │    ├─ Margin warning → Email/SMS/Telegram                │  │
│  │    └─ Margin call → CRITICAL / IMMEDIATE ACTION          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 6. BROADCAST UPDATES (async)                              │  │
│  │    ├─ WebSocket → Mobile Dashboard (real-time)           │  │
│  │    ├─ Telegram → Chat notification                        │  │
│  │    └─ Email → Alert inbox                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  RETURN 202 ACCEPTED (processes in background)                  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SQLite3 (clients.db)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ webhook_events      — Event deduplication log            │  │
│  │ trade_log           — Trades with real-time P&L          │  │
│  │ balance_history     — Account balance changes            │  │
│  │ alerts              — Triggered alerts & thresholds      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  REAL-TIME CONSUMERS                             │
│  ├─ Mobile Dashboard (WebSocket feed)                           │
│  ├─ Telegram Bot (alerts)                                       │
│  ├─ Email Notifications (digest)                                │
│  └─ Analytics Engine (P&L tracking)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Event Processing Flow

### Order Filled Event

```
Robinhood: "AAPL 10 shares bought at $150.25"
                    ↓
Webhook Handler:
  1. Verify signature (HMAC-SHA256)
  2. Check timestamp (not replayed)
  3. Check event_id (not duplicate)
  4. Insert into trade_log:
     - trade_id = order_id
     - symbol = "AAPL"
     - side = "buy"
     - entry_price = 150.25
     - quantity = 10
     - status = "filled"
                    ↓
Database:
  trade_log row:
    trade_id: ord_12345
    symbol: AAPL
    quantity: 10
    entry_price: 150.25
    entry_time: 2026-06-18T14:30:00Z
    status: filled
                    ↓
Mobile Dashboard:
  Real-time update: "AAPL +10 @ $150.25"
```

### Position Closed Event

```
Robinhood: "AAPL position closed, realized P&L +$12.50"
                    ↓
Webhook Handler:
  1. Verify signature & timestamp
  2. Find open trade with matching symbol
  3. Update trade_log:
     - exit_price = 151.50
     - exit_time = now()
     - pnl = 12.50
     - status = "closed"
  4. Check win/loss alerts:
     - If daily_pnl < -$100 → CIRCUIT BREAKER
     - If daily_pnl > $500 → LOCK PROFITS
     - If win_rate < 45% → WARNING
                    ↓
Database:
  trade_log row updated:
    exit_price: 151.50
    exit_time: 2026-06-18T15:00:00Z
    pnl: 12.50
    status: closed
  
  Daily stats recalculated:
    total_trades: 5
    winning_trades: 3
    win_rate: 60%
                    ↓
Alerts Generated:
  none (all thresholds healthy)
                    ↓
Mobile Dashboard:
  Real-time update: "AAPL -10 @ $151.50 | P&L +$12.50"
```

### Margin Call Warning

```
Robinhood: "Margin usage at 80%, cash remaining $500"
                    ↓
Webhook Handler:
  1. Create CRITICAL alert
  2. Record in alerts table
  3. Push to WebSocket
  4. Send SMS/Telegram
                    ↓
Database:
  alerts row:
    alert_type: margin_warning
    severity: critical
    message: "Margin warning - usage 80%, cash $500 remaining"
    triggered_at: 2026-06-18T14:30:00Z
                    ↓
Mobile Dashboard:
  Red alert banner: "MARGIN WARNING"
                    ↓
Telegram:
  @user: "🚨 MARGIN WARNING: 80% used, $500 cash left. Reduce positions immediately."
```

---

## Deployment Scenarios

### Scenario 1: Small Account (<$10k)

**Setup**: Single webhook handler on main API

```bash
# In runtime/api.py:
from robinhood_webhook_handler import app as webhook_app
app.include_router(webhook_app.router, prefix="/webhooks")

# Start:
uvicorn runtime.api:app --port 8000
```

**Expected load**: <10 webhooks/sec
**Database**: SQLite (clients.db)
**Latency**: 50-100ms
**Availability**: 99.5% uptime

---

### Scenario 2: Medium Account ($10k-$100k)

**Setup**: Separate webhook service + main API

```bash
# Terminal 1: Main API
uvicorn runtime.api:app --port 8000

# Terminal 2: Webhook Handler
uvicorn runtime.robinhood_webhook_handler:app --port 8001

# Production: Use reverse proxy
# nginx routes /webhooks to port 8001
```

**Expected load**: 10-100 webhooks/sec
**Database**: SQLite with WAL mode
**Latency**: 20-50ms
**Availability**: 99.9% uptime with health checks

---

### Scenario 3: Large Account (>$100k, High-Frequency)

**Setup**: Multi-instance webhook cluster

```bash
# Start 3 webhook instances behind load balancer
uvicorn robinhood_webhook_handler:app --port 8001
uvicorn robinhood_webhook_handler:app --port 8002
uvicorn robinhood_webhook_handler:app --port 8003

# nginx config (round-robin):
upstream webhook_backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}
```

**Expected load**: 100-1000 webhooks/sec
**Database**: SQLite with aggressive tuning (WAL, PRAGMA)
**Latency**: <50ms p99
**Availability**: 99.99% uptime with failover

---

## Security Checklist

- [ ] **Signature Validation**
  ```bash
  # Verify ROBINHOOD_WEBHOOK_SECRET is set
  echo $ROBINHOOD_WEBHOOK_SECRET
  ```

- [ ] **HTTPS Only**
  ```bash
  # Webhook URL must be HTTPS
  # curl -v https://yourdomain.com/webhooks/webhook/robinhood
  ```

- [ ] **Timestamp Verification**
  - Handler rejects webhooks > 5 minutes old
  - Prevents replay attacks

- [ ] **Idempotency**
  - Duplicate events (same event_id) are rejected
  - Safe for Robinhood to retry

- [ ] **Database Integrity**
  - All updates in transactions
  - No data loss on connection failure
  - Foreign key constraints enabled

- [ ] **Secrets Management**
  ```bash
  # NEVER commit secrets to git
  echo "ROBINHOOD_WEBHOOK_SECRET" >> .gitignore
  # Store in GitHub Secrets, env vars, or secret manager
  ```

---

## Monitoring & Observability

### Health Check

```bash
curl https://yourdomain.com/webhooks/webhook/status
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-06-18T14:30:00Z",
  "webhook_events": {
    "total": 1234,
    "last_hour": 42
  },
  "trades": {
    "total": 5678,
    "today": 15
  },
  "alerts": {
    "unacknowledged": 0
  }
}
```

### Database Monitoring

```bash
# Check recent events
sqlite3 clients.db "SELECT event_type, COUNT(*) FROM webhook_events GROUP BY event_type;"

# Check unacknowledged alerts
sqlite3 clients.db "SELECT alert_type, COUNT(*) FROM alerts WHERE acknowledged = 0 GROUP BY alert_type;"

# Check P&L for today
sqlite3 clients.db "SELECT SUM(pnl) FROM trade_log WHERE date(entry_time) = date('now');"
```

### Logging

```bash
# Tail webhook logs
tail -f /var/log/profitengine/webhook.log

# Search for errors
grep -i "error" /var/log/profitengine/webhook.log

# Count events by type
grep "Successfully processed" /var/log/profitengine/webhook.log | \
  sed 's/.*event: //' | sort | uniq -c
```

### Prometheus Metrics (Optional)

Add to `robinhood_webhook_handler.py`:

```python
from prometheus_client import Counter, Histogram

webhook_events_received = Counter(
    'webhook_events_received_total',
    'Total webhook events received',
    ['event_type']
)

webhook_latency_ms = Histogram(
    'webhook_latency_ms',
    'Webhook processing latency',
    buckets=[10, 25, 50, 100, 250, 500]
)

@app.post("/webhook/robinhood")
async def receive_robinhood_webhook(...):
    start = time.time()
    # ... process webhook ...
    latency_ms = (time.time() - start) * 1000
    webhook_latency_ms.observe(latency_ms)
    webhook_events_received.labels(event_type=payload.event_type).inc()
```

---

## Troubleshooting

### Webhook Not Received

**Check 1: URL Accessibility**

```bash
# From Robinhood's perspective:
curl -v https://yourdomain.com/webhooks/webhook/robinhood

# Should return 400 (missing headers), not 404 or connection refused
```

**Check 2: Firewall**

```bash
# Ensure inbound HTTPS (443) is open
sudo ufw allow 443/tcp

# Verify reverse proxy is running
ss -tulpn | grep :443
```

**Check 3: Handler Status**

```bash
# Is webhook handler running?
curl http://localhost:8001/webhook/status

# Check if route is registered
curl -v http://localhost:8001/webhook/robinhood
```

### Signature Validation Failed

**Check 1: Secret Mismatch**

```bash
# Verify secret matches what you registered with Robinhood
echo $ROBINHOOD_WEBHOOK_SECRET
# Should match: https://robinhood.com/settings/webhooks
```

**Check 2: Payload Encoding**

```bash
# Robinhood must send:
# X-Robinhood-Signature: HMAC-SHA256(timestamp.payload)
# X-Robinhood-Timestamp: ISO-8601-timestamp

# Test locally:
python test_robinhood_webhook.py
```

### Events Not Processed

**Check 1: Database Connectivity**

```bash
# Verify database file is writable
ls -la clients.db
chmod 666 clients.db

# Test write access
sqlite3 clients.db "INSERT INTO webhook_events (event_id, event_type, account_id, payload, processed_at) VALUES ('test_123', 'test', 'test', '{}', datetime('now'));"
```

**Check 2: Handler Logs**

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn robinhood_webhook_handler:app

# Check for exceptions
tail -f webhook.log | grep -i "exception\|error\|traceback"
```

### High Latency (>500ms)

**Check 1: Database Performance**

```bash
# Check for slow queries
sqlite3 clients.db "PRAGMA query_only = ON;"
sqlite3 clients.db ".timer ON"

# See which tables are large
sqlite3 clients.db "SELECT name, COUNT(*) FROM sqlite_master m, sqlite_master t WHERE m.type='table' GROUP BY name;"
```

**Check 2: Add Indices**

```bash
sqlite3 clients.db <<'EOF'
CREATE INDEX idx_event_id ON webhook_events(event_id);
CREATE INDEX idx_trade_user_date ON trade_log(user_id, date(entry_time));
CREATE INDEX idx_alert_unack ON alerts(user_id, acknowledged);
EOF
```

**Check 3: Enable WAL Mode**

```bash
sqlite3 clients.db <<'EOF'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
EOF
```

---

## Production Checklist

Before going live:

- [ ] Webhook secret configured in environment
- [ ] HTTPS enabled and working
- [ ] Signature validation tested
- [ ] Database backup strategy in place
- [ ] Monitoring/alerting configured
- [ ] Log aggregation enabled
- [ ] Health check endpoint working
- [ ] Webhook handler running (standalone or integrated)
- [ ] Load balancer configured (if using multiple instances)
- [ ] Database indices created
- [ ] Webhook retry logic tested
- [ ] Alert notification channels working
- [ ] Mobile dashboard WebSocket connected
- [ ] Load testing done (100+ events/sec verified)
- [ ] Failover/recovery tested
- [ ] Documentation updated
- [ ] Team trained on how to respond to alerts
- [ ] Monitoring dashboard set up
- [ ] Incident response plan created
- [ ] Regulatory compliance reviewed (if applicable)

---

## Performance Targets

| Metric | Target | Method |
|--------|--------|--------|
| Event Latency | <100ms | Time from webhook POST to database write |
| P99 Latency | <250ms | 99th percentile latency |
| Throughput | 100+ events/sec | With 3x load balancing |
| Availability | 99.9%+ | Uptime monitoring |
| Error Rate | <0.1% | Signature validation + idempotency |
| Alert Latency | <200ms | Time to trigger alert notification |
| Database Write | <10ms | SQLite with WAL mode |

---

## Support

For help, check:

1. **Webhook Handler Logs**
   ```bash
   tail -f /var/log/profitengine/webhook.log
   ```

2. **Status Endpoint**
   ```bash
   curl https://yourdomain.com/webhooks/webhook/status
   ```

3. **Database Queries**
   ```bash
   sqlite3 clients.db "SELECT * FROM webhook_events LIMIT 10;"
   ```

4. **Robinhood API Docs**
   - https://developer.robinhood.com/webhooks
   - Contact: api-support@robinhood.com

---

**Last Updated:** 2026-06-18  
**Version:** 1.0.0  
**Status:** Production-ready
