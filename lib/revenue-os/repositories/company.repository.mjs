import { getCollection } from '../../mongodb.mjs';
import { ObjectId } from 'mongodb';

const COLLECTION = 'companies';

let indexesEnsured = false;

export async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ duplicateKey: 1 });
  await col.createIndex({ domain: 1 });
  await col.createIndex({ 'locations.zipCode': 1 });
  try {
    await col.createIndex({ displayName: 'text', legalName: 'text' });
  } catch (err) {
    console.warn('[company.repository] text index warning:', err.message);
  }
  indexesEnsured = true;
}

export function normalizeDomain(website) {
  if (!website) return '';
  try {
    const url = new URL(website.startsWith('http') ? website : `https://${website}`);
    let host = url.hostname.toLowerCase().replace(/^www\./, '');
    return host;
  } catch {
    return String(website).toLowerCase().trim().replace(/^www\./, '');
  }
}

export function normalizeCompanyName(name) {
  return String(name || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .trim();
}

export function buildDuplicateKey(company) {
  const domain = normalizeDomain(company.website || company.domain);
  if (domain) return `domain:${domain}`;
  const name = normalizeCompanyName(company.legalName || company.displayName);
  const zip = String(company.locations?.[0]?.zipCode || '');
  return `name:${name}|zip:${zip}`;
}

export async function findCompanies(options = {}) {
  await ensureIndexes();
  const {
    industry,
    companyType,
    search,
    qualificationStatus,
    sortBy = 'createdAt',
    order = 'desc',
    page = 1,
    limit = 20,
  } = options;

  const col = await getCollection(COLLECTION);
  const filter = {};
  if (industry) filter.industry = industry;
  if (companyType) filter.companyType = companyType;
  if (qualificationStatus) filter.qualificationStatus = qualificationStatus;
  if (search) {
    const escaped = escapeRegex(search);
    filter.$or = [
      { displayName: { $regex: escaped, $options: 'i' } },
      { legalName: { $regex: escaped, $options: 'i' } },
      { industry: { $regex: escaped, $options: 'i' } },
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

export async function getCompanyById(id) {
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

export async function getCompanyByDuplicateKey(key) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  return col.findOne({ duplicateKey: key });
}

export async function createCompany(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const now = new Date();
  const normalized = normalizeCompany(doc, now);
  const result = await col.insertOne(normalized);
  return { _id: result.insertedId, ...normalized };
}

export async function updateCompany(id, updates) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const existing = await getCompanyById(id);
  if (!existing) return null;

  const merged = { ...existing, ...updates };
  const normalized = normalizeCompany(merged, existing.createdAt || new Date());
  const { _id, ...setDoc } = normalized;

  await col.updateOne({ _id: existing._id }, { $set: setDoc });
  return getCompanyById(id);
}

function normalizeCompany(doc, createdAt, updatedAt = new Date()) {
  const locations = Array.isArray(doc.locations) ? doc.locations : [];
  const serviceLanes = Array.isArray(doc.serviceLanes) ? doc.serviceLanes : [];
  const company = {
    legalName: String(doc.legalName || ''),
    displayName: String(doc.displayName || doc.legalName || ''),
    website: doc.website ? String(doc.website) : undefined,
    domain: doc.domain ? String(doc.domain) : normalizeDomain(doc.website),
    industry: String(doc.industry || ''),
    companyType: String(doc.companyType || ''),
    locations: locations.map((loc) => ({
      street: loc.street ? String(loc.street) : undefined,
      city: loc.city ? String(loc.city) : undefined,
      state: loc.state ? String(loc.state) : undefined,
      zipCode: loc.zipCode ? String(loc.zipCode) : undefined,
      country: loc.country ? String(loc.country) : undefined,
      coordinates: loc.coordinates || undefined,
    })),
    serviceLanes: serviceLanes.map(String),
    source: String(doc.source || 'manual'),
    qualificationStatus: String(doc.qualificationStatus || 'Prospect'),
    createdAt: createdAt ? new Date(createdAt) : new Date(),
    updatedAt: new Date(updatedAt),
  };
  company.duplicateKey = buildDuplicateKey(company);
  return company;
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
