import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { evaluateSkillGatewayGate, loadSkillRegistry, routeSkill, selectSkill } from '../lib/skill-gateway.mjs';

const auditDir = await mkdtemp(join(tmpdir(), 'profitengine-skill-gateway-eval-'));
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

let registry;
await check('registry_loaded', async () => {
  registry = await loadSkillRegistry();
  if (!registry.skills.length) throw new Error('registry contains no skills');
});

await check('skill_auto_selection', async () => {
  const result = selectSkill(registry, { task: 'rag_design' });
  if (!result.ok || result.selectedSkill?.id !== 'rag-blueprint') throw new Error('rag-blueprint was not selected');
});

await check('restricted_action_rejected', async () => {
  const restrictedRegistry = {
    ...registry,
    allowed_actions: ['reference_lookup'],
    restricted_actions: ['rag_design']
  };
  const result = selectSkill(restrictedRegistry, { task: 'rag_design' });
  if (!result.blocked) throw new Error('restricted action was not rejected');
});

await check('high_risk_requires_review', async () => {
  const skill = registry.skills.find((item) => item.id === 'nemoclaws-user-deploy-remote');
  if (!skill || skill.risk !== 'critical' || skill.auto_eligible !== false) throw new Error('critical skill is not review-gated');
});

await check('audit_written', async () => {
  await routeSkill({ task: 'security_review' }, { auditPath, registry });
  const text = await readFile(auditPath, 'utf8');
  if (!text.includes('skill_gateway_request')) throw new Error('audit event not written');
});

await check('offline_fallback_operational', async () => {
  const result = await routeSkill({ task: 'inference_configuration' }, { auditPath, registry, offlineMode: true });
  if (!result.ok || result.fallbackUsed !== true || result.offlineSafe !== true) throw new Error('offline fallback failed');
});

await check('promotion_gate_blocks_unqualified_skill', async () => {
  const gate = evaluateSkillGatewayGate([{ id: 'registry_loaded', pass: true }]);
  if (gate.ok || gate.nextStage !== 'controlled_full_automation') throw new Error('promotion gate did not block incomplete eval');
});

const gate = evaluateSkillGatewayGate(checks);
console.log(JSON.stringify({ checks, promotion: gate }, null, 2));
await rm(auditDir, { recursive: true, force: true });

if (!gate.ok) process.exitCode = 1;
