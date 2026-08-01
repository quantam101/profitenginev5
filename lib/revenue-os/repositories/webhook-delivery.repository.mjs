import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'webhook_deliveries';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ idempotencyKey: 1 }, { unique: true });
  await col.createIndex({ eventType: 1 });
  await col.createIndex({ status: 1 });
  await col.createIndex({ createdAt: -1 });
  indexesEnsured = true;
}

export async function createDelivery(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const normalized = {
    provider: String(doc.provider || 'zapier'),
    eventType: String(doc.eventType || 'unknown'),
    idempotencyKey: String(doc.idempotencyKey || new ObjectId().toHexString()),
    targetUrl: String(doc.targetUrl || ''),
    payload: doc.payload || {},
    signature: doc.signature ? String(doc.signature) : undefined,
    status: String(doc.status || 'PENDING'),
    attempts: Number(doc.attempts || 0),
    lastResponseStatus: doc.lastResponseStatus ? Number(doc.lastResponseStatus) : undefined,
    lastError: doc.lastError ? String(doc.lastError) : undefined,
    createdAt: now,
    updatedAt: now,
  };
  const result = await col.insertOne(normalized);
  return { _id: result.insertedId, ...normalized };
}

export async function updateDeliveryStatus(id, updates) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getDeliveryById(id);
  if (!existing) return null;
  const update = { ...updates, updatedAt: new Date() };
  await col.updateOne({ _id: existing._id }, { $set: update, $inc: { attempts: 1 } });
  return getDeliveryById(id);
}

export async function getDeliveryByIdempotencyKey(key) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  return col.findOne({ idempotencyKey: String(key) });
}

export async function getDeliveryById(id) {
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

/**
 * @param {Record<string, unknown>} [options]
 * @returns {Promise<{ records: any[]; total: number; page: number; limit: number }>}
 */
export async function findDeliveries(options = {}) {
  await ensureIndexes();
  const { provider, eventType, status, sortBy = 'createdAt', order = 'desc', page = 1, limit = 20 } = options;
  const col = await getCollection(COLLECTION);
  const filter = {};
  if (provider) filter.provider = provider;
  if (eventType) filter.eventType = eventType;
  if (status) filter.status = status;

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
