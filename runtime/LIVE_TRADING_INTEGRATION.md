# Live Trading Integration Guide

## Overview

This document shows how to integrate the Live Trading Trigger System into the existing ProfitEngine v5 architecture.

---

## 1. Integrate into Main FastAPI App

Add to `runtime/api.py`:

```python
# At the top with other imports
from runtime import live_trading_api

# In your FastAPI app initialization
app = FastAPI()

# Include live trading router
app.include_router(live_trading_api.router)

# Other routes...
```

Now all live trading endpoints are available at `/api/live-trading/*`

---

## 2. Initialize Database Schema on Startup

Add to `runtime/api.py` startup:

```python
from runtime.live_trading_state import initialize_live_trading_schema, verify_live_trading_schema

@app.on_event("startup")
async def startup_event():
    """Initialize database schema and resources on startup"""
    
    # Existing startup code...
    
    # Initialize live trading schema
    try:
        initialize_live_trading_schema("clients.db")
        if verify_live_trading_schema("clients.db"):
            logger.info("Live trading schema verified")
        else:
            logger.error("Live trading schema verification failed")
    except Exception as e:
        logger.error(f"Live trading init error: {e}")
```

---

## 3. Start Monitoring Loop as Background Task

Add to `runtime/api.py`:

```python
import asyncio
from runtime.live_trading_trigger import LiveTradingTrigger

# Global reference to monitoring task
monitoring_task = None

@app.on_event("startup")
async def start_monitoring():
    """Start live trading monitoring loop in background"""
    global monitoring_task
    
    # Existing startup code...
    
    # Start live trading trigger
    trigger = LiveTradingTrigger()
    monitoring_task = asyncio.create_task(trigger.start_monitoring())
    logger.info("Live trading monitoring started")

@app.on_event("shutdown")
async def shutdown_monitoring():
    """Gracefully stop monitoring loop"""
    global monitoring_task
    
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Live trading monitoring stopped")
```

---

## 4. Integrate with Paper Trading Loop

The paper trading system (`paper_trader_pro.py`) runs continuously. When a user's balance hits $1,000, the live trading trigger detects it:

```python
# In paper_trader_pro.py report_status() method

async def report_status(self):
    """Print current portfolio status"""
    # ... existing code ...
    
    if PORTFOLIO.account_balance >= target:
        logger.info(" TARGET REACHED! $1000 achieved!")
        self.running = False
        
        # INTEGRATION: Notify trigger system that user hit target
        # (Trigger system checks for this via daily_trades table)
        # No code change needed - trigger watches daily_trades table
```

---

## 5. Trade Execution Integration

When `mcp_native_trading_engine.py` executes trades on the live account:

```python
# In your trade execution handler (agent_impls/agent_trade_execution.py)

from runtime.robinhood_integration import RobinhoodLiveTrader

async def execute_live_trade(
    user_id: int,
    symbol: str,
    direction: str,
    amount_usd: float
):
    """Execute trade on live account if user is in LIVE tier"""
    
    # Check user tier
    user = get_user(user_id)
    if user['trading_tier'] != 'live':
        return  # Skip live execution if not in live tier
    
    # Get live account info
    live_account = get_live_account(user_id)
    if not live_account or live_account['status'] != 'active':
        return  # Account not active
    
    # Check circuit breaker
    circuit = CircuitBreaker()
    if not await circuit.is_trading_allowed(user_id):
        logger.warning(f"Trading paused for user {user_id}")
        return
    
    # Execute on Robinhood
    robinhood = RobinhoodLiveTrader(
        oauth_token=os.getenv("ROBINHOOD_OAUTH_TOKEN"),
        account_id=live_account['robinhood_account_id']
    )
    
    try:
        order = await robinhood.place_order(
            symbol=symbol,
            direction=direction,
            order_type="market",
            amount_usd=amount_usd
        )
        
        # Log trade
        log_live_trade(
            user_id=user_id,
            robinhood_order_id=order['order_id'],
            symbol=symbol,
            side=direction,
            quantity=order['quantity'],
            entry_price=order['fill_price']
        )
        
        logger.info(f"Live trade executed: {symbol} {direction} {amount_usd}")
        
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        # Log error but don't crash
```

---

## 6. Daily P&L Reconciliation

Add a scheduled task to update daily P&L metrics:

```python
# In runtime/scheduled_tasks.py or similar

import schedule
from runtime.live_trading_state import initialize_live_trading_schema

def update_live_daily_pnl():
    """End-of-day: calculate and log daily P&L for live accounts"""
    
    conn = sqlite3.connect("clients.db")
    cur = conn.cursor()
    
    # Get all active live accounts
    cur.execute("""
        SELECT id, user_id, robinhood_account_id, current_balance, peak_balance
        FROM live_accounts
        WHERE status IN ('active', 'paused')
    """)
    
    for account in cur.fetchall():
        user_id = account['user_id']
        opening_balance = account['current_balance']
        
        # Get end-of-day balance from Robinhood
        robinhood = RobinhoodLiveTrader(oauth_token=ROBINHOOD_TOKEN)
        account_state = await robinhood.get_account()
        closing_balance = account_state['equity']
        
        daily_pnl = closing_balance - opening_balance
        daily_pnl_pct = (daily_pnl / opening_balance) if opening_balance > 0 else 0
        
        # Count trades and wins for the day
        cur.execute("""
            SELECT COUNT(*) as trades, 
                   SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM live_trades
            WHERE user_id = ? AND DATE(entry_time) = DATE('now')
        """, (user_id,))
        
        trade_stats = cur.fetchone()
        trades_count = trade_stats['trades'] or 0
        wins_count = trade_stats['wins'] or 0
        losses_count = trades_count - wins_count
        win_rate = wins_count / trades_count if trades_count > 0 else 0
        
        # Insert daily P&L record
        cur.execute("""
            INSERT INTO live_daily_pnl (
                user_id, date, opening_balance, closing_balance,
                daily_pnl, daily_pnl_pct, trades_count, wins_count,
                losses_count, win_rate
            ) VALUES (?, DATE('now'), ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, opening_balance, closing_balance,
            daily_pnl, daily_pnl_pct, trades_count, wins_count,
            losses_count, win_rate
        ))
        
        # Update current balance
        cur.execute("""
            UPDATE live_accounts
            SET current_balance = ?, peak_balance = MAX(peak_balance, ?), updated_at = ?
            WHERE id = ?
        """, (closing_balance, closing_balance, datetime.now().isoformat(), account['id']))
    
    conn.commit()
    conn.close()
    logger.info("Daily P&L reconciliation complete")

# Schedule for 16:00 UTC daily (after market close)
schedule.every().day.at("16:00").do(update_live_daily_pnl)
```

---

## 7. Circuit Breaker Updates

Continuously monitor and update circuit breaker state:

```python
# In a scheduled health check task

async def update_circuit_breakers():
    """Check all live accounts and update circuit breaker states"""
    
    from runtime.live_trading_safety import CircuitBreaker
    
    cb = CircuitBreaker()
    conn = sqlite3.connect("clients.db")
    cur = conn.cursor()
    
    # Get all active live accounts
    cur.execute("""
        SELECT user_id, daily_loss_limit, max_drawdown_pct
        FROM live_accounts
        WHERE status IN ('active', 'paused')
    """)
    
    for account in cur.fetchall():
        user_id = account['user_id']
        
        # Get today's P&L
        cur.execute("""
            SELECT daily_pnl FROM live_daily_pnl
            WHERE user_id = ? AND date = DATE('now')
        """, (user_id,))
        
        pnl_row = cur.fetchone()
        daily_pnl = Decimal(str(pnl_row['daily_pnl'])) if pnl_row else Decimal("0")
        
        # Get current drawdown
        cur.execute("""
            SELECT peak_balance, current_balance FROM live_accounts
            WHERE user_id = ?
        """, (user_id,))
        
        balance_row = cur.fetchone()
        if balance_row:
            peak = Decimal(str(balance_row['peak_balance']))
            current = Decimal(str(balance_row['current_balance']))
            drawdown_pct = ((peak - current) / peak * 100) if peak > 0 else Decimal("0")
        else:
            drawdown_pct = Decimal("0")
        
        # Evaluate circuit breaker
        state, reason = await cb.check_circuit_breaker(
            user_id=user_id,
            daily_pnl=daily_pnl,
            max_daily_loss=Decimal(str(account['daily_loss_limit'])),
            drawdown_pct=drawdown_pct,
            max_drawdown_pct=Decimal(str(account['max_drawdown_pct']))
        )
        
        # Update circuit breaker
        await cb.update_circuit_breaker(user_id, state, reason)
        
        # If RED state, pause trading
        if state == "red":
            trigger = LiveTradingTrigger()
            await trigger.pause_live_trading(user_id, reason=reason)
    
    conn.close()

# Schedule every 15 minutes
schedule.every(15).minutes.do(update_circuit_breakers)
```

---

## 8. Email Integration

The system uses `gmail_client.py` which is already in the codebase. Verify Gmail config:

```bash
# In your .env
GMAIL_USER=noreply@alreadyherellc.com
GMAIL_APP_PASSWORD=<16-char app password>
ALERT_EMAIL=dispatch@alreadyherellc.com
```

Test:
```python
from runtime.gmail_client import send_email

success = send_email(
    subject="Test",
    body_html="<p>Test</p>",
    to="dispatch@alreadyherellc.com"
)
print(f"Sent: {success}")
```

---

## 9. Webhook Integration (Optional - Robinhood Trade Notifications)

If Robinhood sends webhooks for trade fills:

```python
# Add to live_trading_api.py

from fastapi import Request

@router.post("/webhooks/robinhood")
async def robinhood_webhook(request: Request):
    """Handle webhook from Robinhood for trade updates"""
    
    try:
        payload = await request.json()
        event_type = payload.get("event_type")
        
        # Store webhook for processing
        conn = sqlite3.connect("clients.db")
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO robinhood_webhooks (
                user_id, webhook_id, event_type, event_data, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            payload.get("user_id"),
            payload.get("id"),
            event_type,
            json.dumps(payload),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Webhook received: {event_type}")
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 400
```

---

## 10. Admin Dashboard Integration

Add to your admin dashboard:

```javascript
// Example: React component for live trading dashboard

import React, { useState, useEffect } from 'react';

export function LiveTradingDashboard() {
    const [accounts, setAccounts] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch live accounts
        fetch('/api/live-trading/admin/active-accounts', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        })
            .then(r => r.json())
            .then(data => setAccounts(data))
            .catch(e => console.error(e));

        // Fetch system stats
        fetch('/api/live-trading/stats', {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        })
            .then(r => r.json())
            .then(data => setStats(data))
            .catch(e => console.error(e))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div>Loading...</div>;

    return (
        <div className="live-trading-dashboard">
            <h1>Live Trading Monitor</h1>

            <div className="stats">
                <div className="stat">
                    <h3>Active Accounts</h3>
                    <p>{stats?.live_accounts_by_status?.active || 0}</p>
                </div>
                <div className="stat">
                    <h3>Total Capital</h3>
                    <p>${stats?.total_live_capital?.toFixed(2) || 0}</p>
                </div>
                <div className="stat warning">
                    <h3>RED State</h3>
                    <p>{stats?.red_state_count || 0}</p>
                </div>
                <div className="stat caution">
                    <h3>YELLOW State</h3>
                    <p>{stats?.yellow_state_count || 0}</p>
                </div>
            </div>

            <table className="accounts-table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Account ID</th>
                        <th>Balance</th>
                        <th>Daily P&L</th>
                        <th>State</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {accounts.map(account => (
                        <tr key={account.user_id}>
                            <td>{account.email}</td>
                            <td>{account.robinhood_account_id}</td>
                            <td>${account.current_balance.toFixed(2)}</td>
                            <td className={account.daily_pnl >= 0 ? 'positive' : 'negative'}>
                                ${account.daily_pnl.toFixed(2)}
                            </td>
                            <td className={`state-${account.circuit_state}`}>
                                {account.circuit_state.toUpperCase()}
                            </td>
                            <td>
                                {account.status === 'active' && (
                                    <button onClick={() => pauseUser(account.user_id)}>
                                        Pause
                                    </button>
                                )}
                                {account.status === 'paused' && (
                                    <button onClick={() => resumeUser(account.user_id)}>
                                        Resume
                                    </button>
                                )}
                                <button onClick={() => viewAudit(account.user_id)}>
                                    Audit
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
```

---

## 11. Logging & Observability

Add structured logging for monitoring:

```python
# In runtime/api.py or telemetry module

import json
from datetime import datetime

def log_live_trading_event(
    event_type: str,
    user_id: int,
    details: dict
):
    """Log live trading event for monitoring/debugging"""
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        **details
    }
    
    # Log to file
    with open("logs/live_trading.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Also log to CloudWatch / Datadog if configured
    logger.info(f"Live Trading: {event_type}", extra=log_entry)
```

---

## 12. Testing the Integration

```bash
# 1. Initialize schema
python runtime/live_trading_state.py --init

# 2. Start the API server
uvicorn runtime.api:app --reload

# 3. In another terminal, add a test user
sqlite3 clients.db << 'EOF'
INSERT INTO users (email, signup_date, trading_tier, is_active) 
VALUES ('test@example.com', datetime('now', '-35 days'), 'paper', 1);

INSERT INTO daily_trades (user_id, date, num_trades, win_count, loss_count, pnl_dollars, balance) 
VALUES (1, date('now'), 10, 4, 6, 45.00, 1000.00);
EOF

# 4. Monitor the trigger system
# (Should detect user 1 and initiate deployment)

# 5. Confirm deployment via API
curl -X POST http://localhost:8000/api/live-trading/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "approval_code": "123456"
  }'

# 6. Check live account created
sqlite3 clients.db "SELECT * FROM live_accounts WHERE user_id = 1;"
```

---

## 13. Deployment Checklist

- [ ] Database schema initialized and verified
- [ ] Environment variables set (.env)
- [ ] Robinhood OAuth token tested
- [ ] Gmail credentials working
- [ ] Monitoring loop started on app startup
- [ ] Trade execution integrated
- [ ] Circuit breaker updates running on schedule
- [ ] Daily P&L reconciliation scheduled
- [ ] Admin dashboard integrated
- [ ] API endpoints accessible
- [ ] Logging configured
- [ ] Error handling and fallbacks tested
- [ ] Production security review complete

---

## 14. Troubleshooting

### Schema Error on Startup

```bash
# Verify and reinitialize
python runtime/live_trading_state.py --verify
python runtime/live_trading_state.py --init
```

### Monitoring Loop Not Starting

Check logs:
```bash
tail -f logs/app.log | grep "live"
```

Verify in `api.py` startup:
```python
logger.info("Live trading monitoring started")  # Should appear
```

### Robinhood Connection Failed

```bash
# Test connection
export ROBINHOOD_OAUTH_TOKEN="your_token"
python -m runtime.robinhood_integration
```

### Emails Not Sending

```bash
# Test Gmail
python << 'EOF'
from runtime.gmail_client import send_email
print(send_email("Test", "<p>Test</p>", to="test@example.com"))
EOF
```

---

**Version:** 1.0
**Last Updated:** 2026-06-19
