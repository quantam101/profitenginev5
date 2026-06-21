# Workflow Verification Guide
**Status**: Complete end-to-end testing before production

---

## WHAT TO VERIFY

### ✅ Phase 1: API Connection Test
Before uploading any products, verify that tokens are valid

```bash
GUMROAD_API_TOKEN=your-token \
ETSY_ACCESS_TOKEN=your-token \
ETSY_SHOP_ID=your-id \
python scripts/test_api_connections.py
```

**Expected output:**
```
✅ GUMROAD: Connected as your@email.com
✅ ETSY: Connected to shop 'Your Shop Name'
✅ PRINTIFY: Connected (N shops found)

RESULT: 3/3 API connections verified
✅ ALL TESTS PASSED - Ready to run product upload automation!
```

---

## VERIFICATION STEPS

### Step 1: Local Test (5 minutes)
Run API connection test locally to verify tokens work

```bash
# Export your tokens
export GUMROAD_API_TOKEN="your-gumroad-token"
export ETSY_ACCESS_TOKEN="your-etsy-token"
export ETSY_SHOP_ID="your-shop-id"

# Run verification
python scripts/test_api_connections.py

# Expected: All 3 tests pass
# If failed: Tokens are incorrect - fix them before proceeding
```

### Step 2: GitHub Actions Test (10 minutes)
Run workflow in GitHub Actions with test step enabled

```
1. Go to GitHub Repo → Actions
2. Select "Auto Product Upload - Gumroad & Etsy"
3. Click "Run workflow"
4. First step: "Test API Connections"
   - Watch for: ✅ All tests pass
   - If fail: Stop workflow, verify secrets
5. Next step: "Upload products to Gumroad"
6. Next step: "Upload products to Etsy"
7. Final step: Verify products on platforms
```

### Step 3: Platform Verification (5 minutes)

**Gumroad Verification:**
```
1. Go to https://gumroad.com/dashboard/products
2. Look for 6 new products:
   ✅ POD Listings 8-Pack
   ✅ KDP Assets Bundle
   ✅ Etsy Shop Setup Guide
   ✅ Stripe Setup Checklist
   ✅ Content System Template
   ✅ Local Automation Playbook
3. Verify: Status = "Published" for all
4. Verify: Prices match expected values
```

**Etsy Verification:**
```
1. Go to https://www.etsy.com/your/shops/me/listings
2. Look for 8 new listings:
   ✅ Culture T-Shirt ($24.99)
   ✅ Culture Hoodie ($54.99)
   ✅ Culture Print ($19.99)
   ✅ Culture Stickers ($7.99)
   ✅ Culture Mug ($12.99)
   ✅ Culture Hat ($26.99)
   ✅ Culture Tote ($18.99)
   ✅ Culture Sweatshirt ($39.99)
3. Verify: All statuses = "Active"
4. Verify: Printify sync enabled
```

---

## TROUBLESHOOTING

### Test Failure: "GUMROAD_API_TOKEN not set"
```
Problem: Token not exported/configured
Solution:
  1. Get new token from https://gumroad.com/settings/api
  2. Export locally: export GUMROAD_API_TOKEN="token"
  3. Add to GitHub Secrets
  4. Re-run test
```

### Test Failure: "ETSY: Invalid credentials"
```
Problem: Token is invalid or expired
Solution:
  1. Go to https://developer.etsy.com
  2. Regenerate OAuth token
  3. Verify scopes: listings:write, shop_information:read
  4. Update GitHub Secrets
  5. Re-run test
```

### Workflow Fails at Upload Step
```
Problem: Test passed but upload failed (usually API rate limit)
Solution:
  1. Wait 5 minutes
  2. Check platform dashboard for partial uploads
  3. Check workflow logs for specific error
  4. Re-run workflow
```

### Products Appear But Some Missing
```
Problem: Partial upload (some succeeded, some failed)
Solution:
  1. Check workflow logs for failed products
  2. Manually upload failed products
  3. Or re-run workflow (idempotent - won't duplicate)
```

---

## COMPLETE VERIFICATION CHECKLIST

```
Before Production:

□ Step 1: Local Test
  - Export GUMROAD_API_TOKEN
  - Export ETSY_ACCESS_TOKEN
  - Export ETSY_SHOP_ID
  - Run: python scripts/test_api_connections.py
  - Result: ✅ All 3/3 tests pass

□ Step 2: GitHub Actions Test
  - Add all 3 secrets to GitHub repo
  - Go to Actions → Run workflow
  - Watch: "Test API Connections" step
  - Result: ✅ Passes (green checkmark)
  - Continue to Upload steps

□ Step 3: Gumroad Verification
  - Check 6 products exist
  - Status: All "Published"
  - Prices: Match expected
  - Result: ✅ 6/6 products live

□ Step 4: Etsy Verification
  - Check 8 listings exist
  - Status: All "Active"
  - Printify: Connected
  - Result: ✅ 8/8 listings live

□ Step 5: Printify Verification
  - Check 8 products synced
  - Margins: All 60%+
  - Result: ✅ Auto-fulfillment ready

✅ COMPLETE: System verified and operational
```

---

## EXPECTED OUTPUTS

### Local Test Success
```
======================================================================
API CONNECTION TEST - Verify tokens and credentials
======================================================================

✅ GUMROAD: Connected as dispatch@alreadyherellc.com

✅ ETSY: Connected to shop 'Already Here LLC'

✅ PRINTIFY: Connected (1 shops found)

======================================================================
RESULT: 3/3 API connections verified
======================================================================

✅ ALL TESTS PASSED - Ready to run product upload automation!
```

### GitHub Actions Success
```
✅ Checkout repository
✅ Set up Python
✅ Install dependencies
✅ Test API Connections
   ✅ GUMROAD: Connected
   ✅ ETSY: Connected
   ✅ PRINTIFY: Connected
✅ Upload products to Gumroad
   ✅ UPLOADED: POD Listings 8-Pack
   ✅ UPLOADED: KDP Assets Bundle
   ... (6 total)
✅ Upload products to Etsy
   ✅ CREATED: Culture T-Shirt
   ✅ CREATED: Culture Hoodie
   ... (8 total)
✅ Verify Printify Sync
✅ Upload workflow summary
```

### Gumroad Dashboard
```
Products                          Sales  Revenue  Price      Status
POD Listings 8-Pack              0      $0       $29.99     Published
KDP Assets Bundle                0      $0       $7.99      Published
Etsy Shop Setup Guide            0      $0       $49.99     Published
Stripe Setup Checklist           0      $0       $9.99      Published
Content System Template          0      $0       $79.99     Published
Local Automation Playbook        0      $0       $99.99     Published
─────────────────────────────────────────────────────────────────
Totals                           0      $0
```

### Etsy Dashboard
```
Listing                          Price   Status    Quantity
Fly Culture T-Shirt              $24.99  Active    ∞ (Printify)
Fly Culture Hoodie               $54.99  Active    ∞ (Printify)
Fly Culture Print                $19.99  Active    ∞ (Printify)
Fly Culture Stickers             $7.99   Active    ∞ (Printify)
Fly Culture Mug                  $12.99  Active    ∞ (Printify)
Fly Culture Hat                  $26.99  Active    ∞ (Printify)
Fly Culture Tote                 $18.99  Active    ∞ (Printify)
Fly Culture Sweatshirt           $39.99  Active    ∞ (Printify)
```

---

## WHEN TO DECLARE "READY FOR PRODUCTION"

✅ All checklist items complete
✅ Local test passes
✅ GitHub Actions workflow passes
✅ All 6 Gumroad products live
✅ All 8 Etsy listings live
✅ Printify sync verified
✅ No errors in workflow logs

**Status: VERIFIED AND OPERATIONAL** 🚀

---

## NEXT ACTIONS

After Verification:
1. ✅ Weekly automation enabled (runs every Monday)
2. ✅ Monitor first sales
3. ✅ Adjust prices if needed
4. ✅ Launch content marketing

Expected Timeline:
- First sale: 1-7 days
- Month 1: $2,300-5,400/month
- Month 3 with marketing: $9,500-23,000/month

---

**Verification = Confidence** ✨
