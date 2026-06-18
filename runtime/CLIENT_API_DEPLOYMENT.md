# Client API Deployment Guide

Complete instructions for deploying the Client API to OCI, Vercel, or local environments.

## Prerequisites

- Python 3.11+
- FastAPI + uvicorn
- SQLite3
- Access to `clients.db` database
- API key for authentication

---

## Option 1: OCI Server Deployment (Recommended)

### 1.1 SSH Into OCI Server

```bash
ssh opc@129.146.167.73
```

### 1.2 Create Application Directory

```bash
mkdir -p /opt/profitengine/runtime
cd /opt/profitengine/runtime
```

### 1.3 Clone Runtime Files

Copy the following files to OCI:

```bash
# From your local machine
scp -r runtime/client_api.py opc@129.146.167.73:/opt/profitengine/runtime/
scp runtime/client_api_integration.py opc@129.146.167.73:/opt/profitengine/runtime/
scp runtime/client_api_config.example.env opc@129.146.167.73:/opt/profitengine/.env.client_api
```

### 1.4 Set Up Environment

```bash
cd /opt/profitengine

# Copy and customize config
cp .env.client_api .env

# Edit .env with production values
nano .env

# Generate API key hash
python3 << 'EOF'
import hashlib
api_key = "your-secure-32-char-random-key"
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
print(f"API Key: {api_key}")
print(f"Hash: {key_hash}")
print(f"Add to .env: CLIENT_API_KEY_HASH={key_hash}")
EOF
```

### 1.5 Install Dependencies

```bash
# Install Python packages
pip3 install fastapi uvicorn pydantic python-multipart

# Verify installation
python3 -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
```

### 1.6 Create Systemd Service

```bash
sudo tee /etc/systemd/system/profitengine-client-api.service > /dev/null <<EOF
[Unit]
Description=ProfitEngine Client API
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/opt/profitengine
Environment="PATH=/home/opc/.local/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/profitengine/.env
ExecStart=/usr/bin/python3 -m uvicorn runtime.client_api:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 1.7 Start Service

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable profitengine-client-api
sudo systemctl start profitengine-client-api

# Check status
sudo systemctl status profitengine-client-api

# View logs
journalctl -u profitengine-client-api -f
```

### 1.8 Configure Firewall

```bash
# Allow port 8001
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload

# Or via OCI Console → Instance → Security Groups
# Add Ingress Rule: Port 8001 from 0.0.0.0/0
```

### 1.9 Test Endpoint

```bash
# Health check (no auth needed)
curl http://129.146.167.73:8001/api/health

# With API key
API_KEY="your-api-key"
curl -H "Authorization: Bearer $API_KEY" \
  http://129.146.167.73:8001/api/clients/stats
```

---

## Option 2: Docker Container Deployment

### 2.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
RUN pip install fastapi uvicorn pydantic python-multipart

# Copy application
COPY runtime/client_api.py .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1

# Run app
CMD ["uvicorn", "client_api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2.2 Build Image

```bash
docker build -t profitengine-client-api:latest .
```

### 2.3 Run Container

```bash
docker run -d \
  --name profitengine-client-api \
  --port 8001:8001 \
  --volume /data/clients.db:/app/clients.db \
  --env-file .env \
  profitengine-client-api:latest
```

### 2.4 Push to Registry (Optional)

```bash
# Tag for registry
docker tag profitengine-client-api:latest gcr.io/your-project/profitengine-client-api:latest

# Push
docker push gcr.io/your-project/profitengine-client-api:latest
```

---

## Option 3: Vercel Deployment (For profitengine-tau)

### 3.1 Create API Route

In `profitengine-tau`:

```bash
mkdir -p api/clients
cat > api/clients/stats.ts << 'EOF'
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const apiKey = process.env.PROFITENGINE_CLIENT_API_KEY;
  const baseUrl = process.env.PROFITENGINE_CLIENT_API_URL;

  const response = await fetch(`${baseUrl}/api/clients/stats?days=30`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });

  if (!response.ok) {
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: response.status }
    );
  }

  return NextResponse.json(await response.json());
}
EOF
```

### 3.2 Update Vercel Environment

```bash
# In Vercel Console → Settings → Environment Variables

PROFITENGINE_CLIENT_API_URL=https://runtime.alreadyhere.com
PROFITENGINE_CLIENT_API_KEY=<your-api-key>
```

### 3.3 Call from Frontend

```javascript
// In React component
const [stats, setStats] = useState(null);

useEffect(() => {
  fetch('/api/clients/stats')
    .then(r => r.json())
    .then(data => setStats(data));
}, []);

return (
  <div>
    <h2>{stats?.total_traders} Traders</h2>
    <p>{stats?.total_pnl} P&L</p>
  </div>
);
```

---

## Option 4: Local Development

### 4.1 Install Dependencies

```bash
pip install fastapi uvicorn pydantic python-multipart
```

### 4.2 Run Locally

```bash
cd profitengine-v5-final
python -m uvicorn runtime.client_api:app --reload
```

### 4.3 Test with Examples

```bash
# Run integration examples
export PROFITENGINE_CLIENT_API_KEY="dev-key-change-in-production"
python runtime/client_api_integration.py
```

---

## Reverse Proxy Setup (Nginx)

Route `/api/clients/*` to client API service:

```nginx
server {
    listen 80;
    server_name runtime.alreadyhere.com;

    # Proxy to client API
    location /api/clients {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /api/health {
        proxy_pass http://127.0.0.1:8001;
    }
}
```

---

## Database Seeding

### Initial Setup

```python
import sqlite3
from datetime import datetime, timedelta, timezone
import random

db_path = "clients.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create schema (API does this automatically)
from runtime.client_api import ClientDB
db = ClientDB(db_path)

# Insert sample clients
for i in range(1, 11):
    account_created = (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))).isoformat()
    cursor.execute(
        "INSERT INTO clients (user_id, username, email, account_created, account_status, tier) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (f"user_{i}", f"trader_{i}", f"user{i}@example.com", account_created, "active", "free")
    )

# Insert sample trades
for user_id in [f"user_{i}" for i in range(1, 6)]:
    for j in range(random.randint(20, 100)):
        entry_time = (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat()
        exit_time = (datetime.now(timezone.utc) - timedelta(minutes=random.randint(30, 1440))).isoformat()
        pnl = random.uniform(-500, 500)
        
        cursor.execute(
            "INSERT INTO trades "
            "(trade_id, user_id, symbol, side, entry_price, exit_price, shares, pnl, pnl_percent, entry_time, exit_time, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"trade_{user_id}_{j}",
                user_id,
                random.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]),
                random.choice(["BUY", "SELL"]),
                random.uniform(100, 500),
                random.uniform(100, 500),
                random.randint(1, 100),
                pnl,
                (pnl / 250) * 100,
                entry_time,
                exit_time,
                "closed"
            )
        )

conn.commit()
conn.close()
print("Database seeded successfully!")
```

---

## Monitoring & Alerting

### 4.1 Health Check Script

```bash
#!/bin/bash
# /opt/profitengine/check_api_health.sh

API_URL="http://127.0.0.1:8001/api/health"
TIMEOUT=5

response=$(curl -s --max-time $TIMEOUT "$API_URL")
status=$(echo "$response" | grep -o '"ok":true' || echo "")

if [ -z "$status" ]; then
    echo "CRITICAL: Client API health check failed"
    # Send alert
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
      -d '{"text":"Client API is down!"}'
    exit 1
fi

echo "OK: Client API is healthy"
exit 0
```

Run via cron:

```bash
# Every 5 minutes
*/5 * * * * /opt/profitengine/check_api_health.sh
```

### 4.2 Performance Monitoring

```bash
# Test response time
time curl -H "Authorization: Bearer $API_KEY" \
  http://127.0.0.1:8001/api/clients/stats
```

---

## Troubleshooting

### API won't start

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check port availability
netstat -tlnp | grep 8001

# Kill process if needed
pkill -f "uvicorn.*client_api"
```

### Database connection error

```bash
# Verify database exists
ls -la /data/clients.db

# Check permissions
chmod 644 /data/clients.db

# Verify schema
sqlite3 /data/clients.db ".tables"
```

### Authentication failures

```bash
# Verify API key hash
python3 << 'EOF'
import hashlib
api_key = "your-key"
print(hashlib.sha256(api_key.encode()).hexdigest())
EOF

# Check .env file
cat /opt/profitengine/.env | grep CLIENT_API_KEY_HASH
```

### High response times

```bash
# Monitor database queries
sqlite3 /data/clients.db "PRAGMA query_only = ON; EXPLAIN QUERY PLAN SELECT * FROM trades;"

# Check system resources
top -b -n 1 | head -20
df -h
```

---

## Security Checklist

- [ ] API key is strong (32+ random characters)
- [ ] API key hash stored in backend .env only
- [ ] Database file is not world-readable (`chmod 600`)
- [ ] Firewall rules restrict port 8001 to known IPs (optional)
- [ ] HTTPS enforced in production (via reverse proxy)
- [ ] Rate limiting enabled (default: 100/hour)
- [ ] CORS origins restricted if needed
- [ ] Logs don't contain sensitive data
- [ ] Database backups configured
- [ ] API key rotation scheduled (90 days)

---

## Performance Optimization

### Enable Query Caching

```python
# In client_api.py, add caching layer
from functools import lru_cache

@lru_cache(maxsize=128)
def get_leaderboard_cached(metric, days):
    # ... expensive query ...
    pass
```

### Materialized Views for Stats

```sql
-- Create materialized view for faster stats queries
CREATE TABLE trader_stats_cache AS
SELECT
  user_id,
  COUNT(*) as total_trades,
  SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
  SUM(pnl) as total_pnl,
  ROUND(AVG(CASE WHEN pnl > 0 THEN 100.0 ELSE 0 END), 2) as win_rate
FROM trades
WHERE entry_time > datetime('now', '-30 days')
GROUP BY user_id;

-- Refresh periodically
INSERT OR REPLACE INTO trader_stats_cache ...
```

### Database Indexes

```sql
-- Add indexes for common queries
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_clients_tier ON clients(tier);
```

---

## Logging & Debugging

### Enable debug logs

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FILE=/var/log/profitengine/client_api.log
```

### View logs

```bash
# Systemd
journalctl -u profitengine-client-api -f

# Log file
tail -f /var/log/profitengine/client_api.log

# Docker
docker logs -f profitengine-client-api
```

---

## Summary

- **OCI**: Recommended for production (direct server, systemd, full control)
- **Docker**: Good for containerized deployments and scaling
- **Vercel**: Lightweight for frontend integration via API routes
- **Local**: Development and testing

Choose based on your infrastructure and team preferences.
