# Printify Webhook Setup Guide

Real-time POD (Print on Demand) order tracking via Printify API webhooks.

## Architecture

```
Printify Shop
    ↓
    └─→ Webhook: order.created event
            ↓
        POST /api/webhooks/printify
            ↓
        app/api/webhooks/printify/route.ts
            ↓
        .runtime/revenue/transactions.jsonl
            ↓
        Dashboard aggregation + revenue tracking
```

## Prerequisites

1. **Printify Account** — https://printify.com
   - At least one connected product shop
   - API access enabled

2. **Production Domain** — `profitengine.alreadyherellc.com`
   - Must be publicly accessible for webhook delivery
   - HTTPS required by Printify

3. **Printify API Token** — from Account settings
   - Never commit to git
   - Set in `.env` (server only) or GitHub Secrets (for CI/CD)

## Step 1: Get Your Printify API Token

1. Go to https://printify.com/dashboard
2. Click **Account** (bottom left menu)
3. Scroll to **API** section
4. Click **Create token**
5. Copy the token (you won't see it again — store securely)

## Step 2: Add PRINTIFY_API_TOKEN to Environment

### Option A: Server `.env` (OCI/local development)

```bash
echo 'PRINTIFY_API_TOKEN="your-token-here"' >> .env
```

### Option B: GitHub Secrets (for CI/CD)

1. Go to https://github.com/quantam101/profitenginev5/settings/secrets/actions
2. Click **New repository secret**
3. Name: `PRINTIFY_API_TOKEN`
4. Value: paste your token
5. Click **Add secret**

### Option C: Vercel Environment (if needed for frontend)

1. Go to https://vercel.com/quantam101/profitengine-tau/settings/environment-variables
2. Add `PRINTIFY_API_TOKEN` with your token
3. **Important:** Mark as "Plaintext" only if absolutely needed (webhook handler uses server-side env)

## Step 3: Register the Webhook

Choose one method below.

### Method A: Python Script (Recommended)

```bash
# Quick setup with automatic shop selection
PRINTIFY_API_TOKEN="your-token" python3 scripts/register_printify_webhook.py

# For specific shop
PRINTIFY_API_TOKEN="your-token" python3 scripts/register_printify_webhook.py --shop-id 12345

# Verify endpoint is reachable
PRINTIFY_API_TOKEN="your-token" python3 scripts/register_printify_webhook.py --verify

# Remove webhook
PRINTIFY_API_TOKEN="your-token" python3 scripts/register_printify_webhook.py --remove webhook_id_xyz
```

### Method B: Bash Script

```bash
# Requires .env to be loaded
./scripts/register_printify_webhook.sh

# For specific shop
./scripts/register_printify_webhook.sh --shop-id 12345

# Verify only
./scripts/register_printify_webhook.sh --verify
```

### Method C: Manual (cURL)

```bash
PRINTIFY_API_TOKEN="your-token"
SHOP_ID="12345"  # from scripts/printify_get_shop_id.py
DOMAIN="https://profitengine.alreadyherellc.com"

curl -X POST https://api.printify.com/v1/shops/${SHOP_ID}/webhooks.json \
  -H "Authorization: Bearer ${PRINTIFY_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "order:created",
    "address": "'${DOMAIN}'/api/webhooks/printify"
  }'
```

## Step 4: Verify Webhook Delivery

### Check Webhook Registration

```bash
PRINTIFY_API_TOKEN="your-token" python3 scripts/register_printify_webhook.py --verify
```

Expected output:
```
Webhook endpoint: reachable (HTTP 200)
```

### Monitor Real Orders

```bash
# Watch incoming orders in real-time
tail -f .runtime/revenue/transactions.jsonl

# Query specific time window
jq 'select(.timestamp > "2026-06-20T00:00:00Z")' .runtime/revenue/transactions.jsonl
```

### Check Webhook Logs

```bash
# Webhook delivery audit trail
tail -f .runtime/webhooks/printify.log

# Sample output:
# [2026-06-20T14:35:42.123Z] Order shop_order_12345: pending - $89.99
# [2026-06-20T14:35:45.456Z] Order shop_order_12346: completed - $149.99
```

## Webhook Response Format

### Success Response (HTTP 200)

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

### Transaction Log Format

File: `.runtime/revenue/transactions.jsonl`

Each line is a complete JSON object:

```json
{
  "channel": "printify",
  "amount_usd": 89.99,
  "cogs": 53.99,
  "profit": 36.00,
  "profit_margin": 40,
  "timestamp": "2026-06-20T14:35:42.123Z",
  "source_id": "printify_order_shop_order_12345",
  "description": "POD: Premium T-Shirt (qty: 1) - pending",
  "content_id": "shop_order_12345",
  "metadata": {
    "order_id": "shop_order_12345",
    "product": "Premium T-Shirt",
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

## Profit Calculation Logic

### COGS (Cost of Goods Sold) Estimation

The webhook handler auto-calculates COGS based on product type:

| Product Type | COGS % | Margin % |
|---|---|---|
| T-Shirt / Standard Apparel | 60% | 40% |
| Hoodie / Sweatshirt | 55% | 45% |
| Mug / Hard Goods | 50% | 50% |
| Poster / Canvas / Print | 45% | 55% |
| Sticker / Decal | 40% | 60% |
| Other / Default | 60% | 40% |

**Example:**
- Product: "Premium T-Shirt"
- Revenue: $89.99
- COGS (estimated): $53.99 (60%)
- Profit: $36.00
- Margin: 40%

### Using Actual COGS (if available from Printify)

If Printify provides actual `cost` field in the webhook payload, it overrides the estimated COGS:

```json
{
  "total_price": 89.99,
  "cost": 45.00,  // ← Uses this instead of estimation
  // Calculated profit: 44.99 (profit_margin: 50%)
}
```

## Testing & Troubleshooting

### Test Webhook Endpoint Locally

```bash
# Create test payload
cat > /tmp/test_printify.json <<'EOF'
{
  "action": "order.created",
  "data": {
    "id": "test_12345",
    "status": "pending",
    "total_price": 99.99,
    "currency": "USD",
    "line_items": [
      {
        "title": "Test Premium Hoodie",
        "quantity": 1
      }
    ],
    "shipping_address": {
      "first_name": "Test",
      "last_name": "Customer"
    }
  }
}
EOF

# Test locally (port 3000 for Next.js dev)
curl -X POST http://localhost:3000/api/webhooks/printify \
  -H "Content-Type: application/json" \
  -d @/tmp/test_printify.json

# Test production (requires public endpoint)
curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/printify \
  -H "Content-Type: application/json" \
  -d @/tmp/test_printify.json
```

### Common Issues

| Issue | Solution |
|---|---|
| **"Webhook endpoint unreachable"** | Check that domain is publicly accessible (`curl https://profitengine.alreadyherellc.com/api/webhooks/printify`) |
| **"PRINTIFY_API_TOKEN not found"** | Ensure `.env` file exists and includes `PRINTIFY_API_TOKEN=...` |
| **"No shops found"** | Create a shop in Printify and ensure it's connected to a sales channel |
| **Orders not appearing in log** | Check Printify dashboard → Integrations to verify webhook is active |
| **Invalid JSON in transactions.jsonl** | Webhook handler catches write errors — check disk space and file permissions |

### Enable Debug Logging

```bash
# Increase log level (if using structured logging)
LOG_LEVEL=DEBUG PRINTIFY_API_TOKEN="..." python3 scripts/register_printify_webhook.py

# Watch webhook processing in real-time
docker logs -f profitenginev5-runtime  # or your container name
```

## Data Flow & Integration

### Revenue Dashboard

The webhook handler logs to `.runtime/revenue/transactions.jsonl`, which is consumed by:

- **Revenue Summary API** — `GET /api/revenue/summary`
- **Dashboard Widget** — Real-time order count, revenue, profit
- **CSV Export** — Monthly/quarterly reporting

### Schema Compatibility

Transactions follow the standard schema:
- `channel` — always `"printify"`
- `amount_usd` — total sale price
- `cogs` — estimated cost (or actual, if provided)
- `profit` — `amount_usd - cogs`
- `profit_margin` — profit percentage
- `timestamp` — ISO 8601 UTC
- `metadata` — product details, customer info, margin breakdown

### Query Examples

```bash
# Total Printify revenue (June 2026)
jq 'select(.channel == "printify" and .timestamp | startswith("2026-06"))
    | .amount_usd
    | add' .runtime/revenue/transactions.jsonl

# Profit by product type
jq 'select(.channel == "printify")
    | {product: .metadata.product, profit: .profit, margin: .profit_margin}
    | @csv' .runtime/revenue/transactions.jsonl | column -t -s,

# Top-performing products
jq 'select(.channel == "printify")
    | {product: .metadata.product, revenue: .amount_usd}
    | @csv' .runtime/revenue/transactions.jsonl \
  | sort -t, -k2 -rn | head -10
```

## Security Considerations

### Token Rotation

Regenerate your token periodically (every 90 days recommended):

1. Go to https://printify.com/dashboard → Account → API
2. Click **Regenerate** next to your old token
3. Update `.env` and GitHub Secrets with new token
4. Verify webhook still works: `python3 scripts/register_printify_webhook.py --verify`

### Webhook Validation (Future)

Currently, Printify webhooks are not signed. Best practices:

1. **IP Allowlist** — Consider restricting to Printify's IP ranges (if available)
2. **Rate Limiting** — Next.js handler should implement rate limiting for production
3. **Idempotency** — Multiple deliveries of same order should be handled gracefully (currently using `source_id` for deduplication)

### Environment Variable Security

```bash
# ✅ Secure: Only on server
echo 'PRINTIFY_API_TOKEN="token"' >> /path/to/server/.env

# ✅ Secure: GitHub Secret for CI/CD
# Go to Settings → Secrets → Actions → PRINTIFY_API_TOKEN

# ❌ Insecure: In git history
git add .env  # Don't do this!

# ❌ Insecure: In Vercel frontend env
# Frontend code can't access PRINTIFY_API_TOKEN anyway (server-only)
```

## Deployment Checklist

- [ ] Printify account created and API token generated
- [ ] `.env` includes `PRINTIFY_API_TOKEN` (server only)
- [ ] GitHub Secrets includes `PRINTIFY_API_TOKEN` (if using CI/CD)
- [ ] Domain `profitengine.alreadyherellc.com` is live and HTTPS
- [ ] Webhook registered: `python3 scripts/register_printify_webhook.py`
- [ ] Webhook endpoint verified: `--verify` flag returns success
- [ ] Test order placed and appears in `.runtime/revenue/transactions.jsonl`
- [ ] Revenue dashboard queries work correctly
- [ ] Logs monitored for errors: `tail -f .runtime/webhooks/printify.log`

## Appendix: Helper Scripts

### Get Your Shop ID

```bash
PRINTIFY_API_TOKEN="your-token" python3 scripts/printify_get_shop_id.py

# Output:
# Shop ID: 12345  |  Name: My Print Shop  |  Platform: shopify
```

### View All Webhooks for a Shop

```bash
SHOP_ID="12345"
PRINTIFY_API_TOKEN="your-token"

curl -s https://api.printify.com/v1/shops/${SHOP_ID}/webhooks.json \
  -H "Authorization: Bearer ${PRINTIFY_API_TOKEN}" \
  | jq '.'
```

### Remove a Webhook

```bash
SHOP_ID="12345"
WEBHOOK_ID="webhook_abc123"
PRINTIFY_API_TOKEN="your-token"

# Via script
python3 scripts/register_printify_webhook.py --remove $WEBHOOK_ID

# Via cURL
curl -X DELETE \
  https://api.printify.com/v1/shops/${SHOP_ID}/webhooks/${WEBHOOK_ID}.json \
  -H "Authorization: Bearer ${PRINTIFY_API_TOKEN}"
```

## Support

- **Printify API Docs** — https://developers.printify.com/
- **Webhook Events** — https://developers.printify.com/webhooks
- **Status Page** — https://status.printify.com/
