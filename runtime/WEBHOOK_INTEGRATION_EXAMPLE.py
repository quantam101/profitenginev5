"""
WEBHOOK INTEGRATION EXAMPLE
===========================

Example showing how to integrate the Robinhood webhook handler
into your main FastAPI application.

Three approaches:
1. Include router (recommended for separate concerns)
2. Mount as sub-application
3. Run on separate port/process
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ============================================================================
# APPROACH 1: INCLUDE ROUTER (RECOMMENDED)
# ============================================================================

def setup_api_with_webhook_router():
    """
    Mount webhook handler as a router.
    Best for: sharing database, middleware, authentication
    """
    from fastapi import APIRouter
    from robinhood_webhook_handler import app as webhook_app

    main_app = FastAPI(title="ProfitEngine Main API", version="1.0.0")

    # Setup CORS
    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount webhook routes as sub-router
    main_app.include_router(
        webhook_app.router,
        prefix="/webhooks",
        tags=["webhooks"]
    )

    # Your existing routes
    @main_app.get("/health")
    async def health():
        return {"status": "ok"}

    return main_app


# ============================================================================
# APPROACH 2: MOUNT AS SUB-APPLICATION
# ============================================================================

def setup_api_with_webhook_mount():
    """
    Mount webhook handler as a separate FastAPI app.
    Best for: isolation, independent scaling
    """
    from robinhood_webhook_handler import app as webhook_app

    main_app = FastAPI(title="ProfitEngine Main API", version="1.0.0")

    # Setup CORS
    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount webhook app
    main_app.mount("/webhooks", webhook_app)

    # Your existing routes
    @main_app.get("/health")
    async def health():
        return {"status": "ok"}

    return main_app


# ============================================================================
# APPROACH 3: RUN ON SEPARATE PORT
# ============================================================================

def setup_main_api_only():
    """
    Run webhook handler on separate port.
    Best for: microservices, independent processes
    """
    main_app = FastAPI(title="ProfitEngine Main API", version="1.0.0")

    # Setup CORS
    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Your existing routes
    @main_app.get("/health")
    async def health():
        return {"status": "ok"}

    return main_app


def setup_webhook_api_only():
    """
    Run webhook handler on separate port (e.g., 8001).
    """
    from robinhood_webhook_handler import app as webhook_app
    return webhook_app


# ============================================================================
# EXAMPLE: UNIFIED SETUP IN runtime/api.py
# ============================================================================

"""
In your main api.py file, add this:

from robinhood_webhook_handler import app as webhook_app

# Mount webhook routes at /api/webhooks
app.include_router(webhook_app.router, prefix="/webhooks", tags=["webhooks"])

Then start with:
  uvicorn runtime.api:app --host 0.0.0.0 --port 8000

Webhook endpoint will be at:
  https://yourdomain.com/api/webhooks/webhook/robinhood
"""

# ============================================================================
# DEPLOYMENT CONFIGURATIONS
# ============================================================================

"""
DEPLOYMENT OPTION 1: Single FastAPI + Webhook Handler
=====================================================

Single process running main API + webhook handler:

File: main.py
    from fastapi import FastAPI
    from robinhood_webhook_handler import app as webhook_app

    app = FastAPI()
    app.include_router(webhook_app.router, prefix="/api/webhooks")

    @app.get("/health")
    async def health():
        return {"ok": True}

Start:
    uvicorn main:app --host 0.0.0.0 --port 8000

Endpoints:
    Main API: http://localhost:8000
    Webhook: http://localhost:8000/api/webhooks/webhook/robinhood
    Status: http://localhost:8000/api/webhooks/webhook/status


DEPLOYMENT OPTION 2: Separate Webhook Service
==============================================

Independent webhook handler service:

File: webhook_service.py
    from robinhood_webhook_handler import app

Start:
    uvicorn webhook_service:app --host 0.0.0.0 --port 8001

Endpoints:
    Webhook: http://localhost:8001/webhook/robinhood
    Status: http://localhost:8001/webhook/status

Register with Robinhood:
    https://yourdomain.com:8001/webhook/robinhood


DEPLOYMENT OPTION 3: Docker Container
======================================

Dockerfile for webhook service:

FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY runtime/robinhood_webhook_handler.py .

ENV ROBINHOOD_WEBHOOK_SECRET=\${WEBHOOK_SECRET}
ENV CLIENTS_DB_PATH=/data/clients.db

EXPOSE 8001
CMD ["uvicorn", "robinhood_webhook_handler:app", "--host", "0.0.0.0", "--port", "8001"]

Build:
    docker build -t profitengine-webhook .

Run:
    docker run -p 8001:8001 \\
      -e ROBINHOOD_WEBHOOK_SECRET=your-secret \\
      -v /path/to/db:/data \\
      profitengine-webhook

Register with Robinhood:
    https://yourdomain.com/webhook/robinhood


DEPLOYMENT OPTION 4: Kubernetes
================================

Helm/K8s deployment of webhook handler as microservice:

apiVersion: v1
kind: ConfigMap
metadata:
  name: webhook-config
data:
  ROBINHOOD_WEBHOOK_SECRET: "your-secret"
  LOG_LEVEL: "INFO"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: profitengine-webhook
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webhook
  template:
    metadata:
      labels:
        app: webhook
    spec:
      containers:
      - name: webhook
        image: profitengine-webhook:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: webhook-config
        volumeMounts:
        - name: db
          mountPath: /data
      volumes:
      - name: db
        persistentVolumeClaim:
          claimName: webhook-db

---
apiVersion: v1
kind: Service
metadata:
  name: webhook-service
spec:
  ports:
  - port: 80
    targetPort: 8001
  selector:
    app: webhook
  type: LoadBalancer

Deploy:
    kubectl apply -f webhook.yaml

Register with Robinhood:
    https://yourdomain.com/webhook/robinhood
"""

# ============================================================================
# LOAD BALANCING & SCALING
# ============================================================================

"""
For high-volume webhook traffic (100+ events/sec), run multiple instances:

1. Load Balancer (nginx)
   - Routes to multiple webhook instances
   - Sticky session not needed (idempotent)

nginx.conf:
    upstream webhook_backend {
        server localhost:8001;
        server localhost:8002;
        server localhost:8003;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        location /webhook/robinhood {
            proxy_pass http://webhook_backend;
            proxy_set_header X-Forwarded-For \$remote_addr;
        }
    }

2. Start multiple instances:
    uvicorn robinhood_webhook_handler:app --port 8001
    uvicorn robinhood_webhook_handler:app --port 8002
    uvicorn robinhood_webhook_handler:app --port 8003

3. All share same database (clients.db)
   - Webhook events table enforces uniqueness on event_id
   - Safe for concurrent writes


DATABASE OPTIMIZATION FOR SCALE
================================

For 100+ webhook events/second, add indices:

sqlite3 clients.db <<'EOF'
CREATE INDEX IF NOT EXISTS idx_webhook_event_id ON webhook_events(event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_timestamp ON webhook_events(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_trade_user_date ON trade_log(user_id, date(entry_time));
CREATE INDEX IF NOT EXISTS idx_alert_unack ON alerts(user_id, acknowledged);
CREATE INDEX IF NOT EXISTS idx_balance_user_time ON balance_history(user_id, timestamp DESC);
EOF

Or with WAL mode for concurrent writers:

sqlite3 clients.db 'PRAGMA journal_mode=WAL;'
sqlite3 clients.db 'PRAGMA synchronous=NORMAL;'
sqlite3 clients.db 'PRAGMA cache_size=10000;'
"""

# ============================================================================
# MONITORING & OBSERVABILITY
# ============================================================================

"""
Monitor webhook handler health:

1. Health Check Endpoint
    curl https://yourdomain.com/webhooks/webhook/status

2. Prometheus Metrics (add to webhook_handler.py)
    from prometheus_client import Counter, Histogram, generate_latest

    webhook_events_total = Counter('webhook_events_total', 'Total webhooks received')
    webhook_latency = Histogram('webhook_latency_ms', 'Webhook processing time')

3. CloudWatch / DataDog / New Relic
    Send logs to:
    - Webhook events received/processed
    - Latency metrics
    - Error rates
    - Database connection pool

4. Alerts
    - Webhook error rate > 1% → page
    - P99 latency > 500ms → warn
    - Database connection failures → page
    - Unacknowledged critical alerts → page

5. Logging
    import logging
    logging.getLogger("robinhood_webhook").setLevel(logging.INFO)

    Log all:
    - Webhook received (event_type, event_id, timestamp)
    - Processing result (success/failure, latency)
    - Database updates (trades, balance, alerts)
    - Errors with full traceback
"""

# ============================================================================
# TESTING IN PRODUCTION
# ============================================================================

"""
Test webhook handler in production safely:

1. Create test events via API
    curl -X POST https://yourdomain.com/webhooks/webhook/robinhood \\
      -H "X-Robinhood-Signature: ..." \\
      -H "X-Robinhood-Timestamp: ..." \\
      -d '{"event_type":"order_filled","event_id":"evt_test_123",...}'

2. Query test results
    curl https://yourdomain.com/webhooks/webhook/status
    curl https://yourdomain.com/webhooks/trades/daily/1
    curl https://yourdomain.com/webhooks/alerts/user/1

3. Check database
    sqlite3 clients.db 'SELECT * FROM webhook_events WHERE event_id LIKE "evt_test_%";'

4. Roll back if needed
    sqlite3 clients.db 'DELETE FROM webhook_events WHERE event_id = "evt_test_123";'
"""

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Choose deployment approach:
    # app = setup_api_with_webhook_router()        # Approach 1
    # app = setup_api_with_webhook_mount()         # Approach 2
    app = setup_main_api_only()                   # Approach 3 (main API only)

    print("Starting ProfitEngine API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

    # In separate terminal, run webhook:
    # python -m uvicorn robinhood_webhook_handler:app --port 8001
