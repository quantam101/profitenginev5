# Printify Webhook Implementation — Complete

Real-time POD (Print on Demand) order tracking via Printify API webhooks with automatic profit margin calculation.

## Overview

The webhook handler captures order events from Printify, extracts revenue and product data, calculates profit margins, and logs transactions to a persistent JSONL file for dashboard aggregation.

## What's Implemented

### 1. Webhook Handler: `app/api/webhooks/printify/route.ts`

**Features:**
- Accepts POST requests from Printify API (`order.created`, `order.completed` events)
- Parses JSON payload and extracts order details
- Calculates COGS (Cost of Goods Sold) based on product type:
  - T-Shirt: 60% COGS (40% margin)
  - Hoodie: 55% COGS (45% margin)
  - Mug/Hard Goods: 50% COGS (50% margin)
  - Poster/Print: 45% COGS (55% margin)
  - Sticker/Decal: 40% COGS (60% margin)
- Falls back to Printify-provided `cost` if available
- Logs transactions to `.runtime/revenue/transactions.jsonl` (JSONL format)
- Creates webhook audit log at `.runtime/webhooks/printify.log`
- Returns 200 OK with revenue/profit summary
- Handles errors gracefully (non-fatal file I/O failures)

**Request Input:**
```json
{
  "action": "order.created",
  "data": {
    "id": "shop_order_12345",
    "status": "pending",
    "total_price": 89.99,
    "currency": "USD",
    "line_items": [{"title": "T-Shirt", "quantity": 1}],
    "shipping_address": {"first_name": "John", "last_name": "Doe"}
  }
}
```

**Response Output (HTTP 200):**
```json
{
  "ok": true,
  "order_id": "shop_order_12345",
  "amount": 89.99,
  "cogs": 53.99,
  "profit": 36.00,
  "profit_margin": 40,
  "status": "pending",
  "timestamp": "2026-06-20T14:35:42.123Z"
}
```

**Transaction Log Entry:**
Each order creates one JSON line in `.runtime/revenue/transactions.jsonl`:
```json
{
  "channel": "printify",
  "amount_usd": 89.99,
  "cogs": 53.99,
  "profit": 36.00,
  "profit_margin": 40,
  "timestamp": "2026-06-20T14:35:42.123Z",
  "source_id": "printify_order_shop_order_12345",
  "description": "POD: T-Shirt (qty: 1) - pending",
  "content_id": "shop_order_12345",
  "metadata": {
    "order_id": "shop_order_12345",
    "product": "T-Shirt",
    "quantity": 1,
    "status": "pending",
    "currency": "USD",
    "customer_name": "John Doe",
    "calculation": {
      "revenue": 89.99,
      "cogs": 53.99,
      "profit": 36.00,
      "margin_percent": 40
    }
  }
}
```

### 2. Registration Scripts

#### Python Script: `scripts/register_printify_webhook.py`

**Interactive webhook registration with automatic shop selection.**

Features:
- Loads `.env` file automatically
- Queries Printify API for available shops
- Auto-detects single shop, prompts for selection if multiple
- Registers webhook for `order:created` topic
- Checks for existing webhooks (prevents duplicates)
- Verifies endpoint is publicly reachable
- Supports shop ID override: `--shop-id 12345`
- Remove webhook: `--remove webhook_id`
- Verify only: `--verify` (no registration)

**Usage:**
```bash
# Automatic (loads .env)
python3 scripts/register_printify_webhook.py

# With token
PRINTIFY_API_TOKEN="token" python3 scripts/register_printify_webhook.py

# Specific shop
python3 scripts/register_printify_webhook.py --shop-id 12345

# Verify endpoint
python3 scripts/register_printify_webhook.py --verify

# Remove webhook
python3 scripts/register_printify_webhook.py --remove webhook_abc123
```

#### Bash Script: `scripts/register_printify_webhook.sh`

**Shell-based registration for CI/CD integration.**

Features:
- Sources `.env` automatically
- Lists available shops with colored output
- Uses `jq` for JSON parsing
- Supports all Python script options
- Integrates with GitHub Actions/OCI deployment

**Usage:**
```bash
./scripts/register_printify_webhook.sh
./scripts/register_printify_webhook.sh --shop-id 12345
./scripts/register_printify_webhook.sh --verify
```

### 3. Documentation

#### `docs/PRINTIFY_WEBHOOK_SETUP.md` (12 KB)
Comprehensive setup guide covering:
- Architecture and data flow
- Step-by-step registration (Python, Bash, cURL)
- Webhook response formats
- Profit calculation logic
- Testing and troubleshooting
- Security considerations
- Deployment checklist

#### `docs/PRINTIFY_WEBHOOK_API.md` (8.4 KB)
Technical API reference:
- Endpoint specification
- Request/response schemas
- Transaction log format
- COGS calculation algorithm
- Webhook events tracked
- Query examples
- Rate limiting and retry behavior

#### `docs/PRINTIFY_QUICK_START.md` (2.6 KB)
5-minute quick reference:
- TL;DR setup
- Files created
- Sample data
- One-liner test
- Troubleshooting table

### 4. Environment Documentation

Updated `.env.example` with:
```
# ── Printify POD Order Tracking ──────────────────────────────────────
# Real-time webhook ingestion: POST /api/webhooks/printify
# Webhook events: order.created, order.completed
# Order data logged to: .runtime/revenue/transactions.jsonl
# Registration script: python scripts/register_printify_webhook.py
#
# Setup:
# 1. Get API token from https://printify.com/dashboard → Account → API
# 2. Run: PRINTIFY_API_TOKEN='<token>' python scripts/register_printify_webhook.py
# 3. Script auto-selects your shop and registers webhook endpoint
# 4. View orders: tail -f .runtime/revenue/transactions.jsonl
#
# Variable: PRINTIFY_API_TOKEN (set in server .env + GitHub Secrets, not here)
```

## Setup Instructions

### 1. Get Printify API Token

1. Go to https://printify.com/dashboard
2. Account → API section
3. Click "Create token"
4. Copy token (shown only once)

### 2. Register Webhook

```bash
# Quick registration
PRINTIFY_API_TOKEN="your-token-here" python3 scripts/register_printify_webhook.py
```

**Script will:**
- Authenticate with Printify API
- List your shops
- Auto-select single shop (or ask if multiple)
- Register webhook for order events
- Verify endpoint is reachable

### 3. Verify Setup

```bash
# Check webhook is active
PRINTIFY_API_TOKEN="your-token-here" python3 scripts/register_printify_webhook.py --verify

# Monitor incoming orders
tail -f .runtime/revenue/transactions.jsonl

# Check webhook audit log
tail -f .runtime/webhooks/printify.log
```

## Data Flow

```
1. Customer places order on Printify shop
   ↓
2. Printify sends POST to webhook endpoint
   POST https://profitengine.alreadyherellc.com/api/webhooks/printify
   ↓
3. Next.js handler processes request
   - Parse JSON payload
   - Extract order & product data
   - Calculate COGS & profit
   ↓
4. Transaction logged to JSONL file
   .runtime/revenue/transactions.jsonl (one JSON per line)
   ↓
5. Revenue dashboard aggregates
   GET /api/revenue/summary
   GET /api/revenue/dashboard
   ↓
6. Metrics displayed
   Total revenue, profit, margin %, orders by product
```

## File Locations

### Source Code
- `app/api/webhooks/printify/route.ts` — Webhook handler (TypeScript)

### Registration Tools
- `scripts/register_printify_webhook.py` — Python registration (recommended)
- `scripts/register_printify_webhook.sh` — Bash registration

### Documentation
- `docs/PRINTIFY_WEBHOOK_SETUP.md` — Full setup guide
- `docs/PRINTIFY_WEBHOOK_API.md` — API reference
- `docs/PRINTIFY_QUICK_START.md` — Quick start guide

### Runtime Data
- `.runtime/revenue/transactions.jsonl` — Order log (JSONL format)
- `.runtime/webhooks/printify.log` — Webhook audit trail

### Configuration
- `.env` — PRINTIFY_API_TOKEN (server only, not committed)
- `.env.example` — Documentation of PRINTIFY_API_TOKEN

## Example Workflows

### Deploy to Production (OCI)

```bash
# 1. Add token to server .env
ssh opc@129.146.236.177
echo 'PRINTIFY_API_TOKEN="your-token"' >> .env

# 2. Register webhook
PRINTIFY_API_TOKEN="your-token" python3 scripts/register_printify_webhook.py

# 3. Verify
python3 scripts/register_printify_webhook.py --verify

# 4. Monitor
tail -f .runtime/revenue/transactions.jsonl
```

### Deploy to Vercel (if needed)

```bash
# 1. Add to Vercel environment (project dashboard)
PRINTIFY_API_TOKEN = "your-token"

# 2. Can trigger via `/api/webhooks/printify` webhook
# (Vercel auto-restarts with new env vars)

# 3. Webhook logs available via Vercel function logs
# (if debugging is needed)
```

### Monitor Orders

```bash
# Real-time tail
tail -f .runtime/revenue/transactions.jsonl | jq '.'

# Filter by date
jq 'select(.timestamp > "2026-06-20T00:00:00Z")' .runtime/revenue/transactions.jsonl

# Total revenue
jq '[.[] | select(.channel == "printify") | .amount_usd] | add' .runtime/revenue/transactions.jsonl

# Profit summary
jq '[.[] | select(.channel == "printify")] | {
  orders: length,
  revenue: map(.amount_usd) | add,
  profit: map(.profit) | add,
  margin_avg: (map(.profit_margin) | add / length)
}' .runtime/revenue/transactions.jsonl
```

## Security Notes

### Environment Variables
- **PRINTIFY_API_TOKEN** — Never commit to git
- Store in: `.env` (server only), GitHub Secrets, or Vercel environment
- Rotate token every 90 days via Printify dashboard

### Webhook Validation
- Currently no signature validation (Printify doesn't sign webhooks by default)
- Recommendation: Use IP allowlist if available in Printify settings

### Data Logging
- JSONL file contains customer names and order IDs
- Ensure `.runtime/` directory has proper file permissions
- Audit trail available in `.runtime/webhooks/printify.log`

## Testing

### Test Locally (Development)

```bash
# Start Next.js dev server
npm run dev

# Send test webhook
curl -X POST http://localhost:3000/api/webhooks/printify \
  -H "Content-Type: application/json" \
  -d '{
    "action": "order.created",
    "data": {
      "id": "test_order_123",
      "status": "pending",
      "total_price": 99.99,
      "currency": "USD",
      "line_items": [{"title": "Test T-Shirt", "quantity": 1}]
    }
  }'

# Check response and log
tail -f .runtime/revenue/transactions.jsonl
```

### Test Production

```bash
# Verify endpoint is reachable
curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/printify \
  -H "Content-Type: application/json" \
  -d '{"action": "test", "data": {}}'

# Expected: 200 OK with skipped message
```

## Integration with Revenue Dashboard

The webhook handler follows the standard transaction schema used by:
- Gumroad webhook (`/api/webhooks/gumroad`)
- Newsletter/Beehiiv (`/api/webhooks/newsletter`)
- YouTube Analytics sync

All transactions are aggregated in:
- `.runtime/revenue/transactions.jsonl` (master log)
- Revenue summary API (`/api/revenue/summary`)
- Dashboard widget

## Troubleshooting

| Problem | Diagnosis | Solution |
|---------|-----------|----------|
| Webhook never fires | Check Printify dashboard → Integrations | Ensure webhook shows "active" status |
| Token error | Script can't authenticate | Verify `PRINTIFY_API_TOKEN` is set correctly |
| Endpoint unreachable | Domain not live or wrong URL | Check domain resolves: `curl https://profitengine.alreadyherellc.com` |
| Orders not appearing | Handler error or file permission issue | Check logs: `tail -f .runtime/webhooks/printify.log` |
| Profit calculation incorrect | COGS estimation doesn't match reality | Use actual `cost` from Printify if available, or adjust thresholds |

## Deployment Checklist

- [ ] PRINTIFY_API_TOKEN added to server `.env` or GitHub Secrets
- [ ] Webhook registered: `python3 scripts/register_printify_webhook.py`
- [ ] Endpoint verified: `--verify` flag returns success
- [ ] Test order placed and appears in `.runtime/revenue/transactions.jsonl`
- [ ] Revenue dashboard queries work correctly
- [ ] Webhook audit log monitored for errors
- [ ] Token documented in runbook for on-call rotation

## Related Files

- `docs/PRINTIFY_IMPLEMENTATION_SUMMARY.md` — Product publishing integration
- `docs/PRINTIFY_POD_PUBLISHING.md` — Publishing workflow
- `scripts/printify_get_shop_id.py` — List available shops
- `scripts/printify_product_publisher.py` — Publish products to Printify
- `scripts/push_printify_catalog.py` — Bulk catalog management
- `scripts/register-webhooks.sh` — Register all webhooks (Gumroad, Printify, Newsletter)

## Support

- **Printify API Documentation**: https://developers.printify.com/
- **Webhook Events Reference**: https://developers.printify.com/webhooks
- **Printify Dashboard**: https://printify.com/dashboard
- **Status & Uptime**: https://status.printify.com/
