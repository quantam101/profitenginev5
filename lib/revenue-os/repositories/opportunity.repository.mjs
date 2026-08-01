import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'opportunities';

let indexesEnsured = false;

export const OPPORTUNITY_STAGES = [
  'Research',
  'Qualified',
  'Approval Needed',
  'Outreach Approved',
  'Contacted',
  'Conversation',
  'Proposal',
  'Negotiation',
  'Won',
  'Lost',
  'On Hold',
];

const CLOSED_STAGES = new Set(['Won', 'Lost']);
const TERMINAL_STAGES = new Set(['Won', 'Lost', 'On Hold']);

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ revenuePlayId: 1 });
  await col.createIndex({ companyId: 1 });
  await col.createIndex({ contactIds: 1 });
  await col.createIndex({ stage: 1, nextFollowUpDate: 1 });
  await col.createIndex({ assignedTo: 1 });
  await col.createIndex({ createdAt: -1 });
  await col.createIndex({ updatedAt: -1 });
  try {
    await col.createIndex({ location: '2dsphere' });
  } catch (err) {
    console.warn('[opportunity.repository] 2dsphere index warning:', err.message);
  }
  indexesEnsured = true;
}

export function isActiveOpportunity(doc) {
  return doc && !CLOSED_STAGES.has(doc.stage);
}

export function isTerminalStage(stage) {
  return TERMINAL_STAGES.has(stage);
}

export function getNextStage(currentStage) {
  const idx = OPPORTUNITY_STAGES.indexOf(currentStage);
  if (idx === -1) return undefined;
  if (idx >= OPPORTUNITY_STAGES.length - 1) return undefined;
  if (isTerminalStage(currentStage)) return undefined;
  const next = OPPORTUNITY_STAGES[idx + 1];
  return isTerminalStage(next) && next !== currentStage ? undefined : next;
}

export async function findOpportunities(options = {}) {
  await ensureIndexes();
  const {
    stage,
    companyId,
    revenuePlayId,
    assignedTo,
    search,
    active,
    sortBy = 'createdAt',
    order = 'desc',
    page = 1,
    limit = 20,
  } = options;

  const col = await getCollection(COLLECTION);
  const filter = {};
  if (stage) filter.stage = stage;
  if (companyId) filter.companyId = toObjectId(companyId);
  if (revenuePlayId) filter.revenuePlayId = toObjectId(revenuePlayId);
  if (assignedTo) filter.assignedTo = assignedTo;
  if (active) filter.stage = { $nin: Array.from(CLOSED_STAGES) };
  if (search) {
    const escaped = escapeRegex(search);
    filter.$or = [
      { title: { $regex: escaped, $options: 'i' } },
      { nextAction: { $regex: escaped, $options: 'i' } },
    ];
  }

  const sort = {};
  sort[sortBy] = order === 'asc' ? 1 : -1;

  const requestedPage = Number(page);
  const requestedLimit = Number(limit);
  const currentPage = Number.isNaN(requestedPage) || requestedPage < 1 ? 1 : requestedPage;
  const take = Number.isNaN(requestedLimit) ? 20 : Math.max(1, Math.min(100, requestedLimit));
  const skip = (currentPage - 1) * take;

  const [records, total] = await Promise.all([
    col.find(filter).sort(sort).skip(skip).limit(take).toArray(),
    col.countDocuments(filter),
  ]);
  return { records, total, page: currentPage, limit: take };
}

export async function getOpportunityById(id) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  let query = id;
  try {
    query = new ObjectId(String(id));
  } catch {
    query = id;
  }
  return col.findOne({ _id: query });
}

export async function createOpportunity(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const normalized = normalizeOpportunity(doc, now);
  const result = await col.insertOne(normalized);
  return { _id: result.insertedId, ...normalized };
}

export async function updateOpportunity(id, updates) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getOpportunityById(id);
  if (!existing) return null;

  const now = new Date();
  const merged = { ...existing, ...updates };
  const normalized = normalizeOpportunity(merged, existing.createdAt || now, now);
  const { _id, ...setDoc } = normalized;

  await col.updateOne({ _id: existing._id }, { $set: setDoc });
  return getOpportunityById(id);
}

export async function updateOpportunityStage(id, stage) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getOpportunityById(id);
  if (!existing) return null;
  await col.updateOne(
    { _id: existing._id },
    { $set: { stage, updatedAt: new Date() } }
  );
  return getOpportunityById(id);
}

export async function countOpportunitiesByStage() {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const rows = await col
    .aggregate([{ $group: { _id: '$stage', count: { $sum: 1 } } }])
    .toArray();
  const result = {};
  for (const row of rows) result[row._id] = row.count;
  for (const stage of OPPORTUNITY_STAGES) {
    if (result[stage] === undefined) result[stage] = 0;
  }
  return result;
}

function normalizeOpportunity(doc, createdAt, updatedAt = new Date()) {
  const estimatedValue = Number(doc.estimatedValue) || 0;
  const probability = Number(doc.probability) || 0;
  const weightedValue = estimatedValue * probability;
  const recurringMonthlyValue = Number(doc.recurringMonthlyValue) || 0;

  return {
    revenuePlayId: toObjectId(doc.revenuePlayId),
    companyId: toObjectId(doc.companyId),
    contactIds: (doc.contactIds || []).map((c) => toObjectId(c)).filter(Boolean),
    title: String(doc.title || ''),
    stage: String(doc.stage || 'Research'),
    estimatedValue,
    recurringMonthlyValue,
    probability,
    weightedValue,
    location: doc.location || undefined,
    nextAction: String(doc.nextAction || ''),
    nextFollowUpDate: doc.nextFollowUpDate ? new Date(doc.nextFollowUpDate) : undefined,
    assignedTo: doc.assignedTo ? String(doc.assignedTo) : undefined,
    approvalStatus: String(doc.approvalStatus || 'Pending'),
    createdAt: createdAt ? new Date(createdAt) : new Date(),
    updatedAt: new Date(updatedAt),
  };
}

function toObjectId(value) {
  if (!value) return value;
  if (value instanceof ObjectId) return value;
  try {
    return new ObjectId(String(value));
  } catch {
    return value;
  }
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
