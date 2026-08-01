import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import { normalizeSeedRecord, parseEstimatedTicketValue, parseCostRequired, parseTimeToRevenue } from '../lib/revenue-os/schemas.mjs';
import { calculateOverallScore, calculateMetrics } from '../lib/revenue-os/scoring.mjs';
import { importRevenueOsSeed } from '../lib/revenue-os/services/seed-import.mjs';
import { findRevenuePlays, getRevenuePlayByRecordId } from '../lib/revenue-os/repositories/revenue-play.repository.mjs';
import { getDb, closeClient } from '../lib/mongodb.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');

const seedText = fs.readFileSync(path.join(root, 'data/revenue-os/revenue-plays.seed.json'), 'utf8');
const seedJson = JSON.parse(seedText);

process.env.MONGODB_URI = 'mongodb://127.0.0.1:27017/revenue-os-test';
process.env.MONGODB_DB = 'revenue-os-test';

function test(name, fn) {
  try {
    fn();
    console.log(`PASS ${name}`);
  } catch (err) {
    console.error(`FAIL ${name}: ${err.message}`);
    process.exitCode = 1;
  }
}

async function testAsync(name, fn) {
  try {
    await fn();
    console.log(`PASS ${name}`);
  } catch (err) {
    console.error(`FAIL ${name}: ${err.message}`);
    process.exitCode = 1;
  }
}

// 1. Seed validation script
const validationOutput = execSync('node scripts/validate-revenue-os-seed.mjs', { cwd: root, encoding: 'utf8' });
test('validate-revenue-os-seed exits 0 with 65 records', () => {
  assert.match(validationOutput, /Validated 65 Revenue OS seed records/);
});

// 2. Schema normalization
test('normalizeSeedRecord maps snake_case seed to camelCase', () => {
  const raw = seedJson.records[0];
  const play = normalizeSeedRecord(raw);
  assert.equal(play.recordId, raw.id);
  assert.equal(play.revenuePlayName, raw.revenue_play_name);
  assert.equal(play.status, 'SEED_READY');
  assert.equal(typeof play.estimatedTicketValue.minimum, 'number');
  assert.equal(typeof play.estimatedTicketValue.maximum, 'number');
  assert.ok(['dispatch', 'project', 'month', 'route', 'location'].includes(play.estimatedTicketValue.unit));
});

test('parseEstimatedTicketValue extracts ranges and units', () => {
  const a = parseEstimatedTicketValue('$300-$2,500 monthly');
  assert.equal(a.minimum, 300);
  assert.equal(a.maximum, 2500);
  assert.equal(a.unit, 'month');

  const b = parseEstimatedTicketValue('$500-$5,000');
  assert.equal(b.minimum, 500);
  assert.equal(b.maximum, 5000);
  assert.equal(b.unit, 'project');
});

test('parseCostRequired returns 0 for $0 seed values', () => {
  assert.equal(parseCostRequired('$0 new spend under existing-tools and partner-first model'), 0);
});

test('parseTimeToRevenue converts ranges to average days', () => {
  const days = parseTimeToRevenue('7-30 days');
  assert.equal(days, 19);
});

// 3. Scoring engine
test('calculateOverallScore is deterministic and 0-100', () => {
  const play = normalizeSeedRecord(seedJson.records[0]);
  const score = calculateOverallScore(play);
  assert.equal(typeof score, 'number');
  assert.ok(score >= 0 && score <= 100);
  assert.equal(score, 58); // weighted normalized score for RP-001
});

test('calculateMetrics computes ticket and recurring estimates', () => {
  const play = normalizeSeedRecord(seedJson.records[0]);
  const metrics = calculateMetrics(play);
  assert.equal(typeof metrics.expectedFirst30DayRevenue, 'number');
  assert.equal(typeof metrics.weightedPipelineValue, 'number');
  assert.equal(typeof metrics.monthlyRecurringPotential, 'number');
});

test('calculateOverallScore falls back to derived values when scoreInputs are missing', () => {
  const score = calculateOverallScore({
    estimatedTicketValue: { minimum: 100, maximum: 200, unit: 'project' },
    timeToRevenueDays: 10,
    costRequired: 0,
    profitPotential: 0.8,
    stackingFit: 0.9,
    recurringPotential: 0.7,
    liabilityScore: 0.5,
    databaseValueScore: 0.6,
  });
  assert.equal(typeof score, 'number');
  assert.ok(Number.isFinite(score));
  assert.ok(score >= 0 && score <= 100);
});

// 4. Seed importer (dry-run, no DB)
await testAsync('dry-run import reports 65 records without touching DB', async () => {
  const summary = await importRevenueOsSeed({ dryRun: true });
  assert.equal(summary.total, 65);
  assert.equal(summary.inserted, 65);
  assert.equal(summary.updated, 0);
  assert.equal(summary.unchanged, 0);
  assert.equal(summary.errors.length, 0);
  assert.equal(summary.dryRun, true);
});

// 5. Integration tests against MongoDB (optional)
const mongoUri = process.env.MONGO_URL || process.env.MONGODB_URI;
if (!mongoUri) {
  console.log('SKIP MongoDB integration tests: MONGO_URL/MONGODB_URI not set');
} else {
  await testAsync('real import inserts 65 revenue plays and is idempotent', async () => {
    const db = await getDb();
    await db.collection('revenue_plays').deleteMany({});
    await db.collection('activities').deleteMany({});

    const first = await importRevenueOsSeed({ dryRun: false });
    assert.equal(first.total, 65);
    assert.equal(first.inserted, 65);
    assert.equal(first.updated, 0);
    assert.equal(first.unchanged, 0);
    assert.equal(first.errors.length, 0);

    const second = await importRevenueOsSeed({ dryRun: false });
    assert.equal(second.total, 65);
    assert.equal(second.inserted, 0);
    assert.equal(second.updated, 0);
    assert.equal(second.unchanged, 65);
    assert.equal(second.errors.length, 0);
  });

  await testAsync('findRevenuePlays returns the seeded records', async () => {
    const result = await findRevenuePlays({ limit: 10 });
    assert.equal(result.total, 65);
    assert.equal(result.records.length, 10);
    assert.ok(result.records[0].overallScore >= 0);
  });

  await testAsync('findRevenuePlays paginates consistently and clamps large limits', async () => {
    const page1 = await findRevenuePlays({ limit: 10, page: 1 });
    const page2 = await findRevenuePlays({ limit: 10, page: 2 });
    const largeLimit = await findRevenuePlays({ limit: 500, page: 1 });

    assert.equal(page1.records.length, 10);
    assert.equal(page2.records.length, 10);
    assert.notEqual(page1.records[0].recordId, page2.records[0].recordId);
    assert.equal(page1.page, 1);
    assert.equal(page2.page, 2);
    assert.equal(largeLimit.limit, 100);
    assert.ok(largeLimit.records.length <= 100);
  });

  await testAsync('getRevenuePlayByRecordId returns RP-001', async () => {
    const play = await getRevenuePlayByRecordId('RP-001');
    assert.ok(play);
    assert.equal(play.recordId, 'RP-001');
    assert.equal(play.revenuePlayName, seedJson.records[0].revenue_play_name);
  });

  await testAsync('search filter returns fewer than 65 results for a narrow term', async () => {
    const result = await findRevenuePlays({ search: 'clinic', limit: 100 });
    assert.ok(result.total < 65);
    assert.ok(result.records.length > 0);
    assert.ok(result.records.every((r) => JSON.stringify(r).toLowerCase().includes('clinic')));
  });

  await closeClient().catch(() => {});
}

console.log('revenue-os tests done');
