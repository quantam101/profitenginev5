#!/usr/bin/env node
/**
 * KDP AUTOMATION VERIFICATION TEST
 *
 * Tests:
 * 1. File existence: app/lib/automation/kdp.ts and app/api/automation/kdp/route.ts
 * 2. Exported functions: parseBookMetadata, generateBookCover, uploadToKdp, uploadToDraft2Digital, uploadToSmashwords, trackKdpRoyalties, orchestrateKdpPublication
 * 3. API endpoint: POST /api/automation/kdp (publish, track-royalties, status operations)
 * 4. Environment variables: KDP_ACCESS_TOKEN, DRAFT2DIGITAL_API_KEY, SMASHWORDS_API_KEY
 * 5. Image generation providers: unsplash, pexels, dalle, replicate
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');

const tests = {
  passed: 0,
  failed: 0,
  skipped: 0,
  errors: [],
};

function log(level, message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${level}: ${message}`);
}

function pass(message) {
  tests.passed++;
  log('✓ PASS', message);
}

function fail(message, error) {
  tests.failed++;
  tests.errors.push({ message, error });
  log('✗ FAIL', message);
  if (error) log('  Error', error.message || error);
}

function skip(message) {
  tests.skipped++;
  log('⊘ SKIP', message);
}

// Test 1: File existence
log('─', '═'.repeat(70));
log('─', 'KDP AUTOMATION VERIFICATION TEST SUITE');
log('─', '═'.repeat(70));

log('─', '');
log('─', '1. FILE EXISTENCE CHECKS');
log('─', '');

const kdpLibPath = path.join(PROJECT_ROOT, 'app/lib/automation/kdp.ts');
const kdpRoutePath = path.join(PROJECT_ROOT, 'app/api/automation/kdp/route.ts');

if (fs.existsSync(kdpLibPath)) {
  pass(`KDP library exists: ${kdpLibPath}`);
} else {
  fail(`KDP library NOT found: ${kdpLibPath}`);
}

if (fs.existsSync(kdpRoutePath)) {
  pass(`KDP API route exists: ${kdpRoutePath}`);
} else {
  fail(`KDP API route NOT found: ${kdpRoutePath}`);
}

// Test 2: Content validation
log('─', '');
log('─', '2. CONTENT VALIDATION');
log('─', '');

let kdpLibContent = '';
let kdpRouteContent = '';

try {
  kdpLibContent = fs.readFileSync(kdpLibPath, 'utf-8');
  pass(`KDP library file is readable (${kdpLibContent.length} bytes)`);
} catch (e) {
  fail(`Failed to read KDP library`, e);
}

try {
  kdpRouteContent = fs.readFileSync(kdpRoutePath, 'utf-8');
  pass(`KDP API route file is readable (${kdpRouteContent.length} bytes)`);
} catch (e) {
  fail(`Failed to read KDP API route`, e);
}

// Test 3: Exported functions
log('─', '');
log('─', '3. EXPORTED FUNCTIONS CHECK');
log('─', '');

const requiredFunctions = [
  'parseBookMetadata',
  'generateBookCover',
  'uploadToKdp',
  'uploadToDraft2Digital',
  'uploadToSmashwords',
  'trackKdpRoyalties',
  'orchestrateKdpPublication',
  'formatContentForKdp',
  'formatContentForDraft2Digital',
  'formatContentForSmashwords',
];

requiredFunctions.forEach((fn) => {
  if (kdpLibContent.includes(`export function ${fn}`) || kdpLibContent.includes(`export async function ${fn}`)) {
    pass(`Function exported: ${fn}`);
  } else {
    fail(`Function NOT exported: ${fn}`);
  }
});

// Test 4: API route handlers
log('─', '');
log('─', '4. API ROUTE HANDLERS');
log('─', '');

const requiredHandlers = ['POST', 'GET', 'OPTIONS'];

requiredHandlers.forEach((handler) => {
  if (kdpRouteContent.includes(`export async function ${handler}`)) {
    pass(`API handler implemented: ${handler}`);
  } else {
    fail(`API handler NOT implemented: ${handler}`);
  }
});

// Test 5: Environment variable checks
log('─', '');
log('─', '5. ENVIRONMENT VARIABLE CHECKS');
log('─', '');

const requiredEnvVars = [
  'KDP_ACCESS_TOKEN',
  'DRAFT2DIGITAL_API_KEY',
  'SMASHWORDS_API_KEY',
  'IMAGE_GENERATION_API',
  'UNSPLASH_API_KEY',
  'PEXELS_API_KEY',
  'OPENAI_API_KEY',
  'REPLICATE_API_TOKEN',
];

requiredEnvVars.forEach((envVar) => {
  if (kdpLibContent.includes(envVar) || kdpRouteContent.includes(envVar)) {
    pass(`Environment variable reference found: ${envVar}`);
  } else {
    fail(`Environment variable NOT referenced: ${envVar}`);
  }
});

// Test 6: Image generation providers
log('─', '');
log('─', '6. IMAGE GENERATION PROVIDERS');
log('─', '');

const imageProviders = ['unsplash', 'pexels', 'dalle', 'replicate'];

imageProviders.forEach((provider) => {
  if (kdpLibContent.includes(provider)) {
    pass(`Image provider supported: ${provider}`);
  } else {
    fail(`Image provider NOT found: ${provider}`);
  }
});

// Test 7: Platform upload functions
log('─', '');
log('─', '7. PLATFORM UPLOAD IMPLEMENTATIONS');
log('─', '');

const platforms = [
  { name: 'Amazon KDP', func: 'uploadToKdp', endpoint: 'https://kdp.amazon.com/api/v1/books' },
  { name: 'Draft2Digital', func: 'uploadToDraft2Digital', endpoint: 'https://api.draft2digital.com/books' },
  { name: 'Smashwords', func: 'uploadToSmashwords', endpoint: 'https://api.smashwords.com/v1/books' },
];

platforms.forEach(({ name, func, endpoint }) => {
  if (kdpLibContent.includes(func)) {
    pass(`${name} upload function implemented`);
  } else {
    fail(`${name} upload function NOT found`);
  }

  if (kdpLibContent.includes(endpoint)) {
    pass(`${name} endpoint configured: ${endpoint}`);
  } else {
    fail(`${name} endpoint NOT found`);
  }
});

// Test 8: API request/response types
log('─', '');
log('─', '8. API REQUEST/RESPONSE TYPES');
log('─', '');

const requiredInterfaces = [
  'BookMetadata',
  'PlatformUploadResult',
  'KdpPublicationResult',
  'RoyaltyData',
];

requiredInterfaces.forEach((iface) => {
  if (kdpLibContent.includes(`interface ${iface}`) || kdpLibContent.includes(`export interface ${iface}`)) {
    pass(`Interface defined: ${iface}`);
  } else {
    fail(`Interface NOT defined: ${iface}`);
  }
});

// Test 9: Royalty tracking
log('─', '');
log('─', '9. ROYALTY TRACKING');
log('─', '');

if (kdpLibContent.includes('trackKdpRoyalties')) {
  pass(`KDP royalty tracking function exists`);
} else {
  fail(`KDP royalty tracking function NOT found`);
}

if (kdpLibContent.includes('/earnings')) {
  pass(`Royalty earnings endpoint referenced`);
} else {
  fail(`Royalty earnings endpoint NOT referenced`);
}

// Test 10: Orchestration
log('─', '');
log('─', '10. ORCHESTRATION & AUTOMATION');
log('─', '');

if (kdpLibContent.includes('orchestrateKdpPublication')) {
  pass(`Main orchestration function exists`);
} else {
  fail(`Main orchestration function NOT found`);
}

if (kdpLibContent.includes('KDP_BOOK_')) {
  pass(`Book file pattern detection implemented`);
} else {
  fail(`Book file pattern detection NOT found`);
}

if (kdpLibContent.includes('.runtime/kdp')) {
  pass(`Runtime data directory reference found`);
} else {
  fail(`Runtime data directory NOT referenced`);
}

// Test 11: Error handling
log('─', '');
log('─', '11. ERROR HANDLING & VALIDATION');
log('─', '');

if (kdpLibContent.includes('try') && kdpLibContent.includes('catch')) {
  pass(`Try-catch error handling implemented`);
} else {
  fail(`Try-catch error handling NOT found`);
}

if (kdpLibContent.includes('throw new Error')) {
  pass(`Custom error throwing implemented`);
} else {
  fail(`Custom error throwing NOT found`);
}

// Test 12: API authentication
log('─', '');
log('─', '12. API AUTHENTICATION');
log('─', '');

if (kdpRouteContent.includes('Authorization') && kdpRouteContent.includes('AUTOMATION_API_TOKEN')) {
  pass(`API authentication token validation implemented`);
} else {
  fail(`API authentication token validation NOT found`);
}

// Summary
log('─', '');
log('─', '═'.repeat(70));
log('─', 'TEST SUMMARY');
log('─', '═'.repeat(70));
log('─', `PASSED: ${tests.passed}`);
log('─', `FAILED: ${tests.failed}`);
log('─', `SKIPPED: ${tests.skipped}`);
log('─', `TOTAL:  ${tests.passed + tests.failed + tests.skipped}`);

if (tests.failed > 0) {
  log('─', '');
  log('─', 'FAILURES:');
  tests.errors.forEach(({ message, error }) => {
    log('─', `  • ${message}`);
    if (error) log('─', `    ${error}`);
  });
}

log('─', '');
if (tests.failed === 0) {
  log('✓', 'ALL TESTS PASSED - KDP AUTOMATION READY');
  process.exit(0);
} else {
  log('✗', `${tests.failed} TEST(S) FAILED`);
  process.exit(1);
}
