# Article Monetization Workflow (Gumroad + Printify)

## Overview

The daily publishing workflow (`scripts/publish_article_resilient.py`) now automatically creates monetization assets after successfully publishing articles to GitHub Pages:

1. **Ebook Creation (Gumroad)** — Articles with 1000+ words auto-convert to premium ebooks
2. **POD Product Queuing (Printify)** — Smart product suggestions based on article topic
3. **Monetization Reporting** — Revenue potential and next action tracking

---

## Configuration

### Environment Variables

```bash
# Gumroad Integration
GUMROAD_ENABLED=true                    # Enable/disable ebook publishing (default: true)
GUMROAD_API_KEY=<your-gumroad-api-key>  # Required to publish (get from Gumroad account)
GUMROAD_BASE_PRICE=4.99                 # Ebook price (default: 4.99 USD)
GUMROAD_AMAZON_TAG=alreadyhere-20       # Amazon Associates tag in ebook footer

# Printify Integration
PRINTIFY_ENABLED=true                   # Enable/disable POD product creation (default: true)
PRINTIFY_API_KEY=<your-printify-api-key> # Required to create products (get from Printify)

# Monetization Thresholds
EBOOK_WORD_LIMIT=1000                   # Minimum words to trigger ebook creation (default: 1000)
```

### Getting API Keys

#### Gumroad
1. Go to https://gumroad.com/dashboard/settings
2. Navigate to **API Access**
3. Create a new API key
4. Copy the token and set `GUMROAD_API_KEY`

#### Printify
1. Go to https://printify.com/dashboard/settings
2. Navigate to **API Keys**
3. Create a new API key
4. Copy the token and set `PRINTIFY_API_KEY`

---

## Workflow

### 1. Article Publication (GitHub)
- Article generated or fallback generated
- Revenue execution brief auto-attached
- Published to GitHub Pages (creates canonical URL)

### 2. Ebook Generation (Conditional)
**Trigger:** Article word count >= `EBOOK_WORD_LIMIT` (default: 1000)

**Process:**
- Article markdown converted to ebook format
- Includes front matter, table of contents, action checklist
- Footer with Already Here LLC branding and Amazon Associates tag
- Saved as `{slug}_ebook.md`

**Example Output:**
```
/scripts/my-article_ebook.md
```

### 3. Gumroad Publication (Conditional)
**Trigger:** Ebook successfully generated AND `GUMROAD_ENABLED=true`

**Process:**
- Markdown ebook uploaded to Gumroad via API
- Product created with title, description, tags
- Price set to `GUMROAD_BASE_PRICE`
- Email capture enabled (opt-in for customer list)

**Output:**
```json
{
  "status": "success",
  "product_id": "xyz123",
  "url": "https://gumroad.com/d/xyz123",
  "price": 4.99
}
```

### 4. POD Product Suggestions & Queuing (Conditional)
**Trigger:** `PRINTIFY_ENABLED=true`

**Smart Suggestions:**
- Article title + tags analyzed
- Product types matched to topic:
  - `automation`, `ai` → t-shirt, mug, hat, notebook
  - `small business` → notebook, mug, poster
  - `revenue`, `affiliate` → poster, canvas-print
  - Default: t-shirt, mug, notebook

**Process (Per Product Type):**
1. Product created on Printify via API
2. Status: "pending_design" (requires manual upload + approval)
3. Links sent to Printify dashboard for design work
4. Once designed + approved, product goes live

**Output:**
```json
{
  "t-shirt": {
    "status": "pending_design",
    "product_id": "abc456",
    "product_type": "t-shirt",
    "url": "https://printify.com/dashboard/products/abc456",
    "note": "Product created. Requires design upload and manual approval before publishing."
  },
  "mug": { ... },
  "notebook": { ... }
}
```

---

## Reports

### 1. Distribution Report
**File:** `distribution_report_YYYYMMDD_HHMMSS.json`

Tracks social media + ecommerce platform distribution:
```json
{
  "timestamp": "2026-06-19T14:32:00Z",
  "canonical_url": "https://quantam101.github.io/...",
  "social_media": {
    "twitter": { "status": "success", "url": "..." },
    "linkedin": { "status": "skipped", "reason": "no_credentials" }
  },
  "ecommerce": {
    "gumroad": { "status": "success", "url": "..." },
    "printify": { ... }
  },
  "summary": {
    "total_platforms": 14,
    "successful": 8,
    "failed": 0,
    "skipped": 6
  }
}
```

### 2. Monetization Report
**File:** `monetization_report_YYYYMMDD_HHMMSS.json`

Comprehensive monetization overview:
```json
{
  "article": {
    "title": "AI Automation Systems for Small Business Revenue",
    "word_count": 1847,
    "tags": ["ai", "automation", "revenue", "smallbusiness"],
    "canonical_url": "https://quantam101.github.io/..."
  },
  "monetization": {
    "ebook": {
      "eligible": true,
      "created": true,
      "price": 4.99,
      "url": "https://gumroad.com/d/xyz123"
    },
    "pod_products": {
      "queued_count": 3,
      "products": [
        {
          "type": "t-shirt",
          "status": "pending_design",
          "url": "https://printify.com/dashboard/products/abc1"
        },
        {
          "type": "mug",
          "status": "pending_design",
          "url": "https://printify.com/dashboard/products/abc2"
        },
        {
          "type": "notebook",
          "status": "pending_design",
          "url": "https://printify.com/dashboard/products/abc3"
        }
      ]
    }
  },
  "distribution": {
    "social_platforms": 8,
    "canonical_url": "https://quantam101.github.io/..."
  },
  "revenue_potential": {
    "gumroad_ebook": 4.99,
    "expected_sales_10_percent": 0.499,
    "expected_sales_1_percent": 0.0499,
    "pod_potential_conservative": 15.0,
    "currency": "USD",
    "note": "Conservative estimates based on typical content monetization rates"
  },
  "next_actions": [
    "Monitor Gumroad sales and email opt-ins",
    "Review Printify designs and approve POD products",
    "Add product links to related articles",
    "Create email sequence promoting the ebook",
    "Track affiliate clicks and conversions"
  ],
  "timestamp": "2026-06-19T14:32:00Z"
}
```

---

## Manual Workflow Steps

### After Ebook Created (Gumroad)

1. **Check Gumroad Dashboard**
   - Go to https://gumroad.com/dashboard/products
   - Verify product created with correct title and price
   - Add cover image (optional but recommended)
   - Customize description if needed

2. **Test Purchase Flow**
   - Use incognito/private browser
   - Complete test purchase
   - Verify email capture works
   - Check download link

3. **Promote**
   - Email to subscriber list
   - Pin to relevant social platform
   - Add link to related articles

### After POD Products Queued (Printify)

1. **Review Each Product**
   - Go to https://printify.com/dashboard/products
   - Click each product link from monetization report
   - Upload custom design OR
   - Use Printify design templates

2. **Design Approval Checklist**
   - [ ] Product image matches article theme
   - [ ] Text is readable and branded
   - [ ] Color palette professional
   - [ ] Mockup preview looks good
   - [ ] Print quality meets standards

3. **Publish**
   - Select print providers (Printful, Merch by Amazon, etc.)
   - Set profit margin above print cost
   - Publish to Printify storefront
   - (Optional) Sync to Shopify/WooCommerce

4. **Promote**
   - Add product links to article footer
   - Create email announcing products
   - Share on social media
   - Link from related products

---

## Function Reference

### `_word_count(text: str) -> int`
Count words in markdown text (excludes formatting).

### `_get_product_suggestions(article: Dict[str, Any]) -> List[str]`
Smart POD product suggestions based on article topic.

**Returns:** List of product types: "t-shirt", "mug", "hoodie", "notebook", "poster", "sticker"

### `_convert_article_to_ebook(article: Dict[str, Any], output_dir: str = ".") -> Optional[str]`
Convert article to ebook markdown with front matter and checklists.

**Returns:** Path to generated `{slug}_ebook.md` or None on failure

### `_publish_to_gumroad(ebook_path: str, article: Dict[str, Any]) -> Optional[Dict[str, str]]`
Upload ebook to Gumroad API.

**Returns:**
- Success: `{"status": "success", "product_id": "...", "url": "...", "price": 4.99}`
- Failure: `{"status": "failed", "error": "..."}`

### `_create_printify_product(article: Dict[str, Any], product_type: str) -> Optional[Dict[str, str]]`
Queue POD product creation on Printify (requires manual design).

**Returns:**
- Success: `{"status": "pending_design", "product_id": "...", "url": "...", "note": "..."}`
- Failure: `{"status": "failed", "product_type": "...", "error": "..."}`

### `_build_monetization_report(...) -> Dict[str, Any]`
Generate comprehensive monetization report with revenue estimates and next actions.

---

## Log Output Examples

### Successful Flow
```
[EBOOK][OK] Generated ebook markdown: ./ai-automation_ebook.md
[GUMROAD][OK] Product published: https://gumroad.com/d/xyz123
[MONETIZE] Generating POD product suggestions...
[MONETIZE] Queuing t-shirt for Printify...
[PRINTIFY][OK] Product queued for t-shirt: https://printify.com/dashboard/products/abc1
[MONETIZE] Queuing mug for Printify...
[PRINTIFY][OK] Product queued for mug: https://printify.com/dashboard/products/abc2
[MONETIZE][SUMMARY] Ebook: CREATED, POD Products Queued: 2
```

### Word Count Too Low
```
[MONETIZE] Article has 812 words (threshold: 1000). Skipping ebook.
```

### Missing Credentials
```
[GUMROAD][SKIP] Gumroad disabled or no API key configured
[PRINTIFY][SKIP] Printify disabled or no API key configured
```

---

## Revenue Math

### Gumroad Ebook
- **Base Price:** $4.99 (configurable)
- **Gumroad Fee:** ~10% (~$0.50)
- **Your Revenue:** ~$4.49/sale
- **At 10 sales:** ~$44.90
- **At 50 sales:** ~$224.50

### Printify POD Products (Conservative)
- **Avg Profit/Product:** $5-15 depending on design and provider
- **With 3 products queued:** $15-45 potential revenue
- **Realistic target:** 1-3 sales per product per month = $20-90/month baseline

### Combined Monthly Target
With consistent publishing (2 articles/week):
- 4 ebooks/month @ $4.49 each = ~$18/month
- 12 POD products queued, 2-3 sales avg = $40-60/month
- **Total:** $60-80/month baseline (scales with audience growth)

---

## Troubleshooting

### Gumroad Product Not Appearing
- Check API key in `GUMROAD_API_KEY`
- Verify Gumroad account has API permissions
- Check file size of ebook (Gumroad may have file limits)
- Review Gumroad dashboard for error details

### Printify Designs Not Uploading
- Verify Printify API key (`PRINTIFY_API_KEY`)
- Check Printify account has product creation permission
- Ensure product type is valid (t-shirt, mug, notebook, etc.)
- Manual design upload required in Printify dashboard

### Word Count Too Low for Ebook
- Increase article length (add examples, checklists, case studies)
- Lower threshold: `export EBOOK_WORD_LIMIT=800`
- Not all articles need ebooks — focus on comprehensive guides

### Revenue Reports Not Generating
- Ensure `GUMROAD_ENABLED=true` and `PRINTIFY_ENABLED=true`
- Check file write permissions in script directory
- Review error logs: `[MONETIZE][WARN] Failed to save...`

---

## Integration with CI/CD

### GitHub Actions Workflow
```yaml
- name: Publish Article with Monetization
  env:
    GUMROAD_API_KEY: ${{ secrets.GUMROAD_API_KEY }}
    PRINTIFY_API_KEY: ${{ secrets.PRINTIFY_API_KEY }}
    EBOOK_WORD_LIMIT: 1000
    GUMROAD_BASE_PRICE: 4.99
  run: python scripts/publish_article_resilient.py [TOPIC]
```

### Secrets Required
- `GUMROAD_API_KEY` — Gumroad API token
- `PRINTIFY_API_KEY` — Printify API token

All other env vars are optional (use defaults if not set).

---

## Next Steps

1. **Get API Keys**
   - Gumroad: https://gumroad.com/dashboard/settings → API Access
   - Printify: https://printify.com/dashboard/settings → API Keys

2. **Test with Sample Article**
   ```bash
   export GUMROAD_API_KEY="your-key"
   export PRINTIFY_API_KEY="your-key"
   python scripts/publish_article_resilient.py "ai automation systems"
   ```

3. **Monitor Reports**
   - Check `monetization_report_*.json` after each publish
   - Review Gumroad and Printify dashboards
   - Approve POD designs within 24 hours for max revenue

4. **Iterate**
   - Track which topics generate best ebook downloads
   - Optimize POD designs based on sales data
   - Add affiliate links to ebooks for additional revenue

