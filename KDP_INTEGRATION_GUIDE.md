# KDP Integration Guide — Adding to Automation Orchestration

## Overview

This guide shows how to integrate the KDP automation system into ProfitEngine's main automation orchestration engine. This allows KDP publishing to run alongside Gumroad, Instagram, and Email automation.

## Step 1: Update orchestrate.ts

Add KDP to the automation tasks list:

```typescript
// app/lib/automation/orchestrate.ts

import { orchestrateKdpPublication } from './kdp';

// In createDefaultConfig() function, add KDP task:
tasks: [
  {
    name: 'KDP Book Publication',
    type: 'kdp',
    enabled: process.env.KDP_ACCESS_TOKEN ? true : false,
    retryMaxAttempts: 3,
  },
  // ... existing tasks ...
]

// In executeTask() function, add handler:
if (task.type === 'kdp') {
  result = await orchestrateKdpPublication();
}
```

Full implementation:

```typescript
/**
 * ORCHESTRATION ENGINE — with KDP Integration
 */

import { orchestrateGumroadUpload } from './gumroad';
import { orchestrateKdpPublication } from './kdp';
import { generateAndPostCarousel } from './instagram-carousel';
import { generateAndPostReel } from './instagram-reel';
import { generateAndPostStories } from './instagram-stories';
import { setupEmailSequences } from './email-setup';
import { mkdir, writeFile, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

interface AutomationTask {
  name: string;
  type: 'gumroad' | 'kdp' | 'carousel' | 'reel' | 'stories' | 'email';
  enabled: boolean;
  parallel?: boolean;
  retryMaxAttempts?: number;
}

// ... rest of types ...

function createDefaultConfig(): AutomationConfig {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';

  return {
    runId: `automation-${Date.now()}`,
    timestamp: new Date().toISOString(),
    parallel: process.env.AUTOMATION_PARALLEL !== 'false',
    retryMaxAttempts: parseInt(process.env.AUTOMATION_RETRY_MAX_ATTEMPTS || '3', 10),
    retryBackoffMs: parseInt(process.env.AUTOMATION_RETRY_BACKOFF_MS || '5000', 10),
    runtimeDataDir: runtimeDir,
    tasks: [
      {
        name: 'KDP Book Publication',
        type: 'kdp',
        enabled: process.env.KDP_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 3,
      },
      {
        name: 'Gumroad Product Upload',
        type: 'gumroad',
        enabled: process.env.GUMROAD_API_TOKEN ? true : false,
        retryMaxAttempts: 3,
      },
      {
        name: 'Instagram Carousel Generation',
        type: 'carousel',
        enabled: process.env.FB_PAGE_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 2,
      },
      {
        name: 'Instagram Reel Generation',
        type: 'reel',
        enabled: process.env.FB_PAGE_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 2,
      },
      {
        name: 'Instagram Stories Generation',
        type: 'stories',
        enabled: process.env.FB_PAGE_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 2,
      },
      {
        name: 'Email Sequence Setup',
        type: 'email',
        enabled: process.env.EMAIL_SERVICE ? true : false,
        retryMaxAttempts: 2,
      },
    ],
  };
}

async function executeTask(
  task: AutomationTask,
  config: AutomationConfig
): Promise<AutomationTaskResult> {
  const startTime = new Date();
  let lastError: Error | undefined;
  let result: unknown;

  for (let attempt = 1; attempt <= (task.retryMaxAttempts || 3); attempt++) {
    try {
      console.log(`\n[${task.name}] Attempt ${attempt}/${task.retryMaxAttempts || 3}`);

      if (task.type === 'kdp') {
        result = await orchestrateKdpPublication();
      } else if (task.type === 'gumroad') {
        result = await orchestrateGumroadUpload();
      } else if (task.type === 'carousel') {
        result = await generateAndPostCarousel();
      } else if (task.type === 'reel') {
        result = await generateAndPostReel(1);
      } else if (task.type === 'stories') {
        result = await generateAndPostStories();
      } else if (task.type === 'email') {
        result = await setupEmailSequences();
      }

      const resultObj = result as Record<string, unknown>;
      if (resultObj.success || Array.isArray(resultObj)) {
        const endTime = new Date();
        return {
          taskName: task.name,
          taskType: task.type,
          success: true,
          duration: endTime.getTime() - startTime.getTime(),
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          result,
          attempts: attempt,
        };
      } else {
        lastError = new Error(resultObj.error as string || 'Task failed');
      }
    } catch (error) {
      lastError = error as Error;
      console.error(`[${task.name}] Error: ${lastError.message}`);

      if (attempt < (task.retryMaxAttempts || 3)) {
        const backoffMs = config.retryBackoffMs * Math.pow(2, attempt - 1);
        console.log(`[${task.name}] Retrying in ${backoffMs}ms...`);
        await new Promise((resolve) => setTimeout(resolve, backoffMs));
      }
    }
  }

  const endTime = new Date();
  return {
    taskName: task.name,
    taskType: task.type,
    success: false,
    duration: endTime.getTime() - startTime.getTime(),
    startTime: startTime.toISOString(),
    endTime: endTime.toISOString(),
    error: lastError?.message || 'Task failed',
    attempts: task.retryMaxAttempts || 3,
  };
}

// ... rest of orchestration functions remain the same ...
```

## Step 2: Update API Route

Update the launch endpoint to include KDP in the task list:

```typescript
// app/api/automation/launch/route.ts

// ... existing code ...

return NextResponse.json({
  success: true,
  runId,
  status: 'initiated',
  estimatedDuration: parallel ? '180s' : '300s',
  tasks: ['kdp', 'gumroad', 'carousel', 'reel', 'stories', 'email'].filter(
    (t) => !skipTasks.includes(t)
  ),
});
```

## Step 3: Environment Variables

Add to `.env.local`, `.env.production`, or GitHub Secrets:

```env
# KDP Integration
KDP_ACCESS_TOKEN=your-kdp-api-token
DRAFT2DIGITAL_API_KEY=your-draft2digital-key
SMASHWORDS_API_KEY=your-smashwords-key

# Cover Generation (pick one)
IMAGE_GENERATION_API=dalle
OPENAI_API_KEY=sk-...

# Or use Unsplash
# IMAGE_GENERATION_API=unsplash
# UNSPLASH_API_KEY=your-key

# Automation control
AUTOMATION_PARALLEL=true
AUTOMATION_RETRY_MAX_ATTEMPTS=3
```

## Step 4: Create GitHub Actions Workflow (Optional)

Schedule automated KDP publishing:

```yaml
# .github/workflows/kdp-publish.yml

name: KDP Publishing Automation

on:
  schedule:
    - cron: '0 0 * * MON'  # Run Mondays at midnight
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm install
      
      - name: Run KDP publishing
        env:
          KDP_ACCESS_TOKEN: ${{ secrets.KDP_ACCESS_TOKEN }}
          DRAFT2DIGITAL_API_KEY: ${{ secrets.DRAFT2DIGITAL_API_KEY }}
          SMASHWORDS_API_KEY: ${{ secrets.SMASHWORDS_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          AUTOMATION_API_TOKEN: ${{ secrets.AUTOMATION_API_TOKEN }}
        run: |
          curl -X POST http://localhost:3000/api/automation/kdp \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${{ secrets.AUTOMATION_API_TOKEN }}" \
            -d '{"operation": "publish"}'
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: kdp-publication-results
          path: .runtime/kdp/
```

## Step 5: Update Documentation

Add KDP to main automation docs:

```markdown
# ProfitEngine Automation — Updated

## Supported Automations

- **KDP Publishing** — Auto-publish eBooks to Amazon KDP, Draft2Digital, Smashwords
- **Gumroad Upload** — Auto-upload products to Gumroad
- **Instagram Carousel** — Generate and post carousels
- **Instagram Reel** — Generate and post reels
- **Instagram Stories** — Generate and post stories
- **Email Sequences** — Setup automated email sequences

## API

### Publish Books to KDP

```bash
POST /api/automation/kdp
{
  "operation": "publish"
}
```

### Track Royalties

```bash
GET /api/automation/kdp?asin=B0A1B2C3D4E5F6G7
```

### Full Orchestration

```bash
POST /api/automation/launch
{
  "parallel": true,
  "skipTasks": []
}
```

This will run all enabled automations (KDP, Gumroad, Instagram, Email).
```

## Step 6: Testing Integration

### Test 1: Check KDP is Enabled

```bash
curl http://localhost:3000/api/automation/launch -X GET
```

Should show `kdp` in the tasks list.

### Test 2: Run KDP Only

```bash
curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel": false,
    "skipTasks": ["gumroad", "carousel", "reel", "stories", "email"]
  }'
```

### Test 3: Run Full Orchestration with KDP

```bash
curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel": true,
    "skipTasks": []
  }'
```

This will run KDP, Gumroad, and all Instagram tasks in parallel.

## Step 7: Monitoring & Logging

View KDP publication results:

```bash
# View latest publication summary
tail -1 .runtime/kdp/publication-summary_*.json | jq '.'

# View individual book results
cat .runtime/kdp/*.json | jq '.metadata.title, .overallSuccess'

# View KDP-specific uploads
cat .runtime/kdp/*.json | jq '.uploads[] | select(.platform == "kdp")'

# Check success rate
cat .runtime/kdp/publication-summary_*.json | jq '.totalBooks, .successfulPublications'
```

## Step 8: Error Handling & Recovery

If KDP publishing fails:

1. **Check environment variables** — Ensure all tokens are set
2. **Verify book files** — Ensure `KDP_BOOK_*.md` files exist
3. **Review logs** — Check `.runtime/kdp/` for error details
4. **Check API quotas** — Ensure you haven't exceeded rate limits
5. **Retry with exponential backoff** — Automatic via orchestration engine

The orchestration engine automatically retries failed tasks 3 times with exponential backoff.

## Step 9: Performance Optimization

### For Multiple Books

If publishing 10+ books, use sequential mode instead of parallel:

```bash
curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel": false,
    "skipTasks": ["gumroad", "carousel", "reel", "stories", "email"]
  }'
```

This publishes books one at a time, with rate limiting to avoid API throttling.

### For Single Book

If publishing 1 book, use parallel mode:

```bash
curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel": true,
    "skipTasks": ["gumroad", "carousel", "reel", "stories", "email"]
  }'
```

## Step 10: Advanced Configuration

### Custom Retry Behavior

```typescript
// In orchestrateFullLaunch config override:
const result = await orchestrateFullLaunch({
  retryMaxAttempts: 5,
  retryBackoffMs: 10000, // 10 seconds
  tasks: [
    {
      name: 'KDP Book Publication',
      type: 'kdp',
      enabled: true,
      retryMaxAttempts: 5, // Override default 3
    },
  ],
});
```

### Skip KDP in Orchestration

```bash
curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel": true,
    "skipTasks": ["kdp"]  # Skip KDP, run others
  }'
```

## Integration Summary

| Component | Integration | Status |
|-----------|-----------|--------|
| Library | `app/lib/automation/kdp.ts` | ✓ Complete |
| API Endpoint | `app/api/automation/kdp/route.ts` | ✓ Complete |
| Orchestration | `app/lib/automation/orchestrate.ts` | ⚠ Requires manual update |
| Launch API | `app/api/automation/launch/route.ts` | ⚠ Minor update for KDP task |
| Environment | `.env.local`, GitHub Secrets | ✓ Ready |
| Workflows | GitHub Actions | ✓ Optional template provided |
| Documentation | `KDP_AUTOMATION_GUIDE.md` | ✓ Complete |
| Examples | `KDP_AUTOMATION_EXAMPLES.md` | ✓ Complete |

## Manual Update Steps Required

1. **Update orchestrate.ts** — Add KDP import, task definition, and executeTask handler
2. **Update launch/route.ts** — Add 'kdp' to tasks array
3. **Set environment variables** — Add KDP API tokens
4. **Create book files** — Add `KDP_BOOK_*.md` files to project root
5. **Test** — Run sample publication to verify integration

Total time to integrate: ~15 minutes

## Next Steps

After integration:

1. Create your first book file (`KDP_BOOK_test.md`)
2. Test cover generation
3. Run KDP publishing via API
4. Verify results in `.runtime/kdp/`
5. Check ASINs in Amazon KDP dashboard
6. Track earnings via royalty tracking API
7. Set up GitHub Actions for automated publishing
8. Monitor performance and adjust as needed

You now have a complete, integrated eBook publishing system!
