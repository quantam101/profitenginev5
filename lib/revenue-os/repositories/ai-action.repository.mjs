import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'ai_actions';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ entityType: 1, entityId: 1 });
  await col.createIndex({ actionType: 1 });
  await col.createIndex({ status: 1 });
  await col.createIndex({ createdBy: 1 });
  await col.createIndex({ createdAt: -1 });
  await col.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 });
  indexesEnsured = true;
}

export async function createAIAction(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const normalized = {
    entityType: String(doc.entityType || 'system'),
    entityId: doc.entityId ? toObjectId(doc.entityId) : undefined,
    actionType: String(doc.actionType || 'intro_email'),
    content: String(doc.content || ''),
    status: String(doc.status || 'Draft'),
    metadata: doc.metadata || {},
    createdBy: String(doc.createdBy || 'system'),
    reviewedBy: doc.reviewedBy ? String(doc.reviewedBy) : undefined,
    reviewedAt: doc.reviewedAt ? new Date(doc.reviewedAt) : undefined,
    expiresAt: doc.expiresAt ? new Date(doc.expiresAt) : undefined,
    createdAt: now,
    updatedAt: now,
  };
  const result = await col.insertOne(normalized);
  return { _id: result.insertedId, ...normalized };
}

export async function getAIActionById(id) {
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

export async function updateAIActionStatus(id, status, reviewer) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getAIActionById(id);
  if (!existing) return null;
  const update = {
    status: String(status),
    updatedAt: new Date(),
  };
  if (reviewer) {
    update.reviewedBy = String(reviewer);
    update.reviewedAt = new Date();
  }
  await col.updateOne({ _id: existing._id }, { $set: update });
  return getAIActionById(id);
}

export async function findAIActions(options = {}) {
  await ensureIndexes();
  const { entityType, entityId, status, actionType, sortBy = 'createdAt', order = 'desc', page = 1, limit = 20 } = options;
  const col = await getCollection(COLLECTION);
  const filter = {};
  if (entityType) filter.entityType = entityType;
  if (entityId) filter.entityId = toObjectId(entityId);
  if (status) filter.status = status;
  if (actionType) filter.actionType = actionType;

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

export async function deleteExpiredActions(before = new Date()) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  return col.deleteMany({ expiresAt: { $lt: before } });
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
