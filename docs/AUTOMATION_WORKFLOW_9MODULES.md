# GitHub Actions Automation Workflow: 9-Module Architecture

## Overview

Updated `.github/workflows/automation.yml` now orchestrates **all 9 automation modules** with:
- Parallel execution (40-60% faster)
- Comprehensive error recovery
- Detailed metrics collection
- Health monitoring & alerting

## Module Groups (9 Total)

### Existing Production Modules (5)
1. **Gumroad Product Upload** - Automated product deployment
2. **Instagram Carousel Generation** - Multi-image content posts
3. **Instagram Reel Generation** - Short-form video content
4. **Instagram Stories Generation** - Daily story automation
5. **Email Sequence Setup** - Newsletter/campaign sequences

### Enhancement Modules (4)
6. **Sentiment Analysis** - Content quality & tone monitoring
7. **Compliance Check** - Regulatory & policy enforcement
8. **Attribution Analysis** - Performance tracking & ROI measurement
9. **Backup Rotation** - Data protection & disaster recovery

### Additional Modules (2)
10. **Correlation Monitor** - Signal correlation analysis
11. **Dynamic Risk Analysis** - Risk parameter optimization

## Workflow Architecture

### Triggers

**Manual Trigger (UI):**
```bash
# Via GitHub UI: Actions → Full Automation Launch (9 Modules) → Run workflow
# Inputs:
#  - parallel_execution: true/false
#  - skip_tasks: comma-separated module names to skip
#  - enable_metrics: true/false
```

**Scheduled Trigger:**
```bash
# Daily at 9 AM UTC (4 AM ET)
# Cron: 0 9 * * *
```

**Workflow Call Trigger:**
```bash
# Programmatic trigger from other workflows
# Passes parallel_execution and enable_metrics
```

## Job Structure

### Job 1: `automation-launch` (Primary Orchestration)
**Purpose:** Execute all 9 modules with parallel/sequential execution

**Steps:**
1. **Checkout** - Clone repository
2. **Setup Node.js** - Install Node runtime & dependencies
3. **Setup Python** - Install Python runtime for enhancement modules
4. **Install Dependencies** - npm + pip packages
5. **Validate Configuration** - Check all 9 module secrets & settings
6. **Execute Orchestration** - Run existing 5 modules (Node.js)
7. **Execute Enhancement Modules** - Run 6 enhancement modules (Python, parallel)
8. **Collect Performance Metrics** - JSON metrics from all modules
9. **Generate Comprehensive Report** - GitHub Actions summary
10. **Upload Logs & Metrics** - Artifact retention (30 days)
11. **Error Recovery** - Retry failed modules with backoff
12. **Notify on Failure** - GitHub issue + Slack message
13. **Commit Results** - Save metrics to repo (scheduled runs only)
14. **Slack Notification** - Status update with detailed metrics

**Timeout:** 90 minutes (parallelism reduces actual runtime to 20-40 min)

**Outputs:**
```
run-id              # Unique run identifier
success-rate        # Percentage of successful modules
tasks-passed        # Count of passed modules
tasks-failed        # Count of failed modules
total-duration      # Total execution time in seconds
```

### Job 2: `monitoring` (Health & Trend Analysis)
**Purpose:** Monitor automation health across all 9 modules

**Steps:**
1. Download logs from Job 1
2. Analyze detailed metrics
   - Last 10 runs (trend analysis)
   - Success rate statistics
   - Module-specific log sizes
3. Generate trend analysis (3-run comparison)
4. Archive metrics (90-day retention)
5. Create health alert issue (if unhealthy)

**Output:**
```
health-status       # healthy/unhealthy
```

### Job 3: `metrics-summary` (Final Consolidation)
**Purpose:** Generate final comprehensive report across all jobs

**Steps:**
1. Download all artifacts from Jobs 1 & 2
2. Consolidate metrics across 9 modules
3. Generate GitHub Actions summary with:
   - Run ID
   - Overall success rate
   - Health status
   - Module groupings

## Execution Modes

### Parallel Execution (Default)
```yaml
AUTOMATION_PARALLEL: 'true'
```

**Benefits:**
- 5 existing modules run concurrently
- 6 enhancement modules run concurrently
- Total time: ~20-30 minutes vs ~60 minutes sequential
- **Speedup:** 40-60% faster

**Module Dependencies:** None - all modules are independent

### Sequential Execution
```yaml
AUTOMATION_PARALLEL: 'false'
```

**Use Cases:**
- Debugging module interactions
- Constrained CI/CD resources
- Sensitive data operations

**Total Time:** ~60 minutes

## Configuration & Secrets

### Required GitHub Secrets (19 Total)

**Existing Modules (5):**
- `GUMROAD_API_TOKEN` - Gumroad account
- `OPENAI_API_KEY` - OpenAI API
- `IG_USER_ID` - Instagram Business Account
- `FB_PAGE_ACCESS_TOKEN` - Meta Graph API
- `REPLICATE_API_TOKEN` - Replicate API
- `ELEVENLABS_API_KEY` - ElevenLabs API
- `BEEHIIV_API_KEY` - Beehiiv account
- `BEEHIIV_PUBLICATION_ID` - Beehiiv publication

**Enhancement Modules (4):**
- `SENTIMENT_API_KEY` - Sentiment analysis service
- `COMPLIANCE_API_KEY` - Compliance check service
- (Backup: local/SSH, no key needed)
- (Attribution: internal data, no key needed)

**Additional Modules (2):**
- `CORRELATION_API_KEY` - Correlation analysis
- `DYNAMIC_RISK_API_KEY` - Dynamic risk analysis

**Infrastructure:**
- `RUNTIME_API_URL` - Backend service (e.g., `http://129.146.236.177:8000`)
- `MONGODB_URI` - MongoDB connection string
- `SLACK_WEBHOOK_URL` - (Optional) Slack notifications

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AUTOMATION_PARALLEL` | `true` | Enable parallel execution |
| `AUTOMATION_RETRY_MAX_ATTEMPTS` | `3` | Max retries per module |
| `AUTOMATION_RETRY_BACKOFF_MS` | `5000` | Backoff between retries (ms) |
| `AUTOMATION_ENABLE_METRICS` | `true` | Collect performance metrics |
| `RUNTIME_DATA_DIR` | `.runtime/automation` | Metrics storage path |
| `NODE_ENV` | `production` | Node environment |
| `NODE_OPTIONS` | `--max-old-space-size=2048` | Node memory limit |

## Metrics Collection

### Collected Metrics

**Per-Run:**
- Run ID (unique identifier)
- Timestamp
- Execution mode (parallel/sequential)
- Success rate (0-100%)
- Tasks passed / failed counts
- Total duration (seconds)

**Per-Module:**
- Module name
- Task type (gumroad, carousel, reel, stories, email, sentiment, etc.)
- Success/failure status
- Duration (milliseconds)
- Start/end timestamps
- Retry attempts
- Error messages (if failed)

**Trend Analysis:**
- Last 10 runs statistics
- Average duration
- Average success rate
- Failure patterns
- Performance trends

### Metrics Output Files

```
.runtime/automation/
├── launch-status.jsonl          # JSONL log of all runs
├── {run-id}.json                # Detailed JSON for specific run
├── metrics.json                 # Current run metrics summary
├── gumroad.log                  # Module-specific logs
├── carousel.log
├── reel.log
├── stories.log
├── email.log
├── sentiment.log
├── compliance.log
├── attribution.log
├── correlation.log
├── dynamic-risk.log
└── backup.log
```

## Error Recovery

### Retry Strategy

**Exponential Backoff:**
```
Attempt 1: Immediate
Attempt 2: backoff_ms × 2¹ = 10,000ms (10s)
Attempt 3: backoff_ms × 2² = 20,000ms (20s)
```

**Per-Module Retry Limits:**
- Gumroad: 3 attempts
- Instagram (carousel/reel/stories): 2 attempts each
- Email: 2 attempts
- Enhancement modules: 2-3 attempts (configurable)

### Recovery Actions

1. **Module Failure** → Retry with exponential backoff
2. **3+ Consecutive Failures** → GitHub issue created
3. **Health Status Unhealthy** → Alert job triggered
4. **Run Failure** → Recovery phase attempts retry
5. **Sustained Failure** → High-priority GitHub issue with details

## Notifications

### Slack Notifications
- **On:** Always (success or failure)
- **Content:**
  - Workflow status
  - Run ID
  - Success rate (%)
  - Passed/Failed counts
  - Execution mode
  - Workflow name
  - Repository & commit info

### GitHub Issue Notifications
- **Failure Comment:** Created on issue that triggered workflow
- **Health Alert:** New issue if 3+ consecutive failures
- **Details Include:**
  - All 9 modules affected
  - Run ID
  - Success rate
  - Link to Actions logs

## Summary Report

### GitHub Actions Summary Output

```markdown
## Comprehensive Automation Report

### 9-Module Automation Status
- Run ID: automation-1234567890
- Execution Mode: Parallel
- Duration: 28.5s

### Orchestration Results
- Success Rate: 88.9%
- Tasks Passed: 8
- Tasks Failed: 1

### Module Breakdown (9 Total)
**Existing Modules (5):**
- Gumroad Product Upload
- Instagram Carousel Generation
- Instagram Reel Generation
- Instagram Stories Generation
- Email Sequence Setup

**Enhancement Modules (4):**
- Sentiment Analysis
- Compliance Check
- Attribution Analysis
- Backup Rotation

**Additional Modules (2):**
- Correlation Monitor
- Dynamic Risk Analysis

### Module Health Report
- gumroad: 125 lines, 4KB
- carousel: 89 lines, 3KB
- sentiment: 156 lines, 5KB
- compliance: 0 lines (skipped)
- ...

### Trend Analysis (9 Modules)
3-Run Trend:
  Run 1: 88.9%
  Run 2: 100.0%
  Run 3: 88.9%
📈 Stable
```

## Usage Examples

### Example 1: Manual Parallel Execution with Metrics
```bash
# GitHub UI → Actions → Full Automation Launch (9 Modules) → Run workflow
# Inputs:
#   parallel_execution: true
#   enable_metrics: true
#   skip_tasks: (leave empty)
```

### Example 2: Skip Compliance Module
```bash
# GitHub UI → Run workflow
# Inputs:
#   skip_tasks: compliance
# Result: 8 modules run, compliance skipped
```

### Example 3: Sequential Execution (Debug)
```bash
# GitHub UI → Run workflow
# Inputs:
#   parallel_execution: false
# Result: Modules run one-at-a-time for debugging
```

### Example 4: Scheduled Daily Run
```bash
# Automatic execution daily at 9 AM UTC
# Parallel execution: enabled (default)
# Metrics: enabled (default)
# Results: Committed to repo via automation bot
```

## Performance Characteristics

### Typical Execution Times

**Parallel Mode (Default):**
- Existing modules (5): 15-20 min
- Enhancement modules (6): 10-15 min
- Monitoring: 2-3 min
- **Total: 20-30 minutes**

**Sequential Mode:**
- ~3-4 min per module
- 9 modules × 3.5 min avg = 31.5 min
- Monitoring: 2-3 min
- **Total: 35-45 minutes**

### Resource Usage
- **CPU:** 2-4 cores during parallel execution
- **Memory:** 2GB Node.js + 1GB Python processes
- **Disk:** ~100MB logs + metrics per run
- **Network:** 50-200 MB (API calls + artifact upload)

## Troubleshooting

### All Modules Fail
1. Check all 19 GitHub secrets are configured
2. Verify external API availability
3. Run security scan: `npm run security:scan`
4. Check runtime service: `curl $RUNTIME_API_URL/health`

### Specific Module Fails
1. Review module-specific log: `.runtime/automation/{module}.log`
2. Check module secret: `XXXX_API_KEY` is current
3. Manual test: Run module standalone
4. Create GitHub issue with error details

### Metrics Not Collected
1. Verify `AUTOMATION_ENABLE_METRICS=true`
2. Check `.runtime/automation/` directory exists
3. Review Python errors in `metrics` step logs
4. Ensure Python 3.11+ installed

### Parallel Execution Issues
1. Set `parallel_execution: false` to debug
2. Review module dependencies (should be none)
3. Check for race conditions in shared resources
4. Increase timeout: `timeout-minutes: 120`

## Best Practices

1. **Run Manually First** - Test new module with `workflow_dispatch`
2. **Enable Metrics** - Always collect metrics for trend analysis
3. **Monitor Trends** - Review weekly success rates
4. **Rotate Secrets** - Refresh API keys quarterly
5. **Document Changes** - Update this file when adding modules
6. **Test Serially** - Debug new modules with `parallel_execution: false`

## File Location

```
.github/workflows/automation.yml
```

## Recent Updates

- **2026-06-20:** Updated to 9-module architecture
  - Added 4 enhancement modules (sentiment, compliance, attribution, backup)
  - Added 2 additional modules (correlation, dynamic-risk)
  - Implemented parallel execution with error recovery
  - Added comprehensive metrics collection
  - Added health monitoring & trend analysis
  - Created 3-job pipeline (launch → monitoring → metrics-summary)
