# Printify Webhook — Quick Start

5-minute setup for POD order tracking.

## TL;DR

```bash
# 1. Get token from https://printify.com/dashboard → Account → API
# 2. Set environment
export PRINTIFY_API_TOKEN="your-token-here"

# 3. Register webhook (auto-selects shop)
python3 scripts/register_printify_webhook.py

# 4. Done! Orders now tracked at:
tail -f .runtime/revenue/transactions.jsonl
```

## Files Created/Modified

| File | Purpose |
|------|---------|
| `app/api/webhooks/printify/route.ts` | Webhook handler + COGS calculation |
| `scripts/register_printify_webhook.py` | Python registration script (recommended) |
| `scripts/register_printify_webhook.sh` | Bash registration script |
| `docs/PRINTIFY_WEBHOOK_SETUP.md` | Full documentation |
| `.env.example` | Updated with PRINTIFY_API_TOKEN docs |

## What Happens When an Order Comes In

```
Printify Shop
    ↓ (webhook POST)
/api/webhooks/printify (Next.js route handler)
    ↓
[Parse order + calculate profit]
    ↓
.runtime/revenue/transactions.jsonl (log entry)
    ↓
Revenue dashboard + analytics
```

## Sample Data Logged

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
  "metadata": {
    "order_id": "shop_order_12345",
    "product": "Premium T-Shirt",
    "quantity": 1,
    "status": "pending",
    "customer_name": "John Doe"
  }
}
```

## One-Liner Test

```bash
# Verify endpoint is working (after deployment)
curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/printify \
  -H "Content-Type: application/json" \
  -d '{
    "action": "order.created",
    "data": {
      "id": "test_123",
      "status": "pending",
      "total_price": 99.99,
      "currency": "USD",
      "line_items": [{"title": "Test Hoodie", "quantity": 1}]
    }
  }'

# Expected: HTTP 200 with JSON response
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `PRINTIFY_API_TOKEN not found` | Run: `export PRINTIFY_API_TOKEN="your-token"` |
| `No shops found` | Create a shop in Printify, connect to sales channel |
| `Webhook endpoint unreachable` | Check domain is live: `curl https://profitengine.alreadyherellc.com` |
| Orders not appearing | Verify Printify dashboard → Integrations shows webhook as "active" |

## Documentation

- **Full Setup Guide**: `docs/PRINTIFY_WEBHOOK_SETUP.md`
- **API Reference**: https://developers.printify.com/webhooks
- **Printify Dashboard**: https://printify.com/dashboard
