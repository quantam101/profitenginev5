#!/usr/bin/env node

/**
 * Faceless Videos CLI — Command-line tool for video generation automation
 *
 * Usage:
 *   node scripts/faceless-videos-cli.mjs generate [post-number]
 *   node scripts/faceless-videos-cli.mjs batch [post1] [post2] ...
 *   node scripts/faceless-videos-cli.mjs schedule [post-number] [iso-datetime]
 *   node scripts/faceless-videos-cli.mjs process-scheduled
 *   node scripts/faceless-videos-cli.mjs metrics
 *   node scripts/faceless-videos-cli.mjs status
 */

import https from 'https';
import http from 'http';

const API_BASE_URL = process.env.RUNTIME_API_URL || 'http://localhost:3000';
const API_TOKEN = process.env.AUTOMATION_API_TOKEN;

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(color, ...args) {
  console.log(`${color}${args.join(' ')}${colors.reset}`);
}

async function request(method, endpoint, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(API_BASE_URL);
    const isHttps = url.protocol === 'https:';
    const client = isHttps ? https : http;

    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: endpoint,
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (API_TOKEN) {
      options.headers.Authorization = `Bearer ${API_TOKEN}`;
    }

    const req = client.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode}: ${parsed.error || data}`));
          } else {
            resolve(parsed);
          }
        } catch {
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          } else {
            resolve({ raw: data });
          }
        }
      });
    });

    req.on('error', reject);

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

async function handleGenerate(args) {
  const postNumber = parseInt(args[0]) || 1;
  const provider = args[1] || 'replicate';

  log(colors.cyan, '🎬 Generating faceless video...');
  log(colors.cyan, `Post #${postNumber} with ${provider}`);

  try {
    const response = await request('POST', '/api/automation/faceless-videos/generate', {
      postNumber,
      videoProvider: provider,
      platforms: ['youtube', 'tiktok', 'instagram'],
    });

    if (response.success) {
      log(colors.green, '✓ Generation initiated');
      log(colors.blue, `Request ID: ${response.requestId}`);

      response.data.results.forEach((r) => {
        const status = r.success ? colors.green + '✓' : colors.red + '✗';
        log(colors.reset, `${status} ${r.platform}: ${r.status}`);
      });
    } else {
      log(colors.red, `✗ Generation failed: ${response.error}`);
    }
  } catch (error) {
    log(colors.red, `✗ Error: ${error.message}`);
    process.exit(1);
  }
}

async function handleBatch(args) {
  const postNumbers = args.map((x) => parseInt(x)).filter((x) => !isNaN(x));

  if (postNumbers.length === 0) {
    log(colors.red, '✗ No valid post numbers provided');
    process.exit(1);
  }

  log(colors.cyan, '📦 Batch generating videos...');
  log(colors.cyan, `Posts: ${postNumbers.join(', ')}`);

  try {
    const response = await request('POST', '/api/automation/faceless-videos/batch', {
      postNumbers,
      videoProvider: 'replicate',
      platforms: ['youtube', 'tiktok'],
      simultaneousGenerations: 2,
    });

    if (response.success) {
      log(colors.green, '✓ Batch generation complete');
    } else {
      log(colors.yellow, '⚠ Batch generation partial success');
    }

    log(colors.blue, `Generated: ${response.data.generated.length}`);
    log(colors.blue, `Failed: ${response.data.failed.length}`);
    log(colors.blue, `Scheduled: ${response.data.scheduled?.length || 0}`);

    if (response.data.failed.length > 0) {
      log(colors.yellow, '\nFailed posts:');
      response.data.failed.forEach((f) => {
        log(colors.red, `  Post ${f.postNumber}: ${f.error}`);
      });
    }
  } catch (error) {
    log(colors.red, `✗ Error: ${error.message}`);
    process.exit(1);
  }
}

async function handleSchedule(args) {
  const postNumber = parseInt(args[0]);
  const scheduledTime = args[1];

  if (!postNumber || !scheduledTime) {
    log(colors.red, '✗ Usage: schedule [post-number] [iso-datetime]');
    log(colors.red, '✗ Example: schedule 5 2024-06-21T14:00:00Z');
    process.exit(1);
  }

  log(colors.cyan, '📅 Scheduling video generation...');
  log(colors.cyan, `Post #${postNumber} for ${scheduledTime}`);

  try {
    const response = await request('POST', '/api/automation/faceless-videos/schedule', {
      postNumber,
      scheduledTime,
      timezone: 'UTC',
      platforms: ['youtube', 'tiktok'],
      videoProvider: 'replicate',
    });

    if (response.success) {
      log(colors.green, '✓ Video scheduled successfully');
      log(colors.blue, `Schedule ID: ${response.data.scheduledId}`);
    } else {
      log(colors.red, `✗ Scheduling failed: ${response.error}`);
    }
  } catch (error) {
    log(colors.red, `✗ Error: ${error.message}`);
    process.exit(1);
  }
}

async function handleProcessScheduled() {
  log(colors.cyan, '⏰ Processing scheduled videos...');

  try {
    const response = await request('POST', '/api/automation/faceless-videos/process-scheduled', {});

    if (response.success) {
      log(colors.green, '✓ All scheduled videos processed');
    } else {
      log(colors.yellow, '⚠ Some scheduled videos failed');
    }

    log(colors.blue, `Processed: ${response.data.processed}`);
    log(colors.blue, `Errors: ${response.data.errors.length}`);

    if (response.data.errors.length > 0) {
      log(colors.yellow, '\nErrors:');
      response.data.errors.forEach((e) => {
        log(colors.red, `  ${e.scheduleId}: ${e.error}`);
      });
    }
  } catch (error) {
    log(colors.red, `✗ Error: ${error.message}`);
    process.exit(1);
  }
}

async function handleMetrics() {
  log(colors.cyan, '📊 Fetching metrics...');

  try {
    const response = await request('GET', '/api/automation/faceless-videos/metrics');

    log(colors.green, '\n=== Video Generation Metrics ===');
    log(colors.blue, `Total Generated: ${response.data.totalGenerated}`);
    log(colors.blue, `Total Published: ${response.data.totalPublished}`);
    log(colors.blue, `Total Scheduled: ${response.data.totalScheduled}`);
    log(colors.blue, `Success Rate: ${response.data.successRate.toFixed(2)}%`);

    log(colors.cyan, '\nProvider Usage:');
    Object.entries(response.data.providerUsage).forEach(([provider, count]) => {
      log(colors.blue, `  ${provider}: ${count}`);
    });

    log(colors.cyan, '\nPlatform Usage:');
    Object.entries(response.data.platformUsage).forEach(([platform, count]) => {
      log(colors.blue, `  ${platform}: ${count}`);
    });

    const costPerVideo = 0.08;
    const monthlyCost = response.data.totalGenerated * costPerVideo;
    log(colors.cyan, `\nEstimated Monthly Cost: $${monthlyCost.toFixed(2)}`);
  } catch (error) {
    log(colors.red, `✗ Error: ${error.message}`);
    process.exit(1);
  }
}

async function handleStatus() {
  log(colors.cyan, '📋 Fetching status...');

  try {
    const response = await request('GET', '/api/automation/faceless-videos/status');

    log(colors.green, '\n=== System Status ===');
    log(colors.blue, `Runtime Dir: ${response.data.runtimeDir}`);
    log(colors.blue, `API Requests: ${response.data.apiRequests}`);
    log(colors.blue, `Webhooks: ${response.data.webhooks}`);
    log(colors.blue, `Executions: ${response.data.executions}`);

    log(colors.cyan, '\nLog Files:');
    response.data.logs.forEach((log_) => {
      const icon = log_.exists ? '✓' : '✗';
      log(colors.blue, `  ${icon} ${log_.path} (${log_.type})`);
    });
  } catch (error) {
    log(colors.red, `✗ Error: ${error.message}`);
    process.exit(1);
  }
}

function showHelp() {
  log(
    colors.cyan,
    `
Faceless Videos CLI — Video Generation Automation

Usage:
  generate [post-number] [provider]
    Generate a single video
    Example: generate 1 replicate

  batch [post1] [post2] ...
    Generate multiple videos in batch
    Example: batch 1 2 3 4 5

  schedule [post-number] [iso-datetime]
    Schedule video for specific time
    Example: schedule 5 2024-06-21T14:00:00Z

  process-scheduled
    Process all scheduled videos (run via cron)

  metrics
    Show video generation metrics

  status
    Show system status and log files

  help
    Show this help message

Environment Variables:
  RUNTIME_API_URL      Backend API URL (default: http://localhost:3000)
  AUTOMATION_API_TOKEN Optional API token for authentication

Examples:
  node scripts/faceless-videos-cli.mjs generate
  node scripts/faceless-videos-cli.mjs batch 1 2 3
  node scripts/faceless-videos-cli.mjs schedule 5 2024-06-21T14:00:00Z
  node scripts/faceless-videos-cli.mjs process-scheduled
  node scripts/faceless-videos-cli.mjs metrics
`
  );
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'help';

  switch (command) {
    case 'generate':
      await handleGenerate(args.slice(1));
      break;
    case 'batch':
      await handleBatch(args.slice(1));
      break;
    case 'schedule':
      await handleSchedule(args.slice(1));
      break;
    case 'process-scheduled':
      await handleProcessScheduled();
      break;
    case 'metrics':
      await handleMetrics();
      break;
    case 'status':
      await handleStatus();
      break;
    case 'help':
    default:
      showHelp();
      break;
  }
}

main().catch((error) => {
  log(colors.red, `Fatal error: ${error.message}`);
  process.exit(1);
});
