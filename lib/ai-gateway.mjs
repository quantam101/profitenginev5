import { appendFile, mkdir, readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

const DEFAULT_MODEL = 'nvidia/Qwen3.6-35B-A3B-NVFP4';
const DEFAULT_BASE_URL = 'https://integrate.api.nvidia.com/v1';
const DEFAULT_AUDIT_PATH = '.runtime/audit/ai-gateway.jsonl';
const BREAKER_FAILURE_THRESHOLD = 3;
const BREAKER_OPEN_MS = 300000;

export const ALLOWED_AI_GATEWAY_TASKS = Object.freeze([
  'agent_planning',
  'code_review',
  'document_analysis',
  'failure_analysis',
  'internal_planning',
  'offer_optimization',
  'rag_answering',
  'summarization',
  'workflow_analysis',
  'workflow_optimization'
]);

export const BLOCKED_HIGH_RISK_TASKS = Object.freeze([
  'autonomous_payment_action',
  'bulk_outreach_send',
  'credential_handling',
  'customer_facing_unreviewed_answer',
  'financial_trading_execution',
  'legal_decision',
  'medical_decision',
  'production_deploy_without_review',
  'security_change_without_review',
  'tax_decision'
]);

export const PROMOTION_STAGES = Object.freeze([
  'experimental',
  'internal_default_for_selected_tasks',
  'production_allowed'
]);

const allowedTasks = new Set(ALLOWED_AI_GATEWAY_TASKS);
const blockedTasks = new Set(BLOCKED_HIGH_RISK_TASKS);
const promotionStages = new Set(PROMOTION_STAGES);
const breakerState = new Map();

function boolFromEnv(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return ['1', 'true', 'yes', 'on'].includes(String(value).trim().toLowerCase());
}

function numberFromEnv(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function getSecret(env, names) {
  for (const name of names) {
    if (env[name] && String(env[name]).trim()) return String(env[name]).trim();
  }
  return '';
}

function sanitizeError(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/g, 'Bearer [redacted]')
    .replace(/token\s+[A-Za-z0-9._~+/=-]+/gi, 'token [redacted]')
    .slice(0, 800);
}

function estimateTokens(value) {
  const text = typeof value === 'string' ? value : JSON.stringify(value ?? '');
  return Math.max(1, Math.ceil(text.length / 4));
}

function estimateCostUsd({ promptTokens, completionTokens, inputPerMillion, outputPerMillion }) {
  return Number((((promptTokens / 1000000) * inputPerMillion) + ((completionTokens / 1000000) * outputPerMillion)).toFixed(8));
}

async function appendAudit(auditPath, event) {
  const fullPath = resolve(auditPath || DEFAULT_AUDIT_PATH);
  await mkdir(dirname(fullPath), { recursive: true });
  await appendFile(fullPath, `${JSON.stringify(event)}\n`, 'utf8');
}

function isBreakerOpen(providerId) {
  const state = breakerState.get(providerId);
  if (!state) return false;
  if (state.openUntil && state.openUntil > Date.now()) return true;
  if (state.openUntil && state.openUntil <= Date.now()) breakerState.delete(providerId);
  return false;
}

function recordFailure(providerId) {
  const current = breakerState.get(providerId) || { failures: 0, openUntil: 0 };
  const failures = current.failures + 1;
  breakerState.set(providerId, {
    failures,
    openUntil: failures >= BREAKER_FAILURE_THRESHOLD ? Date.now() + BREAKER_OPEN_MS : 0
  });
}

function recordSuccess(providerId) {
  breakerState.delete(providerId);
}

function normalizeMessages(input) {
  if (Array.isArray(input.messages) && input.messages.length) {
    return input.messages.map((message) => ({
      role: String(message.role || 'user'),
      content: String(message.content || '')
    }));
  }
  return [
    {
      role: 'system',
      content: String(input.system || 'You are ProfitEngineV5 AI Gateway. Produce secure, auditable, operational responses.')
    },
    {
      role: 'user',
      content: String(input.prompt ?? input.input ?? '')
    }
  ];
}

function policyForTask(task) {
  if (blockedTasks.has(task)) {
    return { allowed: false, riskLevel: 'critical', reason: `Blocked high-risk task: ${task}` };
  }
  if (!allowedTasks.has(task)) {
    return { allowed: false, riskLevel: 'high', reason: `Task is not allowlisted: ${task}` };
  }
  return { allowed: true, riskLevel: task.includes('code') || task.includes('failure') ? 'medium' : 'low', reason: 'Task allowed' };
}

export function getAIGatewayConfig(overrides = {}) {
  const env = overrides.env || process.env;
  const stage = overrides.promotionStage || env.AI_GATEWAY_QWEN_STAGE || 'experimental';
  return {
    env,
    auditPath: overrides.auditPath || env.AI_GATEWAY_AUDIT_PATH || DEFAULT_AUDIT_PATH,
    offlineMode: overrides.offlineMode ?? boolFromEnv(env.AI_GATEWAY_OFFLINE_MODE, false),
    timeoutMs: overrides.timeoutMs ?? numberFromEnv(env.AI_GATEWAY_TIMEOUT_MS, 30000),
    qwen: {
      id: 'nvidia_qwen_nvfp4',
      enabled: overrides.qwenEnabled ?? boolFromEnv(env.AI_GATEWAY_ENABLE_NVIDIA_QWEN, false),
      promotionStage: promotionStages.has(stage) ? stage : 'experimental',
      model: overrides.qwenModel || env.AI_GATEWAY_QWEN_MODEL || DEFAULT_MODEL,
      baseUrl: (overrides.qwenBaseUrl || env.AI_GATEWAY_QWEN_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, ''),
      token: overrides.qwenToken || getSecret(env, ['AI_GATEWAY_NVIDIA_TOKEN', 'NVIDIA_NIM_TOKEN', 'NVIDIA_API_TOKEN']),
      inputPerMillion: overrides.qwenInputPerMillion ?? numberFromEnv(env.AI_GATEWAY_QWEN_INPUT_USD_PER_MILLION, 0),
      outputPerMillion: overrides.qwenOutputPerMillion ?? numberFromEnv(env.AI_GATEWAY_QWEN_OUTPUT_USD_PER_MILLION, 0)
    },
    fallback: { id: 'local_rules_fallback', enabled: true }
  };
}

async function callNvidiaQwen({ config, messages, maxTokens, temperature, signal }) {
  if (!config.qwen.enabled) throw new Error('NVIDIA Qwen provider disabled by feature flag');
  if (!config.qwen.token) throw new Error('NVIDIA Qwen token not configured');
  if (isBreakerOpen(config.qwen.id)) throw new Error('NVIDIA Qwen circuit breaker is open');

  const response = await fetch(`${config.qwen.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.qwen.token}`,
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify({
      model: config.qwen.model,
      messages,
      temperature,
      max_tokens: maxTokens,
      stream: false
    }),
    signal
  });

  const raw = await response.text();
  if (!response.ok) throw new Error(`NVIDIA Qwen request failed with ${response.status}: ${raw.slice(0, 500)}`);
  const payload = JSON.parse(raw);
  const text = payload?.choices?.[0]?.message?.content;
  if (!text || typeof text !== 'string') throw new Error('NVIDIA Qwen response missing message content');
  const usage = payload.usage || {};
  return {
    text,
    model: payload.model || config.qwen.model,
    usage: {
      promptTokens: Number(usage.prompt_tokens || 0),
      completionTokens: Number(usage.completion_tokens || 0),
      totalTokens: Number(usage.total_tokens || 0)
    }
  };
}

function localRulesFallback({ task, messages, policy, reason }) {
  const digest = messages.map((message) => `${message.role}: ${message.content}`).join('\n').slice(0, 6000);
  const playbooks = {
    code_review: 'Check build errors, type safety, dependency risk, secrets exposure, missing tests, rollback gaps, and runtime failure modes.',
    failure_analysis: 'Classify the failure, identify root cause, assign owner, define correction, retest, and log the lesson.',
    workflow_optimization: 'Remove duplicate steps, add automation, queue unsafe work, add observability, preserve rollback, and measure throughput.',
    offer_optimization: 'Clarify buyer pain, measurable outcome, proof, price, urgency, delivery scope, and payment action.',
    agent_planning: 'Split work across orchestrator, revenue, product, QA, security, audit, offline, and recovery agents.',
    summarization: 'Extract objective, blockers, decisions, risks, owners, deadlines, and next executable actions.',
    rag_answering: 'Answer only from retrieved context, identify missing facts, and avoid unsupported claims.',
    document_analysis: 'Extract requirements, constraints, dependencies, risks, acceptance criteria, and action items.',
    internal_planning: 'Prioritize measurable actions, dependencies, risks, verification steps, and rollback.',
    workflow_analysis: 'Map current state, bottleneck, failure mode, control, and optimized future state.'
  };
  return [
    'Processed in deterministic offline-safe fallback mode.',
    `Fallback reason: ${reason || 'primary provider unavailable'}.`,
    `Task: ${task}. Risk: ${policy.riskLevel}.`,
    `Playbook: ${playbooks[task] || playbooks.internal_planning}`,
    'Next action: execute the safest measurable step, record the result, and retry cloud inference when provider health recovers.',
    `Input digest: ${digest}`
  ].join('\n');
}

async function withTimeout(timeoutMs, fn) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error(`AI Gateway timeout after ${timeoutMs}ms`)), timeoutMs);
  try {
    return await fn(controller.signal);
  } finally {
    clearTimeout(timer);
  }
}

export async function routeAI(input = {}, overrides = {}) {
  const startedAt = Date.now();
  const config = getAIGatewayConfig(overrides);
  const requestId = input.requestId || randomUUID();
  const task = String(input.task || 'internal_planning');
  const policy = policyForTask(task);
  const messages = normalizeMessages(input);
  const promptEstimate = estimateTokens(messages);
  const maxTokens = Number(input.maxTokens || 700);
  const temperature = Number(input.temperature ?? 0.2);
  const baseAudit = {
    event: 'ai_gateway_request',
    requestId,
    timestamp: new Date().toISOString(),
    task,
    policy,
    qwenStage: config.qwen.promotionStage,
    offlineMode: config.offlineMode,
    metadata: input.metadata || {}
  };

  if (!policy.allowed) {
    const latencyMs = Date.now() - startedAt;
    await appendAudit(config.auditPath, { ...baseAudit, status: 'blocked', provider: 'policy_guard', latencyMs, costUsd: 0 });
    return { ok: false, blocked: true, requestId, provider: 'policy_guard', task, riskLevel: policy.riskLevel, reason: policy.reason, text: policy.reason, latencyMs, costUsd: 0, fallbackUsed: false, offlineSafe: true, auditPath: config.auditPath };
  }

  let providerError = '';
  if (!config.offlineMode) {
    try {
      const result = await withTimeout(config.timeoutMs, (signal) => callNvidiaQwen({ config, messages, maxTokens, temperature, signal }));
      recordSuccess(config.qwen.id);
      const promptTokens = result.usage.promptTokens || promptEstimate;
      const completionTokens = result.usage.completionTokens || estimateTokens(result.text);
      const costUsd = estimateCostUsd({ promptTokens, completionTokens, inputPerMillion: config.qwen.inputPerMillion, outputPerMillion: config.qwen.outputPerMillion });
      const latencyMs = Date.now() - startedAt;
      await appendAudit(config.auditPath, { ...baseAudit, status: 'success', provider: config.qwen.id, model: result.model, latencyMs, costUsd, tokens: { prompt: promptTokens, completion: completionTokens, total: promptTokens + completionTokens }, fallbackUsed: false });
      return { ok: true, requestId, provider: config.qwen.id, model: result.model, task, riskLevel: policy.riskLevel, text: result.text, latencyMs, costUsd, tokens: { prompt: promptTokens, completion: completionTokens, total: promptTokens + completionTokens }, fallbackUsed: false, offlineSafe: false, auditPath: config.auditPath, promotionStage: config.qwen.promotionStage };
    } catch (error) {
      providerError = sanitizeError(error);
      recordFailure(config.qwen.id);
    }
  } else {
    providerError = 'offline mode enabled';
  }

  const text = localRulesFallback({ task, messages, policy, reason: providerError });
  const latencyMs = Date.now() - startedAt;
  await appendAudit(config.auditPath, { ...baseAudit, status: 'fallback_success', provider: config.fallback.id, failedProvider: config.qwen.id, failureReason: providerError, latencyMs, costUsd: 0, fallbackUsed: true });
  return { ok: true, requestId, provider: config.fallback.id, task, riskLevel: policy.riskLevel, text, latencyMs, costUsd: 0, fallbackUsed: true, offlineSafe: true, failureReason: providerError, auditPath: config.auditPath, promotionStage: config.qwen.promotionStage };
}

export function getAIGatewayPolicy() {
  return { allowedTasks: [...ALLOWED_AI_GATEWAY_TASKS], blockedHighRiskTasks: [...BLOCKED_HIGH_RISK_TASKS], promotionStages: [...PROMOTION_STAGES] };
}

export async function readAuditEvents(auditPath = DEFAULT_AUDIT_PATH) {
  const raw = await readFile(resolve(auditPath), 'utf8');
  return raw.trim().split('\n').filter(Boolean).map((line) => JSON.parse(line));
}

export function evaluatePromotionGate(results = []) {
  const required = ['allowlist_enforced', 'blocked_tasks_rejected', 'fallback_operational', 'audit_written', 'latency_recorded', 'cost_recorded', 'offline_mode_operational'];
  const passed = new Set(results.filter((item) => item?.pass).map((item) => item.id));
  const missing = required.filter((id) => !passed.has(id));
  return { ok: missing.length === 0, currentStage: 'experimental', nextStage: missing.length === 0 ? 'internal_default_for_selected_tasks' : 'experimental', missing, required };
}
