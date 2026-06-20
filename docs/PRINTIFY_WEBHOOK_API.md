# Printify Webhook API Reference

Technical specification for the order tracking webhook.

## Endpoint

```
POST https://profitengine.alreadyherellc.com/api/webhooks/printify
```

## Request Format

Printify sends POST requests with `Content-Type: application/json`.

### Request Body

```typescript
interface PrintifyWebhookRequest {
  action: "order.created" | "order.completed" | string;
  data: PrintifyOrder;
}

interface PrintifyOrder {
  id: string;                    // Unique order ID (e.g., "shop_order_12345")
  status: string;                // "pending", "processing", "completed", etc.
  total_price: number;           // Total amount in primary currency
  currency: string;              // Currency code (e.g., "USD")
  line_items?: LineItem[];       // Product items in order
  shipping_address?: Address;    // Shipping/billing address
  cost?: number;                 // Optional: actual COGS provided by Printify
}

interface LineItem {
  title: string;                 // Product name
  quantity: number;              // Quantity ordered
  sku?: string;                  // Product SKU
}

interface Address {
  first_name?: string;
  last_name?: string;
  // ... other address fields
}
```

### Example Request

```json
{
  "action": "order.created",
  "data": {
    "id": "shop_order_987654",
    "status": "pending",
    "total_price": 149.99,
    "currency": "USD",
    "line_items": [
      {
        "title": "Premium Hoodie - Navy Blue",
        "quantity": 2,
        "sku": "HOODIE-NB-M"
      }
    ],
    "shipping_address": {
      "first_name": "Jane",
      "last_name": "Smith"
    }
  }
}
```

## Response Format

### Success Response (HTTP 200 OK)

```json
{
  "ok": true,
  "order_id": "shop_order_987654",
  "amount": 149.99,
  "cogs": 82.49,
  "profit": 67.50,
  "profit_margin": 45,
  "status": "pending",
  "timestamp": "2026-06-20T14:35:42.123Z"
}
```

### Error Response (HTTP 400 Bad Request)

```json
{
  "error": "Webhook processing failed",
  "details": "Invalid JSON payload"
}
```

### Skipped Response (HTTP 200 OK)

For non-order events (e.g., `action: "product.updated"`):

```json
{
  "ok": true,
  "skipped": "Action 'product.updated' not tracked"
}
```

## Transaction Log Format

Each successful webhook is appended to `.runtime/revenue/transactions.jsonl` as a single JSON line.

### Transaction Schema

```typescript
interface Transaction {
  channel: "printify";                    // Fixed identifier
  amount_usd: number;                     // Total revenue in USD
  cogs: number;                           // Cost of goods sold
  profit: number;                         // amount_usd - cogs
  profit_margin: number;                  // profit % (0-100)
  timestamp: string;                      // ISO 8601 UTC (e.g., "2026-06-20T14:35:42.123Z")
  source_id: string;                      // Unique ID (printify_order_<id>)
  description: string;                    // Human-readable summary
  content_id: string;                     // Original order ID from Printify
  metadata: TransactionMetadata;
}

interface TransactionMetadata {
  order_id: string;                       // Printify order ID
  product: string;                        // First product title
  quantity: number;                       // Total quantity ordered
  status: string;                         // Order status from Printify
  currency: string;                       // Currency code
  customer_name: string;                  // Extracted from shipping_address
  calculation: {
    revenue: number;
    cogs: number;
    profit: number;
    margin_percent: number;
  };
}
```

### Example Log Entry

```json
{
  "channel": "printify",
  "amount_usd": 149.99,
  "cogs": 82.49,
  "profit": 67.50,
  "profit_margin": 45,
  "timestamp": "2026-06-20T14:35:42.123Z",
  "source_id": "printify_order_shop_order_987654",
  "description": "POD: Premium Hoodie - Navy Blue (qty: 2) - pending",
  "content_id": "shop_order_987654",
  "metadata": {
    "order_id": "shop_order_987654",
    "product": "Premium Hoodie - Navy Blue",
    "quantity": 2,
    "status": "pending",
    "currency": "USD",
    "customer_name": "Jane Smith",
    "calculation": {
      "revenue": 149.99,
      "cogs": 82.49,
      "profit": 67.50,
      "margin_percent": 45
    }
  }
}
```

## Profit Calculation

### COGS Estimation

When `data.cost` is not provided, COGS is estimated based on product type:

```typescript
const cogsRatios = {
  hoodie: 0.55,        // 45% margin
  shirt: 0.60,         // 40% margin
  mug: 0.50,           // 50% margin
  poster: 0.45,        // 55% margin
  sticker: 0.40,       // 60% margin
  default: 0.60        // 40% margin
};

profit = total_price - (total_price * cogsRatio);
margin = (profit / total_price) * 100;
```

### Using Actual COGS

If Printify provides `data.cost`:

```typescript
profit = data.total_price - data.cost;
margin = (profit / data.total_price) * 100;
```

## Webhook Events Tracked

| Event | Tracked? | Notes |
|-------|----------|-------|
| `order.created` | ✅ Yes | New order placed |
| `order.completed` | ✅ Yes | Order fulfilled/shipped |
| `order.updated` | ❌ No | Status updates (use created/completed) |
| `product.*` | ❌ No | Product catalog changes (not revenue) |
| Other | ❌ No | Events other than order events are skipped |

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success — webhook processed or skipped |
| 400 | Error — invalid payload or processing failure |

**Note:** Both success and skip cases return 200. Only genuine errors return 4xx.

## Retry Behavior

Printify's webhook system:
- Retries failed (non-2xx) requests up to 5 times
- Exponential backoff: 30s, 5m, 30m, 2h, 24h
- Stores failed deliveries in dashboard for manual replay

To trigger a manual retry in Printify:
1. Dashboard → Integrations → Webhook Settings
2. View failed delivery history
3. Click "Retry" on any failed event

## Rate Limiting

No explicit rate limit enforced on the handler. For high-volume shops:
- Concurrent orders are handled sequentially (async file append)
- Each request is processed independently
- JSONL appends are atomic (single line per write)

## Deduplication

Transactions are deduplicated by `source_id`:

```
source_id = f"printify_order_{order.id}"
```

If the same order ID is received multiple times (webhook retry), it appears as a duplicate in the log but can be deduplicated by uniqueness on `source_id` during aggregation.

## Security

### Authentication

Currently, webhooks are unauthenticated (open POST endpoint).

**Recommendations for production:**
1. Restrict to Printify's IP ranges (request from API docs)
2. Verify webhook signature (if Printify implements signing)
3. Add rate limiting middleware
4. Log all requests for audit trail

### Example: Adding Signature Verification (future)

```typescript
import crypto from 'crypto';

function verifyPrintifySignature(payload: string, signature: string, secret: string): boolean {
  const computed = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return computed === signature;
}
```

## Webhook Logs

Successful webhook deliveries are logged to:

```
.runtime/webhooks/printify.log
```

Format: `[ISO_TIMESTAMP] Order {id}: {status} - ${amount}`

Example:
```
[2026-06-20T14:35:42.123Z] Order shop_order_987654: pending - $149.99
[2026-06-20T14:35:45.456Z] Order shop_order_987655: completed - $79.99
```

## Query Examples

### All Printify orders in June 2026

```bash
jq 'select(.channel == "printify" and .timestamp | startswith("2026-06"))' \
  .runtime/revenue/transactions.jsonl
```

### Total revenue and profit

```bash
jq 'select(.channel == "printify")
    | {revenue: .amount_usd, profit: .profit}
    | [.revenue, .profit]' \
  .runtime/revenue/transactions.jsonl | \
jq -s 'map(.[0]) | add as $rev | map(.[1]) | add as $prof | {total_revenue: $rev, total_profit: $prof}'
```

### Orders by product type

```bash
jq 'select(.channel == "printify")
    | {product: .metadata.product, amount: .amount_usd, margin: .profit_margin}' \
  .runtime/revenue/transactions.jsonl
```

### Profit margins by product

```bash
jq 'select(.channel == "printify")
    | {product: .metadata.product, margin: .profit_margin}
    | @csv' \
  .runtime/revenue/transactions.jsonl | \
sort | uniq -c
```

## Related Documentation

- **Setup Guide**: `docs/PRINTIFY_WEBHOOK_SETUP.md`
- **Quick Start**: `docs/PRINTIFY_QUICK_START.md`
- **Printify API**: https://developers.printify.com/
- **Webhook Events**: https://developers.printify.com/webhooks
