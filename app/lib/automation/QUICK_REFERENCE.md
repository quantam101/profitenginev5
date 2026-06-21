# Master Orchestrator - Quick Reference

## Simplest Usage

```typescript
import { orchestrateFullLaunch } from '@/lib/automation/master-orchestrator';

await orchestrateFullLaunch();
```

## Common Configurations

### SMART Mode (Recommended Production)
```typescript
const result = await orchestrateFullLaunch({
  mode: 'smart',
  poolSize: 4,
});
```

### SEQUENTIAL Mode (Debugging)
```typescript
const result = await orchestrateFullLaunch({
  mode: 'sequential',
  logLevel: 'debug',
});
```

### PARALLEL Mode (Max Speed)
```typescript
const result = await orchestrateFullLaunch({
  mode: 'parallel',
});
```

## Environment Variables

```bash
# Essential
export AUTOMATION_MODE=smart
export PROFITENGINE_WEBHOOK_TOKEN=your-token

# Module credentials (enables/disables modules)
export GUMROAD_API_TOKEN=...
export FB_PAGE_ACCESS_TOKEN=...
export EMAIL_SERVICE=...
export RUNTIME_API_URL=http://localhost:8000

# Optional tuning
export AUTOMATION_POOL_SIZE=4
export AUTOMATION_RETRY_MAX_ATTEMPTS=3
export AUTOMATION_LOG_LEVEL=info
```

## Module Coordinates

| # | Module | Type | Enabled By | Timeout |
|---|--------|------|-----------|---------|
| 1 | Gumroad | Local | GUMROAD_API_TOKEN | 5m |
| 2 | Instagram (Carousel) | Local | FB_PAGE_ACCESS_TOKEN | 4m |
| 3 | Instagram (Reel) | Local | FB_PAGE_ACCESS_TOKEN | 5m |
| 4 | Instagram (Stories) | Local | FB_PAGE_ACCESS_TOKEN | 3m |
| 5 | Email | Local | EMAIL_SERVICE | 2m |
| 6 | Attribution | Remote | RUNTIME_API_URL | 3m |
| 7 | Risk | Remote | RUNTIME_API_URL | 2m |
| 8 | Sentiment | Remote | RUNTIME_API_URL | 2.5m |
| 9 | Correlation | Remote | RUNTIME_API_URL | 2m |
| 10 | Compliance | Remote | RUNTIME_API_URL | 1.5m |
| 11 | Backup | Remote | RUNTIME_API_URL | 10m |

## Execution Modes at a Glance

```
PARALLEL        SEQUENTIAL      SMART (Recommended)
────────────    ──────────      ──────────
A ────────┐     A ──→ B ──→     A ────┐
B ────────┼─→   C ──→ D ──→     C ────┼─→
C ────────┤                      B ────┘
D ────────┘
                                 (parallel with deps)
```

## Task Priorities

```
CRITICAL (Must succeed)          HIGH (Important)           NORMAL (Optional)
─────────────────────            ──────────────             ─────────────────
• Attribution                    • Gumroad                  • Instagram posts
• Dynamic Risk                   • Email                    • Backup
• Compliance                     • Sentiment
                                 • Correlation
```

## Common Results

```typescript
result.runId                     // "orchestration-1718900000000"
result.tasksRun                  // 9
result.tasksPassed               // 8
result.tasksFailed               // 1
result.successRate               // 0.8889 (88.89%)
result.totalDuration             // 45230 (ms)

result.summary.criticalFailures  // Array of failed CRITICAL tasks
result.summary.warnings          // Human-readable warnings
result.failedTasks               // Array of failed TaskResults
result.deadLetterQueue           // Tasks removed by circuit breaker
```

## Logging Output Locations

```
Console              (real-time, filtered by AUTOMATION_LOG_LEVEL)
.runtime/automation/orchestration-TIMESTAMP.log  (formatted logs)
.runtime/automation/orchestration-TIMESTAMP.json (full results)
.runtime/automation/orchestration-status.jsonl   (history)
```

## Query Status

```typescript
import { getLatestAutomationStatus } from '@/lib/automation/master-orchestrator';

const status = await getLatestAutomationStatus();
status.lastRun    // Most recent run
status.allRuns    // All historical runs
```

## Error Handling

| Issue | Fix |
|-------|-----|
| Circuit breaker open | Wait for reset timeout (~5 min) |
| Tasks timeout | Increase timeout value |
| Memory grows | Archive old logs in .runtime/automation/ |
| Webhook fails | Verify URL and PROFITENGINE_WEBHOOK_TOKEN |
| Module disabled | Verify required credential env var is set |

## Retry Logic

```
Attempt 1: Immediate
Attempt 2: Wait 5s      (base backoff)
Attempt 3: Wait 10s     (base × 2)
Attempt 4: Wait 20s     (base × 4)
Attempt 5: FAILED

(Exponential backoff: 5s × 2^(n-1))
```

## CI/CD Integration

```yaml
# .github/workflows/automation.yml
name: Automation
on:
  schedule:
    - cron: '0 2 * * *'  # Daily 2 AM UTC

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

## Performance Targets

| Mode | Speed | Use Case |
|------|-------|----------|
| SEQUENTIAL | ~120s | Debugging, small pools |
| SMART | ~45s | Production (recommended) |
| PARALLEL | ~25s | Max speed, no dependencies |

## Run Examples

```bash
# Quick start
npx ts-node app/lib/automation/master-orchestrator-examples.ts 1

# Sequential debugging
npx ts-node app/lib/automation/master-orchestrator-examples.ts 2

# Parallel mode
npx ts-node app/lib/automation/master-orchestrator-examples.ts 3

# Performance analysis
npx ts-node app/lib/automation/master-orchestrator-examples.ts 13

# Production workflow
npx ts-node app/lib/automation/master-orchestrator-examples.ts 16

# All 16 examples available
```

## Advanced: Custom Configuration

```typescript
import { MasterOrchestrator, ExecutionMode, TaskPriority } from '@/lib/automation/master-orchestrator';

const orchestrator = new MasterOrchestrator({
  mode: ExecutionMode.SMART,
  poolSize: 6,
  retryMaxAttempts: 4,
  retryBackoffMs: 8000,
  circuitBreakerThreshold: 3,
  circuitBreakerResetMs: 600000,
  logLevel: 'debug',
  enableMetrics: true,
  webhookUrl: 'https://your-domain.com/api/automation-webhook',
});

const result = await orchestrator.run();
```

## Advanced: Custom Tasks

```typescript
const orchestrator = new MasterOrchestrator({
  tasks: [
    {
      id: 'custom-task',
      name: 'My Custom Task',
      type: 'attribution',  // Which backend module to call
      enabled: true,
      priority: 'critical',
      timeout: 180000,      // 3 minutes
      retryMaxAttempts: 2,
      dependencies: [
        { taskId: 'other-task', required: true, wait: true }
      ],
      metadata: { custom: 'data' },
    },
  ],
});
```

## Circuit Breaker States

```
CLOSED (Normal)
  └─→ 5 failures in a row
      └─→ OPEN (Task type disabled)
          └─→ (wait 5 minutes for reset)
              └─→ HALF-OPEN (single retry allowed)
                  ├─→ Success → CLOSED (normal again)
                  └─→ Failure → OPEN (retry reset timer)
```

## Webhook Payload

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
    "fastestTask": { "taskName": "Email", "duration": 234 },
    "slowestTask": { "taskName": "Carousel", "duration": 15400 },
    "averageTaskDuration": 4567,
    "criticalFailures": [],
    "warnings": ["Success rate below 100%"]
  }
}
```

## Troubleshooting Quick Guide

1. **Nothing runs**
   - Check: RUNTIME_API_URL, PROFITENGINE_WEBHOOK_TOKEN
   - Verify: At least one module credential set

2. **All tasks fail**
   - Check: Circuit breaker (set AUTOMATION_CIRCUIT_BREAKER_RESET_MS=0)
   - Try: AUTOMATION_MODE=sequential for details

3. **Slow execution**
   - Increase: AUTOMATION_POOL_SIZE (try 8)
   - Check: External service latency

4. **High memory usage**
   - Clear: .runtime/automation/ old files
   - Set: AUTOMATION_LOG_LEVEL=warn

## One-Liners

```bash
# Run with defaults
npm run automation:launch

# Debug mode (verbose logging)
AUTOMATION_LOG_LEVEL=debug npm run automation:launch

# Sequential (slower, clearer errors)
AUTOMATION_MODE=sequential npm run automation:launch

# Max speed
AUTOMATION_MODE=parallel npm run automation:launch

# High concurrency
AUTOMATION_POOL_SIZE=8 npm run automation:launch

# Check latest status
cat .runtime/automation/orchestration-status.jsonl | tail -1 | jq .
```

## Files Created

```
✅ app/lib/automation/master-orchestrator.ts           (37 KB)
✅ app/lib/automation/master-orchestrator-examples.ts  (25 KB)
✅ app/lib/automation/MASTER_ORCHESTRATOR_GUIDE.md     (20 KB)
✅ app/lib/automation/README.md                        (10 KB)
✅ app/lib/automation/QUICK_REFERENCE.md              (this file)
✅ MASTER_ORCHESTRATOR_DELIVERY.md                     (10 KB)
```

Total: **92 KB of complete, working code**

---

For full documentation, see: `MASTER_ORCHESTRATOR_GUIDE.md`  
For examples, see: `master-orchestrator-examples.ts`  
For API reference, see: `master-orchestrator.ts` (code comments)
