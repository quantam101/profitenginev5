import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { evaluatePromotionGate, getAIGatewayConfig, getAIGatewayPolicy, routeAI } from '../lib/ai-gateway.mjs';

const auditDir = await mkdtemp(join(tmpdir(), 'profitengine-ai-gateway-'));
const auditPath = join(auditDir, 'audit.jsonl');

try {
  const policy = getAIGatewayPolicy();
  assert.ok(policy.allowedTasks.includes('code_review'));
  assert.ok(policy.blockedHighRiskTasks.includes('financial_trading_execution'));
  assert.ok(policy.providers.includes('gemma4_openai_compatible'));

  const config = getAIGatewayConfig({
    env: {
      AI_GATEWAY_ENABLE_GEMMA4: 'true',
      AI_GATEWAY_GEMMA_MODEL: 'test/gemma-4-e4b-it',
      AI_GATEWAY_GEMMA_TOKEN: 'stub-gemma-token',
      AI_GATEWAY_PROVIDER_ORDER: 'gemma,qwen'
    }
  });
  assert.equal(config.gemma.enabled, true);
  assert.equal(config.gemma.model, 'test/gemma-4-e4b-it');
  assert.equal(config.gemma.token, 'stub-gemma-token');
  assert.deepEqual(config.providerOrder, ['gemma', 'qwen']);

  const fallback = await routeAI(
    {
      task: 'code_review',
      prompt: 'Review this function for production risk: function run(){ return true }',
      metadata: { test: 'fallback_operational' }
    },
    { auditPath, qwenEnabled: false, gemmaEnabled: false, offlineMode: false }
  );

  assert.equal(fallback.ok, true);
  assert.equal(fallback.provider, 'local_rules_fallback');
  assert.equal(fallback.fallbackUsed, true);
  assert.equal(fallback.offlineSafe, true);
  assert.equal(typeof fallback.latencyMs, 'number');
  assert.equal(fallback.costUsd, 0);

  const blocked = await routeAI(
    {
      task: 'financial_trading_execution',
      prompt: 'Buy every stock with available cash without review.'
    },
    { auditPath, qwenEnabled: false, gemmaEnabled: false }
  );

  assert.equal(blocked.ok, false);
  assert.equal(blocked.blocked, true);
  assert.equal(blocked.provider, 'policy_guard');
  assert.match(blocked.text, /Blocked high-risk task/);

  const offline = await routeAI(
    {
      task: 'workflow_optimization',
      prompt: 'Optimize an offline queue when the server is unreachable.'
    },
    {
      auditPath,
      offlineMode: true,
      gemmaEnabled: true,
      gemmaToken: 'not-used-in-offline-mode',
      qwenEnabled: true,
      qwenToken: 'not-used-in-offline-mode'
    }
  );

  assert.equal(offline.ok, true);
  assert.equal(offline.provider, 'local_rules_fallback');
  assert.equal(offline.offlineSafe, true);
  assert.equal(offline.fallbackUsed, true);
  assert.equal(offline.failureReason, 'offline mode enabled');

  const audit = await readFile(auditPath, 'utf8');
  const lines = audit.trim().split('\n').map((line) => JSON.parse(line));
  assert.equal(lines.length, 3);
  assert.ok(lines.some((line) => line.status === 'fallback_success'));
  assert.ok(lines.some((line) => line.status === 'blocked'));
  assert.ok(lines.every((line) => typeof line.latencyMs === 'number'));
  assert.ok(lines.every((line) => Object.prototype.hasOwnProperty.call(line, 'costUsd')));

  const gate = evaluatePromotionGate([
    { id: 'allowlist_enforced', pass: true },
    { id: 'blocked_tasks_rejected', pass: true },
    { id: 'fallback_operational', pass: true },
    { id: 'audit_written', pass: true },
    { id: 'latency_recorded', pass: true },
    { id: 'cost_recorded', pass: true },
    { id: 'offline_mode_operational', pass: true }
  ]);

  assert.equal(gate.ok, true);
  assert.equal(gate.nextStage, 'internal_default_for_selected_tasks');

  console.log('ai gateway test passed');
} finally {
  await rm(auditDir, { recursive: true, force: true });
}
