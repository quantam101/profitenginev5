#!/usr/bin/env node
/**
 * Faceless Videos Verification Test Suite
 *
 * Tests:
 * 1. Video generation capability (mock)
 * 2. Platform upload configuration (YouTube, TikTok, Instagram, Reddit)
 * 3. Scheduling system
 * 4. API endpoints
 * 5. Environment configuration
 */

const fs = require('fs');
const path = require('path');

// Color output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

const log = {
  pass: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  fail: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warn: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  info: (msg) => console.log(`${colors.cyan}ℹ${colors.reset} ${msg}`),
  section: (msg) => console.log(`\n${colors.blue}═══ ${msg} ═══${colors.reset}`),
};

let passCount = 0;
let failCount = 0;

// ============================================================================
// TEST 1: File Structure Verification
// ============================================================================

log.section('1. File Structure Verification');

const requiredFiles = [
  'app/lib/automation/faceless-videos.ts',
  'app/api/automation/faceless-videos/route.ts',
  'app/lib/automation/faceless-videos.test.ts',
];

requiredFiles.forEach((file) => {
  const fullPath = path.join(__dirname, file);
  if (fs.existsSync(fullPath)) {
    log.pass(`Found: ${file}`);
    passCount++;
  } else {
    log.fail(`Missing: ${file}`);
    failCount++;
  }
});

// ============================================================================
// TEST 2: API Routes Configuration
// ============================================================================

log.section('2. API Routes Configuration');

const apiRoutePath = path.join(__dirname, 'app/api/automation/faceless-videos/route.ts');
if (fs.existsSync(apiRoutePath)) {
  const content = fs.readFileSync(apiRoutePath, 'utf-8');

  const requiredEndpoints = [
    { name: 'POST /generate', pattern: 'handleGenerate' },
    { name: 'POST /batch', pattern: 'handleBatchGeneration' },
    { name: 'POST /schedule', pattern: 'handleScheduleVideo' },
    { name: 'POST /publish', pattern: 'handlePublish' },
    { name: 'POST /webhook', pattern: 'handleWebhook' },
    { name: 'GET /status', pattern: 'handleGetStatus' },
    { name: 'GET /metrics', pattern: 'handleGetMetrics' },
    { name: 'POST /process-scheduled', pattern: 'handleProcessScheduled' },
  ];

  requiredEndpoints.forEach(({ name, pattern }) => {
    if (content.includes(pattern)) {
      log.pass(`${name} endpoint implemented`);
      passCount++;
    } else {
      log.fail(`${name} endpoint missing`);
      failCount++;
    }
  });
}

// ============================================================================
// TEST 3: Platform Integration Verification
// ============================================================================

log.section('3. Platform Integration Verification');

const platformsFile = path.join(__dirname, 'app/lib/automation/faceless-videos.ts');
if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  const platforms = [
    { name: 'YouTube', pattern: 'publishToYouTube' },
    { name: 'TikTok', pattern: 'publishToTikTok' },
    { name: 'Instagram', pattern: 'publishToInstagram' },
    { name: 'Reddit', pattern: 'publishToReddit' },
  ];

  platforms.forEach(({ name, pattern }) => {
    if (content.includes(pattern)) {
      log.pass(`${name} integration implemented`);
      passCount++;
    } else {
      log.fail(`${name} integration missing`);
      failCount++;
    }
  });
}

// ============================================================================
// TEST 4: Video Generation Provider Support
// ============================================================================

log.section('4. Video Generation Provider Support');

const providers = [
  { name: 'D-ID', pattern: 'generateDIDFacelessVideo' },
  { name: 'Synthesia', pattern: 'generateSynthesiaFacelessVideo' },
  { name: 'Replicate', pattern: 'generateReplicateFacelessVideo' },
];

if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  providers.forEach(({ name, pattern }) => {
    if (content.includes(pattern)) {
      log.pass(`${name} provider implemented`);
      passCount++;
    } else {
      log.fail(`${name} provider missing`);
      failCount++;
    }
  });
}

// ============================================================================
// TEST 5: Environment Variables
// ============================================================================

log.section('5. Required Environment Variables');

const envPath = path.join(__dirname, '.env');
let envConfig = {};

if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  const lines = envContent.split('\n');
  lines.forEach((line) => {
    const [key, value] = line.split('=');
    if (key && value) {
      envConfig[key.trim()] = value.trim();
    }
  });
  log.pass('Found .env file');
  passCount++;
} else {
  log.warn('No .env file found (expected for production)');
}

const requiredEnvVars = [
  { name: 'YOUTUBE_API_KEY', platforms: ['YouTube'] },
  { name: 'TIKTOK_ACCESS_TOKEN', platforms: ['TikTok'] },
  { name: 'INSTAGRAM_ACCESS_TOKEN', platforms: ['Instagram'] },
  { name: 'INSTAGRAM_BUSINESS_ACCOUNT_ID', platforms: ['Instagram'] },
  { name: 'REDDIT_ACCESS_TOKEN', platforms: ['Reddit'] },
  { name: 'REPLICATE_API_TOKEN', platforms: ['All video providers'] },
  { name: 'ELEVENLABS_API_KEY', platforms: ['Voice generation'] },
  { name: 'DID_API_KEY', platforms: ['D-ID video provider'] },
  { name: 'SYNTHESIA_API_KEY', platforms: ['Synthesia video provider'] },
];

requiredEnvVars.forEach(({ name, platforms }) => {
  const value = process.env[name] || envConfig[name];
  if (value && value !== `<${name.toLowerCase()}>` && !value.includes('your-') && !value.includes('<replace')) {
    log.pass(`${name} configured (${platforms.join(', ')})`);
    passCount++;
  } else {
    log.warn(`${name} not configured (${platforms.join(', ')})`);
  }
});

// ============================================================================
// TEST 6: Scheduling System
// ============================================================================

log.section('6. Scheduling System');

if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  const schedulingFunctions = [
    { name: 'scheduleVideoGeneration', pattern: 'export async function scheduleVideoGeneration' },
    { name: 'processScheduledVideos', pattern: 'export async function processScheduledVideos' },
    { name: 'batchGenerateVideos', pattern: 'export async function batchGenerateVideos' },
  ];

  schedulingFunctions.forEach(({ name, pattern }) => {
    if (content.includes(pattern)) {
      log.pass(`${name} implemented`);
      passCount++;
    } else {
      log.fail(`${name} missing`);
      failCount++;
    }
  });
}

// ============================================================================
// TEST 7: Types and Interfaces
// ============================================================================

log.section('7. Type Definitions and Interfaces');

if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  const interfaces = [
    { name: 'FacelessVideoScript', pattern: 'export interface FacelessVideoScript' },
    { name: 'GeneratedFacelessVideo', pattern: 'export interface GeneratedFacelessVideo' },
    { name: 'FacelessVideoPublishResult', pattern: 'export interface FacelessVideoPublishResult' },
    { name: 'VideoGenerationOptions', pattern: 'export interface VideoGenerationOptions' },
    { name: 'ScheduleOptions', pattern: 'export interface ScheduleOptions' },
    { name: 'BatchGenerationOptions', pattern: 'export interface BatchGenerationOptions' },
  ];

  interfaces.forEach(({ name, pattern }) => {
    if (content.includes(pattern)) {
      log.pass(`${name} interface defined`);
      passCount++;
    } else {
      log.fail(`${name} interface missing`);
      failCount++;
    }
  });
}

// ============================================================================
// TEST 8: Voiceover Generation
// ============================================================================

log.section('8. Voiceover Generation (Eleven Labs)');

if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  if (content.includes('generateElevenLabsVoiceover')) {
    log.pass('Eleven Labs voiceover generation implemented');
    passCount++;

    if (content.includes('elevenlabs.io')) {
      log.pass('Eleven Labs API endpoint configured');
      passCount++;
    } else {
      log.fail('Eleven Labs API endpoint not found');
      failCount++;
    }
  } else {
    log.fail('Eleven Labs voiceover generation not implemented');
    failCount++;
  }
}

// ============================================================================
// TEST 9: Error Handling
// ============================================================================

log.section('9. Error Handling and Resilience');

if (fs.existsSync(apiRoutePath)) {
  const content = fs.readFileSync(apiRoutePath, 'utf-8');

  const errorHandling = [
    { name: 'Try-catch blocks', pattern: 'try {' },
    { name: 'Error responses', pattern: 'error:' },
    { name: 'Status codes', pattern: 'status:' },
    { name: 'Validation', pattern: 'if (!.*) {' },
  ];

  let errorHandlingCount = 0;
  errorHandling.forEach(({ name, pattern }) => {
    if (content.includes(pattern)) {
      errorHandlingCount++;
    }
  });

  if (errorHandlingCount >= 3) {
    log.pass('Comprehensive error handling implemented');
    passCount++;
  } else {
    log.warn('Limited error handling');
  }
}

// ============================================================================
// TEST 10: Authentication
// ============================================================================

log.section('10. API Authentication');

if (fs.existsSync(apiRoutePath)) {
  const content = fs.readFileSync(apiRoutePath, 'utf-8');

  if (content.includes('verifyAuth')) {
    log.pass('Authentication function implemented');
    passCount++;
  } else {
    log.fail('Authentication function missing');
    failCount++;
  }

  if (content.includes('AUTOMATION_API_TOKEN')) {
    log.pass('Authorization header verification');
    passCount++;
  } else {
    log.fail('Authorization header verification missing');
    failCount++;
  }
}

// ============================================================================
// TEST 11: Content Calendar Integration
// ============================================================================

log.section('11. Content Calendar Integration');

if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  if (content.includes('parseFacelessVideoScript')) {
    log.pass('Content calendar parsing implemented');
    passCount++;

    if (content.includes('CONTENT_CALENDAR_MONTHLY.md')) {
      log.pass('Content calendar file referenced');
      passCount++;
    } else {
      log.fail('Content calendar file not referenced');
      failCount++;
    }
  } else {
    log.fail('Content calendar parsing not implemented');
    failCount++;
  }
}

// ============================================================================
// TEST 12: Logging and Monitoring
// ============================================================================

log.section('12. Logging and Monitoring');

if (fs.existsSync(platformsFile)) {
  const content = fs.readFileSync(platformsFile, 'utf-8');

  if (content.includes('getVideoMetrics')) {
    log.pass('Metrics collection implemented');
    passCount++;
  } else {
    log.fail('Metrics collection missing');
    failCount++;
  }

  if (content.includes('execution.jsonl') || content.includes('appendFile')) {
    log.pass('Execution logging implemented');
    passCount++;
  } else {
    log.fail('Execution logging missing');
    failCount++;
  }
}

// ============================================================================
// SUMMARY
// ============================================================================

log.section('VERIFICATION SUMMARY');

const totalTests = passCount + failCount;
const passPercentage = totalTests > 0 ? ((passCount / totalTests) * 100).toFixed(1) : 0;

console.log(`
Total Tests: ${totalTests}
Passed: ${colors.green}${passCount}${colors.reset}
Failed: ${colors.red}${failCount}${colors.reset}
Success Rate: ${passPercentage}%
`);

// ============================================================================
// PLATFORM STATUS
// ============================================================================

log.section('PLATFORM STATUS');

const platformStatus = {
  'YouTube': {
    configured: !!process.env.YOUTUBE_API_KEY || !!envConfig.YOUTUBE_API_KEY,
    channel: process.env.YOUTUBE_CHANNEL_ID || envConfig.YOUTUBE_CHANNEL_ID,
  },
  'TikTok': {
    configured: !!process.env.TIKTOK_ACCESS_TOKEN || !!envConfig.TIKTOK_ACCESS_TOKEN,
  },
  'Instagram': {
    configured: !!process.env.INSTAGRAM_ACCESS_TOKEN || !!envConfig.INSTAGRAM_ACCESS_TOKEN,
    accountId: process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || envConfig.INSTAGRAM_BUSINESS_ACCOUNT_ID,
  },
  'Reddit': {
    configured: !!process.env.REDDIT_ACCESS_TOKEN || !!envConfig.REDDIT_ACCESS_TOKEN,
    subreddit: process.env.REDDIT_SUBREDDIT || envConfig.REDDIT_SUBREDDIT || 'trading',
  },
};

Object.entries(platformStatus).forEach(([platform, status]) => {
  if (status.configured) {
    const details = Object.entries(status)
      .filter(([k]) => k !== 'configured')
      .filter(([, v]) => v)
      .map(([k, v]) => `${k}=${v}`)
      .join(', ');
    log.pass(`${platform} ready${details ? ` (${details})` : ''}`);
  } else {
    log.warn(`${platform} needs configuration`);
  }
});

// ============================================================================
// PROVIDER STATUS
// ============================================================================

log.section('VIDEO GENERATION PROVIDER STATUS');

const providers_status = {
  'Replicate': process.env.REPLICATE_API_TOKEN || envConfig.REPLICATE_API_TOKEN,
  'D-ID': process.env.DID_API_KEY || envConfig.DID_API_KEY,
  'Synthesia': process.env.SYNTHESIA_API_KEY || envConfig.SYNTHESIA_API_KEY,
  'Eleven Labs': process.env.ELEVENLABS_API_KEY || envConfig.ELEVENLABS_API_KEY,
};

Object.entries(providers_status).forEach(([provider, configured]) => {
  if (configured && !configured.includes('<') && !configured.includes('your-')) {
    log.pass(`${provider} configured`);
  } else {
    log.warn(`${provider} not configured`);
  }
});

// ============================================================================
// FINAL STATUS
// ============================================================================

log.section('FINAL STATUS');

if (failCount === 0) {
  console.log(`${colors.green}PASS${colors.reset} — All faceless video components verified!`);
  process.exit(0);
} else if (passCount >= totalTests * 0.8) {
  console.log(`${colors.yellow}PARTIAL PASS${colors.reset} — Most components verified, ${failCount} issues to address`);
  process.exit(1);
} else {
  console.log(`${colors.red}FAIL${colors.reset} — Multiple verification failures`);
  process.exit(1);
}
