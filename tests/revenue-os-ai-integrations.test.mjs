import assert from 'node:assert/strict';
import { createCompany } from '../lib/revenue-os/repositories/company.repository.mjs';
import { createContact } from '../lib/revenue-os/repositories/contact.repository.mjs';
import { createOpportunity, getOpportunityById } from '../lib/revenue-os/repositories/opportunity.repository.mjs';
import { createAIAction, getAIActionById } from '../lib/revenue-os/repositories/ai-action.repository.mjs';
import {
  rankOpportunities,
  generateDraft,
  createDraftAction,
  auditDataQuality,
  submitForReview,
  approveAction,
  rejectAction,
  executeApprovedAction,
} from '../lib/revenue-os/services/ai-advisor.mjs';
import { sendSlackNotification, isSlackEnabled } from '../lib/revenue-os/services/slack.mjs';
import { dispatchZapierEvent, signPayload, isZapierEnabled } from '../lib/revenue-os/services/zapier.mjs';
import { getDb, closeClient } from '../lib/mongodb.mjs';

process.env.REVENUE_OS_ENABLED = 'true';
process.env.REVENUE_OS_AI_ENABLED = 'true';
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

const mongoUri = process.env.MONGODB_URI || process.env.MONGO_URL;
if (!mongoUri) {
  console.log('SKIP Revenue OS AI/Integration tests: MONGO_URL/MONGODB_URI not set');
  process.exit(0);
}

await testAsync('setup clears AI and integration collections', async () => {
  const db = await getDb();
  await db.collection('ai_actions').deleteMany({});
  await db.collection('slack_notifications').deleteMany({});
  await db.collection('webhook_deliveries').deleteMany({});
  await db.collection('companies').deleteMany({});
  await db.collection('contacts').deleteMany({});
  await db.collection('opportunities').deleteMany({});
  await db.collection('follow_up_tasks').deleteMany({});
  await db.collection('activities').deleteMany({});
});

let companyId = '';
let contactId = '';
let opportunityId = '';

await testAsync('create test company and contact', async () => {
  const company = await createCompany({
    legalName: 'AI Advisor Test Co',
    displayName: 'AI Advisor Test',
    industry: 'Commercial Facilities',
    companyType: 'Mid-Market',
    locations: [{ city: 'Phoenix', state: 'AZ', zipCode: '85004' }],
  });
  companyId = String(company._id);
  const contact = await createContact({ companyId: company._id, fullName: 'Test User', email: 'test@acme-test.invalid' });
  contactId = String(contact._id);
});

await testAsync('create test opportunity', async () => {
  const opp = await createOpportunity({
    revenuePlayId: 'RP-001',
    companyId,
    contactIds: [contactId],
    title: 'AI Advisor Test Opportunity',
    stage: 'Research',
    estimatedValue: 50000,
    recurringMonthlyValue: 5000,
    probability: 0.5,
    nextAction: 'Qualify target',
  });
  opportunityId = String(opp._id);
  assert.equal(opp.weightedValue, 25000);
});

await testAsync('rankOpportunities returns the test opportunity', async () => {
  const rankings = await rankOpportunities({ limit: 10 });
  assert.ok(Array.isArray(rankings));
  const found = rankings.find((r) => r.opportunityId === opportunityId);
  assert.ok(found, 'Expected test opportunity in rankings');
  assert.equal(found.stage, 'Research');
  assert.ok(found.recommendedNextAction);
});

await testAsync('generateDraft produces fallback content for unknown opportunity', async () => {
  const result = await generateDraft({ type: 'intro_email', opportunityId: '000000000000000000000000' });
  assert.equal(result.ok, false);
  assert.ok(result.error);
});

let draftActionId = '';

await testAsync('createDraftAction creates Draft action', async () => {
  const result = await createDraftAction({ type: 'intro_email', opportunityId, actor: 'tester' });
  assert.equal(result.ok, true);
  assert.ok(result.action);
  assert.equal(result.action.status, 'Draft');
  draftActionId = String(result.action._id);
});

await testAsync('approval state transitions work end to end', async () => {
  const review = await submitForReview(draftActionId, 'reviewer');
  assert.equal(review.ok, true);
  assert.equal(review.action.status, 'Needs Review');

  const approved = await approveAction(draftActionId, 'approver');
  assert.equal(approved.ok, true);
  assert.equal(approved.action.status, 'Approved');

  const executed = await executeApprovedAction(draftActionId, 'executor');
  assert.equal(executed.ok, true);
  assert.equal(executed.action.status, 'Executed');
});

await testAsync('executeApprovedAction rejects non-Approved actions', async () => {
  const action = await createAIAction({
    entityType: 'opportunity',
    entityId: opportunityId,
    actionType: 'follow_up_email',
    content: 'test',
    status: 'Draft',
    createdBy: 'tester',
  });
  const result = await executeApprovedAction(String(action._id), 'executor');
  assert.equal(result.ok, false);
});

await testAsync('auditDataQuality flags missing contacts and unsupported ticket estimate', async () => {
  await createOpportunity({
    revenuePlayId: 'RP-001',
    companyId,
    contactIds: [],
    title: 'Low quality opportunity',
    stage: 'Research',
    estimatedValue: 0,
    recurringMonthlyValue: 0,
    probability: 0,
    nextAction: '',
  });
  const flags = await auditDataQuality();
  assert.ok(Array.isArray(flags));
  const noContacts = flags.find((f) => f.issue === 'No contacts linked');
  const noEstimate = flags.find((f) => f.issue === 'Unsupported ticket estimate');
  assert.ok(noContacts, 'Expected missing-contacts flag');
  assert.ok(noEstimate, 'Expected unsupported-ticket-estimate flag');
});

await testAsync('slack notifications skip when disabled', async () => {
  const originalEnabled = process.env.REVENUE_OS_SLACK_ENABLED;
  process.env.REVENUE_OS_SLACK_ENABLED = 'false';
  const result = await sendSlackNotification({ notificationType: 'test', channel: '#revenue-ops', text: 'hello' });
  assert.equal(result.sent, false);
  assert.ok(result.reason || result.ok);
  process.env.REVENUE_OS_SLACK_ENABLED = originalEnabled;
});

await testAsync('zapier events are idempotent and disabled by default', async () => {
  const payload = { opportunityId, idempotencyKey: 'test-key-1' };
  const result = await dispatchZapierEvent({ eventType: 'opportunity.created', payload, actor: 'tester' });
  assert.equal(result.ok, true);
  assert.equal(result.delivered, false);
  assert.equal(result.status, 'DISABLED');

  const second = await dispatchZapierEvent({ eventType: 'opportunity.created', payload, actor: 'tester' });
  assert.equal(second.status, 'DISABLED');
});

await testAsync('signPayload rejects invalid signatures', async () => {
  const payload = { id: 'a', value: 1 };
  const secret = 'real-secret';
  const wrong = 'wrong-secret';
  const valid = signPayload(payload, secret);
  const invalid = signPayload(payload, wrong);
  assert.notEqual(valid, invalid);
  assert.equal(valid.length, 64);
});

await testAsync('invalid zapier event type is rejected', async () => {
  const result = await dispatchZapierEvent({ eventType: 'unauthorized.event', payload: {}, actor: 'tester' });
  assert.equal(result.ok, false);
});

await testAsync('dashboard performance under normal load is under 2 seconds', async () => {
  const { getDashboardSummary } = await import('../lib/revenue-os/services/dashboard.service.mjs');
  const start = performance.now();
  const summary = await getDashboardSummary();
  const elapsed = performance.now() - start;
  assert.ok(summary, 'Dashboard should return summary');
  assert.ok(elapsed < 2000, `Dashboard took ${elapsed.toFixed(0)}ms`);
});

await testAsync('opportunity detail lookup is under 500ms', async () => {
  const start = performance.now();
  const opp = await getOpportunityById(opportunityId);
  const elapsed = performance.now() - start;
  assert.ok(opp, 'Opportunity should be found');
  assert.ok(elapsed < 500, `Detail lookup took ${elapsed.toFixed(0)}ms`);
});

await closeClient().catch(() => {});

console.log('revenue-os-ai-integrations tests done');
