import { assertProductionControl, payloadDigest } from './execution-control.mjs';

function normalizeAdapterResult(result) {
  if (result && typeof result === 'object' && 'ok' in result) return result;
  return { ok: true, receipt: result ?? null };
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

  try {
    const result = await executionControl.runOnce({
      key: idempotencyKey,
      payload: { action, resource, payload },
      ttlMs: timeoutMs + 5_000,
      execute: async () => {
        const approval = await executionControl.verifyAndConsumeApproval(approvalToken, { action, resource, payload });
        if (!approval.ok) throw new Error(`Delivery approval rejected: ${approval.reason}`);
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(new Error('Delivery adapter timeout')), timeoutMs);
        timer.unref?.();
        try {
          const adapterResult = await adapter({ lane, resource, payload, signal: controller.signal, idempotencyKey });
          const normalized = normalizeAdapterResult(adapterResult);
          if (!normalized.ok) throw new Error(normalized.reason || normalized.error || 'Delivery adapter returned not-ok');
          return {
            ok: true,
            lane,
            resource,
            digest,
            proof: normalized.proof ?? normalized.receipt ?? normalized,
            approvalNonce: approval.approval.nonce,
          };
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

export function buildDeliveryApprovalRequest({ lane, resource, payload }) {
  if (!lane || !resource || !payload) throw new Error('lane, resource, and payload are required');
  return {
    action: `external_publish:${lane}`,
    resource,
    digest: payloadDigest(payload),
    payload,
  };
}
