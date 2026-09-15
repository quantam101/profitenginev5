import test from 'node:test';
import assert from 'node:assert/strict';
import { InMemoryExecutionStore, createExecutionControl } from '../lib/revenue-os/execution-control.mjs';
import { buildDeliveryApprovalRequest, executeControlledDelivery } from '../lib/revenue-os/safe-delivery.mjs';

const SECRET = 'test-only-secret-that-is-longer-than-32-characters';

function fixture() {
  const clock = () => new Date('2026-09-14T12:00:00.000Z');
  const store = new InMemoryExecutionStore();
  const executionControl = createExecutionControl({ store, approvalSecret: SECRET, clock });
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

test('approval request exposes exact digest without executing anything', () => {
  const request = buildDeliveryApprovalRequest({ lane: 'newsletter', resource: 'beehiiv:publication:p1', payload: { title: 'A' } });
  assert.equal(request.action, 'external_publish:newsletter');
  assert.equal(request.resource, 'beehiiv:publication:p1');
  assert.equal(typeof request.digest, 'string');
  assert.equal(request.digest.length, 64);
});
