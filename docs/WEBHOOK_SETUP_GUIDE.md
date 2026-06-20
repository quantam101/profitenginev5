# Webhook Setup Guide — ProfitEngine Revenue Integration

## Overview

ProfitEngine integrates with 4 revenue platforms via webhooks for real-time transaction tracking:

| Platform | Event | Webhook URL | Manual Setup |
|----------|-------|------------|--------------|
| **Gumroad** | Product purchased | `/api/webhooks/gumroad` | [Dashboard](https://app.gumroad.com/settings/webhooks) |
| **Printify** | Order created/completed | `/api/webhooks/printify` | [Integrations](https://printify.com/integrations) |
| **Beehiiv** | Sponsorship payment | `/api/webhooks/newsletter` | [Webhooks](https://dashboard.beehiiv.com/settings/webhooks) |
| **YouTube** | Daily revenue sync | N/A (API polling) | [Analytics](https://myaccount.google.com/permissions) |

---

## 1. Gumroad Integration

### Webhook URL
```
https://profitengine.alreadyherellc.com/api/webhooks/gumroad
```

### Setup Steps

1. Go to [Gumroad Settings → Webhooks](https://app.gumroad.com/settings/webhooks)
2. Click **"Add Webhook"**
3. Enter the webhook URL above
4. Select events: **`product.purchased`**
5. Click **Save**

### Expected Payload

```json
{
  "product_id": "abc123",
  "product_name": "Trading Guide Vol 2",
  "price": 39.99,
  "purchaser": {
    "email": "buyer@example.com",
    "name": "John Doe"
  },
  "timestamp": "2026-06-20T12:30:00Z"
}
```

### Response

```json
{
  "ok": true,
  "transaction_id": "gumroad_abc123_1719922200000",
  "amount": 39.99
}
```

### Troubleshooting

- **Webhook returns 400**: Check JSON formatting in test payload
- **Webhook is silent**: Webhook may be disabled in Gumroad settings; verify "Active" toggle
- **Transactions not appearing**: Verify product is sold and webhook fired (check Gumroad webhook logs)

---

## 2. Printify Integration

### Webhook URL
```
https://profitengine.alreadyherellc.com/api/webhooks/printify
```

### Setup Steps

1. Go to [Printify App Settings](https://printify.com/integrations)
2. Navigate to **Webhooks**
3. Click **Create Webhook**
4. Enter the webhook URL above
5. Select events:
   - `order:created`
   - `order:completed`
6. Click **Save**

### Expected Payload

```json
{
  "action": "order.created",
  "data": {
    "id": "ord_12345678",
    "status": "pending",
    "total_price": 85.50,
    "currency": "USD",
    "line_items": [
      {
        "title": "Classic T-Shirt",
        "quantity": 2
      }
    ],
    "shipping_address": {
      "first_name": "Jane",
      "last_name": "Smith"
    }
  }
}
```

### Response

```json
{
  "ok": true,
  "order_id": "ord_12345678",
  "amount": 85.50,
  "status": "pending"
}
```

### Troubleshooting

- **Order not tracking**: Ensure order.created event is enabled
- **Webhook not firing**: Check Printify Shop Settings → Webhooks for logs
- **Amount is 0**: Verify order includes items before submission

---

## 3. Newsletter (Beehiiv) Sponsorship

### Webhook URL
```
https://profitengine.alreadyherellc.com/api/webhooks/newsletter
```

### Setup Steps

1. Go to [Beehiiv Settings → Webhooks](https://dashboard.beehiiv.com/settings/webhooks)
2. Click **Add Webhook**
3. Enter the webhook URL above
4. Select events:
   - `sponsor:paid`
   - `sponsor:created`
5. Click **Create**

### Expected Payload

```json
{
  "event": "sponsor.paid",
  "data": {
    "sponsor_name": "Acme Technology",
    "sponsorship_amount": 500,
    "sponsorship_duration": "1 month",
    "start_date": "2026-06-20T00:00:00Z",
    "currency": "USD"
  }
}
```

### Response

```json
{
  "ok": true,
  "sponsor": "Acme Technology",
  "amount": 500,
  "recorded_at": "2026-06-20T00:00:00Z"
}
```

### Troubleshooting

- **Webhook not triggering**: Only fires on NEW sponsor payments; test with actual sponsorship
- **Amount not matching**: Verify Beehiiv calculates amount BEFORE webhook fires
- **Duplicate entries**: Each webhook fires once; check Beehiiv webhook logs for retries

---

## 4. YouTube Analytics Integration

### Setup Steps

1. **Enable YouTube Analytics API**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create/select project
   - Enable APIs: YouTube Analytics, YouTube Data API

2. **Create OAuth 2.0 Credentials**
   - Type: **OAuth 2.0 Client ID** (Desktop app)
   - Download JSON

3. **Configure .env**
   ```bash
   YOUTUBE_CLIENT_ID=<from credentials JSON>
   YOUTUBE_CLIENT_SECRET=<from credentials JSON>
   YOUTUBE_REFRESH_TOKEN=<refresh token from auth flow>
   ```

4. **Authorize (one-time)**
   ```bash
   python backend/services/youtube_analytics.py
   # Follow OAuth flow in browser
   ```

### Manual Revenue Sync

```bash
npm run sync:youtube
# Or manually
python backend/services/youtube_analytics.py
```

### Automatic Sync (Optional)

The backend runs this daily via APScheduler:
```
Every 24 hours: Fetch previous day's AdSense revenue
```

### Troubleshooting

- **"Credentials not configured"**: Set YOUTUBE_REFRESH_TOKEN in .env
- **Revenue is 0**: New channels take 1-2 days for AdSense earnings to appear
- **API quota exceeded**: YouTube Analytics has daily limits; check quota in Cloud Console

---

## Testing Webhooks Locally

Before deploying, test with ngrok (local tunnel):

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Start ngrok tunnel
ngrok http 3000

# Terminal 3: Test webhook
curl -X POST https://[your-ngrok-url].ngrok.io/api/webhooks/gumroad \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "test",
    "product_name": "Test Product",
    "price": 99.99,
    "purchaser": {"email": "test@example.com"}
  }'
```

---

## Webhook Retry Logic

| Platform | Retry Policy | Timeout |
|----------|-------------|---------|
| Gumroad | 3 retries (exponential backoff) | 30s |
| Printify | 5 retries (12 hours max) | 30s |
| Beehiiv | 2 retries (1 hour max) | 30s |

If webhook fails after retries, manually check transaction logs:
```bash
tail -f .runtime/revenue/transactions.jsonl
```

---

## Production Verification

After deploying to OCI:

```bash
# Run webhook registration script
bash scripts/register-webhooks.sh

# Check transaction logs
tail -100 .runtime/revenue/transactions.jsonl

# Verify dashboard is receiving data
curl https://profitengine.alreadyherellc.com/api/revenue/dashboard
```

---

## Security

### Signature Verification (Optional)

Some platforms (Stripe, PayPal) sign webhooks. Configure in `.env`:

```bash
GUMROAD_WEBHOOK_SECRET=abc123def456
PRINTIFY_WEBHOOK_SECRET=xyz789
```

Currently NOT enforced in handlers. To enable:

```typescript
import crypto from 'crypto';

function verifySignature(payload: string, signature: string, secret: string): boolean {
  const hash = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return crypto.timingSafeEqual(hash, signature);
}
```

### IP Whitelist (Optional)

For production, whitelist webhook IPs in firewall:

- **Gumroad**: 192.0.2.1/24 (check current IPs in docs)
- **Printify**: 203.0.113.0/24 (check current IPs in docs)
- **Beehiiv**: 198.51.100.0/24 (check current IPs in docs)

---

## Debugging

### Enable Webhook Logging

```bash
# Add to .env
DEBUG=profitengine:webhooks

# Restart backend
npm run dev
```

### View Transaction Logs

```bash
# Last 20 transactions
tail -20 .runtime/revenue/transactions.jsonl | jq .

# Filter by channel
grep '"channel": "gumroad"' .runtime/revenue/transactions.jsonl | jq .

# Calculate daily totals
cat .runtime/revenue/transactions.jsonl | jq -r '.timestamp[:10]' | sort | uniq -c
```

### Check Webhook Delivery Status

- **Gumroad**: https://app.gumroad.com/settings/webhooks (logs tab)
- **Printify**: https://printify.com/integrations (webhook logs)
- **Beehiiv**: https://dashboard.beehiiv.com/settings/webhooks (logs tab)

---

## API Endpoints for Testing

### Test Transaction Recording

```bash
# Manually log a transaction (for testing)
curl -X POST https://profitengine.alreadyherellc.com/api/revenue/log \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "gumroad",
    "amount_usd": 99.99,
    "description": "Test sale",
    "metadata": {"test": true}
  }'
```

### Check Revenue Dashboard

```bash
curl https://profitengine.alreadyherellc.com/api/revenue/dashboard | jq .
```

---

## Support

For integration issues, check:

1. `.github/workflows/ci.yml` — CI validation includes webhook route testing
2. `tests/webhooks/` — Automated tests for all webhook handlers
3. Logs: `docker-compose logs -f web` (Vercel) or `docker-compose logs -f backend` (OCI)
