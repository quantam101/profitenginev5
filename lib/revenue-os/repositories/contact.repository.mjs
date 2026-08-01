import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'contacts';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ companyId: 1 });
  await col.createIndex({ email: 1 });
  await col.createIndex({ phone: 1 });
  await col.createIndex({ contactStatus: 1 });
  indexesEnsured = true;
}

export async function findContacts(options = {}) {
  await ensureIndexes();
  const {
    companyId,
    search,
    contactStatus,
    consentStatus,
    sortBy = 'createdAt',
    order = 'desc',
    page = 1,
    limit = 20,
  } = options;

  const col = await getCollection(COLLECTION);
  const filter = {};
  if (companyId) filter.companyId = toObjectId(companyId);
  if (contactStatus) filter.contactStatus = contactStatus;
  if (consentStatus) filter.consentStatus = consentStatus;
  if (search) {
    const escaped = escapeRegex(search);
    filter.$or = [
      { fullName: { $regex: escaped, $options: 'i' } },
      { email: { $regex: escaped, $options: 'i' } },
      { phone: { $regex: escaped, $options: 'i' } },
      { title: { $regex: escaped, $options: 'i' } },
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

export async function getContactById(id) {
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

export async function createContact(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const normalized = normalizeContact(doc, now);
  const result = await col.insertOne(normalized);
  return { _id: result.insertedId, ...normalized };
}

export async function updateContact(id, updates) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getContactById(id);
  if (!existing) return null;

  const merged = { ...existing, ...updates };
  const normalized = normalizeContact(merged, existing.createdAt || new Date());
  const { _id, ...setDoc } = normalized;

  await col.updateOne({ _id: existing._id }, { $set: setDoc });
  return getContactById(id);
}

function normalizeContact(doc, createdAt, updatedAt = new Date()) {
  return {
    companyId: toObjectId(doc.companyId),
    fullName: doc.fullName ? String(doc.fullName) : undefined,
    title: doc.title ? String(doc.title) : undefined,
    email: doc.email ? String(doc.email).toLowerCase().trim() : undefined,
    phone: doc.phone ? String(doc.phone) : undefined,
    preferredChannel: doc.preferredChannel ? String(doc.preferredChannel) : undefined,
    contactStatus: String(doc.contactStatus || 'Active'),
    consentStatus: String(doc.consentStatus || 'Unknown'),
    source: String(doc.source || 'manual'),
    lastVerifiedAt: doc.lastVerifiedAt ? new Date(doc.lastVerifiedAt) : undefined,
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
