# Gumroad + Printify Setup Guide

Quick 5-minute setup to enable automatic ebook and POD product monetization.

## Step 1: Get Gumroad API Key (2 minutes)

1. Log in to https://gumroad.com/dashboard
2. Click your profile icon → **Settings**
3. Scroll to **API Access**
4. Click **Create an API token**
5. Copy the token (looks like: `prod_...")
6. Keep it safe — you'll only see it once

**Example:**
```
prod_abcdef123456789xyz
```

## Step 2: Get Printify API Key (2 minutes)

1. Log in to https://printify.com/dashboard
2. Click your profile icon → **Settings**
3. Scroll to **API Credentials**
4. Click **Generate new API token**
5. Copy the token
6. Keep it safe

**Example:**
```
sk_live_xyz123456789abcdef
```

## Step 3: Add to GitHub Secrets (1 minute)

1. Go to your repo: https://github.com/quantam101/profitenginev5
2. Click **Settings** tab
3. Left sidebar: **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Create two secrets:

| Name | Value |
|------|-------|
| `GUMROAD_API_KEY` | Your Gumroad token |
| `PRINTIFY_API_KEY` | Your Printify token |

**Screenshot:**
```
Repository Settings
├── Security
│   └── Secrets and variables
│       └── Actions
│           ├── New repository secret
│           │   ├── Name: GUMROAD_API_KEY
│           │   └── Value: prod_xxx...
│           └── New repository secret
│               ├── Name: PRINTIFY_API_KEY
│               └── Value: sk_live_xxx...
```

## Step 4: Test Locally (Optional)

```bash
cd /path/to/profitengine-v5

export GUMROAD_API_KEY="prod_xxx..."
export PRINTIFY_API_KEY="sk_live_xxx..."
export GUMROAD_ENABLED=true
export PRINTIFY_ENABLED=true

python scripts/publish_article_resilient.py "ai automation small business"
```

Check the output for:
- `[EBOOK][OK]` → Ebook markdown generated
- `[GUMROAD][OK]` → Product published to Gumroad
- `[PRINTIFY][OK]` → Product queued on Printify

## Step 5: Monitor After First Publish

1. **Check Gumroad**
   - Go to https://gumroad.com/dashboard/products
   - Your new ebook should appear
   - Add a cover image (recommended)

2. **Check Printify**
   - Go to https://printify.com/dashboard/products
   - You'll see 2-3 products in "pending design"
   - Upload designs or use templates
   - Approve and publish

3. **Review Reports**
   - Look for `monetization_report_*.json` in project root
   - Shows: ebook URL, product links, revenue estimates

## Configuration Options

All optional — defaults work for most cases:

```bash
# Gumroad
GUMROAD_ENABLED=true                  # Set to false to disable ebook publishing
GUMROAD_BASE_PRICE=4.99              # Ebook price in USD (default: 4.99)
GUMROAD_AMAZON_TAG=alreadyhere-20    # Affiliate tag in ebook footer

# Printify
PRINTIFY_ENABLED=true                # Set to false to disable POD products
EBOOK_WORD_LIMIT=1000                # Min words to trigger ebook (default: 1000)
```

## What Happens Automatically

### On Publish (When Article Meets Criteria)

1. **Word Count >= 1000 words**
   - ✅ Markdown ebook created
   - ✅ Uploaded to Gumroad at $4.99
   - ✅ Email capture enabled
   - ✅ Gumroad URL logged

2. **Always (Regardless of Word Count)**
   - ✅ POD products suggested based on topic
   - ✅ 2-3 products queued on Printify
   - ✅ Links sent to your Printify dashboard
   - ✅ Status: "pending design" (manual approval needed)

### Reports Generated

Two JSON files created in your project root:

**`distribution_report_*.json`**
- Social media distribution results
- Ecommerce platform results
- Summary stats

**`monetization_report_*.json`**
- Ebook status and Gumroad link
- POD products queued
- Revenue potential estimates
- Next action checklist

## Next Actions (After First Publish)

### Gumroad
- [ ] Go to https://gumroad.com/dashboard/products
- [ ] Add cover image to ebook
- [ ] Test purchase (incognito browser)
- [ ] Confirm email capture works
- [ ] Share link on social media

### Printify
- [ ] Go to https://printify.com/dashboard/products
- [ ] Open each product link
- [ ] Upload custom designs OR use templates
- [ ] Verify mockup looks professional
- [ ] Publish to print providers (Printful, etc.)
- [ ] Share links from article footer

### Revenue Tracking
- [ ] Monitor Gumroad dashboard for sales
- [ ] Check email opt-in list growth
- [ ] Track Printify product performance
- [ ] Review monetization reports weekly

## Troubleshooting

### "GUMROAD_API_KEY not found"
- Check GitHub Secrets are set (Settings → Secrets and variables)
- Verify exact names: `GUMROAD_API_KEY`, `PRINTIFY_API_KEY`
- Workflow must reference them with `${{ secrets.GUMROAD_API_KEY }}`

### "Product not appearing on Gumroad"
- Check API key is correct (copy directly from Gumroad)
- Verify account has product creation permission
- Check Gumroad dashboard directly
- Review error in workflow logs

### "Printify products showing 'pending_design'"
- This is normal — all new products start as pending
- Upload designs in Printify dashboard
- Approve and publish to go live
- Products can't sell until design + published

### Ebook not created (word count too low)
- Article must be >= 1000 words (default)
- Lower threshold: `export EBOOK_WORD_LIMIT=800`
- Not all articles need ebooks — long-form content only

## Revenue Example

**Typical month (2 articles published):**
- 2 ebooks created @ $4.99 each
- If 1 sale each month: ~$9 revenue
- 6 POD products queued over month
- If 2-3 sell: $15-30 revenue
- **Total realistic: $25-40/month baseline**

**Scales with audience:**
- 100 newsletter subscribers: ~$50-80/month
- 1,000 followers: ~$200-400/month
- 10,000+ audience: $1,000+/month

## Security Notes

- **Never commit API keys** to Git (use GitHub Secrets only)
- **Rotate keys annually** for security
- **Don't share secrets** across repos
- Keys are used only during publish workflow
- Test locally with export (terminal sessions are private)

## Getting Help

- **Gumroad Support:** https://support.gumroad.com
- **Printify Support:** https://support.printify.com
- **Article:** See `docs/MONETIZATION_WORKFLOW.md` for full details

---

**You're all set!** Next article publish will automatically:
1. Create and sell an ebook on Gumroad
2. Queue POD products on Printify
3. Generate revenue reports

Start with this article topic to test:
```bash
python scripts/publish_article_resilient.py "ai automation small business"
```

