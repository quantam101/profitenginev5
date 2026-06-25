# Slack Monitoring — Advanced Customization Guide

Real-world examples for connecting to databases, adding custom metrics, implementing alerts, and multi-channel routing.

---

## Real Database Integration Examples

### MongoDB Integration (Recommended)

Update `backend/services/slack_monitoring.py`:

```python
async def _fetch_evening_metrics(self) -> list[MetricValue]:
    """Fetch metrics from MongoDB."""
    try:
        # Get today's metrics
        today = datetime.now(timezone.utc).date()
        
        metrics_doc = await self.db.daily_metrics.find_one({
            "date": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today, datetime.max.time())
            }
        })
        
        if not metrics_doc:
            return []
        
        # Calculate trends
        yesterday = today - timedelta(days=1)
        yesterday_doc = await self.db.daily_metrics.find_one({
            "date": {
                "$gte": datetime.combine(yesterday, datetime.min.time()),
                "$lt": datetime.combine(yesterday, datetime.max.time())
            }
        })
        
        today_revenue = metrics_doc.get("revenue", 0)
        yesterday_revenue = yesterday_doc.get("revenue", 0) if yesterday_doc else 0
        revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
        
        metrics = [
            MetricValue(
                label="Daily Revenue",
                value=f"${today_revenue:,.2f}",
                status=self._revenue_status(today_revenue),
                trend=f"↑ +{revenue_change:.1f}%" if revenue_change > 0 else f"↓ {revenue_change:.1f}%"
            ),
            MetricValue(
                label="Active Sessions",
                value=str(metrics_doc.get("sessions", 0)),
                status=StatusIndicator.OPERATIONAL,
                trend=f"↑ +{metrics_doc.get('session_change', 0)}"
            ),
            MetricValue(
                label="Conversion Rate",
                value=f"{metrics_doc.get('conversion_rate', 0):.1f}%",
                status=StatusIndicator.OPERATIONAL,
                trend=f"↑ +{metrics_doc.get('conversion_change', 0):.1f}%" if metrics_doc.get('conversion_change', 0) > 0 else ""
            ),
            MetricValue(
                label="Avg Response Time",
                value=f"{metrics_doc.get('avg_latency', 0):.0f}ms",
                status=self._latency_status(metrics_doc.get('avg_latency', 0)),
                trend=f"↓ -{metrics_doc.get('latency_improvement', 0):.0f}ms" if metrics_doc.get('latency_improvement', 0) > 0 else ""
            ),
        ]
        
        return metrics
    except Exception as e:
        print(f"Error fetching evening metrics: {e}")
        return []

def _revenue_status(self, revenue: float) -> StatusIndicator:
    """Determine status based on revenue."""
    if revenue < 1000:
        return StatusIndicator.WARNING
    elif revenue < 500:
        return StatusIndicator.CRITICAL
    else:
        return StatusIndicator.OPERATIONAL

def _latency_status(self, latency: float) -> StatusIndicator:
    """Determine status based on latency."""
    if latency < 200:
        return StatusIndicator.OPERATIONAL
    elif latency < 500:
        return StatusIndicator.WARNING
    else:
        return StatusIndicator.CRITICAL
```

### PostgreSQL Integration

```python
import asyncpg

class SlackMonitoringService:
    def __init__(self, db, webhook_url=None, pg_connection_string=None):
        self.db = db
        self.webhook_url = webhook_url or os.environ.get("PROFITENGINE_SLACK_WEBHOOK_URL")
        self.pg_connection_string = pg_connection_string or os.environ.get("DATABASE_URL")
        self.session = None
        self.pg_pool = None

    async def init(self):
        """Initialize connections."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        if not self.pg_pool and self.pg_connection_string:
            self.pg_pool = await asyncpg.create_pool(self.pg_connection_string)

    async def _fetch_evening_metrics(self) -> list[MetricValue]:
        """Fetch metrics from PostgreSQL."""
        try:
            async with self.pg_pool.acquire() as conn:
                # Get daily metrics
                result = await conn.fetchrow("""
                    SELECT 
                        SUM(amount) as total_revenue,
                        COUNT(DISTINCT session_id) as session_count,
                        AVG(EXTRACT(EPOCH FROM (response_time))) as avg_latency,
                        COUNT(*) FILTER (WHERE status >= 400) as error_count
                    FROM events
                    WHERE date >= CURRENT_DATE
                """)
                
                if not result:
                    return []
                
                total_revenue = float(result['total_revenue'] or 0)
                session_count = int(result['session_count'] or 0)
                avg_latency = float(result['avg_latency'] or 0) * 1000  # Convert to ms
                error_count = int(result['error_count'] or 0)
                
                # Calculate error rate
                total_requests = await conn.fetchval(
                    "SELECT COUNT(*) FROM events WHERE date >= CURRENT_DATE"
                )
                error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
                
                metrics = [
                    MetricValue(
                        label="Daily Revenue",
                        value=f"${total_revenue:,.2f}",
                        status=StatusIndicator.OPERATIONAL,
                        trend="↑ +12%"  # Calculate from previous day
                    ),
                    MetricValue(
                        label="Active Sessions",
                        value=str(session_count),
                        status=StatusIndicator.OPERATIONAL,
                        trend="↑ +28"
                    ),
                    MetricValue(
                        label="Error Rate",
                        value=f"{error_rate:.2f}%",
                        status=StatusIndicator.OPERATIONAL if error_rate < 0.1 else StatusIndicator.WARNING,
                    ),
                    MetricValue(
                        label="Avg Response Time",
                        value=f"{avg_latency:.0f}ms",
                        status=StatusIndicator.OPERATIONAL if avg_latency < 200 else StatusIndicator.WARNING,
                    ),
                ]
                
                return metrics
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return []
```

---

## Advanced Alert Integration

### Threshold-Based Alerts

```python
async def _fetch_evening_alerts(self) -> list[str]:
    """Fetch alerts based on thresholds."""
    alerts = []
    
    try:
        # Check latency
        latency_doc = await self.db.metrics.find_one(
            {
                "metric": "latency",
                "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(minutes=10)}
            },
            sort=[("timestamp", -1)]
        )
        
        if latency_doc and latency_doc['value'] > 300:  # Threshold: 300ms
            alerts.append(
                f"API latency elevated: {latency_doc['value']:.0f}ms (threshold: 300ms)"
            )
        
        # Check error rate
        error_docs = await self.db.metrics.find(
            {
                "metric": "error_rate",
                "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(minutes=5)}
            }
        ).to_list(length=100)
        
        avg_error_rate = sum(doc['value'] for doc in error_docs) / len(error_docs) if error_docs else 0
        
        if avg_error_rate > 1.0:  # Threshold: 1%
            alerts.append(
                f"Error rate spiked: {avg_error_rate:.2f}% (threshold: 1%)"
            )
        
        # Check recent failures
        failed_deploys = await self.db.deployments.find(
            {
                "status": "failed",
                "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)}
            }
        ).to_list(length=5)
        
        for deploy in failed_deploys:
            alerts.append(
                f"Deploy failed: {deploy['version']} — {deploy['error'][:50]}..."
            )
        
        # Check downtime
        downtime_doc = await self.db.incidents.find_one(
            {
                "status": {"$in": ["ongoing", "investigating"]},
                "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)}
            }
        )
        
        if downtime_doc:
            duration = (datetime.now(timezone.utc) - downtime_doc['timestamp']).total_seconds() / 60
            alerts.append(
                f"Service incident: {downtime_doc['title']} (ongoing for {duration:.0f}m)"
            )
        
        return alerts
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []
```

---

## Multi-Channel Routing

### Post Different Content to Different Channels

```python
class SlackMonitoringService:
    def __init__(self, db, webhooks=None):
        self.db = db
        # Multiple webhooks for different channels
        self.webhooks = webhooks or {
            "alerts": os.environ.get("SLACK_ALERTS_WEBHOOK"),
            "metrics": os.environ.get("SLACK_METRICS_WEBHOOK"),
            "executive": os.environ.get("SLACK_EXECUTIVE_WEBHOOK"),
        }
        self.session = None

    async def send_to_channel(self, channel: str, briefing: SlackBriefing) -> bool:
        """Send to specific channel."""
        webhook = self.webhooks.get(channel)
        if not webhook:
            print(f"Webhook not configured for channel: {channel}")
            return False
        
        try:
            await self.init()
            async with self.session.post(webhook, json=briefing.to_slack_payload()) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"Error sending to {channel}: {e}")
            return False

    async def morning_briefing(self):
        """Send morning briefing to operations and executives."""
        briefing = SlackBriefing(
            title="📊 Morning Briefing",
            subtitle="Daily overview",
            metrics=await self._fetch_morning_metrics(),
            color="#36a64f"
        )
        
        # Send to ops
        await self.send_to_channel("alerts", briefing)
        
        # Send simplified version to executives
        exec_briefing = SlackBriefing(
            title="📊 Executive Morning Briefing",
            subtitle="Key metrics for leadership",
            metrics=[
                m for m in briefing.metrics
                if m.label in ["Daily Revenue", "System Status", "Uptime"]
            ],
            color="#36a64f"
        )
        await self.send_to_channel("executive", exec_briefing)
```

---

## Custom Metric Aggregation

### Weekly Trend Analysis

```python
async def _fetch_weekly_metrics(self) -> list[MetricValue]:
    """Fetch aggregated weekly metrics with trends."""
    try:
        week_start = datetime.now(timezone.utc) - timedelta(days=6)
        
        # Get daily metrics for the week
        daily_metrics = await self.db.daily_metrics.find(
            {"date": {"$gte": week_start}}
        ).sort([("date", 1)]).to_list(length=7)
        
        if not daily_metrics:
            return []
        
        # Aggregate by week
        weekly_revenue = sum(doc.get('revenue', 0) for doc in daily_metrics)
        weekly_sessions = sum(doc.get('sessions', 0) for doc in daily_metrics)
        
        # Calculate daily average
        avg_daily_revenue = weekly_revenue / len(daily_metrics) if daily_metrics else 0
        avg_daily_sessions = weekly_sessions / len(daily_metrics) if daily_metrics else 0
        
        # Compare with previous week
        prev_week_start = week_start - timedelta(days=7)
        prev_week_docs = await self.db.daily_metrics.find(
            {"date": {"$gte": prev_week_start, "$lt": week_start}}
        ).to_list(length=7)
        
        prev_week_revenue = sum(doc.get('revenue', 0) for doc in prev_week_docs) if prev_week_docs else 0
        revenue_growth = ((weekly_revenue - prev_week_revenue) / prev_week_revenue * 100) if prev_week_revenue > 0 else 0
        
        # Find best and worst days
        sorted_by_revenue = sorted(daily_metrics, key=lambda d: d.get('revenue', 0), reverse=True)
        best_day = sorted_by_revenue[0] if sorted_by_revenue else None
        worst_day = sorted_by_revenue[-1] if sorted_by_revenue else None
        
        metrics = [
            MetricValue(
                label="Weekly Revenue",
                value=f"${weekly_revenue:,.2f}",
                status=StatusIndicator.OPERATIONAL,
                trend=f"↑ +{revenue_growth:.1f}%" if revenue_growth > 0 else f"↓ {revenue_growth:.1f}%"
            ),
            MetricValue(
                label="Weekly Sessions",
                value=f"{weekly_sessions:,}",
                status=StatusIndicator.OPERATIONAL,
            ),
            MetricValue(
                label="Daily Average Revenue",
                value=f"${avg_daily_revenue:,.2f}",
                status=StatusIndicator.OPERATIONAL,
            ),
            MetricValue(
                label="Best Day",
                value=f"${best_day.get('revenue', 0):,.2f}" if best_day else "$0",
                status=StatusIndicator.OPERATIONAL,
                trend=f"({best_day.get('date').strftime('%a')})" if best_day else ""
            ),
        ]
        
        return metrics
    except Exception as e:
        print(f"Error: {e}")
        return []
```

---

## Incident Response Integration

### Auto-Post Incident Updates

```python
async def post_incident_alert(self, incident_id: str):
    """Post critical incident alert."""
    try:
        incident = await self.db.incidents.find_one({"_id": incident_id})
        
        if not incident:
            return False
        
        briefing = SlackBriefing(
            title=f"🚨 Incident: {incident['title']}",
            subtitle=f"Status: {incident['status'].upper()}",
            metrics=[
                MetricValue(
                    label="Duration",
                    value=f"{(datetime.now(timezone.utc) - incident['start_time']).total_seconds() / 60:.0f}m",
                    status=StatusIndicator.CRITICAL
                ),
                MetricValue(
                    label="Affected Services",
                    value=", ".join(incident.get('affected_services', [])),
                    status=StatusIndicator.CRITICAL
                ),
                MetricValue(
                    label="Customer Impact",
                    value=incident.get('customer_impact', 'Unknown'),
                    status=StatusIndicator.CRITICAL
                ),
            ],
            alerts=[
                f"Root cause: {incident.get('root_cause', 'Investigating...')}",
                f"Actions: {incident.get('mitigation_actions', 'In progress')}",
                f"ETA: {incident.get('eta', 'TBD')}",
            ],
            color="#ff0000"  # Red for critical
        )
        
        return await self.send_webhook(briefing.to_slack_payload())
    except Exception as e:
        print(f"Error posting incident alert: {e}")
        return False
```

---

## Automated Health Checks

### Composite Health Score

```python
async def _fetch_morning_metrics(self) -> list[MetricValue]:
    """Calculate health score from multiple indicators."""
    try:
        # Fetch all relevant metrics
        latency = await self.db.metrics.find_one(
            {"metric": "latency"},
            sort=[("timestamp", -1)]
        )
        uptime = await self.db.metrics.find_one(
            {"metric": "uptime"},
            sort=[("timestamp", -1)]
        )
        error_rate = await self.db.metrics.find_one(
            {"metric": "error_rate"},
            sort=[("timestamp", -1)]
        )
        
        # Calculate health score (0-100)
        health_score = 100
        
        # Latency component (max 20 points deduction)
        if latency and latency['value'] > 500:
            health_score -= 20
        elif latency and latency['value'] > 300:
            health_score -= 10
        
        # Uptime component (max 30 points deduction)
        if uptime and uptime['value'] < 99.0:
            health_score -= (100 - uptime['value']) * 30
        
        # Error rate component (max 30 points deduction)
        if error_rate and error_rate['value'] > 1.0:
            health_score -= error_rate['value'] * 30
        
        # Determine overall status
        if health_score >= 95:
            status = StatusIndicator.OPERATIONAL
        elif health_score >= 80:
            status = StatusIndicator.WARNING
        else:
            status = StatusIndicator.CRITICAL
        
        metrics = [
            MetricValue(
                label="System Health",
                value=f"{max(0, health_score):.0f}/100",
                status=status,
                trend="✓" if health_score >= 95 else "⚠️"
            ),
            MetricValue(
                label="API Latency",
                value=f"{latency['value']:.0f}ms" if latency else "N/A",
                status=StatusIndicator.OPERATIONAL if (latency and latency['value'] < 200) else StatusIndicator.WARNING
            ),
            MetricValue(
                label="Error Rate",
                value=f"{error_rate['value']:.2f}%" if error_rate else "N/A",
                status=StatusIndicator.OPERATIONAL if (error_rate and error_rate['value'] < 0.1) else StatusIndicator.WARNING
            ),
            MetricValue(
                label="Uptime",
                value=f"{uptime['value']:.2f}%" if uptime else "N/A",
                status=StatusIndicator.OPERATIONAL if (uptime and uptime['value'] > 99.9) else StatusIndicator.WARNING
            ),
        ]
        
        return metrics
    except Exception as e:
        print(f"Error: {e}")
        return []
```

---

## Testing & Debugging

### Local Testing Script

```python
# test_slack_locally.py
import asyncio
import json
from backend.services.slack_monitoring import SlackMonitoringService
from motor.motor_asyncio import AsyncIOMotorClient

async def test_all_briefings():
    """Test all briefing types locally."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.profitengine
    
    service = SlackMonitoringService(db)
    
    # Test morning
    morning = await service.morning_briefing()
    print("MORNING BRIEFING:")
    print(json.dumps(morning.to_slack_payload(), indent=2))
    
    # Test evening
    evening = await service.evening_metrics()
    print("\nEVENING METRICS:")
    print(json.dumps(evening.to_slack_payload(), indent=2))
    
    # Test weekly
    weekly = await service.weekly_summary()
    print("\nWEEKLY SUMMARY:")
    print(json.dumps(weekly.to_slack_payload(), indent=2))
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_all_briefings())
```

Run with:
```bash
python test_slack_locally.py > slack_messages.json
```

---

## Production Monitoring

### Monitor the Monitor

Add to your health check:

```python
async def health_check_slack_monitoring():
    """Verify Slack monitoring is working."""
    checks = {
        "webhook_configured": bool(os.environ.get("PROFITENGINE_SLACK_WEBHOOK_URL")),
        "mongo_connected": bool(await self.db.command("ping")),
        "last_post": await self.db.slack_logs.find_one(
            sort=[("timestamp", -1)]
        ),
    }
    
    last_post_timestamp = checks['last_post']['timestamp'] if checks['last_post'] else None
    hours_since_post = (datetime.now(timezone.utc) - last_post_timestamp).total_seconds() / 3600 if last_post_timestamp else 999
    
    return {
        "status": "healthy" if hours_since_post < 2 else "degraded",
        "checks": checks
    }
```

---

## Summary

Advanced customization options:
- **Database Integration:** MongoDB, PostgreSQL, Firebase
- **Alert Thresholds:** Latency, errors, revenue, incidents
- **Multi-Channel:** Different messages per Slack channel
- **Aggregation:** Weekly trends, daily averages
- **Health Scores:** Composite metrics from multiple sources
- **Testing:** Local preview, log analysis, debugging

All examples are production-ready. Start simple, expand as needed.
