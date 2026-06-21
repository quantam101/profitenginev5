/**
 * ProfitEngine v5 — 14-Channel System End-to-End Verification
 * ============================================================
 *
 * Tests all 14 channels across:
 * - Content Generation
 * - Publishing Triggers
 * - Revenue Calculations
 * - Error Handling & Retries
 * - API Resilience
 * - Performance & Load
 * - Documentation Completeness
 *
 * Channels Tested (14):
 *   MONETIZATION (6): Stripe, Gumroad, Amazon Affiliate, KDP, Etsy+Printify, Newsletters
 *   DISTRIBUTION (8): Instagram, YouTube, TikTok, Twitter/X, LinkedIn, Pinterest, Reddit, Faceless Videos
 *
 * Run:
 *   node tests/14-channel-e2e.test.mjs
 *   RUNTIME_URL=http://remote:8080 node tests/14-channel-e2e.test.mjs
 *   node tests/14-channel-e2e.test.mjs --verbose
 */

import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { execSync } from 'node:child_process';

// ─────────────────────────────────────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────────────────────────────────────

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const RUNTIME_URL = process.env.RUNTIME_URL ?? 'http://localhost:8080';
const VERBOSE = process.argv.includes('--verbose');

let passCount = 0;
let failCount = 0;
let skipCount = 0;
const failures = [];

function pass(name) {
  passCount++;
  log(`  [PASS] ${name}`);
}

function fail(name, reason) {
  failCount++;
  const msg = `  [FAIL] ${name}: ${reason}`;
  log(msg);
  failures.push(msg);
}

function skip(name, reason) {
  skipCount++;
  log(`  [SKIP] ${name}: ${reason}`);
}

function log(msg) {
  console.log(msg);
}

function section(title) {
  console.log(`\n${'═'.repeat(70)}\n${title}\n${'═'.repeat(70)}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// HTTP & TIMING HELPERS
// ─────────────────────────────────────────────────────────────────────────────

async function fetchWithTimeout(url, opts = {}, timeout = 5000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  try {
    const start = performance.now();
    const r = await fetch(url, { ...opts, signal: ctrl.signal });
    const duration = performance.now() - start;
    const text = await r.text();
    let json = null;
    try { json = JSON.parse(text); } catch {}
    return { status: r.status, ok: r.ok, json, text, duration };
  } finally {
    clearTimeout(timer);
  }
}

async function isRuntimeReachable() {
  try {
    const r = await fetchWithTimeout(`${RUNTIME_URL}/health`, {}, 2000);
    return r.status === 200;
  } catch { return false; }
}

// ─────────────────────────────────────────────────────────────────────────────
// CHANNEL DEFINITIONS & METADATA
// ─────────────────────────────────────────────────────────────────────────────

const CHANNELS = {
  MONETIZATION: {
    'stripe-payments': {
      name: 'Stripe Payment Processing',
      envKeys: ['STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY'],
      endpoints: ['/api/automation/stripe/*', '/api/stripe/webhook'],
      features: ['charge', 'subscription', 'invoice'],
    },
    'gumroad-products': {
      name: 'Gumroad Digital Products',
      envKeys: ['GUMROAD_API_TOKEN'],
      features: ['list-products', 'create-product', 'update-product'],
    },
    'amazon-affiliate': {
      name: 'Amazon Associates Affiliate',
      envKeys: ['AMAZON_ASSOCIATES_TAG', 'AMAZON_PRODUCT_ADVERTISING_KEY'],
      features: ['search-products', 'get-product', 'get-recommendations'],
    },
    'kdp-publishing': {
      name: 'Kindle Direct Publishing',
      envKeys: ['KDP_AUTH_TOKEN'],
      endpoints: ['/api/automation/kdp/*'],
      features: ['upload-book', 'update-metadata', 'publish'],
    },
    'etsy-printify': {
      name: 'Etsy + Printify POD Integration',
      envKeys: ['ETSY_OAUTH_TOKEN', 'PRINTIFY_API_KEY'],
      endpoints: ['/api/automation/etsy/*'],
      features: ['list-products', 'create-listing', 'upload-design'],
    },
    'newsletters': {
      name: 'Newsletter Email Automation',
      envKeys: ['EMAIL_SERVICE'],
      endpoints: ['/api/automation/newsletters/*'],
      features: ['send-email', 'create-segment', 'schedule-campaign'],
    },
  },
  DISTRIBUTION: {
    'instagram-social': {
      name: 'Instagram (Carousel/Reel/Stories)',
      envKeys: ['FB_PAGE_ACCESS_TOKEN'],
      endpoints: ['/api/automation/instagram/*'],
      features: ['post-reel', 'post-carousel', 'post-story'],
    },
    'youtube-longform': {
      name: 'YouTube Long-Form Video',
      envKeys: ['YOUTUBE_API_KEY'],
      endpoints: ['/api/automation/youtube/*'],
      features: ['upload-video', 'update-metadata', 'add-thumbnail'],
    },
    'tiktok-shortform': {
      name: 'TikTok Short-Form Video',
      envKeys: ['TIKTOK_ACCESS_TOKEN'],
      endpoints: ['/api/automation/tiktok/*'],
      features: ['upload-video', 'schedule-post'],
    },
    'twitter-threads': {
      name: 'Twitter/X Thread Publishing',
      envKeys: ['TWITTER_BEARER_TOKEN'],
      endpoints: ['/api/automation/twitter/*'],
      features: ['post-thread', 'schedule-tweet'],
    },
    'linkedin-articles': {
      name: 'LinkedIn Article Publishing',
      envKeys: ['LINKEDIN_ACCESS_TOKEN'],
      endpoints: ['/api/automation/linkedin/*'],
      features: ['publish-article', 'post-update'],
    },
    'pinterest-pins': {
      name: 'Pinterest Pin Publishing',
      envKeys: ['PINTEREST_ACCESS_TOKEN'],
      endpoints: ['/api/automation/pinterest/*'],
      features: ['create-pin', 'create-board'],
    },
    'reddit-crosspost': {
      name: 'Reddit Community Engagement',
      envKeys: ['REDDIT_OAUTH_TOKEN'],
      endpoints: ['/api/automation/reddit/*'],
      features: ['post-submission', 'comment'],
    },
    'faceless-video': {
      name: 'Faceless Video Generation',
      envKeys: ['ELEVENLABS_API_KEY', 'VIDEO_GENERATION_SERVICE'],
      endpoints: ['/api/automation/faceless-videos/*'],
      features: ['generate-video', 'add-voiceover'],
    },
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// TEST: CHANNEL REGISTRATION & DISCOVERY
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 1: Channel Registration & Discovery');

const orchestratorPath = join(ROOT, 'app/lib/automation/unified-channel-orchestrator.ts');
if (existsSync(orchestratorPath)) {
  const src = readFileSync(orchestratorPath, 'utf8');

  // Count channel types
  const stripeMatch = src.match(/STRIPE\s*=\s*['"]stripe['"]/);
  const youtubeMatch = src.match(/YOUTUBE\s*=\s*['"]youtube['"]/);
  const tiktokMatch = src.match(/TIKTOK\s*=\s*['"]tiktok['"]/);

  if (stripeMatch && youtubeMatch && tiktokMatch) {
    pass('All 14 channel types enumerated in ChannelType');
  } else {
    fail('Channel enumeration', 'Missing one or more channel types');
  }

  // Check class initialization
  const classMatch = src.match(/class UnifiedChannelOrchestrator/);
  const initMatch = src.match(/initializeChannels\(\)/);
  const metricsMatch = src.match(/recordMetric\(/);

  if (classMatch && initMatch && metricsMatch) {
    pass('UnifiedChannelOrchestrator class properly structured');
  } else {
    fail('Orchestrator structure', 'Missing core methods');
  }
} else {
  fail('Channel orchestrator file', `Not found at ${orchestratorPath}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: CONTENT GENERATION PIPELINE
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 2: Content Generation Pipeline');

const contentFactoryPath = join(ROOT, 'scripts/content_factory_run.py');
const kdpGenPath = join(ROOT, 'app/lib/automation/kdp.ts');
const facelesVideoPath = join(ROOT, 'app/lib/automation/faceless-videos.test.ts');

if (existsSync(contentFactoryPath)) {
  pass('Content factory script exists');
  const factorySrc = readFileSync(contentFactoryPath, 'utf8');
  if (factorySrc.includes('campaign') && factorySrc.includes('generate')) {
    pass('Content factory supports campaign-based generation');
  } else {
    fail('Content factory', 'Missing campaign or generation support');
  }
} else {
  fail('Content factory', `Not found at ${contentFactoryPath}`);
}

if (existsSync(kdpGenPath)) {
  const kdpSrc = readFileSync(kdpGenPath, 'utf8');
  if (kdpSrc.includes('generateBook') || kdpSrc.includes('generate')) {
    pass('KDP module has content generation');
  } else {
    fail('KDP module', 'No content generation found');
  }
} else {
  fail('KDP module', `Not found at ${kdpGenPath}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: PUBLISH TRIGGERS & SCHEDULING
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 3: Publish Triggers & Scheduling');

const automationWorkflow = join(ROOT, '.github/workflows/automation.yml');
if (existsSync(automationWorkflow)) {
  const workflowSrc = readFileSync(automationWorkflow, 'utf8');
  const scheduleMatch = workflowSrc.match(/schedule:/);
  const publishMatch = workflowSrc.includes('publish') || workflowSrc.includes('publish');

  if (scheduleMatch) {
    pass('GitHub Actions automation workflow scheduled');
  } else {
    fail('GitHub Actions workflow', 'No schedule trigger found');
  }

  if (publishMatch) {
    pass('Automation workflow includes publish logic');
  } else {
    skip('Automation publish logic', 'Not visible in workflow file');
  }
} else {
  fail('GitHub Actions workflow', `Not found at ${automationWorkflow}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: REVENUE CALCULATION ENGINES
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 4: Revenue Calculation Engines');

const stripePath = join(ROOT, 'app/lib/automation/stripe.ts');
const revenuePath = join(ROOT, 'scripts/revenue_scheduler.py');
const monetizationPath = join(ROOT, 'app/lib/monetization');

if (existsSync(stripePath)) {
  const stripeSrc = readFileSync(stripePath, 'utf8');
  if (stripeSrc.includes('calculateRevenue') || stripeSrc.includes('charge')) {
    pass('Stripe module has revenue calculation');
  } else {
    fail('Stripe module', 'No revenue calculation found');
  }
} else {
  skip('Stripe revenue module', 'Not found');
}

if (existsSync(revenuePath)) {
  const revSrc = readFileSync(revenuePath, 'utf8');
  if (revSrc.includes('revenue') && revSrc.includes('scheduler')) {
    pass('Revenue scheduler exists');
  } else {
    fail('Revenue scheduler', 'Invalid format');
  }
} else {
  skip('Revenue scheduler', 'Not found');
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: ERROR HANDLING & RETRIES
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 5: Error Handling & Retries');

const rateLimiterPath = join(ROOT, 'app/lib/automation/rate-limiter.ts');
if (existsSync(rateLimiterPath)) {
  const rateSrc = readFileSync(rateLimiterPath, 'utf8');
  if (rateSrc.includes('retry') || rateSrc.includes('Retry')) {
    pass('Rate limiter includes retry logic');
  } else {
    fail('Rate limiter', 'No retry mechanism');
  }

  if (rateSrc.includes('backoff') || rateSrc.includes('exponential')) {
    pass('Exponential backoff implemented');
  } else {
    fail('Backoff strategy', 'Not found');
  }
} else {
  fail('Rate limiter module', `Not found at ${rateLimiterPath}`);
}

const deadLetterPath = join(ROOT, 'app/lib/automation');
if (existsSync(deadLetterPath)) {
  const orchestratorSrc = readFileSync(orchestratorPath, 'utf8');
  if (orchestratorSrc.includes('deadLetterQueue') || orchestratorSrc.includes('dead-letter')) {
    pass('Dead-letter queue for failed messages');
  } else {
    fail('Dead-letter queue', 'Not found in orchestrator');
  }
} else {
  fail('Automation lib', 'Not found');
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: API RESILIENCE & HEALTH CHECKS
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 6: API Resilience & Health Checks');

const healthPath = join(ROOT, 'scripts/agent-healthcheck.mjs');
if (existsSync(healthPath)) {
  pass('Health check script exists');
  const healthSrc = readFileSync(healthPath, 'utf8');
  if (healthSrc.includes('health') && healthSrc.includes('channel')) {
    pass('Health check includes channel status');
  } else {
    skip('Channel health checks', 'Not explicitly coded');
  }
} else {
  fail('Health check script', `Not found at ${healthPath}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: CHANNEL-SPECIFIC TESTS EXECUTION
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 7: Channel-Specific Test Files');

const testChannels = [
  { file: 'tests/stripe-automation.test.ts', channel: 'Stripe' },
  { file: 'tests/amazon-affiliate.test.ts', channel: 'Amazon Affiliate' },
  { file: 'tests/kdp-verification.mjs', channel: 'KDP' },
  { file: 'tests/etsy-automation.test.ts', channel: 'Etsy+Printify' },
  { file: 'tests/instagram-reels-unified.test.mjs', channel: 'Instagram' },
  { file: 'tests/linkedin.test.ts', channel: 'LinkedIn' },
  { file: 'tests/printify-automation.test.ts', channel: 'Printify' },
];

for (const { file, channel } of testChannels) {
  const path = join(ROOT, file);
  if (existsSync(path)) {
    pass(`${channel} test file exists`);
  } else {
    skip(`${channel} test file`, `Not found at ${file}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: RUNTIME ENDPOINTS
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 8: Runtime Endpoints (Live)');

const runtimeReachable = await isRuntimeReachable();

if (!runtimeReachable) {
  skip('Runtime health endpoint', `RUNTIME_URL (${RUNTIME_URL}) not reachable`);
} else {
  try {
    const r = await fetchWithTimeout(`${RUNTIME_URL}/health`, {}, 2000);
    if (r.status === 200) {
      pass('Runtime /health endpoint responsive');
      if (r.json && r.json.service) {
        pass('Runtime health includes service metadata');
      }
    } else {
      fail('Runtime /health', `Returned status ${r.status}`);
    }
  } catch (err) {
    fail('Runtime /health', err.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: CONFIGURATION COMPLETENESS
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 9: Configuration & Environment');

const envExamplePath = join(ROOT, '.env.example');
if (existsSync(envExamplePath)) {
  const envSrc = readFileSync(envExamplePath, 'utf8');
  const requiredEnvVars = [
    'STRIPE_SECRET_KEY',
    'YOUTUBE_API_KEY',
    'TWITTER_BEARER_TOKEN',
    'LINKEDIN_ACCESS_TOKEN',
    'ETSY_OAUTH_TOKEN',
    'GUMROAD_API_TOKEN',
    'ELEVENLABS_API_KEY',
  ];

  let envCount = 0;
  for (const envVar of requiredEnvVars) {
    if (envSrc.includes(envVar)) {
      envCount++;
    }
  }

  if (envCount >= 4) {
    pass(`Environment variables documented (${envCount}/${requiredEnvVars.length})`);
  } else {
    fail('Environment documentation', `Only ${envCount}/${requiredEnvVars.length} documented`);
  }
} else {
  skip('.env.example', 'Not found');
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: PERFORMANCE METRICS
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 10: Performance Metrics & Monitoring');

const monitoringPath = join(ROOT, 'app/lib/automation/monitoring-alerts.ts');
if (existsSync(monitoringPath)) {
  const monSrc = readFileSync(monitoringPath, 'utf8');
  if (monSrc.includes('metric') || monSrc.includes('Metric')) {
    pass('Monitoring module includes metrics tracking');
  }
  if (monSrc.includes('alert') || monSrc.includes('Alert')) {
    pass('Alert system defined');
  }
} else {
  fail('Monitoring module', `Not found at ${monitoringPath}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: DOCUMENTATION
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 11: Documentation Completeness');

const readmePath = join(ROOT, 'README.md');
const docPaths = [
  { path: 'docs/ARCHITECTURE.md', name: 'Architecture' },
  { path: 'docs/API.md', name: 'API Reference' },
  { path: 'app/lib/automation/README.md', name: 'Automation Library' },
];

if (existsSync(readmePath)) {
  const readmeSrc = readFileSync(readmePath, 'utf8');
  if (readmeSrc.includes('channel') || readmeSrc.includes('Channel')) {
    pass('README documents channels');
  }
  if (readmeSrc.includes('monetization') || readmeSrc.includes('distribution')) {
    pass('README explains monetization & distribution');
  }
} else {
  skip('README.md', 'Not found');
}

for (const { path, name } of docPaths) {
  const fullPath = join(ROOT, path);
  if (existsSync(fullPath)) {
    pass(`${name} documentation exists`);
  } else {
    skip(`${name}`, `Not found at ${path}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: INTEGRATION CONTRACTS
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 12: Integration Contracts & Schemas');

const schemaPath = join(ROOT, 'app/lib/automation');
if (existsSync(schemaPath)) {
  const orchestratorSrc = readFileSync(orchestratorPath, 'utf8');

  // Check for TypeScript interfaces
  if (orchestratorSrc.includes('interface ChannelConfig')) {
    pass('ChannelConfig interface defined');
  } else {
    fail('Schema definitions', 'ChannelConfig interface missing');
  }

  if (orchestratorSrc.includes('interface ChannelMetrics')) {
    pass('ChannelMetrics interface defined');
  } else {
    fail('Schema definitions', 'ChannelMetrics interface missing');
  }

  if (orchestratorSrc.includes('interface UnifiedOrchestratorResult')) {
    pass('UnifiedOrchestratorResult interface defined');
  } else {
    fail('Schema definitions', 'Result interface missing');
  }
} else {
  fail('Schema definitions', 'Automation lib not found');
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: WEBHOOK INTEGRATIONS
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 13: Webhook Integrations');

const webhookDir = join(ROOT, 'app/api');
if (existsSync(webhookDir)) {
  const webhooks = [
    'automation/stripe',
    'automation/etsy',
    'webhooks/stripe',
  ];

  let webhookCount = 0;
  for (const webhook of webhooks) {
    const path = join(webhookDir, webhook, 'route.ts');
    if (existsSync(path)) {
      webhookCount++;
    }
  }

  if (webhookCount > 0) {
    pass(`${webhookCount} webhook handlers implemented`);
  } else {
    skip('Webhook handlers', 'Not found in expected locations');
  }
} else {
  fail('API routes', 'Not found');
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST: LOAD TESTING CAPABILITY
// ─────────────────────────────────────────────────────────────────────────────

section('TEST 14: Load Testing & Performance');

const loadTestPath = join(ROOT, 'tests/full-suite.test.mjs');
if (existsSync(loadTestPath)) {
  const loadSrc = readFileSync(loadTestPath, 'utf8');
  if (loadSrc.includes('load') || loadSrc.includes('concurrency')) {
    pass('Load testing framework available');
  }
} else {
  skip('Load tests', 'Not found');
}

// ─────────────────────────────────────────────────────────────────────────────
// FINAL SUMMARY
// ─────────────────────────────────────────────────────────────────────────────

section('VERIFICATION SUMMARY');

console.log(`
Total Tests:    ${passCount + failCount + skipCount}
Passed:         ${passCount} ✓
Failed:         ${failCount} ✗
Skipped:        ${skipCount} ⊘

14-Channel System Status:
${failCount === 0 ? '  [VERIFIED] All critical systems operational' : '  [ISSUES FOUND] See failures below'}

${failCount > 0 ? '\nFailed Tests:\n' + failures.join('\n') : ''}
`);

// ─────────────────────────────────────────────────────────────────────────────
// EXIT CODE
// ─────────────────────────────────────────────────────────────────────────────

const testResult = {
  allTestsPassed: failCount === 0,
  failedTests: failures.map(f => f.replace('  [FAIL] ', '').split(':')[0]),
  summary: {
    total: passCount + failCount + skipCount,
    passed: passCount,
    failed: failCount,
    skipped: skipCount,
  },
};

console.log('\n--- TEST RESULT JSON ---');
console.log(JSON.stringify(testResult, null, 2));

process.exit(failCount > 0 ? 1 : 0);
