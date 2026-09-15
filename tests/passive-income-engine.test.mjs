import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildSupervisorPlan,
  defaultLaneScores,
  evaluateActionGate,
  evaluatePlatformGate,
  getPassiveIncomeConfig,
  runPassiveIncomeCycle,
  collectRssSources,
  scoreOpportunity,
} from '../lib/revenue-os/passive-income-engine.mjs';

const fakeAI = async ({ task, prompt }) => {
  const payloads = {
    offer_optimization: {
      title: 'Network Troubleshooting Field Guide', buyer: 'small IT teams', painful_problem: 'slow diagnosis', promise: 'faster triage',
      five_chapter_outline: ['A','B','C','D','E'], code_bundle_manifest: ['diag.ps1'], quality_checks: ['lint'], seo_title: 'Network Troubleshooting Guide',
      seo_description: 'Practical field guide', keywords: ['network'], suggested_price_usd: 19, storefront_copy: 'Resolve incidents faster.'
    },
    workflow_optimization: { concepts: [{ concept_id: 'c1', title: 'Abstract Network Flow', keywords: Array(30).fill('network') }] },
    summarization: { subject: 'Weekly AI Ops Brief', preheader: 'Key updates', lead: 'Summary', briefing_items: [], implications: [], action_items: [], affiliate_disclosure: 'Some links may be affiliate links.', seo_title: 'AI Ops Brief', seo_description: 'Weekly operations briefing' },
  };
  const payload = task === 'workflow_optimization' && String(prompt).includes('Technical Product Build Agent') ? { chapters: [{ title: 'A', typst_body: 'Body' }], code_files: [{ path: 'diag.ps1', language: 'powershell', content: 'Write-Output ok' }], readme: 'Use safely', validation_checklist: ['lint'], source_verification_queue: [] } : payloads[task];
  return { ok: true, provider: 'test', costUsd: 0, fallbackUsed: false, text: JSON.stringify(payload) };
};

test('technical products rank first in the default zero-upfront portfolio', () => {
  const scores = defaultLaneScores();
  assert.equal(scores[0].agentId, 'technical_product');
  assert.ok(scores[0].score >= scores[1].score);
});

test('opportunity score penalizes risk and variable cost', () => {
  const lowRisk = scoreOpportunity({ demand: 90, buyerIntent: 90, proof: 90, reuse: 90, automation: 90, margin: 90, speedToCash: 90, competition: 20, complianceRisk: 10, variableCost: 0 });
  const highRisk = scoreOpportunity({ demand: 90, buyerIntent: 90, proof: 90, reuse: 90, automation: 90, margin: 90, speedToCash: 90, competition: 90, complianceRisk: 90, variableCost: 90 });
  assert.ok(lowRisk > highRisk);
});

test('Shutterstock blocks AI-generated contributor submissions', () => {
  const gate = evaluatePlatformGate('shutterstock', { aiGenerated: true }, {});
  assert.equal(gate.allowed, false);
  assert.equal(gate.mode, 'blocked');
});

test('Adobe Stock requires generative AI disclosure and quality gate', () => {
  assert.equal(evaluatePlatformGate('adobe_stock', { aiGenerated: true, aiDisclosure: false, qualityScore: 95 }, {}).allowed, false);
  assert.equal(evaluatePlatformGate('adobe_stock', { aiGenerated: true, aiDisclosure: true, qualityScore: 95, containsThirdPartyIp: false }, {}).allowed, true);
});

test('Beehiiv API publication requires eligible plan plus credentials', () => {
  const handoff = evaluatePlatformGate('beehiiv', {}, { BEEHIIV_PLAN: 'scale' });
  assert.equal(handoff.mode, 'reviewed_handoff');
  const api = evaluatePlatformGate('beehiiv', {}, { BEEHIIV_PLAN: 'max', BEEHIIV_API_KEY: 'x', BEEHIIV_PUBLICATION_ID: 'pub_x' });
  assert.equal(api.mode, 'api');
});

test('external writes default to off and high-risk actions are always blocked', () => {
  const config = getPassiveIncomeConfig({});
  assert.equal(config.explicitExternalWrites, false);
  assert.equal(evaluateActionGate('external_write', config).allowed, false);
  assert.equal(evaluateActionGate('self_modify_production_code', config).allowed, false);
});

test('supervisor plan brands bounded learning and preserves zero-spend default', () => {
  const plan = buildSupervisorPlan({}, {});
  assert.equal(plan.config.zeroSpend, true);
  assert.equal(plan.learning.brand, 'Lifelong Catch and Correct');
  assert.equal(plan.learning.sourceCodeMutation, 'pull_request_only_after_tests');
});

test('cycle runs the selected profitable agents and produces review queue without write authorization', async () => {
  const result = await runPassiveIncomeCycle({ publish: true, sources: [{ url: 'https://a.example', title: 'A' }, { url: 'https://b.example', title: 'B' }] }, { routeAI: fakeAI, env: {} });
  assert.equal(result.ok, true);
  assert.ok(result.results.length >= 2);
  assert.equal(result.metrics.externalActions, 0);
  assert.equal(result.metrics.aiCostUsd, 0);
  assert.ok(result.reviewQueue.length >= 1);
});

test('RSS collector deduplicates items and strips markup', async () => {
  const xml = `<?xml version="1.0"?><rss><channel><item><title><![CDATA[AI <b>Update</b>]]></title><link>https://example.com/a</link><description><![CDATA[<p>Useful news</p>]]></description></item><item><title>AI Update</title><link>https://example.com/a</link><description>duplicate</description></item></channel></rss>`;
  const fakeFetch = async () => ({ ok: true, text: async () => xml });
  const result = await collectRssSources(['https://feed.example/rss'], { fetchImpl: fakeFetch });
  assert.equal(result.ok, true);
  assert.equal(result.sources.length, 1);
  assert.equal(result.sources[0].title, 'AI Update');
  assert.equal(result.sources[0].summary, 'Useful news');
});
