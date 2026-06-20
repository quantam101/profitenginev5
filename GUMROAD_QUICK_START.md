# Gumroad Integration — Quick Start

## TL;DR Setup (5 minutes)

### 1. Backend Service Ready ✅
- File: `backend/services/gumroad_service.py`
- Async API client for products, sales, and license verification
- Environment: `GUMROAD_ACCESS_TOKEN` and `GUMROAD_SELLER_ID` configured in `.env`

### 2. Webhook Handler Ready ✅
- File: `app/api/webhooks/gumroad/route.ts`
- Endpoint: `https://profitengine.alreadyherellc.com/api/webhooks/gumroad`
- Automatically logs sales to `.runtime/revenue/transactions.jsonl`

### 3. Add Webhook to Gumroad
1. Go to [Gumroad Dashboard](https://app.gumroad.com/dashboard)
2. Settings → Webhooks
3. Add webhook: `https://profitengine.alreadyherellc.com/api/webhooks/gumroad`
4. Select "Sale" event
5. Save

### 4. Test
```bash
# Gumroad dashboard: Click "Send Test"
# Or curl from command line:
curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "test_prod_123",
    "product_name": "Test Ebook",
    "price": "29.99",
    "purchase_email": "test@example.com",
    "license_key": "LICENSE_abc123"
  }'

# Check logs and .runtime/revenue/transactions.jsonl
```

---

## Files Overview

| File | Purpose | Status |
|------|---------|--------|
| `backend/services/gumroad_service.py` | Python async API client | ✅ Created |
| `app/api/webhooks/gumroad/route.ts` | TypeScript webhook handler | ✅ Updated v2.0 |
| `GUMROAD_SETUP.md` | Full documentation | ✅ Created |
| `tests/test_gumroad_webhook.ts` | Integration tests | ✅ Created |
| `.env` | Environment secrets | ✅ Configured |

---

## Webhook URL

**Production**: `https://profitengine.alreadyherellc.com/api/webhooks/gumroad`

**Local Dev**: `http://localhost:3000/api/webhooks/gumroad`

---

## Environment Variables

Already in `.env`:
```bash
GUMROAD_ACCESS_TOKEN=qP1PGdN-zCLeGeaN2r6SOZJKJK6oy2AFHIyVb6G3CuY
GUMROAD_SELLER_ID=KTgbGvItMAkVGByS893WRA==
GUMROAD_BASE_PRICE=9.99
```

---

## Example: Fetch Sales with Python

```python
import asyncio
from backend.services.gumroad_service import get_gumroad_service

async def main():
    service = get_gumroad_service()
    
    # Get all sales
    sales = await service.fetch_sales()
    for sale in sales:
        print(f"{sale.product_name}: ${sale.amount_usd}")
    
    # Get sales for specific product
    product_sales = await service.fetch_sales(product_id="prod_abc123")
    
    # Verify a license
    is_valid = await service.verify_license("prod_abc123", "LICENSE_key")

asyncio.run(main())
```

---

## Example: Parse Webhook Payload

```python
from backend.services.gumroad_service import get_gumroad_service

payload = {
    "product_id": "prod_123",
    "product_name": "My Ebook",
    "price": "19.99",
    "purchase_email": "buyer@example.com",
    "license_key": "LICENSE_xyz",
    "timestamp": "1718920123"
}

service = get_gumroad_service()
sale = service.parse_webhook_payload(payload)
transaction = sale.to_transaction()
print(transaction)
```

---

## Check Webhook Health

```bash
curl https://profitengine.alreadyherellc.com/api/webhooks/gumroad
```

Response shows expected fields and webhook version.

---

## View Revenue

```bash
# Today's Gumroad sales
cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad")'

# Total Gumroad revenue this month
cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad") | .amount_usd' | awk '{sum+=$1} END {print "$" sum}'

# Count of transactions
cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad")' | wc -l
```

---

## Run Tests

```bash
npm test -- test_gumroad_webhook.ts
```

Tests validate:
- Webhook payload parsing
- Price normalization
- Optional field handling
- Transaction logging
- Email normalization
- Response schema
- Edge cases

---

## Troubleshooting

**Webhook not called?**
- Check webhook URL in Gumroad dashboard
- Test with "Send Test" button
- Verify `https://` (not http://)

**Transaction not logged?**
- Check `.runtime/revenue/` directory exists and is writable
- Check Next.js server logs for errors
- Verify JSONL format (one transaction per line)

**Price wrong?**
- Handler normalizes to USD (2 decimal places)
- Prices > 10000 are treated as cents and divided by 100

**License key missing?**
- Ensure product has licensing enabled in Gumroad
- License key only sent if product is licensed

---

## Next: Monitor & Analytics

Once webhooks are flowing, you can:

1. **Build dashboard**: Query `.runtime/revenue/transactions.jsonl` by date/channel
2. **Email alerts**: Send daily summary of Gumroad sales
3. **Revenue forecasting**: Trend analysis on ebook sales
4. **License tracking**: Monitor which licenses are active
5. **Customer analytics**: Segment by purchaser email, variant, price point

---

## Support

See `GUMROAD_SETUP.md` for:
- Detailed webhook configuration
- Complete API documentation
- Schema reference
- Error handling

Contact: dispatch@alreadyherellc.com
