import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'activities';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ entityType: 1, entityId: 1 });
  await col.createIndex({ createdAt: -1 });
  await col.createIndex({ actor: 1, createdAt: -1 });
  indexesEnsured = true;
}

export async function createActivity({ entityType, entityId, actionType, actor, summary, metadata = {} }) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const doc = {
    entityType,
    entityId: toObjectId(entityId),
    actionType,
    actor,
    summary,
    metadata,
    createdAt: now,
  };
  const result = await col.insertOne(doc);
  return { _id: result.insertedId, ...doc };
}

export async function findActivities({ entityType, entityId, actor, limit = 50, page = 1 } = {}) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const filter = {};
  if (entityType) filter.entityType = entityType;
  if (entityId) filter.entityId = toObjectId(entityId);
  if (actor) filter.actor = actor;

  const take = Math.max(1, Math.min(100, Number(limit) || 50));
  const skip = (Math.max(1, Number(page) || 1) - 1) * take;

  const [records, total] = await Promise.all([
    col.find(filter).sort({ createdAt: -1 }).skip(skip).limit(take).toArray(),
    col.countDocuments(filter),
  ]);
  return { records, total, page: Number(page) || 1, limit: take };
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
