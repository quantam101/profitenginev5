# Etsy/Printify Automation Setup Guide

Complete guide to configure and deploy the Print-on-Demand (POD) automation system for automatically uploading products to Etsy via Printify.

## Quick Start

```bash
# 1. Add environment variables to .env
PRINTIFY_API_KEY=your-printify-api-key
PRINTIFY_SHOP_ID=your-printify-shop-id
ETSY_OAUTH_TOKEN=your-etsy-oauth-token
ETSY_SHOP_ID=your-etsy-shop-id

# 2. Verify configuration
npm run verify:etsy-config

# 3. Create a product
curl -X POST http://localhost:3000/api/automation/etsy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "templates": [{
      "name": "Classic Logo T-Shirt",
      "description": "High-quality t-shirt with classic logo",
      "category": "apparel",
      "printifyProductId": "16",
      "basePrice": 24.99,
      "designs": [{
        "id": "design-1",
        "name": "Black Logo",
        "colors": ["black"],
        "sizes": ["S", "M", "L", "XL"]
      }],
      "tags": ["t-shirt", "logo", "apparel"]
    }]
  }'
```

---

## Prerequisites

### 1. Printify Account & API Setup

1. **Create Printify account**: https://printify.com
2. **Get API token**:
   - Go to https://app.printify.com/dashboard
   - Settings → Integrations → API
   - Create new API token → Copy token
3. **Get Shop ID**:
   - Same page → Shop ID (starts with `shopify_` or similar)

### 2. Etsy Account & OAuth

1. **Create Etsy seller account**: https://www.etsy.com/sell
2. **Register app** at https://www.etsy.com/developers
   - App name: "ProfitEngine Automation"
   - Redirect URI: `http://localhost:3000/auth/callback` (dev) or `https://your-domain.com/auth/callback` (prod)
3. **Get OAuth token**:
   - Option A: Use Etsy's OAuth flow (recommended for production)
   - Option B: Generate personal API token (simpler for testing)

### 3. Shop IDs

**Etsy Shop ID**:
- Visit https://www.etsy.com/shop/your-shop-name
- Look for `shop_id` in page source or use: https://api.etsy.com/v3/application/shops/me

**Printify Shop ID**:
- https://app.printify.com/dashboard
- Under Settings → shown at top of page

---

## Environment Variables

Add these to `.env` or `.env.local` (never commit):

```bash
# PRINTIFY API
PRINTIFY_API_KEY=your-actual-api-key
PRINTIFY_SHOP_ID=12345678

# ETSY API
ETSY_OAUTH_TOKEN=your-oauth-token
ETSY_SHOP_ID=98765432

# AUTOMATION CONFIG
POD_BASE_COST_MARKUP=0.4          # 40% profit margin
IMAGE_GENERATION_PROVIDER=dalle   # dalle or replicate
AUTOMATION_API_TOKEN=your-secret-token  # For API authentication
AUTOMATION_DRY_RUN=false          # Set to true to test without publishing
AUTOMATION_TIMEOUT_MS=30000       # API timeout

# RUNTIME
RUNTIME_DATA_DIR=.runtime/automation
```

---

## API Endpoints

All endpoints require `Authorization: Bearer YOUR_API_TOKEN` header.

### 1. Create POD Products

**Endpoint**: `POST /api/automation/etsy`

Create new products on Printify and sync to Etsy.

**Request**:
```json
{
  "action": "create",
  "templates": [
    {
      "name": "Premium T-Shirt",
      "description": "High-quality organic cotton t-shirt",
      "category": "apparel",
      "printifyProductId": "16",
      "basePrice": 24.99,
      "designs": [
        {
          "id": "design-1",
          "name": "Black Logo",
          "colors": ["black"],
          "sizes": ["XS", "S", "M", "L", "XL", "2XL"],
          "imageUrl": "https://example.com/logo.png",
          "sku": "t-shirt-black-001"
        }
      ],
      "tags": ["t-shirt", "logo", "organic"],
      "materials": ["100% organic cotton"]
    }
  ],
  "designUrls": {
    "Premium T-Shirt": "https://example.com/design.png"
  }
}
```

**Response**:
```json
{
  "success": true,
  "action": "create",
  "results": [
    {
      "template": { ... },
      "printifyId": "87654321",
      "etsyId": 123456789
    }
  ],
  "timestamp": "2024-06-20T...",
  "duration": 2341
}
```

**Printify Product IDs** (common types):
- `16` - T-Shirt
- `1` - Long Sleeve Shirt
- `22` - Hoodie
- `25` - Sweatshirt
- `20` - Mug
- `18` - Pillow
- `21` - Phone Case

See full list: https://printify.com/app/doc/products

### 2. Sync Inventory

**Endpoint**: `POST /api/automation/etsy`

Sync quantity from Printify (source) to Etsy (destination).

**Request**:
```json
{
  "action": "sync-inventory",
  "productMappings": [
    {
      "printifyId": "87654321",
      "etsyId": 123456789,
      "variantMapping": {
        "t-shirt-black-001": {
          "printifyId": "variant-001",
          "etsyPropertyId": 200
        }
      }
    }
  ],
  "saveReport": true
}
```

**Response**:
```json
{
  "success": true,
  "action": "sync-inventory",
  "results": [
    {
      "timestamp": "2024-06-20T...",
      "totalProducts": 1,
      "syncedVariants": 6,
      "failedVariants": 0,
      "totalQuantitySync": 600,
      "results": [
        {
          "success": true,
          "productId": "87654321",
          "variantId": "variant-001",
          "newQuantity": 100,
          "printifyStatus": "active"
        }
      ]
    }
  ],
  "duration": 1234
}
```

Report saved to: `.runtime/automation/etsy-sync-{timestamp}.json`

### 3. Update Prices

**Endpoint**: `POST /api/automation/etsy`

Update Etsy prices based on Printify costs + markup percentage.

**Request**:
```json
{
  "action": "update-prices",
  "etsyListingId": 123456789,
  "printifyVariants": [
    {
      "id": "variant-001",
      "title": "Black/S",
      "sku": "t-shirt-black-s",
      "price": 8.99,
      "quantity": 100,
      "options": [
        { "name": "color", "value": "black" },
        { "name": "size", "value": "S" }
      ],
      "status": "active"
    }
  ],
  "markupPercent": 0.4,
  "saveReport": true
}
```

**Response**:
```json
{
  "success": true,
  "action": "update-prices",
  "results": {
    "timestamp": "2024-06-20T...",
    "totalVariants": 1,
    "updatedVariants": 1,
    "failedVariants": 0,
    "totalMarginAdjusted": 3.60,
    "results": [
      {
        "success": true,
        "variantId": "variant-001",
        "newPrice": 14.99,
        "baseCost": 8.99,
        "margin": 3.60
      }
    ]
  },
  "duration": 456
}
```

Report saved to: `.runtime/automation/etsy-price-{timestamp}.json`

### 4. Track Orders

**Endpoint**: `POST /api/automation/etsy`

Get status and tracking info for orders.

**Request**:
```json
{
  "action": "track-orders",
  "orderIds": ["order-123", "order-456"]
}
```

**Response**:
```json
{
  "success": true,
  "action": "track-orders",
  "results": [
    {
      "success": true,
      "orderId": "order-123",
      "status": "in_production",
      "trackingNumber": "1Z999AA10123456784",
      "trackingUrl": "https://tracking.carrier.com/...",
      "carrier": "UPS",
      "estimatedDelivery": "2024-06-27",
      "lastUpdate": "2024-06-20T..."
    },
    {
      "success": true,
      "orderId": "order-456",
      "status": "shipped",
      "trackingNumber": "1Z999BB10987654321",
      "trackingUrl": "https://tracking.carrier.com/...",
      "carrier": "FedEx",
      "estimatedDelivery": "2024-06-28",
      "lastUpdate": "2024-06-20T..."
    }
  ],
  "duration": 789
}
```

### 5. Health Check

**Endpoint**: `GET /api/automation/etsy`

Check configuration and connectivity status.

**Response**:
```json
{
  "status": "ok",
  "configured": {
    "printify": true,
    "etsy": true
  },
  "environment": {
    "PRINTIFY_API_KEY": true,
    "PRINTIFY_SHOP_ID": true,
    "ETSY_OAUTH_TOKEN": true,
    "ETSY_SHOP_ID": true,
    "IMAGE_GENERATION_PROVIDER": true,
    "POD_BASE_COST_MARKUP": true
  },
  "timestamp": "2024-06-20T..."
}
```

---

## Product Templates

Product templates define what gets created on Printify/Etsy. Use this structure:

```typescript
interface ProductTemplate {
  name: string;                    // "Premium T-Shirt"
  description: string;             // Long description
  category: string;               // "apparel", "home", "gifts"
  printifyProductId: string;       // "16" for t-shirt, "22" for hoodie, etc.
  basePrice: number;              // 24.99
  designs: DesignVariant[];       // See below
  tags: string[];                 // ["t-shirt", "logo"]
  shippingProfile?: string;       // Optional: custom shipping
  materials?: string[];           // ["100% organic cotton"]
}

interface DesignVariant {
  id: string;                     // unique ID
  name: string;                   // "Black Logo"
  colors: string[];              // ["black", "white"]
  sizes: string[];               // ["S", "M", "L", "XL"]
  imageUrl?: string;             // URL to design image
  imagePrompt?: string;          // DALL-E/Replicate prompt
  sku?: string;                  // "t-shirt-black-001"
}
```

Example file (`products.json`):
```json
{
  "products": [
    {
      "name": "Classic T-Shirt",
      "description": "Premium 100% organic cotton t-shirt with custom design",
      "category": "apparel",
      "printifyProductId": "16",
      "basePrice": 24.99,
      "designs": [
        {
          "id": "design-1",
          "name": "Black Logo",
          "colors": ["black"],
          "sizes": ["XS", "S", "M", "L", "XL", "2XL"],
          "imageUrl": "https://cdn.example.com/logo-black.png"
        }
      ],
      "tags": ["t-shirt", "organic", "logo"],
      "materials": ["100% organic cotton", "Pre-shrunk"]
    }
  ]
}
```

---

## Testing & Dry Run

### Local Testing

```bash
# 1. Enable dry-run mode in .env
AUTOMATION_DRY_RUN=true

# 2. Run API without publishing
curl -X POST http://localhost:3000/api/automation/etsy \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{ "action": "create", "templates": [...] }'

# 3. Check output — should show what would be created
```

### Verification Script

```bash
npm run verify:etsy-config
```

Checks:
- ✓ All environment variables present
- ✓ Printify API connectivity
- ✓ Etsy API connectivity
- ✓ Shop IDs valid
- ✓ API token format

---

## Common Tasks

### Create a Batch of T-Shirts

```javascript
const templates = [
  {
    name: "Logo T-Shirt (Black)",
    description: "Premium black t-shirt with embroidered logo",
    category: "apparel",
    printifyProductId: "16",
    basePrice: 24.99,
    designs: [{
      id: "black-tee",
      name: "Black",
      colors: ["black"],
      sizes: ["XS", "S", "M", "L", "XL", "2XL"],
      imageUrl: "https://cdn.example.com/logo.png"
    }],
    tags: ["t-shirt", "apparel"]
  },
  {
    name: "Logo T-Shirt (White)",
    description: "Premium white t-shirt with embroidered logo",
    category: "apparel",
    printifyProductId: "16",
    basePrice: 24.99,
    designs: [{
      id: "white-tee",
      name: "White",
      colors: ["white"],
      sizes: ["XS", "S", "M", "L", "XL", "2XL"],
      imageUrl: "https://cdn.example.com/logo-white.png"
    }],
    tags: ["t-shirt", "apparel"]
  }
];

// Send to API
fetch('/api/automation/etsy', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'create',
    templates
  })
});
```

### Sync All Products

```javascript
// Load product mappings from config
const productMappings = [
  {
    printifyId: "12345",
    etsyId: 987654,
    variantMapping: {
      "t-shirt-black-s": { printifyId: "v1", etsyPropertyId: 200 }
    }
  }
];

fetch('/api/automation/etsy', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'sync-inventory',
    productMappings,
    saveReport: true
  })
});
```

---

## Troubleshooting

### "PRINTIFY_API_KEY not configured"

- Check `.env` file exists in project root
- Verify `PRINTIFY_API_KEY` is set (not empty)
- Restart dev server after changing .env

### "Etsy API error [401]"

- OAuth token expired or invalid
- Get new token from https://www.etsy.com/developers
- Verify token has correct scopes: `listings:read`, `listings:write`, `inventory:read`, `inventory:write`

### "404 Not Found" on image upload

- Image URL must be publicly accessible
- Some CDNs require referrer headers
- Try uploading to Etsy first, then use that image URL

### "Variant mapping not found"

- Printify SKU doesn't match Etsy variant
- Verify SKUs are consistent between systems
- Check variant mapping in sync request

### "timeout waiting for response"

- API call took too long (> AUTOMATION_TIMEOUT_MS)
- Increase timeout: `AUTOMATION_TIMEOUT_MS=60000`
- Check API rate limits (Printify: 100 req/min, Etsy: varies by endpoint)

---

## Monitoring & Logs

Reports are saved to `.runtime/automation/`:
- `etsy-sync-{timestamp}.json` - Inventory sync results
- `etsy-price-{timestamp}.json` - Price update results

View latest sync:
```bash
cat .runtime/automation/etsy-sync-*.json | tail -1 | jq .
```

---

## Production Deployment

1. **Add secrets to GitHub Actions**:
   - Settings → Secrets → New repository secret
   - Add: `PRINTIFY_API_KEY`, `ETSY_OAUTH_TOKEN`, `AUTOMATION_API_TOKEN`

2. **Set environment variables on Vercel**:
   - Project Settings → Environment Variables
   - Add same secrets as GitHub

3. **Enable webhook updates** (optional):
   ```bash
   # Printify webhooks notify when orders change
   # Etsy webhooks notify when listings sold
   
   # Register in dashboard:
   # Printify: Settings → Webhooks
   # Etsy: App settings → Webhooks
   ```

4. **Monitor in production**:
   - Check `/api/automation/etsy` (GET) for status
   - Review `.runtime/automation/` reports
   - Set up alerts for failures

---

## Rate Limits

| Platform | Limit | Period |
|----------|-------|--------|
| Printify | 100   | /min   |
| Etsy     | 10    | /sec   |

Automation respects these by default. Adjust with:
```bash
PRINTIFY_RATE_LIMIT=100
ETSY_RATE_LIMIT=10
```

---

## Support

- **Printify Docs**: https://printify.com/app/doc
- **Etsy Docs**: https://developers.etsy.com/documentation/tutorials
- **Issues**: Check `AUTOMATION_DEBUG=true` in .env for verbose logs
