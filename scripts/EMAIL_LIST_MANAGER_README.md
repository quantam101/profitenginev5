# Email List Manager for ProfitEngine v5

Comprehensive subscriber management system with double opt-in, segmentation, engagement tracking, and integrations with Beehiiv, Resend, and Mailchimp.

## Features

### 1. Subscriber Management
- **Double Opt-In Flow**: Confirmation tokens, 7-day expiration
- **Subscriber Lifecycle**: Pending → Active → Paused/Unsubscribed/Bounced
- **Email Validation**: RFC-compliant email format checking
- **Secure Tokens**: URL-safe, cryptographically secure unsubscribe/confirmation tokens
- **Custom Fields**: Store arbitrary metadata per subscriber

### 2. Segmentation
- **Predefined Segments**: Free, Paid, VIP, Sponsor, Inactive, High/Low Engagement
- **Dynamic Criteria**: Create segments based on:
  - Subscription status
  - Minimum opens/clicks
  - Subscription duration
  - Custom attributes
- **Segment Export**: Export any segment to JSON or CSV

### 3. Engagement Tracking
- **Open Tracking**: Pixel-based email open detection
- **Click Tracking**: Link click tracking with URL logging
- **Metrics**: Per-subscriber and per-campaign statistics
  - Open count, click count, referral count
  - Open rate (%), Click-through rate (CTR)
  - Last engagement timestamp
- **User Agent & IP Logging**: Optional user context for clicks/opens

### 4. Double Opt-In Flow
```
1. User subscribes → PENDING status
2. Confirmation email sent with unique token
3. User clicks link → Status changes to ACTIVE
4. Token expires in 7 days if not confirmed
```

### 5. Unsubscribe & Preferences
- **One-Click Unsubscribe**: Via unsubscribe token in email footer
- **Preference Management**:
  - Email frequency (daily/weekly/monthly)
  - Newsletter toggle
  - Product updates toggle
  - Promotions toggle
  - Account notifications toggle
- **Pause/Resume**: Temporarily suspend without unsubscribing

### 6. Growth Automation
- **Referral System**: 
  - Generate referral tokens for existing subscribers
  - Track referred email addresses
  - Mark referrals as completed
  - Increment referrer's referral count
- **Lead Magnets**:
  - Upload free ebooks, templates, guides
  - Track downloads per magnet
  - Track subscriber vs. anonymous downloads
- **Signup Forms**: API endpoints for embedding signup forms

### 7. Email Service Integrations
- **Beehiiv**: Bulk import subscribers, segment syncing
- **Resend**: Contact list management, campaign sending
- **Mailchimp**: List synchronization, batch operations
- **Export Format**: JSON and CSV export for any platform

### 8. API Endpoints (via FastAPI wrapper)

#### Subscriber Management
```
POST   /api/email/subscribe                 - Add new subscriber
POST   /api/email/confirm                   - Confirm double opt-in
POST   /api/email/unsubscribe/{token}       - Unsubscribe via token
GET    /api/email/subscribers/{email}       - Get subscriber details
PUT    /api/email/preferences/{email}       - Update email preferences
POST   /api/email/pause/{email}             - Pause subscription
POST   /api/email/resume/{email}            - Resume subscription
```

#### Engagement Tracking
```
POST   /api/email/track/open                - Track email open (pixel)
POST   /api/email/track/click               - Track link click
GET    /api/email/metrics                   - Get overall metrics
GET    /api/email/campaigns/{id}/stats      - Get campaign stats
```

#### Campaign Management
```
POST   /api/email/campaigns                 - Create campaign
GET    /api/email/campaigns/{id}/stats      - Campaign statistics
GET    /api/email/subscribers               - List active subscribers
```

#### Segmentation
```
POST   /api/email/segments                  - Create segment
GET    /api/email/subscribers?segment=free  - Get segment subscribers
```

#### Lead Magnets
```
POST   /api/email/lead-magnets              - Add lead magnet
POST   /api/email/lead-magnets/download     - Track download
```

#### Referrals
```
POST   /api/email/referrals                 - Create referral link
```

#### Export
```
GET    /api/email/export                    - Export all subscribers
GET    /api/email/export?segment=free       - Export segment
GET    /api/email/export?format=csv         - CSV format
```

## Quick Start

### 1. Basic Usage

```python
from email_list_manager import EmailListManager

# Initialize
manager = EmailListManager("profitengine_subscribers.db")

# Add subscriber
success, msg, subscriber_id = manager.add_subscriber(
    email="user@example.com",
    name="John Doe",
    interests=["investing", "passive-income"],
    segment="free"
)

# Confirm subscription (from confirmation email link)
success, msg = manager.confirm_subscription(confirmation_token)

# Track engagement
success, msg = manager.track_open("user@example.com", campaign_id)
success, msg = manager.track_click("user@example.com", campaign_id, "https://link.com")

# Get metrics
metrics = manager.get_engagement_metrics()
# {
#   'total': 100,
#   'active': 85,
#   'pending': 5,
#   'unsubscribed': 10,
#   'by_segment': {'free': 60, 'paid': 25},
#   'avg_opens': 3.5,
#   'avg_clicks': 1.2
# }

# Export subscribers
json_data = manager.export_subscribers(segment="free", export_format="json")
csv_data = manager.export_subscribers(segment="free", export_format="csv")

manager.close()
```

### 2. Create Segments

```python
# High engagement segment
manager.create_segment(
    name="VIP Subscribers",
    segment_type="high_engagement",
    criteria={"min_opens": 10, "min_clicks": 5}
)

# Paid subscribers
manager.create_segment(
    name="Paying Customers",
    segment_type="paid",
    criteria={"status": "active", "subscription_type": "paid"}
)
```

### 3. Manage Preferences

```python
# Update email frequency
manager.update_preferences(
    subscriber_id="sub-123",
    email_frequency="weekly",
    promotions=False  # Uncheck promotions
)

# Pause/resume
manager.pause_subscription(subscriber_id)
manager.resume_subscription(subscriber_id)
```

### 4. Referral System

```python
# Create referral token
success, msg, ref_token = manager.create_referral(
    referrer_id="sub-123",
    referred_email="newuser@example.com"
)

# When referred user subscribes and confirms, complete referral
manager.complete_referral(ref_token, new_subscriber_id)

# Referrer's referral_count increments automatically
```

### 5. Lead Magnets

```python
# Add free ebook
success, msg, magnet_id = manager.add_lead_magnet(
    name="Passive Income Guide",
    description="Free 50-page guide to generating passive income",
    file_url="https://cdn.example.com/ebook-passive-income.pdf"
)

# Track download
manager.track_magnet_download(
    lead_magnet_id=magnet_id,
    email="user@example.com"
)
```

### 6. Email Service Integration

```python
from email_integrations import EmailServiceSyncManager, BeehiivIntegration

# Initialize sync manager
sync_manager = EmailServiceSyncManager(email_manager)

# Configure platforms
sync_manager.configure_beehiiv(api_key="beehiiv_api_key")
sync_manager.configure_resend(api_key="resend_api_key")

# Sync all platforms
results = sync_manager.sync_all_platforms(segment="free")
# {
#   'beehiiv': (True, 'Imported 150/150 subscribers to Beehiiv'),
#   'resend': (True, 'Imported 150/150 subscribers to Resend'),
#   'mailchimp': (True, 'Synced 150/150 subscribers to Mailchimp')
# }

# Sync specific segment to specific platforms
results = sync_manager.sync_segment(
    segment="paid",
    platforms=["beehiiv", "resend"]
)
```

### 7. FastAPI Integration

```python
from fastapi import FastAPI
from email_api_wrapper import EmailAPIWrapper

app = FastAPI()
api = EmailAPIWrapper()

@app.post("/api/email/subscribe")
async def subscribe(payload: dict):
    return api.subscribe(payload)

@app.post("/api/email/track/open")
async def track_open(payload: dict):
    return api.track_open(payload)

# ... more routes
```

## Database Schema

### Tables
- **subscribers**: Core subscriber data with engagement metrics
- **segments**: Segment definitions and criteria
- **campaigns**: Email campaign metadata
- **engagement**: Open/click event log
- **confirmations**: Double opt-in confirmation tracking
- **preferences**: Subscriber email preferences
- **referrals**: Referral relationship tracking
- **lead_magnets**: Free lead magnet definitions
- **magnet_downloads**: Download tracking per magnet

### Indexes
- `idx_email`: Fast lookup by email
- `idx_status`: Filter by subscription status
- `idx_segment`: Filter by segment
- `idx_campaign_id`: Campaign event lookups
- `idx_subscriber_id`: Subscriber event lookups
- `idx_confirmation_token`: Confirmation validation

## Environment Variables

```bash
# Email service integrations
BEEHIIV_API_KEY=<beehiiv-api-key>
RESEND_API_KEY=<resend-api-key>
RESEND_AUDIENCE_ID=<resend-audience-id>
MAILCHIMP_API_KEY=<mailchimp-api-key>
MAILCHIMP_LIST_ID=<mailchimp-list-id>
MAILCHIMP_SERVER_PREFIX=us1  # e.g., us1, us2, us3

# Database
EMAIL_DB_PATH=profitengine_subscribers.db
```

## API Response Format

All API endpoints return JSON in this format:

```json
{
  "success": true|false,
  "data": {...},  // Optional, present if success=true
  "message": "Human-readable message",
  "error": "Error message",  // Optional, present if success=false
  "code": "STATUS_CODE"  // SUBSCRIBER_ADDED, CONFIRMATION_FAILED, etc.
}
```

## Security Considerations

1. **Token Security**: All tokens are generated using `secrets.token_urlsafe()` - cryptographically secure
2. **Email Validation**: RFC-compliant email format checking
3. **SQL Injection Prevention**: All queries use parameterized statements
4. **Sensitive Data**: No passwords stored; unsubscribe tokens are one-use
5. **Rate Limiting**: Should be added at FastAPI middleware level
6. **CORS**: Configure as needed for your domain
7. **HTTPS Only**: All email links should be HTTPS

## Performance

- **Indexing**: All common query patterns have indexes
- **Pagination**: Limit parameter in list endpoints
- **Batch Operations**: Beehiiv/Mailchimp use batch APIs
- **SQLite Optimization**: WAL mode for concurrent access
- **Connection Pooling**: Ready for PostgreSQL migration

## Monitoring

The system logs all operations to INFO level:
- Subscriber additions/confirmations
- Preference updates
- Engagement events
- Integration syncs
- Errors with context

## Testing

Run the demo to verify installation:

```bash
python3 scripts/email_list_manager.py
```

Expected output:
```
=== ProfitEngine Email List Manager Demo ===

1. Adding subscribers...
2. Confirming subscriptions...
3. Creating segments...
4. Creating campaign...
5. Tracking email engagement...
6. Fetching active subscribers...
7. Engagement metrics...
8. Exporting subscribers...
9. Adding lead magnet...
10. Testing referral system...

=== Demo Complete ===
```

## Migration Path

### From Mailchimp
```python
# Export subscribers from Mailchimp
# Convert to JSON with: email, name, segment, interests
# Import via bulk endpoint
```

### From Beehiiv
```python
# Export subscribers from Beehiiv
# Map fields to local schema
# Import via subscription endpoint
```

### To PostgreSQL
Schema is fully portable - just swap SQLite for PostgreSQL connection string.

## Next Steps

1. **Email Service Setup**: Get API keys for Beehiiv/Resend/Mailchimp
2. **Domain Setup**: Configure your domain for email sending
3. **Integration Testing**: Test with a small batch first
4. **Webhook Handling**: Implement bounce/complaint webhooks from email services
5. **Analytics Dashboard**: Build visualization on top of metrics endpoint

## Support

For issues or questions:
1. Check logs: `tail -f logs/*.log`
2. Verify database: `sqlite3 profitengine_subscribers.db ".tables"`
3. Test API: Run demo script with your configuration
4. Check environment variables are set correctly
