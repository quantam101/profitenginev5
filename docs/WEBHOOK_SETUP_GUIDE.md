# ProfitEngine v5 — Webhook Configuration & Setup Guide

**Last Updated:** 2026-06-20  
**Status:** Production-Ready  
**Scope:** Gumroad, Printify, Beehiiv, YouTube Analytics

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Platform-Specific Setup](#platform-specific-setup)
4. [Webhook Payload Formats](#webhook-payload-formats)
5. [Security & Signature Verification](#security--signature-verification)
6. [Troubleshooting](#troubleshooting)
7. [Testing & Monitoring](#testing--monitoring)
8. [FAQ](#faq)

---

## Overview

ProfitEngine v5 integrates revenue from four key sources via webhooks:

| Platform | Source | Events | Log File |
|----------|--------|--------|----------|
| **Gumroad** | Ebook/course sales | product.purchased | .runtime/revenue/transactions.jsonl |
| **Printify** | POD (print-on-demand) | order.created, order.completed | .runtime/revenue/transactions.jsonl |
| **Beehiiv** | Newsletter sponsorships | sponsor.created, sponsor.paid | .runtime/revenue/transactions.jsonl |
| **YouTube Analytics** | AdSense revenue | Daily sync | .runtime/revenue/transactions.jsonl |

All webhooks write normalized transaction records to a single JSONL file, enabling unified revenue tracking and dashboarding.

### Key Benefits

- **Real-time ingestion** — Sales and sponsorships recorded immediately
- **Unified ledger** — All revenue sources in one queryable file
- **Zero dependencies** — No database required (file-based)
- **Audit trail** — Full event payload preserved in metadata
- **Error resilient** — Webhook processing continues even if file logging fails

---

## Quick Start

### Prerequisites

``ash
# Ensure you have:
1. curl (for testing webhooks)
2. jq (optional, for JSON parsing)
3. .env file with at least PUBLIC_SITE_URL set
``

### Automatic Verification

``ash
# Test all webhook endpoints
./scripts/register-webhooks.sh --verify-only

# Example output:
# 🔗 ProfitEngine v5 — Webhook Registration System
# =====================================
# Testing domain reachability... ✅ Reachable
# 1️⃣  Gumroad... ✅ OK (HTTP 200)
# 2️⃣  Printify... ✅ OK (HTTP 200)
# 3️⃣  Beehiiv... ✅ OK (HTTP 200)
# 4️⃣  YouTube Analytics... ✅ Configured
# 5️⃣  Revenue Dashboard... ✅ OK (HTTP 200)
``

### Full Registration (with API setup)

``ash
# Register all webhooks (requires credentials in .env)
./scripts/register-webhooks.sh

# Log saved to: webhooks-registration.log
``

---

## Platform-Specific Setup

### 1. Gumroad (Ebook/Course Sales)

#### Webhook URL
``
https://profitengine.alreadyherellc.com/api/webhooks/gumroad
``

#### Events Tracked
- product.purchased — Any sale of your product
- license_issued — License key generated (for licensed products)

#### Manual Configuration

1. **Go to Gumroad Dashboard**
   - Visit: https://app.gumroad.com/settings/webhooks

2. **Add Webhook**
   - Webhook URL: https://profitengine.alreadyherellc.com/api/webhooks/gumroad
   - Select events: product.purchased, license_issued

3. **Test**
   ``ash
   curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
     -H "Content-Type: application/json" \
     -d '{
       "product_id": "test-product",
       "product_name": "Test Ebook",
       "price": "29.99",
       "purchase_email": "buyer@example.com"
     }'
   ``

#### Expected Response

``json
{
  "ok": true,
  "transaction_id": "gumroad_test-product_1718832000",
  "amount_usd": 29.99,
  "product_name": "Test Ebook",
  "purchaser_email": "buyer@example.com",
  "logged": true
}
``

---

### 2. Printify (POD Order Tracking)

#### Webhook URL
``
https://profitengine.alreadyherellc.com/api/webhooks/printify
``

#### Events Tracked
- order.created — New order received
- order.completed — Order fulfilled/shipped

#### Automatic Registration (Recommended)

``ash
# Auto-detects your shop and registers the webhook
./scripts/register_printify_webhook.sh

# Or with specific shop ID:
./scripts/register_printify_webhook.sh --shop-id YOUR_SHOP_ID

# Verify endpoint:
./scripts/register_printify_webhook.sh --verify-only
``

#### Manual Configuration

1. Go to: https://printify.com/integrations
2. Add webhook URL: https://profitengine.alreadyherellc.com/api/webhooks/printify
3. Select events: order.created, order.completed

---

### 3. Beehiiv (Newsletter Sponsorships)

#### Webhook URL
``
https://profitengine.alreadyherellc.com/api/webhooks/newsletter
``

#### Events Tracked
- sponsor.created — Sponsorship agreement created
- sponsor.paid — Payment received from sponsor

#### Manual Configuration

1. Go to: https://dashboard.beehiiv.com/settings/webhooks
2. Add webhook URL: https://profitengine.alreadyherellc.com/api/webhooks/newsletter
3. Select events: sponsor.created, sponsor.paid
4. Store API key in .env: BEEHIIV_API_KEY=your_key_here

---

### 4. YouTube Analytics (AdSense Revenue Sync)

#### Overview

YouTube Analytics integration syncs AdSense revenue daily at 08:00 UTC.

#### Manual Configuration

1. Go to: https://console.cloud.google.com/apis/dashboard
2. Enable: YouTube Analytics API
3. Create OAuth 2.0 credentials (Desktop app)
4. Run: python scripts/youtube_oauth_setup.py
5. Set in .env:
   ``ash
   YOUTUBE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=your-client-secret
   YOUTUBE_REFRESH_TOKEN=your-refresh-token
   YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxx
   ``

---

## Webhook Payload Formats

All webhooks normalize to transaction records in .runtime/revenue/transactions.jsonl:

``	ypescript
interface TransactionRecord {
  channel: "gumroad" | "printify" | "newsletter" | "youtube";
  source_id: string;
  timestamp: string;
  amount_usd: number;
  cogs?: number;
  profit?: number;
  profit_margin?: number;
  description: string;
  content_id: string;
  metadata: Record<string, unknown>;
}
``

---

## Security & Signature Verification

### Beehiiv Signature Verification

Verify HMAC-SHA256 signatures before processing:

``	ypescript
import crypto from 'crypto';

function verifyBeehiivSignature(
  payload: string,
  signature: string,
  apiKey: string
): boolean {
  const hash = crypto
    .createHmac('sha256', apiKey)
    .update(payload)
    .digest('hex');
  return hash === signature;
}
``

---

## Troubleshooting

### Issue: "Webhook endpoint unreachable (HTTP 000)"

**Solutions:**
1. Verify domain is publicly accessible: curl https://profitengine.alreadyherellc.com/health
2. Check DNS: 
slookup profitengine.alreadyherellc.com
3. Verify Vercel deployment is live
4. Check backend: docker-compose ps

---

### Issue: "Webhook registered but no events received"

**Solutions:**
1. Verify webhook URL in platform settings
2. Check for typos in domain or endpoint path
3. Trigger test event (e.g., make test purchase)
4. Check logs: ercel logs | grep webhook

---

### Issue: "Invalid signature" (Beehiiv)

**Solutions:**
1. Verify BEEHIIV_API_KEY in .env is correct
2. Ensure using raw request body for verification
3. Regenerate API key in Beehiiv dashboard if needed

---

### Issue: "Transaction not logged"

**Solutions:**
1. Check directory permissions: chmod 755 .runtime/revenue
2. Verify disk space: df -h .runtime/
3. Test write: echo '{}' >> .runtime/revenue/transactions.jsonl

---

## Testing & Monitoring

### Manual Webhook Testing

#### Test Gumroad

``ash
curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
  -H "Content-Type: application/json" \
  -d '{"product_id":"test","price":"29.99","purchase_email":"test@example.com"}'
``

#### Test Printify

``ash
curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/printify \
  -H "Content-Type: application/json" \
  -d '{"action":"order.created","data":{"id":"999","status":"pending","total_price":99.99,"currency":"USD"}}'
``

#### Test Beehiiv

``ash
PAYLOAD='{"event":"sponsor.created","data":{"sponsor_name":"Test","sponsorship_amount":100}}'
SIGNATURE=(echo -n "PAYLOAD" | openssl dgst -sha256 -hmac "BEEHIIV_API_KEY" -hex | cut -d' ' -f2)

curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/newsletter \
  -H "Content-Type: application/json" \
  -H "x-beehiiv-signature: SIGNATURE" \
  -d "PAYLOAD"
``

### Monitoring Transaction Log

``ash
# Real-time tail
tail -f .runtime/revenue/transactions.jsonl

# Watch specific channel
tail -f .runtime/revenue/transactions.jsonl | jq 'select(.channel=="gumroad")'

# Total revenue
cat .runtime/revenue/transactions.jsonl | jq -s 'map(.amount_usd) | add'

# Revenue by channel
cat .runtime/revenue/transactions.jsonl | jq -s 'group_by(.channel) | map({channel: .[0].channel, total: map(.amount_usd) | add})'
``

---

## FAQ

### Q: Do I need all four webhooks?
**A:** No, register only the platforms you use.

### Q: Can I test webhooks without real transactions?
**A:** Yes! All endpoints accept test payloads.

### Q: What if my domain changes?
**A:** Update webhooks in each platform.

### Q: How often are transactions synced?
**A:** Real-time for Gumroad/Printify/Beehiiv; daily at 08:00 UTC for YouTube.

### Q: Can I replay old webhooks?
**A:** Yes, using source_id for idempotency to prevent double-counting.

---

## Support

1. Check logs: cat webhooks-registration.log
2. Monitor transactions: 	ail -f .runtime/revenue/transactions.jsonl
3. Run diagnostic: ./scripts/register-webhooks.sh --verify-only
4. Platform docs: https://gumroad.com/webhooks, https://printify.com/api/webhooks, https://docs.beehiiv.com/webhooks

---

**Last Updated:** 2026-06-20  
**Status:** Production-Ready
