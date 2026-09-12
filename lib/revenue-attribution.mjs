import crypto from 'node:crypto';
import { MongoClient } from 'mongodb';

let clientPromise;
let indexesPromise;

function mongoUri() {
  return process.env.MONGODB_URI || process.env.MONGO_URL;
}

function dbName() {
  if (process.env.MONGODB_DB) return process.env.MONGODB_DB;
  if (process.env.DB_NAME) return process.env.DB_NAME;
  const uri = mongoUri();
  if (uri) {
    try {
      const pathname = new URL(uri).pathname;
      if (pathname && pathname.length > 1) return pathname.slice(1);
    } catch {}
  }
  return 'profitengine';
}

async function getDb() {
  if (!clientPromise) {
    const uri = mongoUri();
    if (!uri) throw new Error('MONGODB_URI or MONGO_URL is not configured');
    const client = new MongoClient(uri, {
      maxPoolSize: Number(process.env.MONGODB_MAX_POOL_SIZE || 10),
      minPoolSize: Number(process.env.MONGODB_MIN_POOL_SIZE || 1),
    });
    clientPromise = client.connect();
  }
  const client = await clientPromise;
  return client.db(dbName());
}

async function ensureIndexes() {
  if (!indexesPromise) {
    indexesPromise = (async () => {
      const db = await getDb();
      await Promise.all([
        db.collection('revenue_leads').createIndex({ leadId: 1 }, { unique: true, name: 'uniq_lead_id' }),
        db.collection('revenue_attribution').createIndex({ bookingId: 1 }, { unique: true, name: 'uniq_booking_id' }),
        db.collection('revenue_attribution').createIndex({ leadId: 1 }, { name: 'lead_lookup' }),
        db.collection('revenue_events').createIndex({ provider: 1, paymentId: 1 }, { unique: true, name: 'uniq_provider_payment' }),
        db.collection('revenue_events').createIndex({ leadId: 1 }, { name: 'revenue_lead_lookup' }),
      ]);
    })();
  }
  return indexesPromise;
}

export function newLeadId() { return `lead_${crypto.randomUUID()}`; }
export function newBookingId() { return `book_${crypto.randomUUID()}`; }
export function newRevenueEventId() { return `rev_${crypto.randomUUID()}`; }
export function safeText(value, max = 1000) { return String(value ?? '').replace(/[<>`]/g, '').trim().slice(0, max); }

export function attributionFromPayload(payload = {}) {
  return {
    source: safeText(payload.source, 120) || 'direct',
    medium: safeText(payload.medium, 120),
    campaign: safeText(payload.campaign, 160),
    content: safeText(payload.content, 160),
    term: safeText(payload.term, 160),
    referrer: safeText(payload.referrer, 500),
    landingPage: safeText(payload.landingPage, 500),
  };
}

export async function persistLead(input) {
  await ensureIndexes();
  const db = await getDb();
  const now = new Date();
  const leadId = input.leadId || newLeadId();
  const doc = {
    leadId, createdAt: now, updatedAt: now, status: 'lead_created',
    name: safeText(input.name, 160), email: safeText(input.email, 320).toLowerCase(),
    phone: safeText(input.phone, 80), service: safeText(input.service, 160),
    message: safeText(input.message, 3000), gaClientId: safeText(input.gaClientId, 160),
    attribution: attributionFromPayload(input),
    metadata: input.metadata && typeof input.metadata === 'object' ? input.metadata : {},
  };
  await db.collection('revenue_leads').updateOne({ leadId }, { $setOnInsert: doc, $set: { updatedAt: now } }, { upsert: true });
  return doc;
}

/**
 * @param {{leadId:string, bookingId?:string, provider?:string, checkoutId?:string, amount?:number|null, currency?:string}} input
 * @returns {Promise<string>}
 */
export async function linkBooking({ leadId, bookingId, provider = 'stripe', checkoutId = '', amount = null, currency = 'usd' }) {
  if (!leadId) throw new Error('leadId is required');
  await ensureIndexes();
  const db = await getDb();
  const now = new Date();
  const resolvedBookingId = bookingId || newBookingId();
  await db.collection('revenue_attribution').updateOne(
    { bookingId: resolvedBookingId },
    { $setOnInsert: { bookingId: resolvedBookingId, createdAt: now }, $set: { leadId, provider, checkoutId, amount, currency: String(currency || 'usd').toLowerCase(), stage: 'booking_created', updatedAt: now } },
    { upsert: true },
  );
  await db.collection('revenue_leads').updateOne({ leadId }, { $set: { status: 'booking_created', bookingId: resolvedBookingId, updatedAt: now } });
  return resolvedBookingId;
}

export async function recordRevenueOnce({ provider, paymentId, providerEventId, leadId, bookingId, checkoutId = '', amount, currency = 'usd', rawType = '' }) {
  if (!provider || !paymentId) throw new Error('provider and paymentId are required');
  await ensureIndexes();
  const db = await getDb();
  const now = new Date();
  const revenueEventId = newRevenueEventId();
  const result = await db.collection('revenue_events').updateOne(
    { provider, paymentId },
    { $setOnInsert: { revenueEventId, provider, paymentId, providerEventId: providerEventId || '', leadId: leadId || '', bookingId: bookingId || '', checkoutId, amount: Number(amount || 0), currency: String(currency || 'usd').toLowerCase(), rawType, status: 'collected', createdAt: now }, $set: { lastSeenAt: now } },
    { upsert: true },
  );
  const inserted = result.upsertedCount === 1;
  const existing = inserted ? { revenueEventId, provider, paymentId, leadId, bookingId, amount: Number(amount || 0), currency: String(currency || 'usd').toLowerCase() } : await db.collection('revenue_events').findOne({ provider, paymentId });
  if (leadId) await db.collection('revenue_leads').updateOne({ leadId }, { $set: { status: 'revenue_collected', bookingId: bookingId || '', updatedAt: now } });
  if (bookingId) await db.collection('revenue_attribution').updateOne({ bookingId }, { $set: { stage: 'revenue_collected', paymentId, revenueEventId: existing?.revenueEventId || revenueEventId, updatedAt: now } });
  return { inserted, duplicate: !inserted, event: existing };
}

export async function sendLeadNotification(lead) {
  const to = process.env.REVENUE_NOTIFICATION_TO || process.env.ALERT_EMAIL || 'dispatch@alreadyherellc.com';
  const from = process.env.REVENUE_NOTIFICATION_FROM || 'Already Here Revenue <onboarding@resend.dev>';
  const subject = `New attributed lead ${lead.leadId}${lead.service ? ` — ${lead.service}` : ''}`;
  const text = [`Lead ID: ${lead.leadId}`, `Name: ${lead.name || '-'}`, `Email: ${lead.email || '-'}`, `Phone: ${lead.phone || '-'}`, `Service: ${lead.service || '-'}`, `Source: ${lead.attribution?.source || 'direct'}`, `Campaign: ${lead.attribution?.campaign || '-'}`, '', lead.message || ''].join('\n');
  const resendKey = process.env.RESEND_API_KEY;
  if (resendKey) {
    try {
      const response = await fetch('https://api.resend.com/emails', { method: 'POST', headers: { Authorization: `Bearer ${resendKey}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ from, to: [to], subject, text }) });
      if (response.ok) return { provider: 'resend', delivered: true };
    } catch {}
  }
  const formspree = process.env.FORMSPREE_REVENUE_ENDPOINT;
  if (formspree) {
    try {
      const url = new URL(formspree);
      if (url.protocol === 'https:' && (url.hostname === 'formspree.io' || url.hostname.endsWith('.formspree.io'))) {
        const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ _subject: subject, lead_id: lead.leadId, name: lead.name, email: lead.email, phone: lead.phone, service: lead.service, message: lead.message, source: lead.attribution?.source, campaign: lead.attribution?.campaign }) });
        if (response.ok) return { provider: 'formspree', delivered: true };
      }
    } catch {}
  }
  return { provider: 'none', delivered: false };
}

export async function sendGa4LeadConversion(lead) {
  const measurementId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || process.env.GA4_MEASUREMENT_ID;
  const apiSecret = process.env.GA4_API_SECRET;
  if (!measurementId || !apiSecret) return { sent: false, reason: 'not_configured' };
  const clientId = lead.gaClientId || `${Date.now()}.${Math.floor(Math.random() * 1_000_000_000)}`;
  const endpoint = new URL('https://www.google-analytics.com/mp/collect');
  endpoint.searchParams.set('measurement_id', measurementId);
  endpoint.searchParams.set('api_secret', apiSecret);
  const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ client_id: clientId, events: [{ name: 'generate_lead', params: { lead_id: lead.leadId, source: lead.attribution?.source || 'direct', campaign: lead.attribution?.campaign || '', service: lead.service || '', engagement_time_msec: 1 } }] }) });
  return { sent: response.ok, status: response.status, clientId };
}

export function verifySquareSignature({ signatureKey, notificationUrl, body, signature }) {
  if (!signatureKey || !notificationUrl || !signature) return false;
  const expected = crypto.createHmac('sha256', signatureKey).update(`${notificationUrl}${body}`).digest('base64');
  const left = Buffer.from(expected);
  const right = Buffer.from(signature);
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}
