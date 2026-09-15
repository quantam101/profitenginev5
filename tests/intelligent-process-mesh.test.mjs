import test from 'node:test';
import assert from 'node:assert/strict';
import {
  PROCESS_AGENTS,
  buildProcessMeshPlan,
  getProcessAgentManifest,
  runIntelligentProcessMesh,
} from '../lib/revenue-os/intelligent-process-mesh.mjs';
import { InMemoryExecutionStore, createExecutionControl } from '../lib/revenue-os/execution-control.mjs';

function executionFixture() {
  return createExecutionControl({
    store: new InMemoryExecutionStore(),
    approvalSecret: 'test-only-secret-that-is-longer-than-32-characters',
    clock: () => new Date('2026-09-14T12:00:00.000Z'),
  });
}

function validEnvelope(overrides = {}) {
  return {
    status: 'ready',
    summary: 'Evidence-backed specialist result.',
    confidence: 91,
    evidence: [{ claim: 'Input was processed', source: 'supplied_context', verified: true }],
    risks: [],
    actions: [{ action: 'Prepare internal artifact', priority: 'P2', externalWrite: false, requiresApproval: false }],
    artifacts: [{ kind: 'analysis', name: 'result', content: { ok: true } }],
    handoff: 'Continue to the next controlled stage.',
    ...overrides,
  };
}

test('mesh exposes a specialist AI agent for every major process and strips external authority', () => {
  const manifest = getProcessAgentManifest();
  assert.ok(manifest.length >= 14);
  for (const agent of manifest) {
    assert.equal(agent.authority.canSpend, false);
    assert.equal(agent.authority.canPublish, false);
    assert.equal(agent.authority.canDeploy, false);
    assert.equal(agent.authority.canMerge, false);
  }
  assert.ok(PROCESS_AGENTS.portfolio_supervisor);
  assert.ok(PROCESS_AGENTS.opportunity_researcher);
  assert.ok(PROCESS_AGENTS.technical_product_builder);
  assert.ok(PROCESS_AGENTS.technical_product_verifier);
  assert.ok(PROCESS_AGENTS.stock_compliance_reviewer);
  assert.ok(PROCESS_AGENTS.newsletter_editor);
  assert.ok(PROCESS_AGENTS.delivery_controller);
  assert.ok(PROCESS_AGENTS.analytics_analyst);
  assert.ok(PROCESS_AGENTS.catch_correct_optimizer);
});

test('DAG puts supervisor first and Catch and Correct last', () => {
  const plan = buildProcessMeshPlan();
  assert.deepEqual(plan[0], ['portfolio_supervisor']);
  assert.deepEqual(plan.at(-1), ['catch_correct_optimizer']);
});

test('zero-spend blocks uncertified AI before invocation', async () => {
  let calls = 0;
  const routeAI = async () => {
    calls += 1;
    return { ok: true, costUsd: 0, text: JSON.stringify(validEnvelope()) };
  };
  const result = await runIntelligentProcessMesh(
    { runId: 'zero-spend-block', processAgents: ['portfolio_supervisor'], context: { objective: 'test' } },
    {
      routeAI,
      routeAICapability: { id: 'unknown-cost-route' },
      executionControl: executionFixture(),
      config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
      clock: () => new Date('2026-09-14T12:00:00.000Z'),
      env: {},
    },
  );
  assert.equal(calls, 0);
  assert.equal(result.outputs.portfolio_supervisor.status, 'review_required');
  assert.match(result.outputs.portfolio_supervisor.risks[0], /Zero-spend preflight blocked/);
});

test('certified zero-cost AI executes the specialist mesh', async () => {
  let calls = 0;
  const zeroCostRouteAI = async ({ metadata }) => {
    calls += 1;
    return {
      ok: true,
      provider: 'test-zero-cost',
      model: 'test-model',
      costUsd: 0,
      text: JSON.stringify(validEnvelope({ summary: `Completed ${metadata.processAgent}` })),
    };
  };
  const result = await runIntelligentProcessMesh(
    { runId: 'mesh-success', context: { objective: 'produce revenue assets from verified inputs' } },
    {
      zeroCostRouteAI,
      executionControl: executionFixture(),
      config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
      clock: () => new Date('2026-09-14T12:00:00.000Z'),
      env: {},
    },
  );
  assert.equal(result.ok, true);
  assert.equal(calls, Object.keys(PROCESS_AGENTS).length);
  assert.equal(result.events.length, Object.keys(PROCESS_AGENTS).length);
  assert.equal(result.policy.specialistExternalAuthority, false);
  assert.equal(result.policy.productionCodeLearning, 'pull_request_only_after_tests');
});

test('independent verifier rejection prevents the mesh from reporting ok', async () => {
  const zeroCostRouteAI = async ({ metadata }) => {
    const rejected = metadata.processAgent === 'technical_product_verifier';
    return {
      ok: true,
      provider: 'test-zero-cost',
      costUsd: 0,
      text: JSON.stringify(validEnvelope(rejected ? {
        status: 'blocked',
        summary: 'Verification failed.',
        confidence: 99,
        risks: ['Required test evidence is missing.'],
      } : {})),
    };
  };
  const result = await runIntelligentProcessMesh(
    { runId: 'verifier-reject', context: { objective: 'test verifier authority' } },
    {
      zeroCostRouteAI,
      executionControl: executionFixture(),
      config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
      clock: () => new Date('2026-09-14T12:00:00.000Z'),
      env: {},
    },
  );
  assert.equal(result.ok, false);
  assert.ok(result.blocked.includes('technical_product_verifier'));
});

test('specialist external-write requests are converted into approval-required requests', async () => {
  const zeroCostRouteAI = async () => ({
    ok: true,
    provider: 'test-zero-cost',
    costUsd: 0,
    text: JSON.stringify(validEnvelope({
      actions: [{ action: 'Publish product', priority: 'P1', externalWrite: true, requiresApproval: false }],
    })),
  });
  const result = await runIntelligentProcessMesh(
    { runId: 'authority-boundary', processAgents: ['portfolio_supervisor'], context: {} },
    {
      zeroCostRouteAI,
      executionControl: executionFixture(),
      config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
      clock: () => new Date('2026-09-14T12:00:00.000Z'),
      env: {},
    },
  );
  assert.equal(result.outputs.portfolio_supervisor.actions[0].requiresApproval, true);
  assert.equal(result.externalActionRequests[0].requiresApproval, true);
});

test('same run id and same inputs replay prior agent results instead of calling AI twice', async () => {
  let calls = 0;
  const control = executionFixture();
  const zeroCostRouteAI = async () => {
    calls += 1;
    return { ok: true, provider: 'test-zero-cost', costUsd: 0, text: JSON.stringify(validEnvelope()) };
  };
  const input = { runId: 'idempotent-mesh', processAgents: ['portfolio_supervisor'], context: { x: 1 } };
  const deps = {
    zeroCostRouteAI,
    executionControl: control,
    config: { zeroSpend: true, maxDailyAiSpendUsd: 0 },
    clock: () => new Date('2026-09-14T12:00:00.000Z'),
    env: {},
  };
  const first = await runIntelligentProcessMesh(input, deps);
  const second = await runIntelligentProcessMesh(input, deps);
  assert.equal(calls, 1);
  assert.equal(first.events[0].replayed, false);
  assert.equal(second.events[0].replayed, true);
});
