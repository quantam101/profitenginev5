import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'revenue_plays';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ recordId: 1 }, { unique: true });
  await col.createIndex({ overallScore: -1 });
  await col.createIndex({ lane: 1, location: 1 });
  await col.createIndex({ status: 1, nextFollowUpDate: 1 });
  try {
    await col.createIndex(
      { revenuePlayName: 'text', painSolved: 'text', notes: 'text' },
      { name: 'revenue_plays_text_index' }
    );
  } catch (err) {
    console.warn('[revenue-play.repository] text index creation warning:', err.message);
  }
  indexesEnsured = true;
}

export async function countRevenuePlays(filter = {}) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  return col.countDocuments(filter);
}

export async function findRevenuePlays(options = {}) {
  await ensureIndexes();
  const {
    lane,
    buyerType,
    location,
    status,
    minScore,
    search,
    sortBy = 'overallScore',
    order = 'desc',
    page = 1,
    limit = 20,
  } = options;

  const col = await getCollection(COLLECTION);
  const filter = {};
  if (lane) filter.lane = lane;
  if (buyerType) filter.buyerType = buyerType;
  if (location) filter.location = { $regex: location, $options: 'i' };
  if (status) filter.status = status;
  if (typeof minScore === 'number') filter.overallScore = { $gte: minScore };

  if (search) {
    const textExists = await indexExists(col, 'revenue_plays_text_index');
    if (textExists) {
      filter.$text = { $search: search };
    } else {
      const regex = { $regex: escapeRegex(search), $options: 'i' };
      filter.$or = [
        { revenuePlayName: regex },
        { painSolved: regex },
        { notes: regex },
        { buyerType: regex },
      ];
    }
  }

  const sort = {};
  if (search && filter.$text) {
    sort.score = { $meta: 'textScore' };
  } else {
    sort[sortBy] = order === 'asc' ? 1 : -1;
  }

  const skip = (Math.max(1, Number(page)) - 1) * Number(limit);
  const take = Math.max(1, Math.min(100, Number(limit)));

  const [records, total] = await Promise.all([
    col.find(filter).sort(sort).skip(skip).limit(take).toArray(),
    col.countDocuments(filter),
  ]);

  return { records, total, page, limit: take };
}

export async function getRevenuePlayByRecordId(recordId) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  return col.findOne({ recordId });
}

export async function getRevenuePlayById(id) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  let query = id;
  try {
    query = new ObjectId(id);
  } catch {
    query = id;
  }
  return col.findOne({ _id: query });
}

export async function upsertRevenuePlay(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const update = { ...doc, updatedAt: now };
  if (!update.createdAt) update.createdAt = now;
  const result = await col.updateOne(
    { recordId: doc.recordId },
    { $set: update, $setOnInsert: { createdAt: now } },
    { upsert: true }
  );
  return {
    upsertedId: result.upsertedId,
    modifiedCount: result.modifiedCount,
    matchedCount: result.matchedCount,
  };
}

async function indexExists(col, name) {
  const indexes = await col.indexes();
  return indexes.some((idx) => idx.name === name);
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
