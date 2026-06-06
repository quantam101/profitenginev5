import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { evaluateSkillGatewayGate, loadSkillRegistry, routeSkill, selectSkill } from '../lib/skill-gateway.mjs';

const auditDir = await mkdtemp(join(tmpdir(), 'profitengine-skill-gateway-'));
const auditPath = join(auditDir, 'audit.jsonl');

try {
  const registry = await loadSkillRegistry();
  assert.equal(registry.system.name, 'ProfitEngineV5 Autonomous Skill Gateway');
  assert.ok(registry.skills.some((skill) => skill.id === 'rag-blueprint'));

  const selected = selectSkill(registry, { task: 'rag_design' });
  assert.equal(selected.ok, true);
  assert.equal(selected.selectedSkill.id, 'rag-blueprint');
  assert.equal(selected.requiresReview, false);

  const security = await routeSkill({ task: 'security_review' }, { auditPath, registry });
  assert.equal(security.ok, true);
  assert.equal(security.selectedSkill, 'nemoclaws-user-configure-security');
  assert.equal(security.offlineSafe, true);

  const offline = await routeSkill({ task: 'inference_configuration' }, { auditPath, registry, offlineMode: true });
  assert.equal(offline.ok, true);
  assert.equal(offline.fallbackUsed, true);
  assert.match(offline.result, /fallback mode/);

  const held = selectSkill(registry, { task: 'code_review' });
  assert.equal(held.ok, true);

  const gate = evaluateSkillGatewayGate([
    { id: 'registry_loaded', pass: true },
    { id: 'skill_auto_selection', pass: true },
    { id: 'restricted_action_rejected', pass: true },
    { id: 'high_risk_requires_review', pass: true },
    { id: 'audit_written', pass: true },
    { id: 'offline_fallback_operational', pass: true },
    { id: 'promotion_gate_blocks_unqualified_skill', pass: true }
  ]);
  assert.equal(gate.ok, true);
  assert.equal(gate.nextStage, 'production_allowed_for_selected_tasks');

  const audit = await readFile(auditPath, 'utf8');
  const lines = audit.trim().split('\n').map((line) => JSON.parse(line));
  assert.equal(lines.length, 2);
  assert.ok(lines.every((line) => line.event === 'skill_gateway_request'));
  assert.ok(lines.every((line) => typeof line.latencyMs === 'number'));

  console.log('skill gateway test passed');
} finally {
  await rm(auditDir, { recursive: true, force: true });
}
