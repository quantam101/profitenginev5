import { appendFile, mkdir, readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

const DEFAULT_REGISTRY_PATH = 'config/ai-skills.registry.json';
const DEFAULT_AUDIT_PATH = '.runtime/audit/skill-gateway.jsonl';

const TASK_TO_ACTIONS = Object.freeze({
  rag_design: ['rag_design', 'reference_lookup'],
  inference_configuration: ['inference_configuration_advice', 'reference_lookup'],
  security_review: ['security_configuration_review', 'reference_lookup'],
  workflow_analysis: ['workflow_analysis', 'reference_lookup'],
  agent_planning: ['agent_planning', 'reference_lookup'],
  code_review: ['code_review', 'reference_lookup'],
  documentation_generation: ['documentation_generation', 'reference_lookup'],
  reference_lookup: ['reference_lookup']
});

const SAFE_STATUSES = new Set(['approved_reference']);
const REVIEW_STATUSES = new Set(['sandbox_only', 'held_for_later', 'blocked_until_approval', 'quarantined']);

function nowIso() {
  return new Date().toISOString();
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

async function appendAudit(auditPath, event) {
  const fullPath = resolve(auditPath || DEFAULT_AUDIT_PATH);
  await mkdir(dirname(fullPath), { recursive: true });
  await appendFile(fullPath, `${JSON.stringify(event)}\n`, 'utf8');
}

export async function loadSkillRegistry(path = DEFAULT_REGISTRY_PATH) {
  const raw = await readFile(resolve(path), 'utf8');
  const parsed = JSON.parse(raw);
  if (!parsed.system || !Array.isArray(parsed.skills)) {
    throw new Error('Invalid skill registry: expected system and skills');
  }
  return parsed;
}

function restrictedActionSet(registry) {
  return new Set(asArray(registry.restricted_actions));
}

function allowedActionSet(registry) {
  return new Set(asArray(registry.allowed_actions));
}

function actionPlanForTask(task) {
  return TASK_TO_ACTIONS[task] || ['reference_lookup'];
}

function scoreSkill(skill, requestedActions) {
  const skillActions = new Set(asArray(skill.allowed_actions));
  const matches = requestedActions.filter((action) => skillActions.has(action)).length;
  const statusWeight = SAFE_STATUSES.has(skill.status) ? 10 : 0;
  const autoWeight = skill.auto_eligible ? 5 : 0;
  const riskPenalty = skill.risk === 'critical' ? 10 : skill.risk === 'high' ? 5 : skill.risk === 'medium' ? 1 : 0;
  return matches * 20 + statusWeight + autoWeight - riskPenalty;
}

export function selectSkill(registry, request = {}) {
  const task = String(request.task || 'reference_lookup');
  const requestedActions = actionPlanForTask(task);
  const allowed = allowedActionSet(registry);
  const restricted = restrictedActionSet(registry);

  for (const action of requestedActions) {
    if (restricted.has(action)) {
      return {
        ok: false,
        blocked: true,
        task,
        requestedActions,
        reason: `Restricted action requested: ${action}`,
        selectedSkill: null,
        requiresReview: true
      };
    }
    if (!allowed.has(action)) {
      return {
        ok: false,
        blocked: true,
        task,
        requestedActions,
        reason: `Action is not allowlisted: ${action}`,
        selectedSkill: null,
        requiresReview: true
      };
    }
  }

  const candidates = registry.skills
    .filter((skill) => skill.auto_eligible === true)
    .map((skill) => ({ skill, score: scoreSkill(skill, requestedActions) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);

  const selected = candidates[0]?.skill || null;
  if (!selected) {
    return {
      ok: true,
      task,
      requestedActions,
      selectedSkill: null,
      status: 'fallback',
      requiresReview: false,
      reason: 'No auto-eligible skill matched; use local fallback playbook'
    };
  }

  return {
    ok: true,
    task,
    requestedActions,
    selectedSkill: selected,
    status: selected.status,
    requiresReview: REVIEW_STATUSES.has(selected.status) || selected.risk === 'critical',
    reason: 'Skill selected by registry policy'
  };
}

function fallbackOutput({ task, selection }) {
  const playbooks = {
    rag_design: 'Use local RAG blueprint: define corpus, access control, chunking, retrieval, reranking, citations, eval set, latency budget, and refresh schedule.',
    inference_configuration: 'Use local inference playbook: define provider order, timeout, budget, model task fit, health check, fallback, and audit fields.',
    security_review: 'Use local security playbook: least privilege, server-side tokens, audit log, allowlist, network boundary, recovery path, and review gate.',
    workflow_analysis: 'Use local workflow playbook: map current state, bottleneck, failure path, queue, retry, owner, metric, and rollback.',
    agent_planning: 'Use local agent playbook: split work across orchestrator, skill router, policy guard, evaluator, audit, and recovery agents.',
    code_review: 'Use local code playbook: check build, types, tests, input validation, provider failure handling, audit logging, and rollback.',
    documentation_generation: 'Use local documentation playbook: state purpose, configuration, operation, limits, risk controls, tests, and promotion path.',
    reference_lookup: 'Use local reference playbook: summarize the known registry record and flag missing source details.'
  };

  return [
    'Skill Gateway fallback mode.',
    `Task: ${task}.`,
    `Reason: ${selection.reason}.`,
    `Playbook: ${playbooks[task] || playbooks.reference_lookup}`
  ].join('\n');
}

export async function routeSkill(request = {}, overrides = {}) {
  const startedAt = Date.now();
  const auditPath = overrides.auditPath || process.env.SKILL_GATEWAY_AUDIT_PATH || DEFAULT_AUDIT_PATH;
  const registry = overrides.registry || await loadSkillRegistry(overrides.registryPath || process.env.SKILL_GATEWAY_REGISTRY_PATH || DEFAULT_REGISTRY_PATH);
  const requestId = request.requestId || randomUUID();
  const task = String(request.task || 'reference_lookup');
  const selection = selectSkill(registry, { task });
  const offlineMode = overrides.offlineMode ?? process.env.SKILL_GATEWAY_OFFLINE_MODE === 'true';

  if (!selection.ok || selection.blocked) {
    const latencyMs = Date.now() - startedAt;
    await appendAudit(auditPath, {
      event: 'skill_gateway_request',
      requestId,
      timestamp: nowIso(),
      status: 'blocked',
      task,
      selection,
      latencyMs
    });
    return {
      ok: false,
      blocked: true,
      requestId,
      task,
      reason: selection.reason,
      selectedSkill: null,
      requiresReview: true,
      latencyMs,
      auditPath
    };
  }

  const selectedSkill = selection.selectedSkill;
  const fallbackUsed = offlineMode || !selectedSkill || selection.requiresReview;
  const result = fallbackUsed
    ? fallbackOutput({ task, selection })
    : `Selected skill ${selectedSkill.id} for ${task}. Use as reference-only autonomous guidance through the AI Gateway policy layer.`;

  const latencyMs = Date.now() - startedAt;
  await appendAudit(auditPath, {
    event: 'skill_gateway_request',
    requestId,
    timestamp: nowIso(),
    status: fallbackUsed ? 'fallback_success' : 'selected',
    task,
    selectedSkill: selectedSkill ? selectedSkill.id : null,
    skillStatus: selectedSkill ? selectedSkill.status : null,
    requiresReview: selection.requiresReview,
    offlineMode,
    fallbackUsed,
    latencyMs
  });

  return {
    ok: true,
    requestId,
    task,
    selectedSkill: selectedSkill ? selectedSkill.id : null,
    skillStatus: selectedSkill ? selectedSkill.status : null,
    requiresReview: selection.requiresReview,
    fallbackUsed,
    offlineSafe: true,
    result,
    latencyMs,
    auditPath
  };
}

export function evaluateSkillGatewayGate(results = []) {
  const required = [
    'registry_loaded',
    'skill_auto_selection',
    'restricted_action_rejected',
    'high_risk_requires_review',
    'audit_written',
    'offline_fallback_operational',
    'promotion_gate_blocks_unqualified_skill'
  ];
  const passed = new Set(results.filter((item) => item?.pass).map((item) => item.id));
  const missing = required.filter((id) => !passed.has(id));
  return {
    ok: missing.length === 0,
    currentStage: 'controlled_full_automation',
    nextStage: missing.length === 0 ? 'production_allowed_for_selected_tasks' : 'controlled_full_automation',
    missing,
    required
  };
}
