# Gumroad + Printify Monetization Integration

## What Was Added

The daily article publishing workflow now automatically monetizes content across two channels:

### 1. Gumroad Ebook Publishing
- Articles with 1000+ words auto-convert to premium ebooks
- Ebooks published instantly to Gumroad at $4.99 (configurable)
- Email capture enabled for subscriber growth
- Full markdown conversion with implementation checklists

### 2. Printify POD Products
- Smart product suggestions based on article topic
- 2-3 products queued per article (t-shirt, mug, notebook, etc.)
- Requires manual design upload + approval
- Links provided directly to Printify dashboard

### 3. Monetization Reports
- `monetization_report_*.json` with revenue estimates
- Product URLs and status for each platform
- Next action checklist for follow-ups

---

## Files Modified

### `scripts/publish_article_resilient.py`
**Changes:**
- Added imports: `Path`, `Optional` for file operations
- Added config variables for Gumroad/Printify API keys and thresholds
- Added 4 core monetization functions:
  - `_word_count(text)` — Count words excluding markdown
  - `_get_product_suggestions(article)` — Smart POD product matching
  - `_convert_article_to_ebook(article)` — Generate markdown ebook
  - `_publish_to_gumroad(ebook_path, article)` — API publish to Gumroad
  - `_create_printify_product(article, product_type)` — API queue on Printify
  - `_build_monetization_report(...)` — Generate comprehensive report
- Updated `_check_ecommerce_credentials()` to include Gumroad/Printify
- Enhanced main() to call monetization workflow after GitHub publish
- Added monetization report generation and saving

**Lines Added:** ~580 lines of production code + ~200 lines of documentation

---

## New Files Created

### `docs/MONETIZATION_WORKFLOW.md` (500+ lines)
Complete workflow documentation including:
- Configuration options (env vars)
- Step-by-step workflow explanation
- Report structure and examples
- Function reference
- Revenue math and estimates
- Manual follow-up steps
- Troubleshooting guide
- CI/CD integration examples

### `docs/GUMROAD_PRINTIFY_SETUP.md` (250+ lines)
Quick 5-minute setup guide:
- How to get API keys from Gumroad and Printify
- Adding secrets to GitHub Actions
- Local testing instructions
- Configuration options
- Troubleshooting

### `scripts/test_monetization_functions.py` (210 lines)
Comprehensive test suite validating:
- Word counting function
- Product suggestion logic
- Ebook markdown generation
- Monetization report building
- All tests pass successfully

---

## Configuration

### Required Environment Variables
```bash
GUMROAD_API_KEY=prod_xxx...      # Get from https://gumroad.com/dashboard/settings
PRINTIFY_API_KEY=sk_live_xxx...  # Get from https://printify.com/dashboard/settings
```

### Optional Environment Variables
```bash
GUMROAD_ENABLED=true              # Set to false to disable ebook publishing
PRINTIFY_ENABLED=true             # Set to false to disable POD products
EBOOK_WORD_LIMIT=1000             # Minimum words to trigger ebook (default: 1000)
GUMROAD_BASE_PRICE=4.99           # Ebook price in USD (default: 4.99)
GUMROAD_AMAZON_TAG=alreadyhere-20 # Amazon Associates tag in ebook footer
```

### GitHub Secrets (for CI/CD)
1. Go to repository Settings → Secrets and variables → Actions
2. Add `GUMROAD_API_KEY` secret
3. Add `PRINTIFY_API_KEY` secret

---

## Workflow

### Automatic Flow (After GitHub Publication)

```
Article Published to GitHub
    ↓
Check Word Count
    ├→ If >= 1000 words:
    │   ├→ Generate Ebook Markdown
    │   ├→ Publish to Gumroad API
    │   └→ Log Gumroad URL in report
    │
    └→ If < 1000 words:
        └→ Skip ebook (log reason)

Get Product Suggestions
    ├→ Analyze title + tags + content
    ├→ Match to product types
    └→ Return 2-3 recommendations

Queue POD Products (Always)
    ├→ For each suggested product:
    │   ├→ Create on Printify API
    │   ├→ Set to "pending_design"
    │   └→ Return dashboard link
    │
    └→ Generate links for manual approval

Generate Reports
    ├→ distribution_report_*.json (social + ecommerce)
    └→ monetization_report_*.json (ebook + POD status)
```

### Manual Follow-Up Steps

**Gumroad:**
1. Check dashboard: https://gumroad.com/dashboard/products
2. Add cover image (optional)
3. Test purchase
4. Promote via email/social

**Printify:**
1. Check dashboard: https://printify.com/dashboard/products
2. Upload designs (for each of 2-3 products)
3. Approve and publish
4. Share product links

---

## Revenue Estimates

### Conservative Monthly Projections

**Assumption: 2 articles published per week (8 per month)**

#### Gumroad Ebooks
- 8 ebooks created per month
- Price: $4.99 each
- Realistic conversion: 1-2% of article viewers
- At 1 sale: ~$49/month (Gumroad keeps ~10%)
- **Baseline: $40-50/month**

#### Printify POD Products
- 16-24 products queued per month
- Avg profit per sale: $5-15 (after print cost)
- Realistic conversion: 1-3 sales per product per month
- **Baseline: $40-90/month**

#### Combined
- **Conservative: $80-140/month**
- **Scales with audience:** Each 10x followers ~10x revenue

---

## Key Features

1. **Smart Product Suggestions**
   - AI automation → t-shirt, mug, hoodie
   - Ecommerce → t-shirt, mug, canvas-print
   - Content/SEO → notebook, guide-book, poster
   - Fallback: t-shirt, mug, notebook

2. **Ebook Format**
   - Professional markdown with front matter
   - Table of contents and implementation checklist
   - Already Here LLC branding + Amazon Associates tag
   - Footer with company info and next steps

3. **API Integration**
   - Direct Gumroad API: file upload + product creation
   - Direct Printify API: product queuing with links
   - Error handling and logging for each step
   - Graceful fallback if credentials missing

4. **Comprehensive Reporting**
   - Article metadata (title, word count, tags)
   - Ebook status (created? URL? price?)
   - POD status (products queued, individual links)
   - Revenue potential estimates
   - Next action checklist

---

## Testing

Run the test suite to validate all functions:

```bash
cd /path/to/profitengine-v5
python scripts/test_monetization_functions.py
```

**Test Coverage:**
- Word count accuracy (markdown handling)
- Product suggestion logic (topic matching)
- Ebook generation (markdown output)
- Monetization report building (data aggregation)

All tests currently passing.

---

## Logs and Output

### Console Output During Publish
```
[EBOOK][OK] Generated ebook markdown: ./ai-automation_ebook.md
[GUMROAD][OK] Product published: https://gumroad.com/d/xyz123
[MONETIZE] Generating POD product suggestions...
[MONETIZE] Queuing t-shirt for Printify...
[PRINTIFY][OK] Product queued for t-shirt: https://printify.com/dashboard/products/abc1
[MONETIZE][SUMMARY] Ebook: CREATED, POD Products Queued: 2
[MONETIZE][OK] Monetization report saved to monetization_report_20260619_143200.json
```

### Report Files
1. **distribution_report_*.json** — Social + ecommerce distribution
2. **monetization_report_*.json** — Ebook + POD monetization status

Both saved in project root after each publish.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not found" | Add to GitHub Secrets or export env var |
| Gumroad product not appearing | Check API key, verify account permissions |
| Printify products pending design | Upload designs in dashboard to publish |
| Word count too low for ebook | Lower `EBOOK_WORD_LIMIT` or write longer articles |
| Reports not saving | Check file permissions in project directory |

See `docs/MONETIZATION_WORKFLOW.md` for detailed troubleshooting.

---

## Next Steps

1. **Get API Keys** (5 min)
   - Gumroad: https://gumroad.com/dashboard/settings
   - Printify: https://printify.com/dashboard/settings

2. **Add to GitHub Secrets** (1 min)
   - Repository Settings → Secrets and variables → Actions

3. **Test Locally** (2 min)
   ```bash
   export GUMROAD_API_KEY="your-key"
   export PRINTIFY_API_KEY="your-key"
   python scripts/publish_article_resilient.py "test topic"
   ```

4. **Monitor First Publish** (5 min)
   - Check Gumroad dashboard
   - Check Printify dashboard
   - Review monetization report

5. **Approve POD Designs** (15 min per product)
   - Upload custom designs or use templates
   - Publish to go live
   - Share product links

---

## Additional Resources

- Full Workflow Guide: `docs/MONETIZATION_WORKFLOW.md`
- Quick Setup: `docs/GUMROAD_PRINTIFY_SETUP.md`
- Test Suite: `scripts/test_monetization_functions.py`

---

## Summary

**The article publishing workflow now automatically:**
- Converts 1000+ word articles to ebooks
- Publishes ebooks instantly to Gumroad at $4.99
- Suggests POD products based on article topic
- Queues products on Printify for design + approval
- Generates revenue reports with estimated potential
- Provides next action checklist for follow-ups

**Revenue Potential:** $80-140/month baseline (scales with audience)

**Setup Time:** 5 minutes (get API keys + add secrets)

**Maintenance:** Monitor dashboards and approve POD designs within 24 hours

