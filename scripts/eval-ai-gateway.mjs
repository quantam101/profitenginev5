import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { evaluatePromotionGate, routeAI } from '../lib/ai-gateway.mjs';

const auditDir = await mkdtemp(join(tmpdir(), 'profitengine-ai-gateway-eval-'));
const auditPath = join(auditDir, 'audit.jsonl');
const checks = [];

async function check(id, fn) {
  try {
    await fn();
    checks.push({ id, pass: true });
  } catch (error) {
    checks.push({ id, pass: false, error: error instanceof Error ? error.message : String(error) });
  }
}

await check('allowlist_enforced', async () => {
  const result = await routeAI({ task: 'not_allowlisted', prompt: 'Run unsupported task.' }, { auditPath });
  if (result.ok !== false || result.provider !== 'policy_guard') throw new Error('unsupported task was not blocked');
});

await check('blocked_tasks_rejected', async () => {
  const result = await routeAI({ task: 'tax_decision', prompt: 'Make a tax decision without review.' }, { auditPath });
  if (result.ok !== false || result.riskLevel !== 'critical') throw new Error('high-risk task was not rejected');
});

await check('fallback_operational', async () => {
  const result = await routeAI({ task: 'summarization', prompt: 'Summarize operational risk.' }, { auditPath, qwenEnabled: false });
  if (!result.ok || result.provider !== 'local_rules_fallback') throw new Error('fallback provider failed');
});

await check('audit_written', async () => {
  const text = await readFile(auditPath, 'utf8');
  if (!text.includes('ai_gateway_request')) throw new Error('audit log missing gateway event');
});

await check('latency_recorded', async () => {
  const text = await readFile(auditPath, 'utf8');
  if (!/"latencyMs":/.test(text)) throw new Error('latency was not recorded');
});

await check('cost_recorded', async () => {
  const text = await readFile(auditPath, 'utf8');
  if (!/"costUsd":/.test(text)) throw new Error('cost was not recorded');
});

await check('offline_mode_operational', async () => {
  const result = await routeAI(
    { task: 'workflow_analysis', prompt: 'Analyze server-down behavior.' },
    { auditPath, offlineMode: true, qwenEnabled: true, qwenToken: 'offline-mode-does-not-call-provider' }
  );
  if (!result.ok || result.provider !== 'local_rules_fallback' || result.offlineSafe !== true) {
    throw new Error('offline mode did not return safe fallback output');
  }
});

const gate = evaluatePromotionGate(checks);
console.log(JSON.stringify({ checks, promotion: gate }, null, 2));
await rm(auditDir, { recursive: true, force: true });

if (!gate.ok) process.exitCode = 1;
