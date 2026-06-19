# GitHub Actions Integration for Gumroad + Printify

## Workflow Configuration

### Update `.github/workflows/publish.yml`

Add Gumroad and Printify API keys to your publish workflow:

```yaml
name: Publish Article with Monetization

on:
  workflow_dispatch:
    inputs:
      topic:
        description: 'Article topic'
        required: true
        default: 'AI Automation Systems'

env:
  # Affiliate & monetization settings
  AFFILIATE_UTM_CAMPAIGN: profitengine_content
  AFFILIATE_DISCLOSURE: Some links below are affiliate or referral links.
  CONTENT_ACTION_BRIEF_ENABLED: 'true'
  
  # Gumroad settings
  GUMROAD_ENABLED: 'true'
  GUMROAD_BASE_PRICE: '4.99'
  GUMROAD_AMAZON_TAG: 'alreadyhere-20'
  EBOOK_WORD_LIMIT: '1000'
  
  # Printify settings
  PRINTIFY_ENABLED: 'true'

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Publish article with monetization
        env:
          # AI Provider credentials
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          HUGGINGFACE_API_KEY: ${{ secrets.HUGGINGFACE_API_KEY }}
          
          # Affiliate links
          AFFILIATE_LINKS: ${{ secrets.AFFILIATE_LINKS }}
          
          # Monetization credentials (NEW)
          GUMROAD_API_KEY: ${{ secrets.GUMROAD_API_KEY }}
          PRINTIFY_API_KEY: ${{ secrets.PRINTIFY_API_KEY }}
          
          # GitHub credentials for publishing
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        
        run: python scripts/publish_article_resilient.py "${{ github.event.inputs.topic }}"
      
      - name: Upload reports as artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: monetization-reports
          path: |
            distribution_report_*.json
            monetization_report_*.json
          retention-days: 30
      
      - name: Comment PR with monetization summary
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const glob = require('glob');
            
            const reportFiles = glob.sync('monetization_report_*.json');
            if (reportFiles.length === 0) return;
            
            const report = JSON.parse(fs.readFileSync(reportFiles[0], 'utf8'));
            const ebook = report.monetization?.ebook || {};
            const podCount = report.monetization?.pod_products?.queued_count || 0;
            const revenue = report.revenue_potential || {};
            
            const comment = `## Monetization Summary
            
- **Ebook Created:** ${ebook.created ? 'Yes' : 'No'} ${ebook.url ? `[View on Gumroad](${ebook.url})` : ''}
- **Price:** $${ebook.price || 'N/A'}
- **POD Products Queued:** ${podCount}
- **Revenue Potential:** $${(revenue.gumroad_ebook || 0).toFixed(2)} (1 ebook sale) + $${(revenue.pod_potential_conservative || 0).toFixed(2)} (POD)

**Next Actions:**
${(report.next_actions || []).map(a => `- [ ] ${a}`).join('\n')}`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## Secrets Configuration

### Required Secrets in GitHub

1. Go to Repository Settings → Secrets and variables → Actions
2. Add these NEW secrets:

| Secret Name | Source | Example |
|------------|--------|---------|
| `GUMROAD_API_KEY` | https://gumroad.com/dashboard/settings | `prod_xxxxx...` |
| `PRINTIFY_API_KEY` | https://printify.com/dashboard/settings | `sk_live_xxxxx...` |

### Existing Secrets (Keep as-is)
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `HUGGINGFACE_API_KEY`
- `GITHUB_TOKEN` (auto-provided)
- `AFFILIATE_LINKS` (if configured)

---

## Running the Workflow

### Via GitHub UI

1. Go to repository → Actions tab
2. Select "Publish Article with Monetization"
3. Click "Run workflow"
4. Enter article topic (e.g., "AI Automation Systems")
5. Click "Run workflow"

### Via GitHub CLI

```bash
gh workflow run publish.yml \
  -f topic="AI Automation Systems"
```

### Via cURL (Advanced)

```bash
curl -X POST \
  https://api.github.com/repos/quantam101/profitenginev5/actions/workflows/publish.yml/dispatches \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ref": "main",
    "inputs": {
      "topic": "AI Automation Systems"
    }
  }'
```

---

## Output and Artifacts

### Workflow Artifacts

After each run, download:
- `distribution_report_*.json`
- `monetization_report_*.json`

**Via GitHub UI:**
1. Click the workflow run
2. Scroll to "Artifacts"
3. Download "monetization-reports"

**Via GitHub CLI:**
```bash
gh run list --workflow=publish.yml --limit=1
gh run download <run-id> --name monetization-reports
```

### Report Contents

#### `monetization_report_*.json`
```json
{
  "article": {
    "title": "Article Title",
    "word_count": 1847,
    "tags": ["tag1", "tag2"],
    "canonical_url": "https://..."
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
          "url": "https://printify.com/dashboard/products/..."
        }
      ]
    }
  },
  "revenue_potential": {
    "gumroad_ebook": 4.99,
    "expected_sales_10_percent": 0.499,
    "expected_sales_1_percent": 0.0499,
    "pod_potential_conservative": 15.0,
    "currency": "USD"
  },
  "next_actions": [
    "Monitor Gumroad sales and email opt-ins",
    "Review Printify designs and approve POD products",
    "Add product links to related articles",
    "Create email sequence promoting the ebook",
    "Track affiliate clicks and conversions"
  ]
}
```

---

## Workflow Logs

### Check Logs in GitHub UI

1. Click the workflow run
2. Click the "publish" job
3. Expand "Publish article with monetization" step
4. Scroll through logs

### Example Log Output

```
[EBOOK][OK] Generated ebook markdown: ./ai-automation_ebook.md
[GUMROAD][OK] Product published: https://gumroad.com/d/xyz123
[MONETIZE] Generating POD product suggestions...
[MONETIZE] Queuing t-shirt for Printify...
[PRINTIFY][OK] Product queued for t-shirt: https://printify.com/dashboard/products/abc1
[MONETIZE][SUMMARY] Ebook: CREATED, POD Products Queued: 2
[MONETIZE][OK] Monetization report saved to monetization_report_20260619_143200.json
```

---

## Failure Handling

### API Key Missing

**Error:**
```
[GUMROAD][SKIP] Gumroad disabled or no API key configured
[PRINTIFY][SKIP] Printify disabled or no API key configured
```

**Fix:**
1. Check GitHub Secrets are set
2. Verify exact secret names: `GUMROAD_API_KEY`, `PRINTIFY_API_KEY`
3. Re-run workflow

### API Authentication Failed

**Error:**
```
[GUMROAD][FAIL] API error 401: Unauthorized
```

**Fix:**
1. Get new API key from respective dashboard
2. Update GitHub Secret
3. Re-run workflow

### Product Creation Failed

**Error:**
```
[PRINTIFY][FAIL] API error 400: Invalid product type
```

**Fix:**
1. Check product type is valid
2. Check Printify API documentation
3. Verify API key has product creation permission
4. Re-run workflow

---

## Monitoring and Alerts

### Slack Notification (Optional)

Add to workflow after monetization step:

```yaml
- name: Notify Slack on monetization success
  if: success()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Article monetized successfully!",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Article Monetization Report*\nGumroad: Published\nPrintify: 3 products queued"
            }
          }
        ]
      }
```

### Email Notification (Optional)

Add after artifact upload:

```yaml
- name: Send monetization report email
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: ${{ secrets.EMAIL_SERVER }}
    server_port: ${{ secrets.EMAIL_PORT }}
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: 'Article Monetization Report'
    body: 'New article published with Gumroad ebook and POD products.'
    to: 'dispatch@alreadyherellc.com'
```

---

## Scheduled Publishing

### Automatic Daily Publish

Schedule workflow to run daily:

```yaml
name: Publish Article Daily

on:
  schedule:
    # Every day at 9 AM UTC
    - cron: '0 9 * * *'

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Publish daily article
        env:
          GUMROAD_API_KEY: ${{ secrets.GUMROAD_API_KEY }}
          PRINTIFY_API_KEY: ${{ secrets.PRINTIFY_API_KEY }}
          # ... other env vars
        
        run: |
          TOPIC="Daily AI and Business Automation Update $(date +%Y-%m-%d)"
          python scripts/publish_article_resilient.py "$TOPIC"
```

---

## Environment Variables in Workflow

### Complete Reference

```yaml
env:
  # Affiliate settings
  AFFILIATE_PROMPT_LIMIT: '12'
  AFFILIATE_TOOL_LIMIT: '8'
  AFFILIATE_FEATURED_LIMIT: '3'
  AFFILIATE_UTM_CAMPAIGN: 'profitengine_content'
  
  # Revenue brief
  CONTENT_ACTION_BRIEF_ENABLED: 'true'
  
  # Gumroad
  GUMROAD_ENABLED: 'true'
  GUMROAD_BASE_PRICE: '4.99'
  GUMROAD_AMAZON_TAG: 'alreadyhere-20'
  
  # Printify
  PRINTIFY_ENABLED: 'true'
  
  # Ebook threshold
  EBOOK_WORD_LIMIT: '1000'
```

---

## Debugging

### Run workflow with debug logs

```bash
gh run rerun <run-id> --debug
```

### View full job logs locally

```bash
gh run view <run-id> --log
```

### Download artifacts locally

```bash
gh run download <run-id> --name monetization-reports
cat monetization_report_*.json | jq .
```

---

## Cost Considerations

### GitHub Actions Usage

**Free tier includes:**
- 2,000 minutes/month on Ubuntu
- Each publish workflow: ~2-5 minutes
- 400+ daily publishes allowed per month

**Estimated cost:** $0 (free tier)

### Gumroad + Printify API

**Free tier:**
- Gumroad: Free, 10% fee on sales
- Printify: Free, margins on print cost

**Estimated cost:** $0 (revenue-share model)

---

## Troubleshooting

### Workflow not running

1. Check workflow file YAML syntax (GitHub shows errors)
2. Verify cron schedule is valid (crontab.guru)
3. Check branch is `main` (default)
4. Check secrets are set properly

### Secrets not being read

1. Go to Settings → Secrets and variables → Actions
2. Verify exact secret names match workflow
3. Delete and recreate secret if stuck
4. Restart workflow

### Reports not uploading

1. Check `upload-artifact` action is not skipped
2. Verify `path:` glob patterns match actual files
3. Check workflow has write permissions
4. See GitHub Actions logs for exact error

---

## Next Steps

1. Update `.github/workflows/publish.yml` with Gumroad/Printify steps
2. Add `GUMROAD_API_KEY` and `PRINTIFY_API_KEY` secrets
3. Test manual workflow run
4. Monitor first publish in GitHub UI
5. Check reports and approve POD designs in Printify dashboard

See `docs/GUMROAD_PRINTIFY_SETUP.md` for API key setup.

