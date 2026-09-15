import { assertProductionControl, payloadDigest } from './execution-control.mjs';

export const DELIVERY_POLICY_VERSION = 'delivery-v2-frozen-20260914';
const DEFAULT_PREPARED_RETENTION_MS = 7 * 24 * 60 * 60 * 1000;

function normalizeAdapterResult(result) {
  if (result && typeof result === 'object' && 'ok' in result) return result;
  return { ok: true, receipt: result ?? null };
}

function asDate(value) {
  return value instanceof Date ? value : new Date(value);
}

function preparedKey({ action, resource, digest }) {
  return `prepared:${payloadDigest({ policyVersion: DELIVERY_POLICY_VERSION, action, resource, digest })}`;
}

export async function prepareControlledDelivery({
  lane,
  resource,
  payload,
  store,
  clock = () => new Date(),
  retentionMs = DEFAULT_PREPARED_RETENTION_MS,
  verification = {},
} = {}) {
  if (!lane) throw new Error('Delivery lane is required');
  if (!resource) throw new Error('Delivery resource is required');
  if (!payload || typeof payload !== 'object') throw new Error('Delivery payload is required');
  if (!store?.putPrepared || !store?.getPrepared) throw new Error('Prepared delivery requires a compatible execution-control store');

  const action = `external_publish:${lane}`;
  const digest = payloadDigest(payload);
  const preparedId = preparedKey({ action, resource, digest });
  const preparedAt = clock();
  const expiresAt = new Date(preparedAt.getTime() + Math.max(60_000, Number(retentionMs || DEFAULT_PREPARED_RETENTION_MS)));
  const record = {
    preparedId,
    policyVersion: DELIVERY_POLICY_VERSION,
    lane,
    action,
    resource,
    digest,
    payload: structuredClone(payload),
    verification: structuredClone(verification || {}),
    preparedAt: preparedAt.toISOString(),
    expiresAt: expiresAt.toISOString(),
  };
  const stored = await store.putPrepared(preparedId, record);
  return {
    ...record,
    ...stored,
    preparedId,
    payload: structuredClone(stored?.payload ?? record.payload),
    verification: structuredClone(stored?.verification ?? record.verification),
  };
}

export async function loadPreparedDelivery({ preparedId, store, clock = () => new Date() } = {}) {
  if (!preparedId) throw new Error('preparedId is required');
  if (!store?.getPrepared) throw new Error('Prepared delivery requires a compatible execution-control store');
  const record = await store.getPrepared(preparedId);
  if (!record) return { ok: false, reason: 'prepared_not_found', preparedId };
  if (record.policyVersion !== DELIVERY_POLICY_VERSION) {
    return { ok: false, reason: 'prepared_policy_version_mismatch', preparedId, policyVersion: record.policyVersion };
  }
  const expiresAt = asDate(record.expiresAt);
  if (!Number.isFinite(expiresAt.getTime()) || expiresAt <= clock()) {
    return { ok: false, reason: 'prepared_expired', preparedId, expiresAt: record.expiresAt };
  }
  const digest = payloadDigest(record.payload);
  if (digest !== record.digest) return { ok: false, reason: 'prepared_digest_mismatch', preparedId };
  const expectedId = preparedKey({ action: record.action, resource: record.resource, digest });
  if (expectedId !== preparedId) return { ok: false, reason: 'prepared_id_mismatch', preparedId };
  return { ok: true, record };
}

export async function executeControlledDelivery({
  lane,
  resource,
  payload,
  adapter,
  executionControl,
  approvalToken,
  production = process.env.NODE_ENV === 'production',
  store,
  timeoutMs = 20_000,
} = {}) {
  if (!lane) throw new Error('Delivery lane is required');
  if (!resource) throw new Error('Delivery resource is required');
  if (!payload || typeof payload !== 'object') throw new Error('Delivery payload is required');
  if (typeof adapter !== 'function') return { attempted: false, ok: false, mode: 'missing_adapter', reason: 'No delivery adapter is configured.' };
  if (!executionControl) throw new Error('Delivery executionControl is required');

  assertProductionControl({ production, externalWrite: true, store });

  const action = `external_publish:${lane}`;
  const digest = payloadDigest(payload);
  const idempotencyKey = `delivery:${action}:${resource}:${digest}`;
  const circuitKey = `delivery:${lane}:${resource}`;

  if (!approvalToken) {
    return {
      attempted: false,
      ok: false,
      mode: 'approval_required',
      action,
      resource,
      digest,
      idempotencyKey,
      reason: 'A signed, scoped approval token is required before any external write.',
    };
  }

  const approvalPreflight = executionControl.verifyApproval(approvalToken, { action, resource, payload });
  if (!approvalPreflight.ok) {
    return {
      attempted: false,
      ok: false,
      mode: 'blocked',
      action,
      resource,
      digest,
      idempotencyKey,
      reason: `Delivery approval rejected: ${approvalPreflight.reason}`,
    };
  }

  try {
    const result = await executionControl.runOnce({
      key: idempotencyKey,
      payload: { action, resource, payload },
      ttlMs: timeoutMs + 5_000,
      execute: async () => {
        const approval = await executionControl.verifyAndConsumeApproval(approvalToken, { action, resource, payload });
        if (!approval.ok) throw new Error(`Delivery approval rejected: ${approval.reason}`);

        const circuit = await executionControl.beforeCircuitCall(circuitKey);
        if (!circuit.allowed) throw new Error(`Delivery circuit ${circuit.mode} for ${resource}`);

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(new Error('Delivery adapter timeout')), timeoutMs);
        timer.unref?.();
        try {
          const adapterResult = await adapter({ lane, resource, payload, signal: controller.signal, idempotencyKey });
          const normalized = normalizeAdapterResult(adapterResult);
          if (!normalized.ok) throw new Error(normalized.reason || normalized.error || 'Delivery adapter returned not-ok');
          await executionControl.recordCircuitSuccess(circuitKey, circuit.probeOwner);
          return {
            ok: true,
            lane,
            resource,
            digest,
            proof: normalized.proof ?? normalized.receipt ?? normalized,
            approvalNonce: approval.approval.nonce,
          };
        } catch (error) {
          await executionControl.recordCircuitFailure(circuitKey, circuit.probeOwner);
          throw error;
        } finally {
          clearTimeout(timer);
        }
      },
    });

    if (result.status === 'busy') {
      return { attempted: false, ok: false, mode: 'in_progress', action, resource, digest, idempotencyKey };
    }
    return {
      attempted: !result.replayed,
      ok: true,
      mode: result.replayed ? 'idempotent_replay' : 'executed',
      action,
      resource,
      digest,
      idempotencyKey,
      replayed: result.replayed,
      proof: result.result?.proof ?? null,
    };
  } catch (error) {
    return {
      attempted: false,
      ok: false,
      mode: 'blocked',
      action,
      resource,
      digest,
      idempotencyKey,
      reason: error instanceof Error ? error.message : String(error),
    };
  }
}

export async function executePreparedDelivery({
  preparedId,
  adapter,
  executionControl,
  approvalToken,
  production = process.env.NODE_ENV === 'production',
  store,
  timeoutMs = 20_000,
  expectedLane,
  expectedResource,
  clock = () => new Date(),
} = {}) {
  const loaded = await loadPreparedDelivery({ preparedId, store, clock });
  if (!loaded.ok) {
    return { attempted: false, ok: false, mode: 'blocked', preparedId, reason: loaded.reason };
  }
  const prepared = loaded.record;
  if (expectedLane && prepared.lane !== expectedLane) {
    return { attempted: false, ok: false, mode: 'blocked', preparedId, reason: 'prepared_lane_mismatch' };
  }
  if (expectedResource && prepared.resource !== expectedResource) {
    return { attempted: false, ok: false, mode: 'blocked', preparedId, reason: 'prepared_resource_mismatch' };
  }
  if (prepared.verification?.ready === false) {
    return { attempted: false, ok: false, mode: 'blocked', preparedId, reason: 'prepared_verification_not_ready' };
  }

  const result = await executeControlledDelivery({
    lane: prepared.lane,
    resource: prepared.resource,
    payload: prepared.payload,
    adapter,
    executionControl,
    approvalToken,
    production,
    store,
    timeoutMs,
  });
  return { ...result, preparedId, preparedDigest: prepared.digest, preparedAt: prepared.preparedAt };
}

export function buildDeliveryApprovalRequest({ lane, resource, payload, preparedId = null }) {
  if (!lane || !resource || !payload) throw new Error('lane, resource, and payload are required');
  return {
    action: `external_publish:${lane}`,
    resource,
    digest: payloadDigest(payload),
    preparedId,
    policyVersion: DELIVERY_POLICY_VERSION,
    payload,
  };
}
