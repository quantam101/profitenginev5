# Affiliate Automation Guide — ProfitEngine v5

Complete reference for the multi-network affiliate automation system.

## Overview

The affiliate automation system provides:
- **Multi-network support**: Amazon Associates, ClickBank, CJ Affiliate, ShareASale
- **Auto-creation**: Generate affiliate links programmatically
- **Link injection**: Inject links into content automatically
- **Tracking**: Click, impression, and conversion tracking
- **Analytics**: Real-time dashboard metrics and commission tracking
- **Optimization**: AI-powered link and niche optimization
- **Batch operations**: Import/export CSV, bulk link creation

## Files

### Core Library
- **`app/lib/automation/affiliate-enhanced.ts`** (31 KB)
  - All affiliate network integrations
  - Link creation, tracking, persistence
  - Analytics and reporting
  - Optimization functions

### API Route
- **`app/api/automation/affiliate/route.ts`** (20 KB)
  - REST API for all affiliate operations
  - POST actions for creation/tracking
  - GET endpoints for status/stats
  - CSV import/export

### Base Library (Existing)
- **`lib/affiliates.ts`** (634 lines)
  - Legacy affiliate partner registry
  - UTM parameter generation
  - FTC disclosure templates

## Environment Setup

### Required Variables

```bash
# Amazon Associates
AMAZON_ASSOCIATES_TAG=alreadyhere-20
AMAZON_PA_API_KEY=your-api-key
AMAZON_PA_SECRET_KEY=your-secret
AMAZON_COMMISSION_RATE=0.04

# ClickBank
CLICKBANK_ACCOUNT=your-account
CLICKBANK_HOPLINK=your-hoplink
CLICKBANK_API_KEY=your-api-key
CLICKBANK_SECRET_KEY=your-secret
CLICKBANK_COMMISSION_RATE=0.50

# CJ Affiliate
CJ_ACCOUNT=your-account
CJ_SITE_ID=your-site-id
CJ_API_KEY=your-api-key
CJ_SECRET_KEY=your-secret
CJ_COMMISSION_RATE=0.10

# ShareASale
SHAREASALE_ACCOUNT=your-account
SHAREASALE_MERCHANT_ID=your-merchant-id
SHAREASALE_API_KEY=your-api-key
SHAREASALE_SECRET_KEY=your-secret
SHAREASALE_COMMISSION_RATE=0.08

# Storage
AFFILIATE_DATA_DIR=.data/affiliates
```

Add to `.env` or `.env.local`.

## API Usage

### Base URL
```
/api/automation/affiliate
```

### Create Single Link

Create affiliate links for a product across all enabled networks.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-link",
    "product": {
      "id": "proj-mgmt-software",
      "title": "Advanced Project Management Suite",
      "description": "Enterprise-grade collaboration platform",
      "price": 99.99,
      "category": "software",
      "niche": "productivity",
      "image": "https://example.com/image.jpg",
      "rating": 4.8,
      "reviews": 1250,
      "vendor": "Acme Inc"
    },
    "networks": ["amazon", "clickbank", "cj"]
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "create-link",
  "productId": "proj-mgmt-software",
  "links": [
    {
      "id": "amazon-proj-mgmt-software-...",
      "productId": "proj-mgmt-software",
      "network": "amazon",
      "affiliateUrl": "https://amazon.com/s?k=Advanced+Project+Management+Suite&tag=alreadyhere-20...",
      "niche": "productivity",
      "createdAt": "2026-06-20T21:45:00Z",
      "status": "active",
      "utmParams": {
        "source": "profitengine",
        "medium": "affiliate",
        "campaign": "productivity"
      }
    },
    // ... more networks
  ],
  "timestamp": "2026-06-20T21:45:00Z",
  "duration": 245
}
```

### Batch Create Links

Create links for multiple products at once.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "batch-create",
    "products": [
      {
        "id": "product-1",
        "title": "Product One",
        "description": "Description",
        "price": 29.99,
        "category": "books",
        "niche": "trading",
        "rating": 4.5,
        "reviews": 800
      },
      {
        "id": "product-2",
        "title": "Product Two",
        "description": "Description",
        "price": 49.99,
        "category": "software",
        "niche": "education"
      }
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "batch-create",
  "productCount": 2,
  "linkCount": 8,
  "links": [...],
  "duration": 512
}
```

### Track Click

Record when user clicks an affiliate link.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "track-click",
    "linkId": "amazon-proj-mgmt-software-...",
    "referer": "mysite.com/blog/productivity",
    "userId": "user-12345"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "track-click",
  "event": {
    "id": "click-1718900700000-abc123",
    "linkId": "amazon-proj-mgmt-software-...",
    "eventType": "click",
    "timestamp": "2026-06-20T21:45:00Z",
    "referer": "mysite.com/blog/productivity",
    "userId": "user-12345",
    "sessionId": "session-1718900700000"
  },
  "duration": 125
}
```

### Track Conversion

Record a sale/conversion with commission value.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "track-conversion",
    "linkId": "amazon-proj-mgmt-software-...",
    "value": 99.99,
    "orderId": "order-78910",
    "metadata": {
      "productCount": 1,
      "tier": "pro"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "track-conversion",
  "event": {
    "id": "conversion-1718900800000-def456",
    "linkId": "amazon-proj-mgmt-software-...",
    "eventType": "conversion",
    "timestamp": "2026-06-20T21:46:00Z",
    "value": 99.99,
    "metadata": {
      "orderId": "order-78910",
      "productCount": 1,
      "tier": "pro"
    }
  },
  "duration": 87
}
```

### Get Links

Retrieve links with optional filtering.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-links",
    "niche": "productivity",
    "network": "amazon",
    "status": "active"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "get-links",
  "count": 12,
  "links": [...]
}
```

### Get Dashboard Metrics

Get comprehensive analytics for a date range.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-metrics",
    "startDate": "2026-06-01",
    "endDate": "2026-06-30"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "get-metrics",
  "metrics": {
    "period": {
      "start": "2026-06-01T00:00:00Z",
      "end": "2026-06-30T23:59:59Z"
    },
    "totalLinks": 48,
    "activeLinks": 45,
    "totalClicks": 1250,
    "totalImpressions": 0,
    "totalConversions": 95,
    "conversionRate": 0.076,
    "estimatedRevenue": 4750.50,
    "byNetwork": {
      "amazon": {
        "links": 15,
        "clicks": 350,
        "conversions": 28,
        "revenue": 1200.75
      },
      "clickbank": {
        "links": 12,
        "clicks": 280,
        "conversions": 42,
        "revenue": 2100.00
      },
      "cj": {
        "links": 12,
        "clicks": 320,
        "conversions": 18,
        "revenue": 900.75
      },
      "shareasale": {
        "links": 9,
        "clicks": 300,
        "conversions": 7,
        "revenue": 549.00
      }
    },
    "byNiche": {
      "productivity": {
        "links": 24,
        "clicks": 600,
        "conversions": 48,
        "revenue": 2400.00
      },
      "education": {
        "links": 12,
        "clicks": 350,
        "conversions": 28,
        "revenue": 1400.00
      },
      "trading": {
        "links": 12,
        "clicks": 300,
        "conversions": 19,
        "revenue": 950.50
      }
    },
    "topProducts": [
      {
        "id": "proj-mgmt-software",
        "title": "Advanced Project Management Suite",
        "clicks": 180,
        "conversions": 24,
        "revenue": 1200.00
      }
    ]
  }
}
```

### Get Niche Metrics

Analytics for a specific niche.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-niche-metrics",
    "niche": "productivity"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "get-niche-metrics",
  "metrics": {
    "niche": "productivity",
    "linkCount": 24,
    "clicks": 600,
    "conversions": 48,
    "revenue": 2400.00,
    "topLinks": [
      {
        "id": "amazon-proj-mgmt-software-...",
        "clicks": 120,
        "conversions": 12
      }
    ]
  }
}
```

### Get Commission Report

Detailed commission tracking and status.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-commissions",
    "startDate": "2026-06-01",
    "endDate": "2026-06-30",
    "status": "pending"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "get-commissions",
  "report": {
    "period": {
      "start": "2026-06-01T00:00:00Z",
      "end": "2026-06-30T23:59:59Z"
    },
    "totalCommissions": 4750.50,
    "pendingCommissions": 2100.00,
    "approvedCommissions": 1800.50,
    "paidCommissions": 850.00,
    "byNetwork": {
      "amazon": 1200.75,
      "clickbank": 2100.00,
      "cj": 900.75,
      "shareasale": 549.00
    },
    "records": [...]
  }
}
```

### Optimize Link

Get optimization suggestions for a link.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "optimize-link",
    "linkId": "amazon-proj-mgmt-software-..."
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "optimize-link",
  "result": {
    "linkId": "amazon-proj-mgmt-software-...",
    "suggestions": [
      "Link has high click volume but low conversions, consider A/B testing",
      "Try cross-promoting with ClickBank for higher commission rates"
    ],
    "recommendations": {
      "abTesting": true,
      "multiNetworkStrategy": true
    }
  }
}
```

### Export CSV

Export links to CSV for external analysis.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "export-csv",
    "niche": "productivity"
  }'
```

**Response:**
CSV file with columns: `id,productId,network,affiliateUrl,niche,status,createdAt`

### Import CSV

Bulk import affiliate links from CSV.

**Request:**
```bash
curl -X POST /api/automation/affiliate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "import-csv",
    "csv": "id,productId,network,affiliateUrl,niche,status,createdAt\namazon-prod-1,prod-1,amazon,https://...,productivity,active,2026-06-20T00:00:00Z"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "import-csv",
  "importedCount": 1,
  "links": [...]
}
```

## Quick Status

Check network availability and stats:

```bash
# List enabled networks
curl /api/automation/affiliate?action=networks

# Get quick statistics
curl /api/automation/affiliate?action=stats
```

## Integration Examples

### JavaScript/Node.js

```typescript
import { createMultiNetworkLinks, trackConversion } from '@/app/lib/automation/affiliate-enhanced';

// Create links
const product = {
  id: 'my-product',
  title: 'My Product',
  description: 'Product description',
  price: 99.99,
  category: 'software',
  niche: 'productivity',
};

const links = await createMultiNetworkLinks(product);

// Track conversion
await trackConversion(links[0].id, 99.99, 'order-123');

// Get metrics
import { getDashboardMetrics } from '@/app/lib/automation/affiliate-enhanced';
const metrics = await getDashboardMetrics(
  new Date('2026-06-01'),
  new Date('2026-06-30')
);
```

### React Component

```typescript
'use client';

import { useState } from 'react';
import { AffiliateLink } from '@/app/lib/automation/affiliate-enhanced';

export default function AffiliateManager() {
  const [links, setLinks] = useState<AffiliateLink[]>([]);
  const [loading, setLoading] = useState(false);

  const createLinks = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/automation/affiliate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create-link',
          product: {
            id: 'test-product',
            title: 'Test Product',
            price: 99.99,
            category: 'software',
            niche: 'productivity',
          },
        }),
      });

      const data = await res.json();
      if (data.success) {
        setLinks(data.links);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={createLinks} disabled={loading}>
        {loading ? 'Creating...' : 'Create Affiliate Links'}
      </button>

      <ul>
        {links.map((link) => (
          <li key={link.id}>
            {link.network}: <a href={link.affiliateUrl} target="_blank">{link.affiliateUrl}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Next.js Server Action

```typescript
'use server';

import { trackConversion } from '@/app/lib/automation/affiliate-enhanced';

export async function recordSale(linkId: string, amount: number, orderId: string) {
  const event = await trackConversion(linkId, amount, orderId);
  return event;
}
```

## Data Storage

Links and events are stored in:
```
.data/affiliates/
  ├── affiliate-links.json          # All created links (JSON array)
  ├── conversion-events.jsonl       # Events (JSONL format, one per line)
  └── commission-records.jsonl      # Commission tracking
```

For production, integrate with your database (PostgreSQL, MongoDB, etc).

## Integrating with Existing Code

### Update `lib/affiliates.ts`

The existing `lib/affiliates.ts` can be extended to use the new system:

```typescript
// Add to lib/affiliates.ts
import { createAmazonLink } from '@/app/lib/automation/affiliate-enhanced';

export function generateAffiliateLink(partnerId: string, source = 'unknown'): string {
  // Existing code or delegate to new system
  if (partnerId === 'amazon') {
    const link = createAmazonLink({
      id: 'product-' + Date.now(),
      title: 'Product',
      description: 'Description',
      price: 0,
      category: 'general',
      niche: source,
    });
    return link.affiliateUrl;
  }
  // ... existing code
}
```

### Inject Links into Content

```typescript
import { createMultiNetworkLinks } from '@/app/lib/automation/affiliate-enhanced';

export async function enrichPostWithAffiliates(post: BlogPost) {
  // Find product mentions
  const products = extractProductMentions(post.content);

  for (const product of products) {
    const links = await createMultiNetworkLinks(product);
    // Inject into content
    post.affiliateLinks = links;
  }

  return post;
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│ Frontend (React/Next.js)                │
│ ├─ Blog Posts (injected links)         │
│ ├─ Product Pages                        │
│ └─ Dashboard (metrics)                  │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ API Layer (/api/automation/affiliate)   │
│ ├─ POST: create, track, optimize       │
│ └─ GET: status, metrics                 │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ Business Logic (affiliate-enhanced.ts)  │
│ ├─ Link Creation (4 networks)           │
│ ├─ Event Tracking                       │
│ ├─ Analytics Engine                     │
│ └─ Optimization                         │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ Storage Layer                           │
│ ├─ File-based (.data/affiliates)       │
│ ├─ PostgreSQL (prod)                    │
│ └─ MongoDB (optional)                   │
└─────────────────────────────────────────┘
```

## Performance Tips

1. **Batch operations**: Create multiple links at once (10-100 per request)
2. **Caching**: Cache link URLs in Redis for frequently accessed products
3. **Async tracking**: Use webhooks for conversion events instead of synchronous calls
4. **Database migration**: Move from file storage to PostgreSQL for production

## Security

1. **API authentication**: Add middleware to protect `/api/automation/affiliate`
2. **Rate limiting**: Prevent abuse (max 100 links/hour per user)
3. **Secrets**: Never commit API keys; use `.env` only
4. **Validation**: Sanitize product data before creating links

## Troubleshooting

### Links not being created
- Check env vars are set: `AMAZON_ASSOCIATES_TAG`, `CLICKBANK_HOPLINK`, etc.
- Verify network is enabled: `NETWORKS.amazon.enabled === true`
- Check API credentials in logs

### Conversions not tracking
- Ensure linkId matches a created link
- Check `.data/affiliates/conversion-events.jsonl` for events
- Verify user session is persisted

### Low conversion rates
- Run optimization: `POST /api/automation/affiliate { action: 'optimize-niche' }`
- Check metrics by network and niche
- A/B test different product positioning

## Next Steps

1. Set up environment variables
2. Deploy to Vercel
3. Start creating affiliate links
4. Monitor dashboard metrics
5. Optimize based on performance data

