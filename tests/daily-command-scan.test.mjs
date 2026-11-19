import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';
import {
  EVENT_TYPE,
  gradeFromProbability,
  gradeFromScore,
  loadSeedRevenuePlays,
  pipelineOpportunityToEvent,
  rankRevenuePlays,
  runDailyCommandScan,
} from '../lib/revenue-os/services/daily-command-scan.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const seedPath = path.join(root, 'data/revenue-os/revenue-plays.seed.json');
const loadSeed = () => loadSeedRevenuePlays(seedPath);

// Mirrors daily-command-os packages/schemas/src/events.ts OpportunityDetected (strict: unknown keys rejected here).
const risk = z.enum(['low', 'medium', 'high']);
const DailyCommandOpportunity = z.object({
  event_type: z.literal('revenue_opportunity.detected'),
  source: z.string().min(1),
  timestamp: z.string().datetime().optional(),
  idempotency_key: z.string().optional(),
  data: z
    .object({
      company: z.string().min(1),
      niche: z.string().optional(),
      location: z.string().optional(),
      source_url: z.string().url().optional(),
      pain_signal: z.string().optional(),
      recommended_offer: z.string().optional(),
      pricing_model: z.string().optional(),
      grade: z.enum(['A', 'B', 'C', 'D']).optional(),
      expected_speed_to_revenue_days: z.number().int().positive().optional(),
      attribution_requirements: z.string().optional(),
      payment_risk: risk.optional(),
      margin_risk: risk.optional(),
      outreach_draft: z.string().optional(),
      external_id: z.string().optional(),
    })
    .strict(),
}).strict();

test('grades map scores and probabilities to Daily Command grades', () => {
  assert.equal(gradeFromScore(85), 'A');
  assert.equal(gradeFromScore(70), 'B');
  assert.equal(gradeFromScore(50), 'C');
  assert.equal(gradeFromScore(10), 'D');
  assert.equal(gradeFromProbability(0.75), 'A');
  assert.equal(gradeFromProbability(0.45), 'B');
  assert.equal(gradeFromProbability(0.25), 'C');
  assert.equal(gradeFromProbability(0), 'D');
});

test('scan without a store emits real seed revenue plays that satisfy the Daily Command contract', async () => {
  const result = await runDailyCommandScan({ store: null, loadSeed, limit: 50, minScore: 0 });
  assert.equal(result.ok, true);
  assert.equal(result.status, 'completed');
  assert.equal(result.sources.revenue_play_source, 'seed_catalog');
  assert.ok(result.event_count > 0);
  assert.equal(result.events.length, result.event_count);
  const seedIds = new Set(loadSeed().map((p) => 'revenue-os:play:' + p.recordId));
  for (const event of result.events) {
    DailyCommandOpportunity.parse(event);
    assert.equal(event.event_type, EVENT_TYPE);
    assert.equal(event.idempotency_key, event.data.external_id);
    assert.ok(seedIds.has(event.data.external_id), 'event must come from the committed catalog');
    for (const value of Object.values(event.data)) assert.notEqual(value, null);
  }
});

test('ranking honours min score, limit, status, and descending score order', () => {
  const plays = loadSeed();
  const ranked = rankRevenuePlays(plays, { minScore: 50, limit: 5 });
  assert.ok(ranked.length <= 5);
  for (let i = 1; i < ranked.length; i += 1) assert.ok(ranked[i - 1].overallScore >= ranked[i].overallScore);
  assert.ok(ranked.length > 0);
  for (const play of ranked) assert.ok(play.overallScore >= 50);
  const paused = plays.map((p) => ({ ...p, status: 'PAUSED' }));
  assert.equal(rankRevenuePlays(paused, { minScore: 0, limit: 50 }).length, 0);
});

test('limit and min score are clamped', async () => {
  const result = await runDailyCommandScan({ store: null, loadSeed, limit: 999, minScore: -5 });
  assert.equal(result.limit, 50);
  assert.equal(result.min_score, 0);
  assert.ok(result.events.length <= 50);
});

test('pipeline opportunities come first, join company/play, and omit empty fields', async () => {
  const opp = {
    _id: 'opp-1',
    title: 'Turnover vendor agreement',
    stage: 'Proposal',
    companyId: 'co-1',
    revenuePlayId: 'rp-1',
    estimatedValue: 4200,
    recurringMonthlyValue: 600,
    probability: 0.5,
    nextAction: 'Send proposal follow-up',
  };
  const store = {
    activePipelineOpportunities: async () => [opp],
    companiesByIds: async (ids) => {
      assert.deepEqual(ids, ['co-1']);
      return [{ _id: 'co-1', displayName: 'Desert Ridge Property Group', website: 'https://desertridge.test', locations: [{ city: 'Phoenix', state: 'AZ' }] }];
    },
    revenuePlaysByIds: async () => [{ _id: 'rp-1', lane: 'Property Services', revenuePlayName: 'Turnover Support', painSolved: 'Slow turnovers', timeToRevenueDays: 14 }],
    scannableRevenuePlays: async () => [],
  };
  const result = await runDailyCommandScan({ store, loadSeed, limit: 3, minScore: 0 });
  assert.equal(result.sources.pipeline_opportunities, 1);
  assert.equal(result.events.length, 3);
  const first = result.events[0];
  DailyCommandOpportunity.parse(first);
  assert.equal(first.data.external_id, 'revenue-os:opportunity:opp-1');
  assert.equal(first.data.company, 'Desert Ridge Property Group');
  assert.equal(first.data.location, 'Phoenix, AZ');
  assert.equal(first.data.grade, 'B');
  assert.equal(first.data.expected_speed_to_revenue_days, 14);
  assert.match(first.data.pricing_model, /\/month recurring/);

  const bare = pipelineOpportunityToEvent({ _id: 'opp-2', title: 'Bare', stage: 'Research', probability: 0 }, undefined, undefined);
  DailyCommandOpportunity.parse(bare);
  assert.equal('source_url' in bare.data, false);
  assert.equal('pricing_model' in bare.data, false);
});

test('store failure falls back to the committed catalog with a visible warning', async () => {
  const store = {
    activePipelineOpportunities: async () => {
      throw new Error('connection refused');
    },
  };
  const result = await runDailyCommandScan({ store, loadSeed, limit: 5 });
  assert.equal(result.ok, true);
  assert.equal(result.sources.revenue_play_source, 'seed_catalog');
  assert.match(result.warnings.join(' '), /connection refused/);
  assert.ok(result.events.length > 0);
});

test('Mongo-backed revenue plays take precedence over the seed catalog', async () => {
  const seed = loadSeed();
  const store = {
    activePipelineOpportunities: async () => [],
    companiesByIds: async () => [],
    revenuePlaysByIds: async () => [],
    scannableRevenuePlays: async () => [{ ...seed[0], status: 'ACTIVE' }],
  };
  const result = await runDailyCommandScan({ store, loadSeed, limit: 5, minScore: 0 });
  assert.equal(result.sources.revenue_play_source, 'mongodb');
  assert.equal(result.events.length, 1);
  assert.equal(result.events[0].data.external_id, 'revenue-os:play:' + seed[0].recordId);
});
