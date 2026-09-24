import test from 'node:test';
import assert from 'node:assert/strict';
import { InMemoryExecutionStore, createExecutionControl } from '../lib/revenue-os/execution-control.mjs';
import {
  buildDeliveryApprovalRequest,
  executeControlledDelivery,
  executePreparedDelivery,
  prepareControlledDelivery,
} from '../lib/revenue-os/safe-delivery.mjs';

const SECRET = 'test-only-secret-that-is-longer-than-32-characters';

function fixture(options = {}) {
  const clock = options.clock || (() => new Date('2026-09-14T12:00:00.000Z'));
  const store = new InMemoryExecutionStore();
  const executionControl = createExecutionControl({
    store,
    approvalSecret: SECRET,
    clock,
    circuitFailureThreshold: options.circuitFailureThreshold || 3,
    circuitResetMs: options.circuitResetMs || 300_000,
  });
  return { store, executionControl, clock };
}

test('missing approval never calls the external adapter', async () => {
  const { store, executionControl } = fixture();
  let calls = 0;
  const result = await executeControlledDelivery({
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload: { id: 'p1' },
    adapter: async () => { calls += 1; return { ok: true }; },
    executionControl,
    store,
    production: false,
  });
  assert.equal(calls, 0);
  assert.equal(result.mode, 'approval_required');
});

test('tampered approval never calls the external adapter', async () => {
  const { store, executionControl, clock } = fixture();
  const payload = { id: 'p1' };
  const approval = executionControl.signApproval({
    action: 'external_publish:technical_product',
    resource: 'storefront:technical_product',
    payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'delivery-tamper',
  });
  const tampered = `${approval.slice(0, -1)}${approval.endsWith('A') ? 'B' : 'A'}`;
  let calls = 0;
  const result = await executeControlledDelivery({
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload,
    adapter: async () => { calls += 1; return { ok: true }; },
    executionControl,
    approvalToken: tampered,
    store,
    production: false,
  });
  assert.equal(calls, 0);
  assert.equal(result.mode, 'blocked');
});

test('valid approval executes once and identical retry replays proof', async () => {
  const { store, executionControl, clock } = fixture();
  const payload = { id: 'p1', version: 1 };
  const approval = executionControl.signApproval({
    action: 'external_publish:technical_product',
    resource: 'storefront:technical_product',
    payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'delivery-once',
  });
  let calls = 0;
  const adapter = async () => ({ ok: true, proof: { receipt: ++calls } });
  const args = {
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload,
    adapter,
    executionControl,
    approvalToken: approval,
    store,
    production: false,
  };
  const first = await executeControlledDelivery(args);
  const second = await executeControlledDelivery(args);
  assert.equal(calls, 1);
  assert.equal(first.mode, 'executed');
  assert.equal(second.mode, 'idempotent_replay');
  assert.deepEqual(second.proof, { receipt: 1 });
});

test('tampered approval cannot retrieve a completed idempotent replay', async () => {
  const { store, executionControl, clock } = fixture();
  const payload = { id: 'p1', version: 2 };
  const approval = executionControl.signApproval({
    action: 'external_publish:technical_product',
    resource: 'storefront:technical_product',
    payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'delivery-replay-auth',
  });
  let calls = 0;
  const adapter = async () => ({ ok: true, proof: { receipt: ++calls } });
  const first = await executeControlledDelivery({
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload,
    adapter,
    executionControl,
    approvalToken: approval,
    store,
    production: false,
  });
  assert.equal(first.mode, 'executed');
  const tampered = `${approval.slice(0, -1)}${approval.endsWith('A') ? 'B' : 'A'}`;
  const replayAttempt = await executeControlledDelivery({
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload,
    adapter,
    executionControl,
    approvalToken: tampered,
    store,
    production: false,
  });
  assert.equal(calls, 1);
  assert.equal(replayAttempt.mode, 'blocked');
  assert.equal(replayAttempt.proof, undefined);
});

test('prepared delivery freezes and executes the exact approved payload', async () => {
  const { store, executionControl, clock } = fixture();
  const candidate = { id: 'frozen-1', title: 'Approved title', nested: { revision: 1 } };
  const prepared = await prepareControlledDelivery({
    lane: 'newsletter',
    resource: 'beehiiv:publication:p1',
    payload: candidate,
    store,
    clock,
    verification: { ready: true, qualityScore: 98 },
  });
  const approval = executionControl.signApproval({
    action: 'external_publish:newsletter',
    resource: 'beehiiv:publication:p1',
    payload: prepared.payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'frozen-payload',
  });

  candidate.title = 'Changed after approval request';
  candidate.nested.revision = 2;
  let received;
  const result = await executePreparedDelivery({
    preparedId: prepared.preparedId,
    adapter: async ({ payload }) => { received = payload; return { ok: true, proof: { externalId: 'post_1' } }; },
    executionControl,
    approvalToken: approval,
    store,
    production: false,
    expectedLane: 'newsletter',
    expectedResource: 'beehiiv:publication:p1',
    clock,
  });

  assert.equal(result.mode, 'executed');
  assert.equal(received.title, 'Approved title');
  assert.equal(received.nested.revision, 1);
  assert.equal(result.preparedId, prepared.preparedId);
});

test('prepared delivery fails closed when destination no longer matches', async () => {
  const { store, executionControl, clock } = fixture();
  const payload = { id: 'frozen-2' };
  const prepared = await prepareControlledDelivery({
    lane: 'newsletter',
    resource: 'beehiiv:publication:p1',
    payload,
    store,
    clock,
    verification: { ready: true },
  });
  const approval = executionControl.signApproval({
    action: 'external_publish:newsletter',
    resource: 'beehiiv:publication:p1',
    payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'frozen-destination',
  });
  let calls = 0;
  const result = await executePreparedDelivery({
    preparedId: prepared.preparedId,
    adapter: async () => { calls += 1; return { ok: true }; },
    executionControl,
    approvalToken: approval,
    store,
    production: false,
    expectedLane: 'newsletter',
    expectedResource: 'beehiiv:publication:changed',
    clock,
  });
  assert.equal(calls, 0);
  assert.equal(result.mode, 'blocked');
  assert.equal(result.reason, 'prepared_resource_mismatch');
});

test('delivery adapter failures open the persistent circuit before another external call', async () => {
  const { store, executionControl, clock } = fixture({ circuitFailureThreshold: 1 });
  const payload = { id: 'circuit-1' };
  const approval1 = executionControl.signApproval({
    action: 'external_publish:technical_product',
    resource: 'storefront:technical_product',
    payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'circuit-fail-1',
  });
  let calls = 0;
  const adapter = async () => { calls += 1; throw new Error('upstream unavailable'); };
  const first = await executeControlledDelivery({
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload,
    adapter,
    executionControl,
    approvalToken: approval1,
    store,
    production: false,
  });
  assert.equal(first.mode, 'blocked');
  assert.equal(calls, 1);

  const approval2 = executionControl.signApproval({
    action: 'external_publish:technical_product',
    resource: 'storefront:technical_product',
    payload,
    expiresAt: new Date(clock().getTime() + 60_000),
    nonce: 'circuit-fail-2',
  });
  const second = await executeControlledDelivery({
    lane: 'technical_product',
    resource: 'storefront:technical_product',
    payload,
    adapter,
    executionControl,
    approvalToken: approval2,
    store,
    production: false,
  });
  assert.equal(second.mode, 'blocked');
  assert.match(second.reason, /Delivery circuit OPEN/);
  assert.equal(calls, 1);
});

test('approval request exposes exact digest and prepared id without executing anything', () => {
  const request = buildDeliveryApprovalRequest({
    lane: 'newsletter',
    resource: 'beehiiv:publication:p1',
    payload: { title: 'A' },
    preparedId: 'prepared:test',
  });
  assert.equal(request.action, 'external_publish:newsletter');
  assert.equal(request.resource, 'beehiiv:publication:p1');
  assert.equal(typeof request.digest, 'string');
  assert.equal(request.digest.length, 64);
  assert.equal(request.preparedId, 'prepared:test');
});
