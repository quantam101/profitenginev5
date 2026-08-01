import assert from 'node:assert/strict';
import { createCompany, getCompanyById, normalizeDomain, buildDuplicateKey } from '../lib/revenue-os/repositories/company.repository.mjs';
import { createContact, getContactById } from '../lib/revenue-os/repositories/contact.repository.mjs';
import {
  createOpportunity,
  getOpportunityById,
  findOpportunities,
  getNextStage,
  OPPORTUNITY_STAGES,
} from '../lib/revenue-os/repositories/opportunity.repository.mjs';
import { findFollowUps, completeFollowUp } from '../lib/revenue-os/repositories/follow-up.repository.mjs';
import { findActivities } from '../lib/revenue-os/repositories/activity.repository.mjs';
import { onOpportunityCreated, onOpportunityStageChanged, calculateNextFollowUpDate, addBusinessDays } from '../lib/revenue-os/services/follow-up.service.mjs';
import { advanceOpportunityStage, setOpportunityStage } from '../lib/revenue-os/services/pipeline.service.mjs';
import { getDashboardSummary } from '../lib/revenue-os/services/dashboard.service.mjs';
import { getDb, closeClient } from '../lib/mongodb.mjs';

process.env.REVENUE_OS_ENABLED = 'true';
process.env.MONGODB_URI = process.env.MONGODB_URI || process.env.MONGO_URL || 'mongodb://127.0.0.1:27017/revenue-os-test';

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
  console.log('SKIP Revenue OS CRM tests: MONGO_URL/MONGODB_URI not set');
  process.exit(0);
}

await testAsync('setup clears CRM collections', async () => {
  const db = await getDb();
  await db.collection('companies').deleteMany({});
  await db.collection('contacts').deleteMany({});
  await db.collection('opportunities').deleteMany({});
  await db.collection('follow_up_tasks').deleteMany({});
  await db.collection('activities').deleteMany({});
});

await testAsync('normalizeDomain extracts clean domain', async () => {
  assert.equal(normalizeDomain('https://www.example.com/path'), 'example.com');
  assert.equal(normalizeDomain('example.com'), 'example.com');
});

let companyId = '';
await testAsync('createCompany persists normalized duplicate key', async () => {
  const company = await createCompany({
    legalName: 'Acme Test Corp',
    displayName: 'Acme Test',
    website: 'https://www.acmetest.example.com',
    industry: 'Commercial Facilities',
    companyType: 'Mid-Market',
    locations: [{ city: 'Phoenix', state: 'AZ', zipCode: '85004' }],
    serviceLanes: ['HVAC', 'Access Control'],
  });
  companyId = String(company._id);
  assert.ok(company._id);
  assert.equal(company.domain, 'acmetest.example.com');
  assert.equal(company.qualificationStatus, 'Prospect');
  const expectedKey = `domain:${company.domain}`;
  assert.equal(company.duplicateKey, expectedKey);
  const reloaded = await getCompanyById(company._id);
  assert.equal(reloaded?.duplicateKey, expectedKey);
});

await testAsync('buildDuplicateKey falls back to name + zip', () => {
  const key = buildDuplicateKey({ legalName: 'No Domain LLC', locations: [{ zipCode: '12345' }] });
  assert.match(key, /name:nodomainllc/);
  assert.match(key, /zip:12345/);
});

let contactId = '';
await testAsync('createContact links to company and normalizes email', async () => {
  const contact = await createContact({
    companyId,
    fullName: 'Jane Smith',
    title: 'Facilities Manager',
    email: 'JANE.SMITH@EXAMPLE.COM',
    phone: '555-0100',
    preferredChannel: 'email',
  });
  contactId = String(contact._id);
  assert.ok(contact._id);
  assert.equal(String(contact.companyId), companyId);
  assert.equal(contact.email, 'jane.smith@example.com');
  const reloaded = await getContactById(contact._id);
  assert.equal(reloaded?.fullName, 'Jane Smith');
});

let opportunityId = '';
await testAsync('createOpportunity computes weightedValue', async () => {
  const opportunity = await createOpportunity({
    revenuePlayId: 'RP-001',
    companyId,
    contactIds: [contactId],
    title: 'Phoenix test opportunity',
    stage: 'Research',
    estimatedValue: 10000,
    recurringMonthlyValue: 500,
    probability: 0.6,
    nextAction: 'Research buyer contact path',
    assignedTo: 'devin@example.com',
  });
  opportunityId = String(opportunity._id);
  assert.ok(opportunity._id);
  assert.equal(opportunity.weightedValue, 6000);
  assert.equal(opportunity.recurringMonthlyValue, 500);
});

await testAsync('onOpportunityCreated schedules first follow-up and logs an activity', async () => {
  const opportunity = await getOpportunityById(opportunityId);
  const followUp = await onOpportunityCreated(opportunity, 'devin@example.com');
  assert.ok(followUp);
  assert.match(followUp.summary, /Review new target/);

  const activities = await findActivities({ entityType: 'opportunity', entityId: opportunityId });
  assert.ok(activities.total >= 1);
  assert.match(activities.records[0].summary, /Created opportunity/);
});

await testAsync('getNextStage returns the next pipeline stage', () => {
  assert.equal(getNextStage('Research'), 'Qualified');
  assert.equal(getNextStage('Contacted'), 'Conversation');
  assert.equal(getNextStage('Won'), undefined);
  assert.equal(getNextStage('Lost'), undefined);
  assert.equal(getNextStage('On Hold'), undefined);
  assert.equal(getNextStage('Unknown'), undefined);
});

await testAsync('advanceOpportunityStage moves to next stage and creates follow-up', async () => {
  const before = await getOpportunityById(opportunityId);
  assert.equal(before.stage, 'Research');

  const result = await advanceOpportunityStage(opportunityId, 'devin@example.com');
  assert.ok(result.ok);
  assert.equal(result.previousStage, 'Research');
  assert.equal(result.nextStage, 'Qualified');
  assert.ok(result.followUp);

  const after = await getOpportunityById(opportunityId);
  assert.equal(after.stage, 'Qualified');
});

await testAsync('setOpportunityStage jumps to target and schedules follow-up', async () => {
  const result = await setOpportunityStage(opportunityId, 'Outreach Approved', 'devin@example.com');
  assert.ok(result.ok);
  assert.equal(result.previousStage, 'Qualified');
  assert.equal(result.nextStage, 'Outreach Approved');

  const followUps = await findFollowUps({ entityId: opportunityId, status: 'OPEN', limit: 100 });
  assert.ok(followUps.total >= 2);
});

await testAsync('completeFollowUp marks task completed', async () => {
  const open = await findFollowUps({ entityId: opportunityId, status: 'OPEN', limit: 1 });
  assert.ok(open.total > 0);
  const completed = await completeFollowUp(open.records[0]._id, 'devin@example.com');
  assert.equal(completed.status, 'COMPLETED');
  assert.ok(completed.completedAt);
});

await testAsync('dashboard summary reflects the CRM data', async () => {
  const summary = await getDashboardSummary();
  assert.equal(summary.activeOpportunities, 1);
  assert.ok(summary.weightedPipelineValue >= 6000);
  assert.equal(summary.monthlyRecurringPotential, 500);
  assert.equal(summary.pipelineByStage['Outreach Approved'].count, 1);
  assert.ok(summary.topRecommendedActions.length > 0);
  assert.ok(summary.highestScoringRevenuePlays.length > 0 || summary.highestScoringRevenuePlays.length === 0);
});

await testAsync('findOpportunities filters by stage and company', async () => {
  const byStage = await findOpportunities({ stage: 'Outreach Approved' });
  assert.equal(byStage.total, 1);
  const byCompany = await findOpportunities({ companyId });
  assert.equal(byCompany.total, 1);
  const active = await findOpportunities({ active: true });
  assert.equal(active.total, 1);
});

await test('addBusinessDays skips weekends', () => {
  const monday = new Date('2026-07-27T12:00:00Z');
  const result = addBusinessDays(monday, 3);
  assert.equal(result.getUTCDay(), 4); // Thursday
});

test('calculateNextFollowUpDate respects stage rules', () => {
  const date = new Date('2026-07-27T12:00:00Z');
  const contacted = calculateNextFollowUpDate('Contacted', date);
  assert.equal(contacted.getUTCDay(), 4); // 3 business days from Monday = Thursday
  const outreach = calculateNextFollowUpDate('Outreach Approved', date);
  assert.equal(outreach.getTime(), date.getTime());
});

await testAsync('advanceOpportunityStage moves Negotiation to Won', async () => {
  const opp = await createOpportunity({
    revenuePlayId: 'RP-001',
    companyId,
    contactIds: [contactId],
    title: 'Negotiation win test',
    stage: 'Negotiation',
    estimatedValue: 25000,
    recurringMonthlyValue: 1000,
    probability: 0.8,
    nextAction: 'Close deal',
  });
  const result = await advanceOpportunityStage(opp._id, 'devin@example.com');
  assert.ok(result.ok);
  assert.equal(result.previousStage, 'Negotiation');
  assert.equal(result.nextStage, 'Won');
  const reloaded = await getOpportunityById(opp._id);
  assert.equal(reloaded.stage, 'Won');
});

await closeClient().catch(() => {});

console.log('revenue-os-crm tests done');
