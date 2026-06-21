# Master Orchestrator Guide

## Overview

The Master Orchestrator (`master-orchestrator.ts`) is a comprehensive automation engine that coordinates all 9 automation modules across ProfitEngine:

### Existing Modules (3)
1. **Gumroad** - Product uploads and marketplace automation
2. **Instagram** - Social media content (Carousel, Reel, Stories)
3. **Email** - Email sequence automation

### Enhancement Modules (6)
4. **Performance Attribution** - Agent P&L decomposition (35/25/25/15% weights)
5. **Dynamic Risk Adjustment** - Volatility-scaled loss limits ($100-$300)
6. **Sentiment Analysis** - News sentiment with reliability weighting (0.6-1.0)
7. **Signal Correlation** - Rolling 4x4 correlation matrix analysis
8. **Compliance Automation** - SEC Form 4 + insider trading validation
9. **Backup & Rotation** - Weekly timestamped backups with SHA256 validation

---

## Architecture

### Core Components

1. **Logger** - Structured logging with file persistence
   - Log levels: DEBUG, INFO, WARN, ERROR
   - File persistence to `.runtime/automation/`
   - Timestamp + level formatting

2. **CircuitBreaker** - Failure prevention with automatic recovery
   - States: closed (normal), open (failing), half-open (recovery)
   - Configurable failure threshold and reset time
   - Per-task type isolation

3. **TaskExecutor** - Individual task execution with timeout handling
   - Executes local tasks (Gumroad, Instagram, Email)
   - Executes remote enhancement modules via HTTP
   - Integrates with circuit breaker

4. **MasterOrchestrator** - Main coordination engine
   - Task scheduling and execution modes
   - Dependency resolution
   - Retry logic with exponential backoff
   - Status tracking and aggregation

### Execution Modes

#### 1. **PARALLEL** Mode
- All enabled tasks run concurrently
- No dependency checking
- Maximum throughput, but could overload resources
- Best for: Independent modules with no dependencies

```
Task A ────────────┐
Task B ────────────┼─→ Done
Task C ────────────┘
```

#### 2. **SEQUENTIAL** Mode
- Tasks run one at a time in order
- Simpler error tracking but slower
- Best for: Resource-constrained environments or task ordering requirements

```
Task A ──→ Task B ──→ Task C ──→ Done
```

#### 3. **SMART** Mode (Recommended Default)
- Parallel execution with dependency awareness
- Resource pooling (configurable pool size)
- Maximizes concurrency while respecting dependencies
- Optimal for production use

```
Task A (no deps) ┐
Task B (wait A) ├─→ Task C ──→ Done
Task D (no deps)┘
```

---

## Usage

### Basic Usage

```typescript
import { orchestrateFullLaunch } from '@/lib/automation/master-orchestrator';

// Run with default configuration
const result = await orchestrateFullLaunch();

console.log(`Success Rate: ${(result.successRate * 100).toFixed(1)}%`);
console.log(`Tasks Passed: ${result.tasksPassed}/${result.tasksRun}`);
```

### Advanced Configuration

```typescript
import { 
  MasterOrchestrator, 
  ExecutionMode, 
  TaskPriority 
} from '@/lib/automation/master-orchestrator';

const orchestrator = new MasterOrchestrator({
  mode: ExecutionMode.SMART,
  poolSize: 6,
  retryMaxAttempts: 4,
  retryBackoffMs: 8000,
  circuitBreakerThreshold: 3,
  circuitBreakerResetMs: 600000, // 10 minutes
  logLevel: 'debug',
  enableMetrics: true,
  webhookUrl: 'https://your-domain.com/api/orchestration-webhook',
});

const result = await orchestrator.run();

// Access results
const status = orchestrator.getStatus();
console.log(`Failed Tasks: ${status.tasksFailed}`);

const taskResults = orchestrator.getResults();
const failures = taskResults.filter(r => r.status === 'failed');
```

---

## Configuration

### Environment Variables

```bash
# Execution mode: 'parallel' | 'sequential' | 'smart' (default: smart)
AUTOMATION_MODE=smart

# Retry policy
AUTOMATION_RETRY_MAX_ATTEMPTS=3          # Default: 3
AUTOMATION_RETRY_BACKOFF_MS=5000         # Default: 5000

# Circuit breaker (failure prevention)
AUTOMATION_CIRCUIT_BREAKER_THRESHOLD=5    # Default: 5 failures
AUTOMATION_CIRCUIT_BREAKER_RESET_MS=300000 # Default: 5 minutes

# Resource pooling (SMART mode)
AUTOMATION_POOL_SIZE=4                   # Default: 4 concurrent tasks

# Logging
AUTOMATION_LOG_LEVEL=info                # debug | info | warn | error
AUTOMATION_LOG_DIR=.runtime/automation   # Default: .runtime/automation
AUTOMATION_ENABLE_METRICS=true           # Default: true
AUTOMATION_ENABLE_CLOUD_LOGGING=false    # Default: false

# Notifications
AUTOMATION_WEBHOOK_URL=https://...       # Optional webhook for status

# Module credentials (enables/disables tasks)
GUMROAD_API_TOKEN=...                    # Gumroad module enabled
FB_PAGE_ACCESS_TOKEN=...                 # Instagram modules enabled
EMAIL_SERVICE=...                        # Email module enabled
RUNTIME_API_URL=http://localhost:8000    # Enhancement modules enabled
PROFITENGINE_WEBHOOK_TOKEN=...           # Auth for remote calls
```

### Task Configuration

Tasks are auto-configured based on environment variables, but can be overridden:

```typescript
const orchestrator = new MasterOrchestrator({
  tasks: [
    {
      id: 'gumroad-upload',
      name: 'Gumroad Product Upload',
      type: 'gumroad',
      enabled: true,
      priority: 'high',
      timeout: 300000,        // 5 minutes
      retryMaxAttempts: 3,
      retryBackoffMs: 5000,
    },
    {
      id: 'performance-attribution',
      name: 'Performance Attribution',
      type: 'attribution',
      enabled: true,
      priority: 'critical',
      timeout: 180000,        // 3 minutes
      retryMaxAttempts: 2,
      dependencies: [
        { taskId: 'sentiment-analysis', required: false, wait: false }
      ],
    },
    // ... more tasks
  ],
});
```

---

## Task Priorities

Tasks have priority levels that guide scheduling:

- **CRITICAL** - Must succeed; failures cause orchestration to warn
  - Performance Attribution
  - Dynamic Risk Adjustment
  - Compliance Automation

- **HIGH** - Important but non-fatal
  - Gumroad Upload
  - Email Sequences
  - Sentiment Analysis
  - Signal Correlation

- **NORMAL** - Nice to have, can be skipped
  - Instagram posts
  - Backup rotation

---

## Error Handling

### Retry Logic

Each task has configurable retry behavior:

1. **Exponential Backoff**: `backoff_n = base_backoff * 2^(n-1)`
   - Attempt 1: Immediate
   - Attempt 2: 5s (base)
   - Attempt 3: 10s (5s * 2)
   - Attempt 4: 20s (5s * 4)

2. **Circuit Breaker**: Prevents cascading failures
   - CLOSED: Normal operation
   - OPEN: Task type disabled after N failures
   - HALF-OPEN: Single attempt allowed, auto-recovery if success

Example:
```
Attempt 1: FAIL ──→ Wait 5s
Attempt 2: FAIL ──→ Wait 10s
Attempt 3: FAIL ──→ Circuit OPEN (stop trying)

After reset timeout:
Attempt 4: Retry allowed (HALF-OPEN)
  - SUCCESS ──→ Circuit CLOSED (normal)
  - FAIL ──→ Circuit OPEN again
```

### Failure Modes

```typescript
result.failedTasks        // Tasks that failed after all retries
result.deadLetterQueue    // Tasks removed due to circuit breaker
result.summary.criticalFailures  // Failed CRITICAL priority tasks
result.summary.warnings   // Human-readable error summaries
```

---

## Logging

### Output Locations

1. **Console** - Real-time log output (level configured by `AUTOMATION_LOG_LEVEL`)
2. **File Logs** - `{.runtime/automation}/{runId}.log`
3. **JSON Results** - `{.runtime/automation}/{runId}.json`
4. **JSONL Status** - `{.runtime/automation}/orchestration-status.jsonl`

### Log Format

```
[2026-06-20T13:52:14.123Z] [INFO] [gumroad-upload] Attempt 1/3
[2026-06-20T13:52:15.456Z] [ERROR] [gumroad-upload] Error: API timeout
[2026-06-20T13:52:20.789Z] [INFO] [gumroad-upload] Retrying in 5000ms...
```

### Status Tracking

Query orchestration history:

```typescript
import { getLatestAutomationStatus } from '@/lib/automation/master-orchestrator';

const status = await getLatestAutomationStatus();
console.log(status.lastRun);  // Most recent run
console.log(status.allRuns);  // All historical runs
```

Output:
```json
{
  "lastRun": {
    "runId": "orchestration-1718900000000",
    "timestamp": "2026-06-20T13:52:14.123Z",
    "mode": "smart",
    "success": true,
    "tasksRun": 9,
    "tasksPassed": 8,
    "tasksFailed": 1,
    "successRate": 0.8889,
    "duration": 45230
  },
  "allRuns": [...]
}
```

---

## Performance Metrics

The orchestrator tracks and reports:

- **Execution Duration** - Total time from start to finish
- **Per-Task Duration** - Individual task execution time
- **Fastest Task** - Minimum execution time
- **Slowest Task** - Maximum execution time
- **Average Duration** - Mean execution time across all tasks
- **Success Rate** - Percentage of successful tasks
- **Retry Efficiency** - Success rate on first attempt vs. all attempts

Example:
```
Duration: 45.23s

Performance Metrics:
  Fastest: Email Sequences (234ms)
  Slowest: Performance Attribution (8456ms)
  Average Task Duration: 4567ms

Results:
  Total Tasks: 9
  Passed: 8 ✓
  Failed: 1 ✗
  Success Rate: 88.9%
```

---

## Task Dependencies

Some tasks depend on others for data. Configure with `dependencies`:

```typescript
{
  id: 'dynamic-risk-adjustment',
  name: 'Dynamic Risk Adjustment',
  dependencies: [
    {
      taskId: 'performance-attribution',
      required: true,   // FAIL if dependency fails
      wait: true,       // WAIT for dependency to complete
    }
  ],
}
```

### Dependency Modes

- **required=true, wait=true** - Parent waits and fails if dependency fails
- **required=true, wait=false** - Check dependency status; fail if it failed
- **required=false, wait=false** - Soft dependency; proceed regardless
- **required=false, wait=true** - Wait for dependency but don't fail if it fails

---

## Webhook Integration

Send orchestration results to an external system:

```bash
AUTOMATION_WEBHOOK_URL=https://your-domain.com/api/orchestration
PROFITENGINE_WEBHOOK_TOKEN=your-secret-token
```

Webhook payload:
```json
{
  "runId": "orchestration-1718900000000",
  "timestamp": "2026-06-20T13:52:14.123Z",
  "success": true,
  "stats": {
    "total": 9,
    "passed": 8,
    "failed": 1,
    "successRate": 0.8889
  },
  "summary": {
    "fastestTask": {...},
    "slowestTask": {...},
    "averageTaskDuration": 4567,
    "criticalFailures": [],
    "warnings": []
  }
}
```

---

## API Integration

### Enhancement Modules (Remote HTTP)

The orchestrator calls Python backend modules via HTTP:

```
POST /api/automation/{module}
Content-Type: application/json
Authorization: Bearer {PROFITENGINE_WEBHOOK_TOKEN}

{
  "taskId": "performance-attribution",
  "metadata": {
    "regime": "daily",
    "reportType": "7-regime-breakdown"
  },
  "timestamp": "2026-06-20T13:52:14.123Z"
}
```

Expects response:
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2026-06-20T13:52:15.456Z"
}
```

---

## Best Practices

### 1. Use SMART Mode for Production
```typescript
AUTOMATION_MODE=smart
```
Balances throughput and resource usage.

### 2. Set Appropriate Timeouts
```typescript
{
  type: 'attribution',      // Complex computation
  timeout: 180000,          // 3 minutes
}
```

### 3. Monitor Circuit Breaker State
```typescript
const orchestrator = new MasterOrchestrator();
await orchestrator.run();
const results = orchestrator.getResults();
const failures = results.filter(r => r.status === 'circuit_break');
if (failures.length > 0) {
  // Alert: module is failing consistently
}
```

### 4. Archive Old Logs
```bash
# Clean up logs older than 7 days
find .runtime/automation -name "*.log" -mtime +7 -delete
```

### 5. Test Before Production
```bash
# Test with sequential mode first
AUTOMATION_MODE=sequential npm run automation:launch

# Then switch to smart mode
AUTOMATION_MODE=smart npm run automation:launch
```

### 6. Schedule Regular Runs
```bash
# Via GitHub Actions (recommended)
# .github/workflows/automation-schedule.yml

# Or via cloud job scheduler
# AWS: EventBridge, Lambda
# GCP: Cloud Scheduler, Cloud Functions
# Azure: Logic Apps, Functions
```

---

## Troubleshooting

### Issue: All tasks fail with "Circuit breaker open"
**Cause:** Too many failures; circuit breaker activated  
**Fix:** 
```bash
# Check error logs
cat .runtime/automation/orchestration-*.log | grep ERROR

# Wait for reset timeout (default 5 minutes)
# Or manually reset circuit breaker:
AUTOMATION_CIRCUIT_BREAKER_RESET_MS=0  # Immediate reset
```

### Issue: Tasks timeout
**Cause:** Timeout too short or external service slow  
**Fix:**
```bash
# Increase timeout
AUTOMATION_RETRY_BACKOFF_MS=10000  # 10s base

# Or increase per-task timeout
{
  type: 'attribution',
  timeout: 300000,  // 5 minutes instead of 3
}
```

### Issue: Memory usage grows over time
**Cause:** Logs accumulating in memory  
**Fix:**
```bash
# Enable file persistence (automatic)
# Restart orchestrator daily
# Clean old log files

find .runtime/automation -name "*.log" -mtime +30 -delete
```

### Issue: Webhook delivery failed
**Cause:** Network issue or invalid URL  
**Fix:**
```bash
# Verify webhook URL is reachable
curl -X POST https://your-domain.com/api/orchestration \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json"

# Check firewall/DNS
# Verify PROFITENGINE_WEBHOOK_TOKEN is correct
```

---

## Integration Examples

### 1. Within API Route

```typescript
// app/api/automation/launch/route.ts
import { orchestrateFullLaunch } from '@/lib/automation/master-orchestrator';

export async function POST() {
  try {
    const result = await orchestrateFullLaunch({
      mode: 'smart',
      webhookUrl: process.env.AUTOMATION_WEBHOOK_URL,
    });

    return Response.json({
      success: result.tasksFailed === 0,
      runId: result.runId,
      stats: {
        total: result.tasksRun,
        passed: result.tasksPassed,
        failed: result.tasksFailed,
      },
    });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}
```

### 2. Scheduled via GitHub Actions

```yaml
# .github/workflows/automation-schedule.yml
name: Daily Automation
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm install
      - run: npm run automation:launch
        env:
          AUTOMATION_MODE: smart
          PROFITENGINE_WEBHOOK_TOKEN: ${{ secrets.WEBHOOK_TOKEN }}
```

### 3. Manual CLI Invocation

```bash
# Run with default config
npm run automation:launch

# Run with custom mode
AUTOMATION_MODE=sequential npm run automation:launch

# Run with debug logging
AUTOMATION_LOG_LEVEL=debug npm run automation:launch

# Run and output to file
npm run automation:launch 2>&1 | tee automation-run-$(date +%s).log
```

---

## File Structure

```
app/lib/automation/
├── master-orchestrator.ts         # Main orchestrator (37 KB)
├── orchestrate.ts                 # Legacy orchestrator (kept for compatibility)
├── gumroad.ts                     # Gumroad module
├── instagram-carousel.ts          # Carousel module
├── instagram-reel.ts              # Reel module
├── instagram-stories.ts           # Stories module
├── email-setup.ts                 # Email module
└── MASTER_ORCHESTRATOR_GUIDE.md   # This file

.runtime/automation/
├── orchestration-TIMESTAMP.json   # Detailed results
├── orchestration-TIMESTAMP.log    # Formatted logs
└── orchestration-status.jsonl     # JSONL history
```

---

## Version History

- **v1.0.0** (2026-06-20)
  - Initial release
  - 3 existing modules (Gumroad, Instagram, Email)
  - 6 enhancement modules (Attribution, Risk, Sentiment, Correlation, Compliance, Backup)
  - SMART execution mode with dependency resolution
  - Circuit breaker pattern for failure prevention
  - Comprehensive logging and status tracking

---

## Support

For issues or questions:
1. Check logs: `.runtime/automation/orchestration-*.log`
2. Review configuration: `AUTOMATION_MODE`, `AUTOMATION_RETRY_*`
3. Test in isolation: Run single tasks with `sequental` mode
4. Escalate: Check GitHub issues or contact engineering team
