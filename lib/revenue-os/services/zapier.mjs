import { createHmac, randomUUID } from 'node:crypto';
import { createDelivery, updateDeliveryStatus, getDeliveryByIdempotencyKey } from '../repositories/webhook-delivery.repository.mjs';
import { createActivity } from '../repositories/activity.repository.mjs';

const ZAPIER_ENABLED = String(process.env.REVENUE_OS_ZAPIER_ENABLED).toLowerCase() === 'true';
const ZAPIER_WEBHOOK_URL = process.env.ZAPIER_REVENUE_WEBHOOK || '';
const SIGNING_SECRET = process.env.WEBHOOK_SIGNING_SECRET || '';
const ZAPIER_TIMEOUT_MS = Number(process.env.ZAPIER_TIMEOUT_MS || 15000);
const ZAPIER_MAX_RETRIES = Number(process.env.ZAPIER_MAX_RETRIES || 3);

const VALID_EVENTS = [
  'revenue_play.created',
  'company.qualified',
  'opportunity.created',
  'opportunity.stage_changed',
  'follow_up.due',
  'proposal.approved',
  'opportunity.won',
];

export function isZapierEnabled() {
  return ZAPIER_ENABLED && ZAPIER_WEBHOOK_URL.startsWith('https://') && SIGNING_SECRET.length > 0;
}

export function getValidEvents() {
  return [...VALID_EVENTS];
}

/**
 * @param {Record<string, unknown>} payload
 * @param {string} [secret]
 * @returns {string}
 */
export function signPayload(payload, secret = SIGNING_SECRET) {
  if (!secret) {
    throw new Error('WEBHOOK_SIGNING_SECRET is required to sign payload');
  }
  const body = JSON.stringify(payload);
  return createHmac('sha256', secret).update(body).digest('hex');
}

/**
 * Dispatch an approved outbound event to Zapier.
 * The event is signed, idempotent, and logged whether enabled or not.
 * @param {{ eventType: string, payload?: Record<string, unknown>, actor?: string }} options
 * @returns {Promise<{ ok: boolean, delivered?: boolean, idempotencyKey: string, status: string, deliveryId?: string, cached?: boolean, error?: string }>}
 */
export async function dispatchZapierEvent({ eventType, payload, actor = 'system' }) {
  if (!VALID_EVENTS.includes(eventType)) {
    return { ok: false, error: `Invalid event type: ${eventType}` };
  }

  const idempotencyKey = payload?.idempotencyKey || randomUUID();
  const existing = await getDeliveryByIdempotencyKey(idempotencyKey);

  const eventPayload = {
    eventType,
    timestamp: new Date().toISOString(),
    idempotencyKey,
    data: payload || {},
  };

  const hasSecret = SIGNING_SECRET.length > 0;
  const signature = hasSecret ? signPayload(eventPayload) : undefined;

  if (!isZapierEnabled()) {
    const delivery = existing || await createDelivery({
      provider: 'zapier',
      eventType,
      idempotencyKey,
      targetUrl: ZAPIER_WEBHOOK_URL,
      payload: eventPayload,
      signature,
      status: 'DISABLED',
    });
    return { ok: true, delivered: false, idempotencyKey, status: 'DISABLED', deliveryId: String(delivery._id), cached: Boolean(existing) };
  }

  if (existing && existing.status === 'DELIVERED') {
    return { ok: true, delivered: true, idempotencyKey, status: 'DELIVERED', cached: true };
  }

  let delivery = existing || await createDelivery({
    provider: 'zapier',
    eventType,
    idempotencyKey,
    targetUrl: ZAPIER_WEBHOOK_URL,
    payload: eventPayload,
    signature,
    status: 'PENDING',
  });

  let lastError = '';
  let lastStatus = 0;

  for (let attempt = 0; attempt <= ZAPIER_MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(new Error('Zapier request timeout')), ZAPIER_TIMEOUT_MS);
      const response = await fetch(ZAPIER_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Zapier-Revenue-Signature': signature,
          'X-Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify(eventPayload),
        signal: controller.signal,
      });
      clearTimeout(timer);
      lastStatus = response.status;
      if (response.ok) {
        delivery = await updateDeliveryStatus(delivery._id, { status: 'DELIVERED', lastResponseStatus: response.status, lastError: undefined });
        break;
      }
      const bodyText = await response.text().catch(() => '');
      lastError = `HTTP ${response.status}: ${bodyText}`;
    } catch (error) {
      lastError = String(error?.message || error);
    }

    if (attempt < ZAPIER_MAX_RETRIES) {
      await new Promise((resolve) => setTimeout(resolve, 1000 * 2 ** attempt));
    }
  }

  if (delivery.status !== 'DELIVERED') {
    delivery = await updateDeliveryStatus(delivery._id, { status: 'FAILED', lastResponseStatus: lastStatus, lastError: lastError });
  }

  await createActivity({
    entityType: 'zapier_delivery',
    entityId: delivery._id,
    actionType: delivery.status.toLowerCase(),
    actor,
    summary: `Zapier ${eventType} ${delivery.status}`,
    metadata: { eventType, idempotencyKey, status: delivery.status, attempts: delivery.attempts },
  });

  return {
    ok: delivery.status === 'DELIVERED',
    delivered: delivery.status === 'DELIVERED',
    idempotencyKey,
    status: delivery.status,
    deliveryId: String(delivery._id),
    error: delivery.status === 'FAILED' ? lastError : undefined,
  };
}
