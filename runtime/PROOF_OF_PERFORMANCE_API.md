# Proof of Performance API Integration

Use the metrics system programmatically in your application.

---

## HTTP Endpoints (if wrapped in FastAPI)

Future option: Expose metrics as API endpoints.

```python
# In runtime/main.py or similar
from fastapi import FastAPI
from proof_of_performance import ProofOfPerformance

app = FastAPI()
pof = ProofOfPerformance()

@app.get("/api/metrics/daily")
async def get_daily_metrics():
    """Current day metrics."""
    metrics = pof.generate_daily_metrics()
    return metrics.__dict__

@app.get("/api/claims/validate")
async def validate_claims():
    """Validate all marketing claims."""
    claims = pof.validate_all_claims()
    return [asdict(c) for c in claims]

@app.get("/api/performers/top")
async def get_top_performers(days: int = 30, limit: int = 10):
    """Get top performers for case studies."""
    stories = pof.get_top_performers(days, limit)
    return [asdict(s) for s in stories]

@app.get("/api/milestones")
async def get_milestones():
    """Check for recent milestones."""
    milestones = pof.check_milestones()
    return [asdict(m) for m in milestones]

@app.get("/api/competitive")
async def get_competitive_report():
    """Competitive advantage analysis."""
    return pof.generate_competitive_report()

@app.get("/api/dashboard/marketing")
async def get_marketing_dashboard():
    """Marketing dashboard metrics."""
    return pof.get_marketing_dashboard()

@app.get("/api/investor-report")
async def get_investor_report(year: int = 2026):
    """Investor/board summary report."""
    return pof.generate_investor_report(year)

@app.get("/api/trends")
async def get_metrics_trends(days: int = 14):
    """Historical trends for charts."""
    return pof.get_metrics_trend(days)
```

### Usage

```bash
# Get today's metrics
curl https://api.profitengine.ai/api/metrics/daily

# Validate claims
curl https://api.profitengine.ai/api/claims/validate

# Get marketing data
curl https://api.profitengine.ai/api/performers/top?limit=5

# Get trends
curl https://api.profitengine.ai/api/trends?days=30
```

---

## Python Integration

### In Django/Flask Applications

```python
# views.py
from runtime.proof_of_performance import ProofOfPerformance

def marketing_dashboard_view(request):
    pof = ProofOfPerformance()
    metrics = pof.generate_daily_metrics()
    dashboard = pof.get_marketing_dashboard()
    
    context = {
        'metrics': metrics,
        'dashboard': dashboard,
        'top_performers': pof.get_top_performers(30, 10),
    }
    
    return render(request, 'dashboard.html', context)
```

### In Next.js API Routes

```javascript
// pages/api/metrics.js
import { ProofOfPerformance } from '@/lib/proof_of_performance.py'

export default async function handler(req, res) {
    const pof = new ProofOfPerformance()
    const metrics = await pof.generateDailyMetrics()
    res.status(200).json(metrics)
}
```

### In Frontend (React/Vue)

```javascript
// hooks/useMetrics.js
import { useEffect, useState } from 'react'

export function useMetrics() {
    const [metrics, setMetrics] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/metrics/daily')
            .then(r => r.json())
            .then(data => {
                setMetrics(data)
                setLoading(false)
            })
    }, [])

    return { metrics, loading }
}

// components/MetricsCard.jsx
function MetricsCard() {
    const { metrics, loading } = useMetrics()

    if (loading) return <div>Loading...</div>

    return (
        <div className="metrics-card">
            <div className="metric">
                <span className="label">Win Rate</span>
                <span className="value">{metrics.overall_win_rate.toFixed(1)}%</span>
            </div>
            <div className="metric">
                <span className="label">Total P&L</span>
                <span className="value">${(metrics.total_pnl_generated).toLocaleString()}</span>
            </div>
            <div className="metric">
                <span className="label">Avg ROI</span>
                <span className="value">{metrics.average_customer_roi.toFixed(1)}%</span>
            </div>
        </div>
    )
}
```

---

## Dashboard Widget Integration

### Landing Page Proof Section

```html
<section class="proof-of-performance">
    <h2>Real Trading Results</h2>
    
    <div class="metrics-grid">
        <div class="metric-box">
            <div class="number" id="win-rate">87%</div>
            <div class="label">System Win Rate</div>
            <div class="source">30-day average</div>
        </div>
        
        <div class="metric-box">
            <div class="number" id="total-pnl">$1.2M</div>
            <div class="label">Total P&L Generated</div>
            <div class="source">Across all traders</div>
        </div>
        
        <div class="metric-box">
            <div class="number" id="active-users">156</div>
            <div class="label">Active Traders</div>
            <div class="source">Last 7 days</div>
        </div>
        
        <div class="metric-box">
            <div class="number" id="avg-roi">24%</div>
            <div class="label">Average ROI</div>
            <div class="source">Per customer</div>
        </div>
    </div>

    <script>
        // Load metrics from API
        fetch('/api/metrics/daily')
            .then(r => r.json())
            .then(m => {
                document.getElementById('win-rate').textContent = 
                    m.overall_win_rate.toFixed(1) + '%'
                document.getElementById('total-pnl').textContent = 
                    '$' + (m.total_pnl_generated / 1000000).toFixed(1) + 'M'
                document.getElementById('active-users').textContent = 
                    m.active_users
                document.getElementById('avg-roi').textContent = 
                    m.average_customer_roi.toFixed(0) + '%'
            })
    </script>
</section>
```

### Social Proof Section

```html
<section class="testimonials">
    <h2>Top Performers</h2>
    <div class="testimonials-grid" id="testimonials"></div>

    <script>
        fetch('/api/performers/top?limit=3')
            .then(r => r.json())
            .then(stories => {
                const html = stories.map(s => `
                    <div class="testimonial-card">
                        <div class="roi-badge">${s.roi_percentage.toFixed(0)}% ROI</div>
                        <p class="quote">
                            "I grew my account from $${s.starting_balance.toLocaleString()} 
                            to $${s.current_balance.toLocaleString()} in ${s.days_active} days 
                            with a ${s.win_rate.toFixed(0)}% win rate. Completely autonomous."
                        </p>
                        <div class="metrics">
                            <span>${s.total_pnl_generated.toLocaleString()} P&L</span>
                            <span>${s.win_rate.toFixed(1)}% win rate</span>
                        </div>
                    </div>
                `).join('')
                
                document.getElementById('testimonials').innerHTML = html
            })
    </script>
</section>
```

### Marketing Claims Section

```html
<section class="claims">
    <h2>Verified Claims</h2>
    <div id="claims-list"></div>

    <script>
        fetch('/api/claims/validate')
            .then(r => r.json())
            .then(claims => {
                const html = claims.map(c => {
                    const icon = c.validated ? '✓' : '✗'
                    const status = c.validated ? 'verified' : 'unmet'
                    return `
                        <div class="claim ${status}">
                            <span class="icon">${icon}</span>
                            <span class="text">${c.claim}</span>
                            <span class="metric">${c.actual_value.toFixed(1)}</span>
                        </div>
                    `
                }).join('')
                
                document.getElementById('claims-list').innerHTML = html
            })
    </script>
</section>
```

### Conversion Funnel Chart

```html
<section class="funnel">
    <h2>Customer Journey</h2>
    <div id="funnel-chart"></div>

    <script>
        fetch('/api/dashboard/marketing')
            .then(r => r.json())
            .then(data => {
                const funnel = data.conversion_funnel
                const stages = [
                    { name: 'Signups', value: funnel.total_signups },
                    { name: 'Active Traders', value: funnel.active_traders_30d },
                    { name: 'Paying', value: funnel.paying_customers },
                    { name: 'Profitable', value: funnel.profitable_customers }
                ]
                
                const html = stages.map(s => {
                    const width = (s.value / stages[0].value) * 100
                    return `
                        <div class="funnel-stage">
                            <div class="bar" style="width: ${width}%"></div>
                            <div class="label">${s.name}: ${s.value}</div>
                        </div>
                    `
                }).join('')
                
                document.getElementById('funnel-chart').innerHTML = html
            })
    </script>
</section>
```

### Metrics Trend Chart

```html
<section class="trends">
    <h2>14-Day Performance Trend</h2>
    <canvas id="trend-chart"></canvas>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        fetch('/api/trends?days=14')
            .then(r => r.json())
            .then(trends => {
                const ctx = document.getElementById('trend-chart').getContext('2d')
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: trends.dates,
                        datasets: [
                            {
                                label: 'Win Rate %',
                                data: trends.win_rate,
                                borderColor: '#1f77b4',
                                fill: false
                            },
                            {
                                label: 'P&L ($)',
                                data: trends.pnl,
                                borderColor: '#ff7f0e',
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                type: 'linear',
                                position: 'left',
                                title: { text: 'Win Rate %' }
                            },
                            y1: {
                                type: 'linear',
                                position: 'right',
                                title: { text: 'P&L ($)' }
                            }
                        }
                    }
                })
            })
    </script>
</section>
```

---

## Email Template Integration

### Daily Newsletter

```html
<!-- Use in email marketing platform (Mailchimp, ConvertKit, etc.) -->

<h2>ProfitEngine Daily Report - {{date}}</h2>

<p>Yesterday, our community achieved:</p>

<table class="metrics" style="width: 100%;">
    <tr>
        <td><strong>Win Rate</strong><br/>{{metrics.win_rate}}%</td>
        <td><strong>Total Trades</strong><br/>{{metrics.total_trades}}</td>
        <td><strong>P&L Generated</strong><br/>{{metrics.total_pnl_generated}}</td>
    </tr>
</table>

<h3>Top Performer Story</h3>

<blockquote>
    "I turned ${{top_performer.starting_balance}} into ${{top_performer.current_balance}} 
    with {{top_performer.win_rate}}% accuracy. No manual work needed."
</blockquote>

<p>{{top_performer.days_active}} days active | {{top_performer.roi_percentage}}% ROI</p>

<!-- Dynamically populated via API -->
```

---

## Mobile App Integration

### iOS/Swift

```swift
import Foundation

struct MetricsAPI {
    static func getDailyMetrics() async throws -> PerformanceMetrics {
        let url = URL(string: "https://api.profitengine.ai/api/metrics/daily")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(PerformanceMetrics.self, from: data)
    }
    
    static func getTopPerformers(limit: Int = 10) async throws -> [CustomerStory] {
        let url = URL(string: "https://api.profitengine.ai/api/performers/top?limit=\(limit)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([CustomerStory].self, from: data)
    }
}

// In SwiftUI
struct MetricsView: View {
    @State var metrics: PerformanceMetrics?
    
    var body: some View {
        if let m = metrics {
            VStack {
                HStack {
                    MetricBox(label: "Win Rate", value: "\(m.overall_win_rate)%")
                    MetricBox(label: "P&L", value: "$\(m.total_pnl_generated)")
                }
            }
        }
    }
    
    func loadMetrics() {
        Task {
            metrics = try await MetricsAPI.getDailyMetrics()
        }
    }
}
```

### Android/Kotlin

```kotlin
import retrofit2.Retrofit
import retrofit2.http.GET
import retrofit2.http.Query

interface MetricsApi {
    @GET("/api/metrics/daily")
    suspend fun getDailyMetrics(): PerformanceMetrics
    
    @GET("/api/performers/top")
    suspend fun getTopPerformers(@Query("limit") limit: Int = 10): List<CustomerStory>
    
    @GET("/api/claims/validate")
    suspend fun validateClaims(): List<PerformanceClaim>
}

// In ViewModel
class MetricsViewModel : ViewModel() {
    private val api = Retrofit.Builder()
        .baseUrl("https://api.profitengine.ai/")
        .build()
        .create(MetricsApi::class.java)
    
    suspend fun loadMetrics() {
        try {
            val metrics = api.getDailyMetrics()
            // Update UI with metrics
        } catch (e: Exception) {
            // Handle error
        }
    }
}
```

---

## Webhook Integration

Notify team/stakeholders when important events occur:

```python
# In daily_metrics_scheduler.py
import requests

def send_webhook_notification(event: str, data: Dict[str, Any]):
    """Send webhook notification for important events."""
    
    webhook_url = os.getenv("METRICS_WEBHOOK_URL")
    if not webhook_url:
        return
    
    payload = {
        "event": event,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        logger.warning(f"Webhook notification failed: {e}")

# Usage
if metrics.overall_win_rate >= 90:
    send_webhook_notification("high_win_rate", {
        "win_rate": metrics.overall_win_rate,
        "date": metrics.timestamp
    })

if milestones:
    for m in milestones:
        send_webhook_notification("milestone_achieved", {
            "type": m.milestone_type,
            "description": m.description,
            "date": m.achieved_date
        })
```

---

## Slack Integration

Post daily metrics to Slack:

```python
# In daily_metrics_scheduler.py
import slack_sdk

def send_slack_message(metrics: PerformanceMetrics, milestones: List[Milestone]):
    """Post daily metrics to Slack."""
    
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        return
    
    client = slack_sdk.WebClient(token=slack_token)
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"ProfitEngine Daily Report - {metrics.timestamp}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Win Rate*\n{metrics.overall_win_rate}%"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Total P&L*\n${metrics.total_pnl_generated:,.0f}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Active Users*\n{metrics.active_users}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Uptime*\n{metrics.uptime_percentage}%"
                }
            ]
        }
    ]
    
    if milestones:
        for m in milestones:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎉 *Milestone*: {m.description}"
                }
            })
    
    try:
        client.chat_postMessage(
            channel="#metrics",
            blocks=blocks
        )
    except slack_sdk.errors.SlackApiError as e:
        logger.error(f"Slack notification failed: {e}")

# Usage
send_slack_message(metrics, milestones)
```

---

## Advanced: Real-time Dashboard

Use WebSockets for live updates:

```python
# In FastAPI
from fastapi import WebSocket
import asyncio

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Send metrics every 60 seconds
            metrics = pof.generate_daily_metrics()
            await websocket.send_json({
                "metrics": asdict(metrics),
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(60)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
```

---

## Rate Limiting & Caching

```python
# Cache metrics for performance
from functools import lru_cache
from datetime import datetime, timedelta

class CachedProofOfPerformance:
    def __init__(self):
        self.pof = ProofOfPerformance()
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
    
    def get_daily_metrics(self):
        """Get metrics with 5-minute cache."""
        cache_key = "daily_metrics"
        
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data
        
        metrics = self.pof.generate_daily_metrics()
        self.cache[cache_key] = (datetime.now(), metrics)
        return metrics
```

---

**Last updated:** 2026-06-18
**API Version:** 1.0.0
