import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'follow_up_tasks';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ entityType: 1, entityId: 1 });
  await col.createIndex({ status: 1, dueDate: 1 });
  await col.createIndex({ assignedTo: 1, dueDate: 1 });
  await col.createIndex({ dueDate: 1 });
  indexesEnsured = true;
}

export async function createFollowUp(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const normalized = {
    entityType: String(doc.entityType || 'opportunity'),
    entityId: toObjectId(doc.entityId),
    type: String(doc.type || 'general'),
    summary: String(doc.summary || ''),
    dueDate: new Date(doc.dueDate || now),
    status: doc.status || 'OPEN',
    assignedTo: doc.assignedTo ? String(doc.assignedTo) : undefined,
    priority: ['LOW', 'MEDIUM', 'HIGH'].includes(doc.priority) ? doc.priority : 'MEDIUM',
    completedAt: doc.completedAt ? new Date(doc.completedAt) : undefined,
    createdAt: now,
    updatedAt: now,
  };
  const result = await col.insertOne(normalized);
  return { _id: result.insertedId, ...normalized };
}

export async function findFollowUps(options = {}) {
  await ensureIndexes();
  const {
    entityType,
    entityId,
    status,
    assignedTo,
    dueBefore,
    dueAfter,
    sortBy = 'dueDate',
    order = 'asc',
    page = 1,
    limit = 20,
  } = options;

  const col = await getCollection(COLLECTION);
  const filter = {};
  if (entityType) filter.entityType = entityType;
  if (entityId) filter.entityId = toObjectId(entityId);
  if (status) filter.status = status;
  if (assignedTo) filter.assignedTo = assignedTo;
  if (dueBefore || dueAfter) {
    filter.dueDate = {};
    if (dueAfter) filter.dueDate.$gte = new Date(dueAfter);
    if (dueBefore) filter.dueDate.$lte = new Date(dueBefore);
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

export async function getFollowUpById(id) {
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

export async function completeFollowUp(id, actor) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getFollowUpById(id);
  if (!existing) return null;
  const now = new Date();
  const update = {
    status: 'COMPLETED',
    completedAt: now,
    updatedAt: now,
  };
  if (actor) update.completedBy = String(actor);
  await col.updateOne({ _id: existing._id }, { $set: update });
  return getFollowUpById(id);
}

export async function countOpenFollowUpsDueBy(date) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const due = date instanceof Date ? date : new Date(date || Date.now());
  const startOfDay = new Date(due.getFullYear(), due.getMonth(), due.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000 - 1);
  return col.countDocuments({
    status: 'OPEN',
    dueDate: { $gte: startOfDay, $lte: endOfDay },
  });
}

export async function countOpenFollowUpsDueBefore(date) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const due = date instanceof Date ? date : new Date(date || Date.now());
  return col.countDocuments({
    status: 'OPEN',
    dueDate: { $lte: due },
  });
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
