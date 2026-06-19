# GitHub Secrets Setup — Secure Finnhub API Key

Store your Finnhub API key securely in GitHub Secrets instead of environment variables.

---

## Step 1: Get Finnhub API Key (If You Don't Have It)

```
https://finnhub.io/register
→ Sign up (free)
→ Copy your API key from dashboard
```

---

## Step 2: Add to GitHub Secrets

### Option A: Using GitHub Web Interface (Easiest)

1. Go to your GitHub repository
2. Click **Settings** (top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Name: `FINNHUB_API_KEY`
6. Value: Paste your API key
7. Click **Add secret**

### Option B: Using GitHub CLI

```bash
# First, login to GitHub
gh auth login

# Then add the secret
gh secret set FINNHUB_API_KEY --body "your_api_key_here"
```

---

## Step 3: Verify Secret Is Set

In GitHub:
```
Settings → Secrets and variables → Actions
→ You should see: FINNHUB_API_KEY ✓
```

The secret is encrypted and never displayed. GitHub automatically injects it when workflows run.

---

## Step 4: Workflow Runs Automatically at 4 AM MST

The GitHub Actions workflow (`.github/workflows/paper-trading-4am.yml`) will:

1. **Run automatically every weekday at 4:00 AM MST**
2. Check out the code
3. Install Python and dependencies
4. Get `FINNHUB_API_KEY` from GitHub Secrets (encrypted)
5. Run: `python deploy_premarket_4am.py`
6. Upload results as artifacts

### View Results

```
GitHub → Actions tab
→ "Pre-Market Paper Trading - 4 AM MST"
→ Click latest run
→ See trading logs and results
```

---

## Running Manually (Without Waiting for 4 AM)

```bash
# Using GitHub CLI
gh workflow run paper-trading-4am.yml

# Or in GitHub UI:
# Actions → Pre-Market Paper Trading - 4 AM MST → Run workflow
```

---

## Workflow Schedule

**Runs automatically:**
- Every **Monday-Friday** at **4:00 AM MST** (11:00 AM UTC)
- Skips weekends (no trading)

**Change the schedule:**
Edit `.github/workflows/paper-trading-4am.yml`:
```yaml
on:
  schedule:
    - cron: '0 11 * * 1-5'  # Change this line
```

Cron format: `minute hour day month weekday`
- `0 11` = 11:00 AM UTC (4 AM MST)
- `1-5` = Monday-Friday

---

## Workflow Outputs

After each run, GitHub stores:
1. **Trading Log:** `premarket_trading_4am.log`
2. **Summary JSON:** `premarket_trading_summary.json`
3. **Artifacts** available for 30 days

### Download Results

```
GitHub → Actions
→ Click run
→ Scroll down to "Artifacts"
→ Download trading-results-XXXXX
```

---

## Security Notes

✓ **API key encrypted** in GitHub Secrets  
✓ **Never shown in logs** or output  
✓ **Only injected** during workflow execution  
✓ **Cannot be read** from GitHub UI after creation  
✓ **Safe to push** code to public repos  

---

## Troubleshooting

### Workflow Fails: "FINNHUB_API_KEY not found"
**Problem:** Secret not set in GitHub  
**Fix:**
```
Settings → Secrets and variables → Actions
→ Add FINNHUB_API_KEY
```

### Workflow Fails: "Invalid API key"
**Problem:** API key is incorrect or expired  
**Fix:**
1. Go to https://finnhub.io
2. Get new/correct API key
3. Update GitHub Secret with new key

### Workflow Doesn't Run at 4 AM
**Problem:** Scheduled workflows only run if repo has activity  
**Fix:** Manually trigger:
```bash
gh workflow run paper-trading-4am.yml
```

### No Results Uploaded
**Problem:** Workflow failed before completion  
**Fix:**
1. Check workflow logs for errors
2. Verify Finnhub API key is valid
3. Check internet/API availability

---

## Viewing Workflow Details

### In GitHub Actions UI

1. Go to **Actions** tab
2. Click **Pre-Market Paper Trading - 4 AM MST**
3. Click latest run
4. View:
   - **Logs** (all console output)
   - **Artifacts** (trading results)
   - **Duration** (how long it took)
   - **Status** (passed/failed)

### Get Live Logs

```bash
# Watch workflow in real-time
gh run watch <RUN_ID>

# Or see recent runs
gh run list --workflow=paper-trading-4am.yml
```

---

## Complete Setup Checklist

- [ ] Registered Finnhub account
- [ ] Copied Finnhub API key
- [ ] Added `FINNHUB_API_KEY` to GitHub Secrets
- [ ] Verified secret appears in Settings
- [ ] Pushed code to GitHub (workflow file included)
- [ ] Checked Actions tab for workflow
- [ ] Tested by running manually (optional)
- [ ] Ready for 4 AM execution tomorrow

---

## Daily Workflow

### Automatic (4 AM MST Monday-Friday)
```
4:00 AM → GitHub Actions starts workflow
         → Pulls code
         → Gets secret from GitHub
         → Runs paper trading
         → Uploads results
         → You can check Results anytime
```

### Manual (Anytime)
```bash
gh workflow run paper-trading-4am.yml
# Or use GitHub UI: Actions → Run workflow
```

---

## Next Steps

1. **If you haven't already:**
   - Commit code to GitHub
   - Push `.github/workflows/paper-trading-4am.yml`

2. **Add the secret:**
   - Settings → Secrets → Add FINNHUB_API_KEY

3. **Wait for 4 AM MST or test manually:**
   - GitHub Actions runs automatically
   - Or use `gh workflow run` to test now

4. **Check results:**
   - GitHub Actions tab
   - Download artifacts
   - View trading summary

---

## Support

**GitHub Actions Docs:** https://docs.github.com/actions  
**GitHub Secrets:** https://docs.github.com/en/actions/security-guides/encrypted-secrets  
**Finnhub API:** https://finnhub.io/docs/api  

---

**Setup Complete?** Your trading system will run automatically at 4 AM MST, every weekday.

API key is safe in GitHub Secrets. Never stored locally or in code.
