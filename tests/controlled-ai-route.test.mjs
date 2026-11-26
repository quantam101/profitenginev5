import test from 'node:test';
import assert from 'node:assert/strict';
import { InMemoryExecutionStore, createExecutionControl } from '../lib/revenue-os/execution-control.mjs';
import { createControlledAIRoute } from '../lib/revenue-os/controlled-ai-route.mjs';

function fixture() {
  const store = new InMemoryExecutionStore();
  const clock = () => new Date('2026-09-14T12:00:00.000Z');
  const executionControl = createExecutionControl({
    store,
    approvalSecret: 'test-only-secret-that-is-longer-than-32-characters',
    clock,
  });
  return { executionControl, clock };
}

test('zero-spend blocks uncertified injected provider before provider call', async () => {
  const { executionControl, clock } = fixture();
  let calls = 0;
  const route = createControlledAIRoute({
    executionControl,
    config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
    routeAI: async () => { calls += 1; return { ok: true, costUsd: 0, text: '{}' }; },
    routeAICapability: { id: 'uncertified-provider' },
    clock,
  });
  const result = await route({ task: 'test', prompt: 'test' });
  assert.equal(calls, 0);
  assert.equal(result.ok, false);
  assert.equal(result.blocked, true);
  assert.match(result.reason, /not certified zero-cost/);
});

test('certified zero-cost route can execute at exactly zero cost', async () => {
  const { executionControl, clock } = fixture();
  let calls = 0;
  const route = createControlledAIRoute({
    executionControl,
    config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
    zeroCostRouteAI: async () => { calls += 1; return { ok: true, provider: 'free', costUsd: 0, text: '{"ok":true}' }; },
    clock,
  });
  const result = await route({ task: 'test', prompt: 'test' });
  assert.equal(calls, 1);
  assert.equal(result.ok, true);
  assert.equal(result.costUsd, 0);
});

test('paid provider is blocked unless its maximum call cost is bounded', async () => {
  const { executionControl, clock } = fixture();
  let calls = 0;
  const route = createControlledAIRoute({
    executionControl,
    config: { zeroSpend: false, maxDailyAiSpendUsd: 1 },
    routeAI: async () => { calls += 1; return { ok: true, costUsd: 0.1, text: '{}' }; },
    routeAICapability: { id: 'unknown-price-provider' },
    clock,
  });
  const result = await route({ task: 'test', prompt: 'test' });
  assert.equal(calls, 0);
  assert.equal(result.blocked, true);
  assert.match(result.reason, /no bounded maximum call cost/);
});

test('daily budget is reserved before paid provider calls', async () => {
  const { executionControl, clock } = fixture();
  let calls = 0;
  const route = createControlledAIRoute({
    executionControl,
    config: { zeroSpend: false, maxDailyAiSpendUsd: 0.5 },
    routeAI: async () => { calls += 1; return { ok: true, provider: 'bounded', costUsd: 0.1, text: '{}' }; },
    routeAICapability: { id: 'bounded-provider', maxCallCostUsd: 0.3 },
    clock,
  });
  const first = await route({ task: 'test', prompt: 'one' });
  const second = await route({ task: 'test', prompt: 'two' });
  assert.equal(first.ok, true);
  assert.equal(second.ok, false);
  assert.equal(second.blocked, true);
  assert.equal(calls, 1);
});

test('provider cannot report a cost above the amount reserved before invocation', async () => {
  const { executionControl, clock } = fixture();
  const route = createControlledAIRoute({
    executionControl,
    config: { zeroSpend: false, maxDailyAiSpendUsd: 1 },
    routeAI: async () => ({ ok: true, provider: 'bounded', costUsd: 0.4, text: '{}' }),
    routeAICapability: { id: 'bounded-provider', maxCallCostUsd: 0.2 },
    clock,
  });
  const result = await route({ task: 'test', prompt: 'test' });
  assert.equal(result.ok, false);
  assert.match(result.reason, /exceeded reserved maximum call cost/);
});

test('local Ollama route sends an explicit capped output budget', async () => {
  const { executionControl, clock } = fixture();
  const bodies = [];
  const fetchImpl = async (_url, init) => {
    bodies.push(JSON.parse(init.body));
    return { ok: true, status: 200, json: async () => ({ message: { content: '{"ok":true}' } }) };
  };
  const route = createControlledAIRoute({
    executionControl,
    config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
    env: { OLLAMA_BASE_URL: 'http://127.0.0.1:11434' },
    fetchImpl,
    clock,
  });
  await route({ task: 'test', prompt: 'test' });
  await route({ task: 'test', prompt: 'test', maxTokens: 9_000_000 });
  assert.equal(bodies.length, 2);
  assert.equal(bodies[0].options.num_predict, 1800);
  assert.equal(bodies[1].options.num_predict, 4096);
});
