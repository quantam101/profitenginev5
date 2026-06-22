# n8n Workflow: GitHub to Gumroad Auto-Post

**Fully automated product posting via n8n webhook**

---

## What It Does

When you push a product file (`products/*COMPLETE.txt`) to GitHub:
1. ✅ GitHub sends webhook to n8n
2. ✅ n8n filters for product files on main branch
3. ✅ Maps filename to product data
4. ✅ POSTs to Gumroad API
5. ✅ Creates and publishes product
6. ✅ Sends notification (optional)

**Result:** Product LIVE on Gumroad in seconds

---

## Setup Steps

### Step 1: Add Gumroad Credentials to n8n

1. Open n8n: `http://your-n8n-server:5678`
2. Go to **Credentials** → **New Credential**
3. Select **HTTP Header Auth**
4. Name: `gumroad_token`
5. Add header:
   ```
   Authorization: Bearer YOUR_GUMROAD_API_TOKEN
   ```
6. Save

### Step 2: Import Workflow

1. Go to **Workflows** → **Import**
2. Upload: `n8n-gumroad-webhook.json`
3. Or copy/paste the JSON
4. Click **Import**

### Step 3: Configure GitHub Webhook

1. Open n8n workflow
2. Click **Webhook** node
3. Copy webhook URL (example: `https://your-n8n.com/webhook/gumroad-products`)
4. Go to GitHub repo: Settings → Webhooks
5. Add webhook:
   ```
   URL: https://your-n8n.com/webhook/gumroad-products
   Event: Push events
   Content type: application/json
   Active: ✓
   ```
6. Save

### Step 4: Test

1. Push a product file to GitHub:
   ```bash
   git push origin main
   ```
2. Watch n8n execution (click Workflow → Executions)
3. Check Gumroad dashboard - product should appear within seconds

---

## Workflow Nodes Explained

| Node | Purpose |
|------|---------|
| **Webhook** | Receives GitHub push events |
| **Filter** | Only process main branch + product files |
| **Map** | Convert filename to product metadata |
| **POST to Gumroad** | Call Gumroad API to create product |
| **Format** | Parse success response |
| **Notify** | Send completion alert (optional) |

---

## Product Mapping

Automatically converts filenames to products:

```
AI_BUSINESS_PROMPT_PACK_COMPLETE.txt
    ↓
AI Business Prompt Pack ($27)
- 50 complete prompts, 768 lines

REAL_ESTATE_COMPLETE.txt
    ↓
Real Estate Copywriting Kit ($19)
- 5 sequences + 3 templates, 454 lines

POD_COMPLETE.txt
    ↓
POD Design Prompt Bundle ($22)
- 100+ design prompts, 419 lines

SEO_COMPLETE.txt
    ↓
Programmatic SEO Starter Kit ($29)
- 100+ keywords + outlines, 389 lines

SOCIAL_MEDIA_COMPLETE.txt
    ↓
Social Media Content Engine ($17)
- 90-day calendar, 327 lines
```

---

## How It Works

### GitHub Webhook Trigger
```
POST https://your-n8n.com/webhook/gumroad-products
{
  "ref": "refs/heads/main",
  "commits": [{
    "modified": ["products/AI_BUSINESS_PROMPT_PACK_COMPLETE.txt"]
  }]
}
```

### Gumroad API Call
```
POST https://api.gumroad.com/v2/products

name: AI Business Prompt Pack
url_name: ai-business-prompt-pack
price: 2700
description: 50 complete AI prompts...
tags: ai,prompts,business,automation
published: true
Authorization: Bearer YOUR_TOKEN
```

### Response
```
{
  "status": "SUCCESS",
  "product_name": "AI Business Prompt Pack",
  "product_id": "xxx",
  "url": "https://gumroad.com/l/xxx",
  "timestamp": "2026-06-21T..."
}
```

---

## Adding More Products

To add a new product to the workflow:

1. Edit **Map to Product Data** node
2. Add to productMap:
   ```javascript
   'YOUR PRODUCT NAME': {
     name: 'Your Product Name',
     url_name: 'your-product-url',
     price: 2999,  // in cents
     description: 'Your product description...'
   }
   ```
3. Save & redeploy

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook not triggering | Check GitHub webhook log (Repo Settings → Webhooks → Recent Deliveries) |
| 401 Unauthorized | Verify GUMROAD_API_TOKEN is correct and active |
| Product not appearing | Check n8n execution logs for error response from Gumroad API |
| Wrong product created | Verify filename matches productMap (case-insensitive) |

---

## Live Status

Once deployed:
- ✅ All 5 products auto-post to Gumroad when pushed
- ✅ No manual dashboard work needed
- ✅ Zero delay between push and live product
- ✅ Fully tracked & logged in n8n

---

## Next Step

1. Import workflow into n8n
2. Add GitHub webhook
3. Test by pushing a product file
4. **Done** - completely automated

