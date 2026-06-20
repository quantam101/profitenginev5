# Gumroad API Integration & Webhook Setup

This guide walks through configuring Gumroad to auto-sync ebook sales directly into ProfitEngine's revenue ledger.

---

## Quick Summary

- **Backend Service**: `backend/services/gumroad_service.py`
  - Async API client for fetching products and sales
  - License key verification
  - Webhook payload parsing

- **Webhook Handler**: `app/api/webhooks/gumroad/route.ts`
  - Accepts POST from Gumroad
  - Logs sales to `.runtime/revenue/transactions.jsonl`
  - Returns 200 OK with transaction ID

- **Environment**: 
  - `GUMROAD_ACCESS_TOKEN`: Already configured in `.env`
  - `GUMROAD_SELLER_ID`: Already configured in `.env`

---

## Webhook Configuration

### Step 1: Get Your Webhook URL

Your production webhook endpoint is:

```
https://profitengine.alreadyherellc.com/api/webhooks/gumroad
```

Test locally during development with:

```
http://localhost:3000/api/webhooks/gumroad
```

### Step 2: Add Webhook to Gumroad Dashboard

1. Log in to [Gumroad Dashboard](https://app.gumroad.com/dashboard)
2. Go to **Settings** → **Webhooks** (or **Integrations**)
3. Click **Add Webhook**
4. Paste the webhook URL: `https://profitengine.alreadyherellc.com/api/webhooks/gumroad`
5. Select events to trigger:
   - ✅ **Sale** (required)
   - ✅ **License Key Generated** (optional, for licensed products)
   - ✅ **Refund** (optional)
6. Click **Save** or **Create**

### Step 3: Test the Webhook

Gumroad provides a "Send Test" button in the webhook settings. Click it to verify connectivity:

```bash
# You should see in logs:
# ✅ Gumroad webhook processed in 45ms | $9.99 from test@example.com | ...
```

---

## Webhook Payload Format

Gumroad sends a `POST` request with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | string | ✅ | Unique product ID |
| `product_name` | string | ✅ | Product display name |
| `price` | string/number | ✅ | Sale price in USD |
| `purchase_email` | string | ✅ | Buyer's email address |
| `license_key` | string | ❌ | Generated if product has licensing enabled |
| `variant_title` | string | ❌ | Selected variant name (if applicable) |
| `timestamp` | number/string | ❌ | Unix timestamp of sale (defaults to now) |
| `currency` | string | ❌ | Currency code (defaults to USD) |

### Example Webhook Payload

```json
{
  "product_id": "prod_abc123xyz",
  "product_name": "Trading Guide: Complete 2026 Edition",
  "price": "29.99",
  "purchase_email": "trader@example.com",
  "license_key": "LICENSE_a1b2c3d4e5f6g7h8",
  "variant_title": "PDF Bundle",
  "timestamp": "1718920123",
  "currency": "usd"
}
```

---

## Transaction Log Schema

All sales are logged to `.runtime/revenue/transactions.jsonl` in this format:

```json
{
  "channel": "gumroad",
  "amount_usd": 29.99,
  "timestamp": "2026-06-20T15:08:43.123Z",
  "source_id": "gumroad_prod_abc123xyz_1718920123",
  "description": "Gumroad sale: Trading Guide: Complete 2026 Edition",
  "content_id": "prod_abc123xyz",
  "metadata": {
    "purchaser_email": "trader@example.com",
    "product_name": "Trading Guide: Complete 2026 Edition",
    "license_key": "LICENSE_a1b2c3d4e5f6g7h8",
    "variant": "PDF Bundle",
    "raw_payload": {
      "product_id": "prod_abc123xyz",
      "currency": "usd"
    }
  }
}
```

---

## Backend Service: `gumroad_service.py`

Use the Python service to interact with Gumroad API directly:

### Fetch All Products

```python
from backend.services.gumroad_service import get_gumroad_service

service = get_gumroad_service()
products = await service.fetch_products()

for product in products:
    print(f"{product.name}: ${product.price}")
```

### Fetch All Sales

```python
sales = await service.fetch_sales()

for sale in sales:
    print(f"{sale.product_name}: ${sale.amount_usd} from {sale.purchaser_email}")
```

### Fetch Sales for Specific Product

```python
product_id = "prod_abc123xyz"
sales = await service.fetch_sales(product_id=product_id)
```

### Verify License Key

```python
is_valid = await service.verify_license(
    product_id="prod_abc123xyz",
    license_key="LICENSE_a1b2c3d4e5f6g7h8"
)
```

### Parse Webhook Payload

```python
payload = {
    "product_id": "prod_abc123xyz",
    "product_name": "Trading Guide",
    "price": "29.99",
    "purchase_email": "trader@example.com",
    "license_key": "LICENSE_a1b2c3d4e5f6g7h8"
}

service = get_gumroad_service()
sale = service.parse_webhook_payload(payload)
transaction = sale.to_transaction()
```

---

## Webhook Handler: `app/api/webhooks/gumroad/route.ts`

The TypeScript handler automatically:

1. **Parses** incoming Gumroad webhook
2. **Normalizes** prices (handles both USD and cents)
3. **Generates** unique transaction ID
4. **Logs** to `.runtime/revenue/transactions.jsonl`
5. **Returns** 200 OK with transaction details

### Response Format

**Success (200 OK)**:
```json
{
  "ok": true,
  "transaction_id": "gumroad_prod_abc123xyz_1718920123",
  "amount_usd": 29.99,
  "product_name": "Trading Guide: Complete 2026 Edition",
  "purchaser_email": "trader@example.com",
  "logged": true,
  "processing_time_ms": 45
}
```

**Error (400 Bad Request)**:
```json
{
  "ok": false,
  "error": "Webhook processing failed",
  "details": "Missing required field: product_id",
  "timestamp": "2026-06-20T15:08:43.123Z"
}
```

### Health Check

Test the webhook endpoint:

```bash
curl -X GET https://profitengine.alreadyherellc.com/api/webhooks/gumroad
```

Response:
```json
{
  "ok": true,
  "service": "Gumroad Webhook Handler",
  "version": "2.0",
  "endpoint": "/api/webhooks/gumroad",
  "method": "POST",
  "expected_fields": [
    "product_id",
    "product_name",
    "price",
    "purchase_email",
    "license_key (optional)",
    "variant_title (optional)",
    "timestamp (optional)"
  ]
}
```

---

## Environment Variables

These are already configured in `.env`:

```bash
# Gumroad API credentials
GUMROAD_ACCESS_TOKEN=qP1PGdN-zCLeGeaN2r6SOZJKJK6oy2AFHIyVb6G3CuY
GUMROAD_SELLER_ID=KTgbGvItMAkVGByS893WRA==

# Optional: Base price for ebooks (used in pricing logic)
GUMROAD_BASE_PRICE=9.99
```

**⚠️ Security Note**: Never commit the `GUMROAD_ACCESS_TOKEN` to the repo. It's stored in:
- `.env` (local development)
- Vercel Environment Variables (production)
- GitHub Actions Secrets (CI/CD)

---

## Revenue Dashboard Integration

Sales are automatically added to the revenue ledger at `.runtime/revenue/transactions.jsonl`.

Query today's Gumroad sales:

```bash
cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad" and .timestamp | startswith("2026-06-20"))'
```

Calculate total Gumroad revenue this month:

```bash
cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad") | .amount_usd' | awk '{sum+=$1} END {print "Total: $" sum}'
```

---

## Troubleshooting

### Webhook Not Being Called

1. **Verify URL is public**: Test with `curl -X GET https://profitengine.alreadyherellc.com/api/webhooks/gumroad`
2. **Check Gumroad dashboard**: Confirm webhook is enabled and URL matches exactly
3. **Send test webhook**: Use Gumroad's "Send Test" button, check logs for errors
4. **Check firewall**: Ensure Gumroad's IP addresses are whitelisted (if applicable)

### Transaction Not Logged

1. **Check filesystem permissions**: `.runtime/revenue/` directory must be writable
2. **Verify JSONL format**: Each transaction should be on a single line
3. **Check Next.js logs**: `npm run dev` shows real-time webhook processing

### Price Not Normalized Correctly

1. Gumroad typically sends prices in USD (e.g., "29.99")
2. Handler converts any prices > 10000 from cents to dollars
3. All amounts are rounded to 2 decimal places

### License Key Not Appearing

1. Ensure product has "Licensing" enabled in Gumroad settings
2. Gumroad only sends `license_key` field if product is licensed
3. Metadata will show `license_key: null` for unlicensed products

---

## Testing Checklist

- [ ] Webhook URL is publicly accessible
- [ ] Gumroad dashboard webhook is configured and enabled
- [ ] Test webhook sends successfully
- [ ] Transaction appears in `.runtime/revenue/transactions.jsonl`
- [ ] Revenue dashboard reflects the sale
- [ ] License key is captured (if product is licensed)
- [ ] Email is normalized to lowercase in metadata
- [ ] Variant title is captured (if product has variants)

---

## Next Steps

1. ✅ Backend service created (`gumroad_service.py`)
2. ✅ Webhook handler implemented (`route.ts`)
3. ✅ Environment variables configured
4. **→ Configure webhook in Gumroad dashboard** (see Step 2 above)
5. **→ Test with real purchase or Gumroad test webhook**
6. Monitor logs and revenue ledger

---

## References

- [Gumroad Webhooks Docs](https://gumroad.com/docs#webhooks)
- [Gumroad API Reference](https://gumroad.com/docs#api)
- [ProfitEngine Architecture](./ARCHITECTURE.md)
- Revenue ledger: `.runtime/revenue/transactions.jsonl`

---

**Setup by**: ProfitEngine v5 / Already Here LLC  
**Last Updated**: 2026-06-20  
**Status**: ✅ Production Ready
