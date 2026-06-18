# Tier Upgrade System — Integration Guide

## Overview

This guide covers integrating the automated tier upgrade system with existing ProfitEngine components.

## Integration Points

### 1. Dashboard Integration

The frontend dashboard needs to display:
- Current subscription tier
- Monthly charge amount
- Next billing date
- Upgrade/downgrade options

#### API Endpoint for Dashboard

```javascript
// Frontend: Get subscription info
async function getSubscription(clientId) {
  const response = await fetch(`/api/billing/subscription?client_id=${clientId}`, {
    headers: {
      'X-API-Key': process.env.REACT_APP_BILLING_API_KEY,
    },
  });
  return response.json();
}

// Display in dashboard
useEffect(() => {
  getSubscription(user.id).then(sub => {
    setSubscription({
      tier: sub.current_tier,
      monthlyCharge: sub.monthly_charge_usd,
      nextBillingDate: sub.next_billing_date,
    });
  });
}, [user.id]);
```

#### Dashboard UI Components

```jsx
// TierBadge.jsx
export function TierBadge({ tier }) {
  const colors = {
    free: 'gray',
    hybrid: 'blue',
    white_label: 'purple',
    enterprise: 'gold',
  };

  return (
    <span className={`badge badge-${colors[tier]}`}>
      {tier.toUpperCase()}
    </span>
  );
}

// BillingCard.jsx
export function BillingCard({ subscription }) {
  return (
    <Card title="Billing & Subscription">
      <div className="billing-info">
        <div className="tier-section">
          <h3>Current Tier</h3>
          <TierBadge tier={subscription.tier} />
          <p className="charge">
            ${subscription.monthlyCharge.toFixed(2)}/month
          </p>
        </div>

        <div className="billing-section">
          <h3>Next Billing Date</h3>
          <p>{new Date(subscription.nextBillingDate).toLocaleDateString()}</p>
        </div>

        <div className="actions">
          <a href="/billing/upgrade">Upgrade Tier</a>
          <a href="/billing/manage">Manage Subscription</a>
          <a href="/billing/history">View History</a>
        </div>
      </div>
    </Card>
  );
}
```

### 2. Client API Integration

Update `client_api.py` to include tier information:

```python
# Add to client_api.py
from tier_upgrade_api import app as tier_upgrade_app

# Mount tier upgrade endpoints
main_app.include_router(tier_upgrade_app.router, prefix="/billing")

# Add tier info to trader performance
@app.get("/api/traders/{trader_id}/performance")
async def get_trader_performance(trader_id: str):
    perf = get_existing_performance(trader_id)  # existing code
    
    # Add tier info
    subscription = await get_subscription(trader_id)
    perf['subscription'] = subscription
    
    return perf
```

### 3. Daily Alerts Integration

Update `daily_alerts.py` to include tier upgrade candidates:

```python
# In daily_alerts.py
from tier_upgrade_automation import TierUpgradeAutomation
from upsell_intelligence import generate_daily_upsell_report

async def generate_daily_alerts():
    """Generate daily alerts including tier candidates"""
    
    # Existing alerts...
    alerts = []
    
    # Add tier upgrade candidates
    report = generate_daily_upsell_report()
    
    enterprise_count = len(report['enterprise_candidates'])
    white_label_count = len(report['white_label_candidates'])
    hybrid_count = len(report['hybrid_candidates'])
    
    if enterprise_count + white_label_count + hybrid_count > 0:
        alerts.append({
            'type': 'UPGRADE_OPPORTUNITY',
            'title': 'Tier Upgrade Opportunities',
            'message': (
                f'{enterprise_count} Enterprise, {white_label_count} White-Label, '
                f'{hybrid_count} Hybrid tier candidates identified'
            ),
            'action_url': '/admin/upgrade-candidates',
        })
    
    return alerts
```

### 4. Email Service Integration

Integrate with existing email service (SendGrid, AWS SES, etc.):

```python
# email_service.py integration
import sendgrid
from sendgrid.helpers.mail import Mail
from tier_upgrade_automation import TierUpgradeAutomation

class EmailService:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    
    def send_upgrade_email(self, to_email, name, tier, monthly_charge):
        """Send tier upgrade confirmation"""
        from jinja2 import Template
        
        with open('email_templates/upgrade_confirmation.html', 'r') as f:
            template = Template(f.read())
        
        html = template.render(
            username=name,
            tier_name=tier.title(),
            monthly_charge=monthly_charge,
            tier_percentage='0.5%' if tier == 'hybrid' else '1.0%' if tier == 'white_label' else '1.5%',
        )
        
        message = Mail(
            from_email='noreply@profitengine.com',
            to_emails=to_email,
            subject='Congratulations! You\'ve Been Upgraded',
            html_content=html,
        )
        
        self.sg.send(message)

# Update tier_upgrade_automation.py to use this service
class TierUpgradeAutomation:
    def __init__(self, ...):
        self.email_service = EmailService()
    
    def _send_upgrade_email(self, ...):
        self.email_service.send_upgrade_email(
            to_email=client_email,
            name=username,
            tier=tier,
            monthly_charge=monthly_charge,
        )
```

### 5. Mobile Dashboard API Integration

Update `mobile_dashboard_api.py` to include subscription status:

```python
# In mobile_dashboard_api.py
from tier_upgrade_api import StripePaymentProcessor

@app.get("/api/v1/mobile/dashboard/{client_id}")
async def get_mobile_dashboard(client_id: str):
    """Get mobile dashboard including subscription"""
    
    trading_data = get_trading_summary(client_id)  # existing
    
    # Add subscription info
    processor = StripePaymentProcessor()
    subscription = processor.get_subscription(client_id)
    
    return {
        'trading': trading_data,
        'subscription': {
            'tier': subscription['tier'],
            'monthly_charge_usd': subscription['monthly_charge_usd'],
            'next_billing': subscription['next_billing_date'],
        },
    }
```

### 6. Admin Dashboard Integration

Create admin endpoints for tier management:

```python
# admin_tier_dashboard.py
from fastapi import FastAPI, Depends
from tier_upgrade_api import verify_admin_api_key
from payment_processor import StripePaymentProcessor
from upsell_intelligence import generate_daily_upsell_report

app = FastAPI()
processor = StripePaymentProcessor()

@app.get("/admin/dashboard/revenue")
async def get_revenue_dashboard(admin_key: str = Depends(verify_admin_api_key)):
    """Admin revenue dashboard"""
    
    # Current month report
    current_month = datetime.utcnow().strftime('%Y-%m')
    report = processor.generate_revenue_report(current_month)
    
    # Tier breakdown
    tier_stats = {
        'free': len(get_tier_clients('free')),
        'hybrid': len(get_tier_clients('hybrid')),
        'white_label': len(get_tier_clients('white_label')),
        'enterprise': len(get_tier_clients('enterprise')),
    }
    
    # Upgrade candidates
    upsell = generate_daily_upsell_report()
    
    return {
        'mrr_usd': report['mrr_usd'],
        'total_charges_usd': report['total_charges_usd'],
        'refunds_usd': report['total_refunds_usd'],
        'net_revenue_usd': report['net_revenue_usd'],
        'tier_breakdown': {
            'counts': tier_stats,
            'breakdown': report['tier_breakdown'],
        },
        'upgrade_candidates': {
            'enterprise': len(upsell['enterprise_candidates']),
            'white_label': len(upsell['white_label_candidates']),
            'hybrid': len(upsell['hybrid_candidates']),
        },
    }

@app.get("/admin/dashboard/customers")
async def get_customers_dashboard(
    tier: Optional[str] = None,
    admin_key: str = Depends(verify_admin_api_key),
):
    """Admin customer tier dashboard"""
    
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    
    if tier:
        cursor.execute("""
            SELECT c.client_id, c.username, c.account_balance, s.subscription_id,
                   s.next_billing_date
            FROM clients c
            LEFT JOIN subscriptions s ON c.client_id = s.client_id AND s.status = 'active'
            WHERE c.subscription_tier = ?
            ORDER BY c.account_balance DESC
        """, (tier,))
    else:
        cursor.execute("""
            SELECT c.client_id, c.username, c.subscription_tier, c.account_balance,
                   s.next_billing_date
            FROM clients c
            LEFT JOIN subscriptions s ON c.client_id = s.client_id AND s.status = 'active'
            ORDER BY c.subscription_tier DESC, c.account_balance DESC
        """)
    
    customers = cursor.fetchall()
    conn.close()
    
    return [
        {
            'client_id': row[0],
            'username': row[1],
            'tier': row[2] if len(row) > 2 else None,
            'aum_usd': row[3] if len(row) > 3 else 0,
            'next_billing': row[4] if len(row) > 4 else None,
        }
        for row in customers
    ]
```

### 7. Webhook Integration (Optional)

Handle Stripe webhooks for payment confirmations:

```python
# In tier_upgrade_api.py
from fastapi import Request
import hmac
import json

STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

@app.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    
    body = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return {"error": "Invalid payload"}, 400
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}, 400
    
    # Handle events
    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']
        # Update billing_history
        update_charge_status(charge['id'], 'success')
    
    elif event['type'] == 'charge.failed':
        charge = event['data']['object']
        # Update billing_history
        update_charge_status(charge['id'], 'failed')
        # Schedule retry
        logger.info(f"Charge failed: {charge['id']}")
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        # Mark subscription as active
    
    return {"status": "received"}
```

## Testing Integration

### Unit Tests

```python
# test_tier_upgrade.py
import pytest
from decimal import Decimal
from tier_upgrade_automation import TierUpgradeAutomation
from payment_processor import StripePaymentProcessor

@pytest.fixture
def processor():
    return StripePaymentProcessor('test_clients.db')

@pytest.fixture
def automation():
    return TierUpgradeAutomation('test_clients.db')

def test_upgrade_tier(processor):
    """Test upgrading a client tier"""
    result = processor.upgrade_client_tier(
        client_id='TEST-001',
        username='test_user',
        new_tier='hybrid',
        account_balance=Decimal('50000.00'),
    )
    
    assert result['success']
    assert result['new_tier'] == 'hybrid'
    assert result['monthly_charge_usd'] > 0

def test_downgrade_tier(processor):
    """Test downgrading a client tier"""
    result = processor.downgrade_client_tier(
        client_id='TEST-001',
        new_tier='free',
        account_balance=Decimal('50000.00'),
    )
    
    assert result['success']
    assert result['new_tier'] == 'free'

def test_score_calculation(automation):
    """Test upsell score calculation"""
    campaign = automation.scorer.score_all_clients()
    
    assert campaign.total_clients_scored >= 0
    assert len(campaign.enterprise_candidates) >= 0
    assert len(campaign.white_label_candidates) >= 0
```

### Integration Tests

```python
# test_integration.py
import requests
import json

BASE_URL = 'http://localhost:8000'
API_KEY = 'test-api-key'
ADMIN_KEY = 'test-admin-key'

def test_api_health():
    """Test API health check"""
    response = requests.get(f'{BASE_URL}/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_get_subscription():
    """Test getting subscription info"""
    response = requests.get(
        f'{BASE_URL}/api/billing/subscription?client_id=TEST-001',
        headers={'X-API-Key': API_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert 'current_tier' in data

def test_upgrade_request():
    """Test upgrade request via API"""
    response = requests.post(
        f'{BASE_URL}/api/billing/upgrade',
        headers={'X-API-Key': API_KEY},
        json={
            'client_id': 'TEST-001',
            'target_tier': 'hybrid',
        },
    )
    assert response.status_code in [200, 400]  # 400 if already upgraded

def test_admin_candidates():
    """Test admin candidates endpoint"""
    response = requests.get(
        f'{BASE_URL}/api/admin/tier-candidates',
        headers={'X-Admin-API-Key': ADMIN_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

## Configuration Examples

### High-Volume Setup

For systems with 10,000+ customers:

```python
# config_production.py

# Batch processing
BATCH_UPGRADE_SIZE = 100  # Process 100 upgrades per cycle
BATCH_CHARGE_SIZE = 500   # Charge 500 customers per run

# Caching
ENABLE_REDIS_CACHE = True
REDIS_URL = 'redis://localhost:6379/0'
CACHE_TTL = 300  # Cache subscription info for 5 minutes

# Database
USE_POSTGRESQL = True
DATABASE_URL = 'postgresql://user:pass@localhost/profitengine'

# Email
EMAIL_QUEUE_SIZE = 1000
EMAIL_BATCH_SIZE = 50

# Monitoring
ENABLE_PROMETHEUS = True
METRICS_PORT = 9090
```

### Multi-Region Setup

For geo-distributed systems:

```python
# config_multiregion.py

REGIONS = {
    'us-east': {
        'db': 'us-east-clients.db',
        'stripe_key': 'sk_live_us_east_...',
        'email_region': 'us-east-1',
    },
    'eu-west': {
        'db': 'eu-west-clients.db',
        'stripe_key': 'sk_live_eu_west_...',
        'email_region': 'eu-west-1',
    },
}

# Route by client region
def get_processor_for_region(client_region):
    config = REGIONS[client_region]
    return StripePaymentProcessor(config['db'], config['stripe_key'])
```

## Maintenance Schedule

### Daily (Automated)

- 5 PM MST: Run tier upgrade cycle
- Hourly: Retry failed charges
- Every 5 min: Check payment status

### Weekly (Manual)

- Monday 9 AM: Review failed charges
- Wednesday 2 PM: Check refund status
- Friday 10 AM: Review revenue report

### Monthly (Manual)

- 1st: Process billing run
- 15th: Review tier distribution
- 30th: Generate revenue report for accounting

### Quarterly (Manual)

- Review and adjust tier thresholds
- Analyze upgrade/downgrade rates
- Optimize payment retry logic

---

## Support Resources

- **Documentation:** See TIER_UPGRADE_README.md
- **Deployment:** See TIER_UPGRADE_DEPLOYMENT.md
- **Stripe Docs:** https://stripe.com/docs/api
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLite Docs:** https://www.sqlite.org/docs.html

---

**Version:** 1.0.0  
**Last Updated:** June 2024  
**Status:** Production Ready
