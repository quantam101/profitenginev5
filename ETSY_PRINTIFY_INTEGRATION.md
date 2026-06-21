# Etsy/Printify Integration — Complete Implementation Guide

Complete working implementation of Print-on-Demand (POD) product automation system for Etsy and Printify.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [Production Checklist](#production-checklist)

---

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy the environment variables to `.env.local`:

```bash
# Printify Configuration
PRINTIFY_API_KEY=your-printify-api-key
PRINTIFY_SHOP_ID=your-shop-id

# Etsy Configuration
ETSY_OAUTH_TOKEN=your-oauth-token
ETSY_SHOP_ID=your-shop-id

# Automation Settings
POD_BASE_COST_MARKUP=0.4
AUTOMATION_API_TOKEN=your-secret-token
AUTOMATION_DRY_RUN=false
```

### 3. Verify Configuration

```bash
# Check all environment variables are set correctly
node -e "console.log({
  printifyKey: !!process.env.PRINTIFY_API_KEY,
  printifyShop: !!process.env.PRINTIFY_SHOP_ID,
  etsyToken: !!process.env.ETSY_OAUTH_TOKEN,
  etsyShop: !!process.env.ETSY_SHOP_ID
})"
```

### 4. Run Local Tests

```bash
# Start dev server
npm run dev

# In another terminal, test the API
curl -X GET http://localhost:3000/api/automation/etsy \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Create Your First Product

```bash
curl -X POST http://localhost:3000/api/automation/etsy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/etsy-create-product-request.json
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   ProfitEngine Frontend                      │
│                    (Next.js App)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ API Requests
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              /api/automation/etsy (Route Handler)            │
│  - Validates auth                                           │
│  - Routes actions to handlers                               │
│  - Returns JSON responses                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
        ┌───────────────────┐   ┌──────────────┐
        │  PrintifyClient   │   │  EtsyClient  │
        │  - Create product │   │ - Create     │
        │  - Sync inventory │   │   listing    │
        │  - Track orders   │   │ - Upload     │
        │                   │   │   images     │
        └───────────────────┘   │ - Update     │
                │               │   inventory  │
                │               └──────────────┘
                │                      │
        ┌───────▼──────────┐  ┌────────▼────────┐
        │  Printify API    │  │   Etsy API      │
        │  /api/v0/shops/* │  │  /v3/            │
        └──────────────────┘  └─────────────────┘
                │                      │
        ┌───────▼────────────────────▼──────────┐
        │  Printify Provider + POD Fulfillment  │
        │  (T-Shirts, Hoodies, Mugs, etc.)     │
        └──────────────────────────────────────┘
```

## Key Components

### `app/lib/automation/etsy.ts`
Main automation library with:
- `PrintifyClient` - Printify API wrapper
- `EtsyClient` - Etsy API wrapper
- Product creation, inventory sync, price management
- Order tracking and bulk operations

### `app/api/automation/etsy/route.ts`
Next.js API route that:
- Validates authentication
- Routes requests to handlers
- Returns JSON responses
- Handles errors gracefully

---

## Installation & Setup

### Step 1: Get API Credentials

#### Printify
1. Go to https://app.printify.com
2. Dashboard → Settings → Integrations → API
3. Generate API token
4. Copy: `PRINTIFY_API_KEY` and `PRINTIFY_SHOP_ID`

#### Etsy
1. Go to https://www.etsy.com/developers
2. Create new app
3. Generate OAuth token or personal access token
4. Copy: `ETSY_OAUTH_TOKEN` and `ETSY_SHOP_ID`

### Step 2: Update Environment Variables

Edit `.env.local`:

```bash
# Required
PRINTIFY_API_KEY=pk_live_xxxxxxxxxxxxxxx
PRINTIFY_SHOP_ID=12345678
ETSY_OAUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5...
ETSY_SHOP_ID=98765432

# Optional
POD_BASE_COST_MARKUP=0.4          # 40% profit margin
AUTOMATION_API_TOKEN=secret-key   # For API authentication
AUTOMATION_DRY_RUN=false          # Test without publishing
AUTOMATION_TIMEOUT_MS=30000       # API timeout
RUNTIME_DATA_DIR=.runtime/automation
```

### Step 3: Test Connectivity

```bash
npm run dev

# Health check
curl -X GET http://localhost:3000/api/automation/etsy \
  -H "Authorization: Bearer secret-key"

# Expected response:
# {
#   "status": "ok",
#   "configured": {
#     "printify": true,
#     "etsy": true
#   },
#   "timestamp": "2024-06-20T..."
# }
```

---

## API Reference

### Endpoints

All requests require: `Authorization: Bearer YOUR_TOKEN`

#### POST /api/automation/etsy

##### Action: create

Create new products on Printify and sync to Etsy.

**Request:**
```json
{
  "action": "create",
  "templates": [
    {
      "name": "Product Name",
      "description": "Product description",
      "category": "apparel",
      "printifyProductId": "16",
      "basePrice": 24.99,
      "designs": [
        {
          "id": "design-1",
          "name": "Color Name",
          "colors": ["black"],
          "sizes": ["S", "M", "L", "XL"],
          "imageUrl": "https://example.com/image.png",
          "sku": "sku-value"
        }
      ],
      "tags": ["tag1", "tag2"],
      "materials": ["100% cotton"]
    }
  ],
  "designUrls": {
    "Product Name": "https://example.com/design.png"
  }
}
```

**Response:**
```json
{
  "success": true,
  "action": "create",
  "results": [
    {
      "template": { ... },
      "printifyId": "123456",
      "etsyId": 987654321
    }
  ],
  "timestamp": "2024-06-20T10:30:00Z",
  "duration": 2345
}
```

##### Action: sync-inventory

Sync quantity from Printify to Etsy.

**Request:**
```json
{
  "action": "sync-inventory",
  "productMappings": [
    {
      "printifyId": "123456",
      "etsyId": 987654321,
      "variantMapping": {
        "sku-value": {
          "printifyId": "variant-id",
          "etsyPropertyId": 200
        }
      }
    }
  ],
  "saveReport": true
}
```

**Response:**
```json
{
  "success": true,
  "action": "sync-inventory",
  "results": [
    {
      "timestamp": "2024-06-20T10:30:00Z",
      "totalProducts": 1,
      "syncedVariants": 6,
      "failedVariants": 0,
      "totalQuantitySync": 600,
      "results": [...]
    }
  ],
  "timestamp": "2024-06-20T10:30:00Z",
  "duration": 1234
}
```

##### Action: update-prices

Update Etsy prices based on Printify costs + markup.

**Request:**
```json
{
  "action": "update-prices",
  "etsyListingId": 987654321,
  "printifyVariants": [
    {
      "id": "variant-1",
      "title": "Black/S",
      "sku": "sku-value-s",
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

**Response:**
```json
{
  "success": true,
  "action": "update-prices",
  "results": {
    "timestamp": "2024-06-20T10:30:00Z",
    "totalVariants": 1,
    "updatedVariants": 1,
    "failedVariants": 0,
    "totalMarginAdjusted": 3.60,
    "results": [
      {
        "success": true,
        "variantId": "variant-1",
        "newPrice": 14.99,
        "baseCost": 8.99,
        "margin": 3.60
      }
    ]
  },
  "timestamp": "2024-06-20T10:30:00Z",
  "duration": 456
}
```

##### Action: track-orders

Get status and tracking info for orders.

**Request:**
```json
{
  "action": "track-orders",
  "orderIds": ["order-1", "order-2", "order-3"]
}
```

**Response:**
```json
{
  "success": true,
  "action": "track-orders",
  "results": [
    {
      "success": true,
      "orderId": "order-1",
      "status": "in_production",
      "trackingNumber": "1Z999AA10123456784",
      "trackingUrl": "https://tracking.carrier.com/...",
      "carrier": "UPS",
      "estimatedDelivery": "2024-06-27",
      "lastUpdate": "2024-06-20T..."
    }
  ],
  "timestamp": "2024-06-20T10:30:00Z",
  "duration": 789
}
```

#### GET /api/automation/etsy

Health check and configuration status.

**Response:**
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

## Usage Examples

### Example 1: Create a Single T-Shirt Product

```javascript
const product = {
  name: "Trading Strategy T-Shirt",
  description: "Premium t-shirt with trading graphics",
  category: "apparel",
  printifyProductId: "16",
  basePrice: 24.99,
  designs: [{
    id: "design-1",
    name: "Black",
    colors: ["black"],
    sizes: ["XS", "S", "M", "L", "XL", "2XL"],
    imageUrl: "https://cdn.example.com/design.png",
    sku: "trad-tshirt-black"
  }],
  tags: ["t-shirt", "trading"],
  materials: ["100% organic cotton"]
};

const response = await fetch('http://localhost:3000/api/automation/etsy', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'create',
    templates: [product]
  })
});

const result = await response.json();
console.log(`Created: Printify ${result.results[0].printifyId}, Etsy ${result.results[0].etsyId}`);
```

### Example 2: Bulk Create Multiple Products

```javascript
const templates = [
  { name: "T-Shirt", printifyProductId: "16", basePrice: 24.99, ... },
  { name: "Hoodie", printifyProductId: "22", basePrice: 49.99, ... },
  { name: "Mug", printifyProductId: "20", basePrice: 12.99, ... }
];

const response = await fetch('http://localhost:3000/api/automation/etsy', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'create',
    templates: templates
  })
});

const { results } = await response.json();
results.forEach(r => {
  console.log(`${r.template.name}: Printify ${r.printifyId}, Etsy ${r.etsyId}`);
});
```

### Example 3: Sync Inventory Weekly

```javascript
// Run every Sunday at 2 AM
const schedule = require('node-cron');

schedule.cron('0 2 * * 0', async () => {
  const mappings = loadProductMappings('config/products.json');
  
  const response = await fetch('http://localhost:3000/api/automation/etsy', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'sync-inventory',
      productMappings: mappings,
      saveReport: true
    })
  });

  const { results } = await response.json();
  console.log(`Synced ${results[0].syncedVariants} variants`);
});
```

### Example 4: Update All Product Prices

```javascript
const products = [
  { etsyId: 123, printifyVariants: [...], markup: 0.4 },
  { etsyId: 456, printifyVariants: [...], markup: 0.35 }
];

for (const product of products) {
  const response = await fetch('http://localhost:3000/api/automation/etsy', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'update-prices',
      etsyListingId: product.etsyId,
      printifyVariants: product.printifyVariants,
      markupPercent: product.markup,
      saveReport: true
    })
  });

  const { results } = await response.json();
  console.log(`Updated ${results.updatedVariants} variants for listing ${product.etsyId}`);
}
```

### Example 5: Monitor Orders

```javascript
// Check order status every hour
setInterval(async () => {
  const orderIds = ['order-1', 'order-2', 'order-3'];
  
  const response = await fetch('http://localhost:3000/api/automation/etsy', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'track-orders',
      orderIds: orderIds
    })
  });

  const { results } = await response.json();
  
  results.forEach(order => {
    if (order.status === 'shipped') {
      console.log(`✓ Order ${order.orderId} shipped: ${order.trackingNumber}`);
    }
  });
}, 3600000);
```

---

## Troubleshooting

### "PRINTIFY_API_KEY not configured"

**Cause**: Environment variable not set

**Fix**:
1. Check `.env.local` has `PRINTIFY_API_KEY`
2. Restart dev server (`npm run dev`)
3. Verify value doesn't have quotes: `PRINTIFY_API_KEY=pk_live_xxx` (not `PRINTIFY_API_KEY="pk_live_xxx"`)

### "Etsy API error [401]"

**Cause**: Invalid or expired OAuth token

**Fix**:
1. Generate new token from https://www.etsy.com/developers
2. Update `ETSY_OAUTH_TOKEN` in `.env.local`
3. Verify token has scopes: `listings:write`, `inventory:write`

### "Variant mapping not found"

**Cause**: SKU mismatch between Printify and Etsy

**Fix**:
1. Get SKU from Printify: `printifyProduct.variants[0].sku`
2. Add to variantMapping with matching key
3. Verify `etsyPropertyId` is valid (usually 200 for color)

### "Timeout waiting for response"

**Cause**: API call took too long

**Fix**:
1. Increase timeout: `AUTOMATION_TIMEOUT_MS=60000`
2. Check API status pages
3. Reduce batch size in bulk operations

### "Image upload failed"

**Cause**: Image URL not publicly accessible

**Fix**:
1. Test image URL in browser
2. Use CDN URL instead of localhost
3. Ensure no authentication required to access image

---

## Production Checklist

Before deploying to production:

- [ ] All environment variables set in `.env` (never in code)
- [ ] GitHub Actions secrets configured (PRINTIFY_API_KEY, ETSY_OAUTH_TOKEN, etc.)
- [ ] Vercel environment variables set for deployment
- [ ] API token (`AUTOMATION_API_TOKEN`) set to strong random string
- [ ] `AUTOMATION_DRY_RUN` set to `false` in production
- [ ] Health check passing: `GET /api/automation/etsy`
- [ ] Test create action with single product
- [ ] Test sync-inventory action
- [ ] Test update-prices action
- [ ] Error logging configured (logs directory exists)
- [ ] Rate limits understood and respected
- [ ] Monitoring/alerts configured for failures
- [ ] Backup/recovery plan documented
- [ ] Rollback procedure tested

---

## File Structure

```
project/
├── app/
│   ├── lib/automation/
│   │   └── etsy.ts                    # Main automation library
│   └── api/automation/
│       └── etsy/
│           └── route.ts               # API endpoint
├── examples/
│   ├── etsy-product-templates.json   # Example templates
│   ├── etsy-automation-demo.ts       # Demo code
│   └── etsy-create-product-request.json
├── ETSY_PRINTIFY_SETUP.md            # Setup guide
├── ETSY_PRINTIFY_INTEGRATION.md      # This file
└── .env.local                        # Environment variables (local)
```

---

## Next Steps

1. **Create Product Templates**: Edit `examples/etsy-product-templates.json`
2. **Set Up Monitoring**: Add error logging and alerting
3. **Automate Scheduling**: Use GitHub Actions or cron jobs
4. **Monitor Production**: Check logs and reports regularly
5. **Scale Products**: Add more templates and run bulk creation

---

## Support & Resources

- **Printify API Docs**: https://printify.com/app/doc
- **Etsy API Docs**: https://developers.etsy.com/documentation
- **Example Templates**: `examples/etsy-product-templates.json`
- **Demo Code**: `examples/etsy-automation-demo.ts`
- **Setup Guide**: `ETSY_PRINTIFY_SETUP.md`

