# Email List Manager - API Quick Reference

## Base URL
```
http://localhost:8000/api/email
```

## Response Format
All endpoints return JSON:
```json
{
  "success": true,
  "data": {...},
  "message": "Description",
  "code": "STATUS_CODE"
}
```

---

## Subscriber Management

### Subscribe (Add Subscriber)
```http
POST /subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "interests": ["investing", "passive-income"],
  "segment": "free"
}
```
**Response**:
```json
{
  "success": true,
  "message": "Confirmation email sent to user@example.com",
  "subscriber_id": "uuid",
  "code": "SUBSCRIBER_ADDED"
}
```

### Confirm Subscription
```http
POST /confirm
Content-Type: application/json

{
  "token": "confirmation_token_from_email"
}
```

### Unsubscribe
```http
POST /unsubscribe
Content-Type: application/json

{
  "token": "unsubscribe_token"
}
```

### Get Subscriber
```http
GET /subscribers/user@example.com
```
**Response**:
```json
{
  "success": true,
  "data": {
    "email": "user@example.com",
    "name": "John Doe",
    "status": "active",
    "segment": "free",
    "open_count": 5,
    "click_count": 2,
    "referral_count": 0,
    "date_joined": "2026-06-19T10:00:00",
    "last_engagement": "2026-06-19T12:00:00"
  },
  "code": "SUBSCRIBER_FOUND"
}
```

### Update Preferences
```http
PUT /preferences/user@example.com
Content-Type: application/json

{
  "email_frequency": "weekly",
  "newsletter": true,
  "product_updates": true,
  "promotions": false,
  "account_notifications": true
}
```

### Pause Subscription
```http
POST /pause/user@example.com
```

### Resume Subscription
```http
POST /resume/user@example.com
```

---

## Engagement Tracking

### Track Open (Pixel Tracking)
```http
POST /track/open
Content-Type: application/json

{
  "email": "user@example.com",
  "campaign_id": "campaign-123",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

### Track Click
```http
POST /track/click
Content-Type: application/json

{
  "email": "user@example.com",
  "campaign_id": "campaign-123",
  "link_url": "https://alreadyherellc.com/article",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

---

## Campaigns

### Create Campaign
```http
POST /campaigns
Content-Type: application/json

{
  "name": "Weekly Newsletter",
  "subject": "Your Weekly Update",
  "segment_id": "segment-id-optional"
}
```
**Response**:
```json
{
  "success": true,
  "campaign_id": "campaign-123",
  "code": "CAMPAIGN_CREATED"
}
```

### Get Campaign Stats
```http
GET /campaigns/campaign-123/stats
```
**Response**:
```json
{
  "success": true,
  "data": {
    "campaign_id": "campaign-123",
    "name": "Weekly Newsletter",
    "sent_count": 500,
    "open_count": 150,
    "click_count": 45,
    "open_rate": 30.0,
    "ctr": 30.0
  },
  "code": "STATS_RETRIEVED"
}
```

---

## Segmentation

### Create Segment
```http
POST /segments
Content-Type: application/json

{
  "name": "VIP Customers",
  "segment_type": "high_engagement",
  "criteria": {
    "min_opens": 10,
    "min_clicks": 5
  }
}
```

### Get Subscribers
```http
GET /subscribers?segment=free&limit=100
```
**Query Parameters**:
- `segment`: Filter by segment (optional)
- `limit`: Max results (default: 1000)

---

## Lead Magnets

### Add Lead Magnet
```http
POST /lead-magnets
Content-Type: application/json

{
  "name": "Passive Income Guide",
  "description": "Free 50-page guide to generating passive income",
  "file_url": "https://cdn.alreadyherellc.com/ebook-passive-income.pdf"
}
```

### Track Download
```http
POST /lead-magnets/download
Content-Type: application/json

{
  "lead_magnet_id": "magnet-123",
  "email": "user@example.com",
  "subscriber_id": "sub-123"
}
```
**Note**: Provide either `email` or `subscriber_id`

---

## Referrals

### Create Referral Link
```http
POST /referrals
Content-Type: application/json

{
  "referrer_id": "subscriber-id",
  "referred_email": "newuser@example.com"
}
```
**Response**:
```json
{
  "success": true,
  "referral_token": "ref_token_123",
  "code": "REFERRAL_CREATED"
}
```

---

## Analytics

### Get Metrics
```http
GET /metrics
```
**Response**:
```json
{
  "success": true,
  "data": {
    "total": 1000,
    "active": 850,
    "pending": 50,
    "unsubscribed": 100,
    "avg_opens": 3.5,
    "avg_clicks": 1.2,
    "max_opens": 25,
    "max_clicks": 10,
    "by_segment": {
      "free": 600,
      "paid": 250
    }
  },
  "code": "METRICS_RETRIEVED"
}
```

### Export Subscribers
```http
GET /export?segment=free&format=json
```
**Query Parameters**:
- `segment`: Filter by segment (optional)
- `format`: `json` or `csv` (default: json)

**JSON Response**:
```json
{
  "success": true,
  "data": "[{\"email\":\"...\",\"name\":\"...\"}]",
  "format": "json",
  "code": "EXPORT_COMPLETE"
}
```

---

## Error Codes

| Code | Meaning | HTTP Status |
|------|---------|-------------|
| `INVALID_INPUT` | Missing or invalid parameters | 400 |
| `SUBSCRIBER_ADDED` | Subscription created | 201 |
| `SUBSCRIBER_FOUND` | Subscriber retrieved | 200 |
| `NOT_FOUND` | Subscriber not found | 404 |
| `CONFIRMED` | Email confirmed | 200 |
| `CONFIRMATION_FAILED` | Confirmation token invalid/expired | 400 |
| `UNSUBSCRIBED` | Successfully unsubscribed | 200 |
| `PREFERENCES_UPDATED` | Preferences saved | 200 |
| `OPEN_TRACKED` | Open recorded | 200 |
| `CLICK_TRACKED` | Click recorded | 200 |
| `CAMPAIGN_CREATED` | Campaign added | 201 |
| `STATS_RETRIEVED` | Stats fetched | 200 |
| `SEGMENT_CREATED` | Segment added | 201 |
| `MAGNET_ADDED` | Lead magnet added | 201 |
| `DOWNLOAD_TRACKED` | Download recorded | 200 |
| `REFERRAL_CREATED` | Referral link generated | 201 |
| `METRICS_RETRIEVED` | Metrics fetched | 200 |
| `EXPORT_COMPLETE` | Export generated | 200 |
| `SERVER_ERROR` | Internal error | 500 |

---

## Email HTML Templates

### Confirmation Email
```html
<h1>Confirm Your Subscription</h1>
<p>Hi {{name}},</p>
<p>Please confirm your email address by clicking the link below:</p>
<a href="https://alreadyherellc.com/email/confirm?token={{token}}">
  Confirm Email Address
</a>
<p>This link expires in 7 days.</p>
```

### Unsubscribe Link (Footer)
```html
<footer>
  <p>Not interested? <a href="https://alreadyherellc.com/email/unsubscribe?token={{unsubscribe_token}}">Unsubscribe</a></p>
</footer>
```

### Open Tracking Pixel
```html
<!-- Add before closing </body> tag -->
<img src="https://api.alreadyherellc.com/api/email/track/open?email={{email}}&campaign_id={{campaign_id}}" 
     width="1" height="1" style="display:none;" alt="" />
```

### Click Tracking Redirect
```html
<!-- Wrap links like this -->
<a href="https://api.alreadyherellc.com/api/email/track/click?email={{email}}&campaign_id={{campaign_id}}&link_url={{encoded_url}}">
  Read Article
</a>
```

---

## Common Use Cases

### 1. Newsletter Signup Form
```javascript
async function signupNewsletter(email, name) {
  const response = await fetch('/api/email/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name, interests: [], segment: 'free' })
  });
  return await response.json();
}
```

### 2. Confirmation Page (from email link)
```javascript
// Extract token from URL: ?token=xyz
async function confirmEmail(token) {
  const response = await fetch('/api/email/confirm', {
    method: 'POST',
    body: JSON.stringify({ token })
  });
  return await response.json();
}
```

### 3. Email Preferences Page
```javascript
async function updatePreferences(email) {
  const response = await fetch(`/api/email/preferences/${email}`, {
    method: 'PUT',
    body: JSON.stringify({
      email_frequency: 'weekly',
      promotions: false
    })
  });
  return await response.json();
}
```

### 4. Track Campaign Opens
```html
<!-- In email template -->
<img src="/api/email/track/open?email={{user_email}}&campaign_id={{campaign_id}}" 
     width="1" height="1" alt="" />
```

### 5. Send Data to Beehiiv
```python
from email_integrations import EmailServiceSyncManager

sync = EmailServiceSyncManager(manager)
sync.configure_beehiiv(api_key)
results = sync.sync_all_platforms(segment='free')
```

### 6. Generate Referral Link
```python
success, msg, ref_token = manager.create_referral(
  referrer_id='sub-123',
  referred_email='friend@example.com'
)
# Share link: https://alreadyherellc.com/refer?token={{ref_token}}
```

---

## Rate Limiting (Production)

Recommended limits per IP address:
- Subscribe endpoint: 10 per hour
- Magnet downloads: 5 per day per email
- Track endpoints: Unlimited (can be IP-specific)
- Export endpoints: 10 per day
- Other endpoints: 100 per hour

---

## Environment Variables

```bash
# Service
EMAIL_DB_PATH=profitengine_subscribers.db

# Email Services
BEEHIIV_API_KEY=xxx
RESEND_API_KEY=xxx
MAILCHIMP_API_KEY=xxx

# URLs
CONFIRMATION_BASE_URL=https://alreadyherellc.com/email/confirm
UNSUBSCRIBE_BASE_URL=https://alreadyherellc.com/email/unsubscribe

# Security
REQUIRE_HTTPS=true
CORS_ALLOWED_ORIGINS=https://alreadyherellc.com,https://app.alreadyherellc.com
```

---

## cURL Examples

### Subscribe
```bash
curl -X POST http://localhost:8000/api/email/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "interests": ["investing"]
  }'
```

### Get Metrics
```bash
curl -X GET http://localhost:8000/api/email/metrics
```

### Export Subscribers
```bash
curl -X GET 'http://localhost:8000/api/email/export?segment=free&format=json' \
  > subscribers.json
```

### Track Open
```bash
curl -X POST http://localhost:8000/api/email/track/open \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "campaign_id": "campaign-123"
  }'
```

---

## Webhooks (For Email Service Notifications)

Implement handlers for:
- `bounce`: Hard bounce detected
- `complaint`: User complaint filed
- `delivery`: Email delivered
- `open`: Email opened (if provider supports)
- `click`: Link clicked (if provider supports)
- `unsubscribe`: Unsubscribed via provider

Update subscriber status accordingly.

---

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "service": "email-manager"}
```

### Check Active Subscribers
```bash
curl http://localhost:8000/api/email/metrics | jq '.data.active'
```

### Verify Database
```bash
sqlite3 profitengine_subscribers.db "SELECT COUNT(*) FROM subscribers WHERE status='active';"
```

---

**Last Updated**: June 19, 2026
**Version**: 1.0.0
**Status**: Production Ready
