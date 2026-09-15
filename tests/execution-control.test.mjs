import test from 'node:test';
import assert from 'node:assert/strict';
import {
  InMemoryExecutionStore,
  assertProductionControl,
  createExecutionControl,
  payloadDigest,
} from '../lib/revenue-os/execution-control.mjs';

const SECRET = 'test-only-secret-that-is-longer-than-32-characters';

function fixture() {
  let now = new Date('2026-09-14T12:00:00.000Z');
  const clock = () => new Date(now);
  const advance = (ms) => { now = new Date(now.getTime() + ms); };
  const store = new InMemoryExecutionStore();
  const control = createExecutionControl({
    store,
    approvalSecret: SECRET,
    clock,
    circuitFailureThreshold: 2,
    circuitResetMs: 1_000,
    leaseTtlMs: 500,
  });
  return { store, control, clock, advance };
}

test('payload digest is stable across object key order', () => {
  assert.equal(payloadDigest({ b: 2, a: 1 }), payloadDigest({ a: 1, b: 2 }));
});

test('idempotent action executes once and replays stored result', async () => {
  const { control } = fixture();
  let calls = 0;
  const first = await control.runOnce({ key: 'publish:item-1', payload: { id: 1 }, execute: async () => ({ receipt: ++calls }) });
  const second = await control.runOnce({ key: 'publish:item-1', payload: { id: 1 }, execute: async () => ({ receipt: ++calls }) });
  assert.equal(calls, 1);
  assert.equal(first.replayed, false);
  assert.equal(second.replayed, true);
  assert.deepEqual(second.result, { receipt: 1 });
});

test('idempotency key collision fails closed', async () => {
  const { control } = fixture();
  await control.runOnce({ key: 'same-key', payload: { id: 1 }, execute: async () => 'ok' });
  await assert.rejects(
    control.runOnce({ key: 'same-key', payload: { id: 2 }, execute: async () => 'wrong' }),
    /Idempotency key collision/,
  );
});

test('lease blocks concurrent owner and becomes available after expiry', async () => {
  const { store, clock, advance } = fixture();
  const first = await store.acquireLease('x', 'owner-a', 500, clock());
  const blocked = await store.acquireLease('x', 'owner-b', 500, clock());
  assert.ok(first);
  assert.equal(blocked, null);
  advance(501);
  const recovered = await store.acquireLease('x', 'owner-b', 500, clock());
  assert.equal(recovered.owner, 'owner-b');
});

test('signed approval binds action resource payload expiration and nonce', async () => {
  const { control, clock } = fixture();
  const payload = { productId: 'p1', version: 3 };
  const expiresAt = new Date(clock().getTime() + 60_000);
  const token = control.signApproval({ action: 'external_publish', resource: 'gumroad:p1', payload, expiresAt, nonce: 'nonce-1' });
  const verified = await control.verifyAndConsumeApproval(token, { action: 'external_publish', resource: 'gumroad:p1', payload });
  assert.equal(verified.ok, true);
  const replay = await control.verifyAndConsumeApproval(token, { action: 'external_publish', resource: 'gumroad:p1', payload });
  assert.deepEqual(replay, { ok: false, reason: 'approval_replay' });
});

test('tampered, mismatched, and expired approvals fail closed', async () => {
  const { control, clock, advance } = fixture();
  const payload = { id: 'x' };
  const token = control.signApproval({ action: 'deploy', resource: 'preview', payload, expiresAt: new Date(clock().getTime() + 100), nonce: 'nonce-2' });
  const tampered = `${token.slice(0, -1)}${token.endsWith('A') ? 'B' : 'A'}`;
  assert.equal((await control.verifyAndConsumeApproval(tampered, { action: 'deploy', resource: 'preview', payload })).ok, false);

  const mismatchToken = control.signApproval({ action: 'deploy', resource: 'preview', payload, expiresAt: new Date(clock().getTime() + 100), nonce: 'nonce-3' });
  assert.deepEqual(
    await control.verifyAndConsumeApproval(mismatchToken, { action: 'deploy', resource: 'production', payload }),
    { ok: false, reason: 'approval_scope_mismatch' },
  );

  const expiredToken = control.signApproval({ action: 'deploy', resource: 'preview', payload, expiresAt: new Date(clock().getTime() + 100), nonce: 'nonce-4' });
  advance(101);
  assert.deepEqual(
    await control.verifyAndConsumeApproval(expiredToken, { action: 'deploy', resource: 'preview', payload }),
    { ok: false, reason: 'approval_expired' },
  );
});

test('circuit transitions CLOSED to OPEN to HALF_OPEN to CLOSED', async () => {
  const { control, advance } = fixture();
  assert.deepEqual(await control.beforeCircuitCall('provider'), { allowed: true, mode: 'CLOSED' });
  await control.recordCircuitFailure('provider');
  assert.equal((await control.beforeCircuitCall('provider')).mode, 'CLOSED');
  await control.recordCircuitFailure('provider');
  const open = await control.beforeCircuitCall('provider');
  assert.equal(open.allowed, false);
  assert.equal(open.mode, 'OPEN');
  advance(1_001);
  const halfOpen = await control.beforeCircuitCall('provider');
  assert.equal(halfOpen.allowed, true);
  assert.equal(halfOpen.mode, 'HALF_OPEN');
  await control.recordCircuitSuccess('provider', halfOpen.probeOwner);
  assert.deepEqual(await control.beforeCircuitCall('provider'), { allowed: true, mode: 'CLOSED' });
});

test('zero-spend and daily budgets are enforced before additional spend', async () => {
  const { control } = fixture();
  assert.equal((await control.reserveBudget({ bucket: 'd1', amountUsd: 0.01, maxUsd: 1, zeroSpend: true })).allowed, false);
  assert.equal((await control.reserveBudget({ bucket: 'd2', amountUsd: 0.6, maxUsd: 1 })).allowed, true);
  assert.equal((await control.reserveBudget({ bucket: 'd2', amountUsd: 0.5, maxUsd: 1 })).allowed, false);
});

test('production external writes reject ephemeral execution state', () => {
  assert.throws(
    () => assertProductionControl({ production: true, externalWrite: true, store: new InMemoryExecutionStore() }),
    /durable execution-control store/,
  );
  assert.equal(assertProductionControl({ production: false, externalWrite: true, store: new InMemoryExecutionStore() }), true);
});
