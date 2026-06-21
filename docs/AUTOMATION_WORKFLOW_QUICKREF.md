# 9-Module Automation Workflow — Quick Reference

## Module Status Overview

| # | Module Name | Type | Language | Config | Status |
|---|---|---|---|---|---|
| 1 | Gumroad Product Upload | Existing | Node.js | `GUMROAD_API_TOKEN` | Prod |
| 2 | Instagram Carousel | Existing | Node.js | `FB_PAGE_ACCESS_TOKEN` | Prod |
| 3 | Instagram Reel | Existing | Node.js | `FB_PAGE_ACCESS_TOKEN` | Prod |
| 4 | Instagram Stories | Existing | Node.js | `FB_PAGE_ACCESS_TOKEN` | Prod |
| 5 | Email Sequences | Existing | Node.js | `BEEHIIV_API_KEY` | Prod |
| 6 | Sentiment Analysis | Enhancement | Python | `SENTIMENT_API_KEY` | New |
| 7 | Compliance Check | Enhancement | Python | `COMPLIANCE_API_KEY` | New |
| 8 | Attribution Analysis | Enhancement | Python | (internal) | New |
| 9 | Backup Rotation | Enhancement | Bash/Python | (SSH) | New |
| 10 | Correlation Monitor | Additional | Python | `CORRELATION_API_KEY` | New |
| 11 | Dynamic Risk Analysis | Additional | Python | `DYNAMIC_RISK_API_KEY` | New |

## Quick Start

### Trigger Manual Run (UI)
```
GitHub → Actions → Full Automation Launch (9 Modules) → Run workflow
```

### Trigger with Options
```
Run workflow
├── parallel_execution: true (default) / false
├── enable_metrics: true (default) / false
└── skip_tasks: (comma-separated module names)
```

### Example: Skip Compliance
```
skip_tasks: compliance
```

### Example: Sequential Execution (Debug)
```
parallel_execution: false
enable_metrics: true
```

## File Locations

```
Workflow:           .github/workflows/automation.yml
Documentation:      docs/AUTOMATION_WORKFLOW_9MODULES.md
Metrics Output:     .runtime/automation/
├── launch-status.jsonl       (historical log)
├── metrics.json              (current run)
├── {run-id}.json             (detailed results)
└── {module}.log              (per-module logs)
```

## Execution Times

| Mode | Duration | Speedup |
|------|----------|---------|
| Parallel (default) | 20-30 min | +40-60% |
| Sequential | 35-45 min | baseline |

## Module Breakdown

### Existing (5) — Production
- Run via Node.js orchestrator
- Retry: 2-3 attempts per module
- Config: Environment variables + secrets

### Enhancement (4) — New
- Run via Python scripts
- Execute in parallel
- Sentiment, Compliance, Attribution, Backup

### Additional (2) — New
- Run via Python scripts
- Correlation & Dynamic Risk analysis
- Enterprise risk monitoring

## Secrets Checklist

### Required for All 9 Modules (19 total)
```
Existing (8):
  [ ] GUMROAD_API_TOKEN
  [ ] OPENAI_API_KEY
  [ ] IG_USER_ID
  [ ] FB_PAGE_ACCESS_TOKEN
  [ ] REPLICATE_API_TOKEN
  [ ] ELEVENLABS_API_KEY
  [ ] BEEHIIV_API_KEY
  [ ] BEEHIIV_PUBLICATION_ID

Enhancement (2):
  [ ] SENTIMENT_API_KEY
  [ ] COMPLIANCE_API_KEY

Additional (2):
  [ ] CORRELATION_API_KEY
  [ ] DYNAMIC_RISK_API_KEY

Infrastructure (3):
  [ ] RUNTIME_API_URL
  [ ] MONGODB_URI
  [ ] SLACK_WEBHOOK_URL (optional)
```

**Setup:**
1. Repo Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add all 19 secrets
4. Test with `workflow_dispatch`

## Jobs Overview

| Job | Duration | Purpose | Triggers |
|-----|----------|---------|----------|
| `automation-launch` | 20-30 min | Execute all 9 modules | primary |
| `monitoring` | 2-3 min | Health & trend analysis | after launch |
| `metrics-summary` | 1 min | Final consolidated report | after monitoring |

## Key Features

### Parallel Execution
```yaml
AUTOMATION_PARALLEL: 'true'
```
- 5 existing modules run concurrently
- 6 enhancement modules run concurrently
- Independent, no module dependencies
- 40-60% faster than sequential

### Error Recovery
```yaml
AUTOMATION_RETRY_MAX_ATTEMPTS: '3'
AUTOMATION_RETRY_BACKOFF_MS: '5000'
```
- Exponential backoff on retry
- Per-module retry limits
- Recovery logging & notifications

### Metrics Collection
```yaml
AUTOMATION_ENABLE_METRICS: 'true'
```
- Per-run JSON snapshots
- Historical JSONL log (90-day retention)
- Trend analysis (last 3/10 runs)
- Module-specific logs

### Health Monitoring
- Track success rate over 10 runs
- Auto-create GitHub issue if unhealthy (3+ failures)
- Slack notifications with full status
- Trend indicators (📈 improving, 📉 declining, ➡️ stable)

## Metrics Output Example

```json
{
  "timestamp": "2026-06-20T15:30:00Z",
  "run_id": "automation-1718903400000",
  "modules": {
    "existing": ["gumroad", "carousel", "reel", "stories", "email"],
    "enhancement": ["sentiment", "compliance", "attribution", "correlation", "dynamic-risk", "backup"]
  },
  "execution_mode": "true",
  "success_rate": 0.889,
  "tasks_passed": 8,
  "tasks_failed": 1,
  "duration_seconds": 28.5,
  "logs": {
    "gumroad": {"size_bytes": 4096, "lines": 125},
    "sentiment": {"size_bytes": 5120, "lines": 156}
  }
}
```

## Troubleshooting

### All Modules Fail
```bash
# Check all secrets
gh secret list

# Check backend
curl $RUNTIME_API_URL/health

# Run security scan
npm run security:scan
```

### Single Module Fails
```bash
# Check module log
cat .runtime/automation/{module}.log

# Verify secret
gh secret list | grep {MODULE}

# Run manually
npm run test:{module}
```

### Metrics Not Collected
```bash
# Verify flag
echo $AUTOMATION_ENABLE_METRICS

# Check directory
ls -la .runtime/automation/

# Check Python
python3 -c "import json; print('OK')"
```

### High Failure Rate (>30%)
1. Run with `parallel_execution: false` to debug
2. Check external API status
3. Review module dependencies
4. Check rate limiting

## Commands

### Manual Trigger
```bash
gh workflow run automation.yml \
  -f parallel_execution=true \
  -f enable_metrics=true
```

### Check Status
```bash
gh run list --workflow automation.yml --limit 10
```

### View Latest Logs
```bash
gh run view --log $(gh run list --workflow automation.yml --limit 1 -q '.[0].databaseId')
```

### Download Artifacts
```bash
gh run download {run-id} -n automation-logs-metrics
```

## Success Criteria

✓ All 9 modules listed in workflow outputs
✓ Success rate ≥ 80% (industry standard for CI/CD)
✓ Parallel execution < 35 minutes (vs 45+ sequential)
✓ Metrics JSON contains all 9 modules
✓ Health status = "healthy" after run
✓ No "unhealthy" GitHub issue created

## Scheduling

**Current Schedule:**
```
Cron: 0 9 * * *
Timezone: UTC
Local Time: 4 AM ET, 1 AM PT
```

**To Change:**
```yaml
schedule:
  - cron: '30 14 * * *'  # 2:30 PM UTC = 9:30 AM ET
```

## Recent Updates (2026-06-20)

- Added 9-module support (was 5)
- Implemented parallel execution engine
- Added Python enhancement modules (6)
- Implemented comprehensive metrics collection
- Added health monitoring & trend analysis
- Created 3-job pipeline architecture
- Added error recovery with exponential backoff
- Increased timeout: 60 → 90 minutes
- Updated documentation & quick reference

## Support

**Issues:** GitHub Issues → label:automation
**Logs:** Actions tab → workflow run
**Metrics:** Download artifacts from Actions run
**Documentation:** docs/AUTOMATION_WORKFLOW_9MODULES.md
