# GITHUB SECRETS WIRING CHECKLIST

**Goal**: Wire up all GitHub/Vercel secrets to the automation system

---

## ✅ STEP 1: Verify Secrets in GitHub

Go to: https://github.com/quantam101/profitenginev5/settings/secrets/actions

**Required secrets (exact names):**

```
GUMROAD_API_TOKEN
INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ACCOUNT_ID
OPENAI_API_KEY
REPLICATE_API_TOKEN
ELEVEN_LABS_API_KEY
KLAVIYO_API_KEY
SLACK_WEBHOOK_URL (optional)
```

**Check each one exists:**
- [ ] GUMROAD_API_TOKEN
- [ ] INSTAGRAM_ACCESS_TOKEN
- [ ] INSTAGRAM_BUSINESS_ACCOUNT_ID
- [ ] OPENAI_API_KEY
- [ ] REPLICATE_API_TOKEN
- [ ] ELEVEN_LABS_API_KEY
- [ ] KLAVIYO_API_KEY
- [ ] SLACK_WEBHOOK_URL (optional)

---

## ✅ STEP 2: Verify GitHub Actions Workflow

Go to: https://github.com/quantam101/profitenginev5/actions

**Check:**
- [ ] "Full Automation Launch" workflow exists
- [ ] Workflow is enabled (toggle on)
- [ ] Can manually trigger via "Run workflow" button

**To trigger manually:**
1. Click "Actions" tab
2. Select "Full Automation Launch"
3. Click "Run workflow" button
4. Select options:
   - parallel_execution: true
   - skip_tasks: (leave empty)
5. Click "Run workflow"

---

## ✅ STEP 3: Check Vercel Environment Variables

Go to: https://vercel.com/quantam101/profitenginev5/settings/environment-variables

**Vercel needs same secrets (copy from GitHub):**
- [ ] GUMROAD_API_TOKEN
- [ ] INSTAGRAM_ACCESS_TOKEN
- [ ] INSTAGRAM_BUSINESS_ACCOUNT_ID
- [ ] OPENAI_API_KEY
- [ ] REPLICATE_API_TOKEN
- [ ] ELEVEN_LABS_API_KEY
- [ ] KLAVIYO_API_KEY

**For each environment:**
- [ ] Production
- [ ] Preview
- [ ] Development

---

## ✅ STEP 4: Wire Up Automation Code

The automation code expects these environment variables. Check they're being read:

**File: `app/lib/automation/orchestrate.ts`**

Should have:
```typescript
const gumroadToken = process.env.GUMROAD_API_TOKEN;
const instagramToken = process.env.INSTAGRAM_ACCESS_TOKEN;
const instagramId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;
const openaiKey = process.env.OPENAI_API_KEY;
const replicateToken = process.env.REPLICATE_API_TOKEN;
const elevenLabsKey = process.env.ELEVEN_LABS_API_KEY;
const klaviyoKey = process.env.KLAVIYO_API_KEY;
```

---

## ✅ STEP 5: Trigger Automation

**Option A: GitHub Actions (Automated Daily)**
```bash
# Already configured to run at 9 AM UTC daily
# View runs at: https://github.com/quantam101/profitenginev5/actions

# To trigger manually via GitHub UI:
# 1. Go to Actions tab
# 2. Select "Full Automation Launch"
# 3. Click "Run workflow"
```

**Option B: API Trigger (Immediate)**
```bash
curl -X POST https://profitengine-tau.vercel.app/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel": true,
    "skipTasks": []
  }'
```

**Option C: Local Trigger (Testing)**
```bash
npm run dev
curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

---

## 🔍 VERIFICATION SCRIPT

Run this to verify everything is wired:

```bash
#!/bin/bash

echo "🔍 AUTOMATION VERIFICATION"
echo ""

# Check GitHub Actions workflow file
if [ -f .github/workflows/automation.yml ]; then
  echo "✅ GitHub Actions workflow exists"
else
  echo "❌ GitHub Actions workflow NOT FOUND"
fi

# Check automation code exists
if [ -f app/lib/automation/orchestrate.ts ]; then
  echo "✅ Automation orchestration module exists"
else
  echo "❌ Automation module NOT FOUND"
fi

# Check API endpoint exists
if [ -f app/api/automation/launch/route.ts ]; then
  echo "✅ Automation API endpoint exists"
else
  echo "❌ API endpoint NOT FOUND"
fi

# Check product files exist
if [ -f GUMROAD_PRODUCT_1_SOCIAL_MEDIA_ENGINE.md ]; then
  echo "✅ Gumroad products exist"
else
  echo "❌ Gumroad products NOT FOUND"
fi

# Check carousel designs exist
if [ -f INSTAGRAM_CAROUSEL_DESIGNS.md ]; then
  echo "✅ Instagram carousel designs exist"
else
  echo "❌ Carousel designs NOT FOUND"
fi

# Check email sequences exist
if [ -f PREMIUM_ONBOARDING_SEQUENCE.md ]; then
  echo "✅ Email sequences exist"
else
  echo "❌ Email sequences NOT FOUND"
fi

# Check environment file
if [ -f .env.automation ]; then
  echo "✅ Environment template exists"
else
  echo "❌ Environment template NOT FOUND"
fi

echo ""
echo "To test automation:"
echo "  npm run dev"
echo "  curl -X POST http://localhost:3000/api/automation/launch"
```

---

## 🎯 WHAT'S MISSING (Checklist)

Based on what you said secrets are already in GitHub/Vercel, here's what we need to verify:

### **GitHub Setup**
- [ ] All 7-8 secrets added to GitHub Actions secrets
- [ ] GitHub Actions workflow "Full Automation Launch" enabled
- [ ] Workflow has correct secret names (check automation.yml for env variable names)

### **Vercel Setup**
- [ ] All 7-8 secrets added to Vercel environment variables
- [ ] Applied to Production environment
- [ ] Applied to Preview environment

### **Code Setup**
- [ ] `app/lib/automation/orchestrate.ts` exists
- [ ] `app/api/automation/launch/route.ts` exists
- [ ] Automation code reads secrets correctly

### **Content Setup**
- [ ] GUMROAD_PRODUCT_*.md files exist (5 products)
- [ ] INSTAGRAM_CAROUSEL_DESIGNS.md exists
- [ ] PREMIUM_ONBOARDING_SEQUENCE.md exists
- [ ] CONTENT_CALENDAR_MONTHLY.md exists

### **Workflow Setup**
- [ ] .github/workflows/automation.yml exists
- [ ] Workflow scheduled for daily at 9 AM UTC
- [ ] Workflow can be manually triggered

---

## 🚀 TO GET FULLY AUTOMATED RIGHT NOW

1. **Run GitHub verification:**
   ```bash
   # Verify workflow is enabled
   gh workflow list
   
   # Enable if disabled
   gh workflow enable automation.yml
   ```

2. **Trigger automation:**
   ```bash
   # Option A: Via GitHub Actions (immediate)
   gh workflow run automation.yml
   
   # Option B: Via API (immediate)
   curl -X POST https://profitengine-tau.vercel.app/api/automation/launch \
     -H "Content-Type: application/json" \
     -d '{"parallel": true}'
   
   # Option C: Wait for scheduled (9 AM UTC tomorrow)
   # (Already configured)
   ```

3. **Monitor:**
   ```bash
   # Watch GitHub Actions run
   gh run list
   gh run watch <run-id>
   
   # Or open dashboard
   open automation-dashboard.html
   ```

---

## ✅ FINAL CHECKLIST

Before you say "go live":

- [ ] All secrets in GitHub Actions (Settings → Secrets)
- [ ] All secrets in Vercel (Settings → Environment Variables)
- [ ] GitHub Actions workflow "Full Automation Launch" is **enabled**
- [ ] Automation code files exist (orchestrate.ts, launch/route.ts)
- [ ] Product content files exist (5 Gumroad products)
- [ ] Instagram designs exist
- [ ] Email sequences exist
- [ ] Can trigger workflow manually via GitHub UI
- [ ] Can trigger API endpoint from Vercel

---

**If all boxes checked**: Everything is wired. Run `gh workflow run automation.yml` to start.

**If any box unchecked**: Tell me which ones, and I'll wire them up.
