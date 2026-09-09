import { getCollection } from '../mongodb.mjs';
import { normalizeEmail, sha256, slugify } from './core.mjs';

const SUBSCRIBERS = 'newsletter_subscribers';
const ISSUES = 'newsletter_issues';
const EVENTS = 'newsletter_events';
let indexesEnsured = false;

async function ensureIndexes() {
  if (indexesEnsured) return;
  const [subscribers, issues, events] = await Promise.all([
    getCollection(SUBSCRIBERS),
    getCollection(ISSUES),
    getCollection(EVENTS),
  ]);
  await Promise.all([
    subscribers.createIndex({ email: 1 }, { unique: true }),
    subscribers.createIndex({ status: 1, createdAt: -1 }),
    issues.createIndex({ slug: 1 }, { unique: true }),
    issues.createIndex({ status: 1, publishedAt: -1 }),
    events.createIndex({ type: 1, createdAt: -1 }),
    events.createIndex({ subscriberId: 1, createdAt: -1 }),
    events.createIndex({ issueId: 1, createdAt: -1 }),
  ]);
  indexesEnsured = true;
}

export async function upsertSubscriber(input) {
  await ensureIndexes();
  const col = await getCollection(SUBSCRIBERS);
  const email = normalizeEmail(input.email);
  const now = new Date();
  const existing = await col.findOne({ email });
  const status = existing?.status === 'active' ? 'active' : 'pending';
  const setDoc = {
    email,
    status,
    source: String(input.source || existing?.source || 'newsletter-page'),
    utmSource: input.utmSource ? String(input.utmSource) : existing?.utmSource,
    utmMedium: input.utmMedium ? String(input.utmMedium) : existing?.utmMedium,
    utmCampaign: input.utmCampaign ? String(input.utmCampaign) : existing?.utmCampaign,
    consentAt: input.consentAt ? new Date(input.consentAt) : existing?.consentAt || now,
    updatedAt: now,
    confirmationTokenHash: status === 'active' ? existing?.confirmationTokenHash : input.confirmationTokenHash,
    confirmationExpiresAt: status === 'active' ? existing?.confirmationExpiresAt : input.confirmationExpiresAt,
    unsubscribeToken: existing?.unsubscribeToken || input.unsubscribeToken,
  };
  const result = await col.findOneAndUpdate(
    { email },
    { $set: setDoc, $setOnInsert: { createdAt: now } },
    { upsert: true, returnDocument: 'after' },
  );
  const subscriber = result?.value || result;
  await recordEvent({
    type: existing ? 'subscriber_refreshed' : 'subscriber_captured',
    subscriberId: subscriber?._id,
    metadata: { source: setDoc.source },
  });
  return subscriber;
}

export async function confirmSubscriber(token) {
  await ensureIndexes();
  const col = await getCollection(SUBSCRIBERS);
  const now = new Date();
  const tokenHash = sha256(token);
  const result = await col.findOneAndUpdate(
    {
      confirmationTokenHash: tokenHash,
      confirmationExpiresAt: { $gt: now },
      status: { $ne: 'unsubscribed' },
    },
    {
      $set: { status: 'active', confirmedAt: now, updatedAt: now },
      $unset: { confirmationTokenHash: '', confirmationExpiresAt: '' },
    },
    { returnDocument: 'after' },
  );
  const subscriber = result?.value || result;
  if (subscriber?._id) {
    await recordEvent({ type: 'subscriber_confirmed', subscriberId: subscriber._id });
  }
  return subscriber || null;
}

export async function unsubscribeSubscriber(token) {
  await ensureIndexes();
  const col = await getCollection(SUBSCRIBERS);
  const subscriber = await col.findOne({ unsubscribeToken: String(token) });
  if (!subscriber) return null;
  const now = new Date();
  await col.updateOne(
    { _id: subscriber._id },
    { $set: { status: 'unsubscribed', unsubscribedAt: now, updatedAt: now } },
  );
  await recordEvent({ type: 'subscriber_unsubscribed', subscriberId: subscriber._id });
  return { ...subscriber, status: 'unsubscribed', unsubscribedAt: now, updatedAt: now };
}

export async function listActiveSubscribers(limit = 5000) {
  await ensureIndexes();
  const col = await getCollection(SUBSCRIBERS);
  return col.find({ status: 'active' }).sort({ createdAt: 1 }).limit(Math.min(Math.max(Number(limit) || 5000, 1), 10000)).toArray();
}

export async function getSubscriberStats() {
  await ensureIndexes();
  const col = await getCollection(SUBSCRIBERS);
  const [total, active, pending, unsubscribed] = await Promise.all([
    col.countDocuments({}),
    col.countDocuments({ status: 'active' }),
    col.countDocuments({ status: 'pending' }),
    col.countDocuments({ status: 'unsubscribed' }),
  ]);
  return { total, active, pending, unsubscribed };
}

export async function upsertIssue(input) {
  await ensureIndexes();
  const col = await getCollection(ISSUES);
  const now = new Date();
  const slug = slugify(input.slug || input.title);
  const doc = {
    slug,
    title: String(input.title || ''),
    subject: String(input.subject || input.title || ''),
    excerpt: String(input.excerpt || ''),
    bodyHtml: String(input.bodyHtml || ''),
    ctaLabel: input.ctaLabel ? String(input.ctaLabel) : undefined,
    ctaUrl: input.ctaUrl ? String(input.ctaUrl) : undefined,
    status: String(input.status || 'draft'),
    monetization: input.monetization || {},
    updatedAt: now,
  };
  const result = await col.findOneAndUpdate(
    { slug },
    { $set: doc, $setOnInsert: { createdAt: now } },
    { upsert: true, returnDocument: 'after' },
  );
  return result?.value || result;
}

export async function getIssueBySlug(slug) {
  await ensureIndexes();
  const col = await getCollection(ISSUES);
  return col.findOne({ slug: slugify(slug) });
}

export async function listPublishedIssues(limit = 12) {
  await ensureIndexes();
  const col = await getCollection(ISSUES);
  return col.find({ status: 'published' }).sort({ publishedAt: -1 }).limit(Math.min(Math.max(Number(limit) || 12, 1), 100)).toArray();
}

export async function markIssuePublished(issueId, summary = {}) {
  await ensureIndexes();
  const col = await getCollection(ISSUES);
  const now = new Date();
  await col.updateOne(
    { _id: issueId },
    { $set: { status: 'published', publishedAt: now, deliverySummary: summary, updatedAt: now } },
  );
  await recordEvent({ type: 'issue_published', issueId, metadata: summary });
  return col.findOne({ _id: issueId });
}

export async function recordEvent({ type, subscriberId = undefined, issueId = undefined, metadata = {} }) {
  await ensureIndexes();
  const col = await getCollection(EVENTS);
  return col.insertOne({
    type: String(type),
    subscriberId: subscriberId || undefined,
    issueId: issueId || undefined,
    metadata,
    createdAt: new Date(),
  });
}

export async function getNewsletterMetrics() {
  await ensureIndexes();
  const [subscribers, issues, events] = await Promise.all([
    getSubscriberStats(),
    getCollection(ISSUES),
    getCollection(EVENTS),
  ]);
  const [drafts, ready, published, sentEvents, failedEvents] = await Promise.all([
    issues.countDocuments({ status: 'draft' }),
    issues.countDocuments({ status: 'ready' }),
    issues.countDocuments({ status: 'published' }),
    events.countDocuments({ type: 'delivery_sent' }),
    events.countDocuments({ type: 'delivery_failed' }),
  ]);
  return {
    subscribers,
    issues: { drafts, ready, published },
    delivery: { sent: sentEvents, failed: failedEvents },
  };
}
