import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import { routeAI as systemRouteAI } from '../ai-gateway.mjs';

export const PROCESS_MESH_VERSION = '1.0.0';

const AgentEnvelopeSchema = z.object({
  status: z.enum(['ready', 'review_required', 'blocked']).default('review_required'),
  summary: z.string().min(1).max(4000),
  confidence: z.number().min(0).max(100),
  evidence: z.array(z.object({
    claim: z.string().min(1).max(1000),
    source: z.string().min(1).max(2000),
    verified: z.boolean(),
  })).max(30).default([]),
  risks: z.array(z.string().max(1000)).max(30).default([]),
  actions: z.array(z.object({
    action: z.string().min(1).max(1000),
    priority: z.enum(['P0', 'P1', 'P2', 'P3']).default('P2'),
    externalWrite: z.boolean().default(false),
    requiresApproval: z.boolean().default(false),
  })).max(30).default([]),
  artifacts: z.array(z.object({
    kind: z.string().min(1).max(100),
    name: z.string().min(1).max(300),
    content: z.unknown(),
  })).max(20).default([]),
  handoff: z.string().max(3000).default(''),
});

const NO_EXTERNAL_AUTHORITY = Object.freeze({
  canSpend: false,
  canPublish: false,
  canSendEmail: false,
  canDeploy: false,
  canMerge: false,
  canAcceptTerms: false,
  canModifyProduction: false,
});

export const PROCESS_AGENTS = Object.freeze({
  portfolio_supervisor: {
    name: 'Portfolio Supervisor AI',
    task: 'agent_planning',
    mission: 'Prioritize the portfolio, route work to specialist agents, reconcile contradictions, and optimize risk-adjusted time-to-cash.',
    stage: 0,
    dependsOn: [],
  },
  opportunity_researcher: {
    name: 'Opportunity Research AI',
    task: 'workflow_analysis',
    mission: 'Identify evidence-backed demand, buyer pain, monetization paths, competitive pressure, and time-to-cash without inventing market facts.',
    stage: 1,
    dependsOn: ['portfolio_supervisor'],
  },
  analytics_analyst: {
    name: 'Revenue Analytics AI',
    task: 'workflow_analysis',
    mission: 'Analyze supplied traffic, conversion, revenue, cost, and fulfillment evidence and identify the highest-leverage bottleneck.',
    stage: 1,
    dependsOn: ['portfolio_supervisor'],
  },
  technical_product_strategist: {
    name: 'Technical Product Strategy AI',
    task: 'offer_optimization',
    mission: 'Convert verified technical expertise and buyer pain into a narrow product offer with scope, price hypothesis, proof requirements, and acceptance criteria.',
    stage: 2,
    dependsOn: ['opportunity_researcher', 'analytics_analyst'],
  },
  stock_concept_designer: {
    name: 'Stock Concept Design AI',
    task: 'workflow_optimization',
    mission: 'Design differentiated stock-asset concepts, metadata, and production specifications while excluding trademark, likeness, artist-style, and third-party-IP risk.',
    stage: 2,
    dependsOn: ['opportunity_researcher'],
  },
  newsletter_researcher: {
    name: 'Briefing Research AI',
    task: 'document_analysis',
    mission: 'Transform supplied sources into traceable briefing research, separating verified facts, inference, and unresolved claims.',
    stage: 2,
    dependsOn: ['opportunity_researcher'],
  },
  technical_product_builder: {
    name: 'Technical Product Builder AI',
    task: 'workflow_optimization',
    mission: 'Build the product content, code-bundle specification, documentation, validation checklist, and storefront package from the approved strategy.',
    stage: 3,
    dependsOn: ['technical_product_strategist'],
  },
  stock_compliance_reviewer: {
    name: 'Stock Compliance Review AI',
    task: 'code_review',
    mission: 'Independently challenge stock concepts for IP, disclosure, similarity, release, metadata, quality, and platform-policy risk; fail closed when evidence is missing.',
    stage: 3,
    dependsOn: ['stock_concept_designer'],
  },
  newsletter_editor: {
    name: 'Newsletter Editor AI',
    task: 'summarization',
    mission: 'Create a concise, useful, source-traceable briefing with claim discipline, monetization disclosure, and explicit unresolved-fact markers.',
    stage: 3,
    dependsOn: ['newsletter_researcher'],
  },
  technical_product_verifier: {
    name: 'Technical Product Verification AI',
    task: 'code_review',
    mission: 'Independently verify completeness, technical safety, originality, runnable instructions, test evidence, claim support, and buyer usability. Reject unsupported quality claims.',
    stage: 4,
    dependsOn: ['technical_product_builder'],
  },
  seo_optimizer: {
    name: 'SEO and Discovery AI',
    task: 'offer_optimization',
    mission: 'Optimize discoverability from supplied evidence without keyword stuffing, fabricated volume claims, misleading promises, or unsupported rankings.',
    stage: 4,
    dependsOn: ['technical_product_builder', 'newsletter_editor', 'stock_compliance_reviewer'],
  },
  independent_critic: {
    name: 'Independent Critic AI',
    task: 'failure_analysis',
    mission: 'Red-team all proposed outputs for contradictions, missing evidence, unsafe assumptions, policy bypasses, fragile dependencies, and hidden variable cost.',
    stage: 5,
    dependsOn: ['technical_product_verifier', 'seo_optimizer', 'stock_compliance_reviewer', 'newsletter_editor'],
  },
  delivery_controller: {
    name: 'Delivery Controller AI',
    task: 'internal_planning',
    mission: 'Prepare an executable delivery plan with idempotency keys, approval requirements, rollback points, destination constraints, and zero-spend checks. Never execute external writes itself.',
    stage: 5,
    dependsOn: ['technical_product_verifier', 'seo_optimizer', 'stock_compliance_reviewer', 'newsletter_editor'],
  },
  catch_correct_optimizer: {
    name: 'Lifelong Catch and Correct AI',
    task: 'failure_analysis',
    mission: 'Learn from evidence, failures, corrections, and performance deltas; propose bounded prompt, heuristic, test, or workflow improvements. Source-code changes are PR-only after tests.',
    stage: 6,
    dependsOn: ['independent_critic', 'delivery_controller'],
  },
});

export function getProcessAgentManifest() {
  return Object.entries(PROCESS_AGENTS).map(([id, agent]) => ({
    id,
    ...agent,
    authority: NO_EXTERNAL_AUTHORITY,
    outputContract: 'AgentEnvelope/v1',
  }));
}

function stripJsonFence(text) {
  const value = String(text || '').trim();
  const fenced = value.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  return fenced ? fenced[1].trim() : value;
}

function parseAgentEnvelope(text) {
  let parsed;
  try {
    parsed = JSON.parse(stripJsonFence(text));
  } catch (error) {
    throw new Error(`Agent returned invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
  }
  return AgentEnvelopeSchema.parse(parsed);
}

function compactContext(value, maxChars = 24_000) {
  const json = JSON.stringify(value ?? {});
  return json.length <= maxChars ? json : `${json.slice(0, maxChars)}…[truncated]`;
}

function promptForAgent(id, agent, input, dependencies) {
  return [
    `You are ${agent.name}, a specialist process agent inside ProfitEngineV5.`,
    `Mission: ${agent.mission}`,
    'Operate as a high-reliability expert. Challenge weak assumptions. Prefer measurable evidence over confidence language.',
    'You have NO authority to spend money, publish externally, send email, deploy, merge code, accept legal terms, or modify production.',
    'If a proposed action would do any of those things, set externalWrite=true and requiresApproval=true. Do not imply it already happened.',
    'Never fabricate citations, test results, revenue, traffic, platform state, credentials, or completion evidence.',
    'Return ONLY JSON matching this exact envelope:',
    '{"status":"ready|review_required|blocked","summary":"...","confidence":0,"evidence":[{"claim":"...","source":"...","verified":false}],"risks":["..."],"actions":[{"action":"...","priority":"P0|P1|P2|P3","externalWrite":false,"requiresApproval":false}],"artifacts":[{"kind":"...","name":"...","content":{}}],"handoff":"..."}',
    `Process id: ${id}`,
    `Input: ${compactContext(input)}`,
    `Dependency outputs: ${compactContext(dependencies)}`,
  ].join('\n');
}

function deterministicEnvelope(id, reason, dependencies = {}) {
  return {
    status: 'review_required',
    summary: `${PROCESS_AGENTS[id].name} could not obtain validated AI output; deterministic fail-safe preserved the workflow for review.`,
    confidence: 0,
    evidence: [],
    risks: [String(reason || 'AI output unavailable')],
    actions: [{ action: `Review ${id} input/output and restore a certified zero-cost AI route`, priority: 'P1', externalWrite: false, requiresApproval: false }],
    artifacts: [{ kind: 'diagnostic', name: `${id}-dependency-snapshot`, content: dependencies }],
    handoff: 'No consequential action is authorized from this fallback result.',
  };
}

function localOllamaInvoker(env = process.env, fetchImpl = fetch) {
  const baseUrl = String(env.PASSIVE_INCOME_OLLAMA_URL || env.OLLAMA_BASE_URL || 'http://127.0.0.1:11434').replace(/\/$/, '');
  const model = String(env.PASSIVE_INCOME_OLLAMA_MODEL || 'qwen2.5:14b');
  return {
    id: `ollama:${model}`,
    costClass: 'zero',
    async invoke(request) {
      const response = await fetchImpl(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          stream: false,
          format: 'json',
          messages: [
            { role: 'system', content: 'Return strict JSON only. Follow the requested schema and authority boundaries.' },
            { role: 'user', content: request.prompt },
          ],
          options: { temperature: 0.15 },
        }),
        signal: AbortSignal.timeout(Number(env.PASSIVE_INCOME_OLLAMA_TIMEOUT_MS || 45_000)),
      });
      if (!response.ok) throw new Error(`Ollama request failed with HTTP ${response.status}`);
      const payload = await response.json();
      const text = payload?.message?.content;
      if (!text) throw new Error('Ollama response missing message content');
      return { ok: true, provider: 'ollama_local', model, text, costUsd: 0, offlineSafe: true };
    },
  };
}

function customInvoker(route, capability = {}) {
  return {
    id: capability.id || 'injected_ai_route',
    costClass: capability.certifiedZeroCost ? 'zero' : (capability.maxCallCostUsd > 0 ? 'bounded' : 'unknown'),
    maxCallCostUsd: Number(capability.maxCallCostUsd || 0),
    async invoke(request) {
      return route(request, capability.overrides || {});
    },
  };
}

function gatewayInvoker(env = process.env) {
  return {
    id: 'system_ai_gateway',
    costClass: 'unknown',
    maxCallCostUsd: 0,
    async invoke(request) {
      return systemRouteAI(request, { env });
    },
  };
}

function selectInvoker(config, deps) {
  if (deps.zeroCostRouteAI) return customInvoker(deps.zeroCostRouteAI, { id: 'injected_zero_cost_ai', certifiedZeroCost: true });
  if (deps.routeAI) return customInvoker(deps.routeAI, deps.routeAICapability || {});
  if (config.zeroSpend) return localOllamaInvoker(deps.env, deps.fetchImpl);
  return gatewayInvoker(deps.env);
}

function budgetBucket(clock) {
  return `ai:${clock().toISOString().slice(0, 10)}`;
}

async function invokeWithControls({ id, agent, prompt, config, deps, executionControl }) {
  const invoker = selectInvoker(config, deps);
  if (config.zeroSpend && invoker.costClass !== 'zero') {
    throw new Error(`Zero-spend preflight blocked AI route ${invoker.id}; route is not certified zero-cost`);
  }

  let reserved = 0;
  if (!config.zeroSpend && invoker.costClass !== 'zero') {
    if (invoker.costClass !== 'bounded' || !(invoker.maxCallCostUsd > 0)) {
      throw new Error(`AI route ${invoker.id} has unknown maximum call cost; refusing unbounded invocation`);
    }
    const reservation = await executionControl.reserveBudget({
      bucket: budgetBucket(deps.clock),
      amountUsd: invoker.maxCallCostUsd,
      maxUsd: config.maxDailyAiSpendUsd,
      zeroSpend: false,
    });
    if (!reservation.allowed) throw new Error(`Daily AI budget blocked ${invoker.id}`);
    reserved = invoker.maxCallCostUsd;
  }

  const circuit = await executionControl.beforeCircuitCall(`ai:${invoker.id}`);
  if (!circuit.allowed) throw new Error(`AI circuit ${circuit.mode} for ${invoker.id}`);
  try {
    const result = await invoker.invoke({
      task: agent.task,
      prompt,
      maxTokens: 1800,
      temperature: 0.15,
      metadata: { processAgent: id, processMeshVersion: PROCESS_MESH_VERSION },
    });
    if (!result?.ok) throw new Error(result?.reason || 'AI route returned not-ok');
    const actualCost = Number(result.costUsd || 0);
    if (config.zeroSpend && actualCost > 0) throw new Error(`AI route violated zero-spend contract with $${actualCost}`);
    if (!config.zeroSpend && actualCost > reserved + Number.EPSILON) {
      throw new Error(`AI route exceeded reserved maximum cost: ${actualCost} > ${reserved}`);
    }
    await executionControl.recordCircuitSuccess(`ai:${invoker.id}`, circuit.probeOwner);
    return { result, invoker: invoker.id };
  } catch (error) {
    await executionControl.recordCircuitFailure(`ai:${invoker.id}`, circuit.probeOwner);
    throw error;
  }
}

function validateAuthority(envelope) {
  for (const action of envelope.actions) {
    if (action.externalWrite && !action.requiresApproval) {
      action.requiresApproval = true;
    }
  }
  return envelope;
}

export function buildProcessMeshPlan(selectedAgentIds = Object.keys(PROCESS_AGENTS)) {
  const selected = new Set(selectedAgentIds);
  return [...new Set(Object.values(PROCESS_AGENTS).map((agent) => agent.stage))]
    .sort((a, b) => a - b)
    .map((stage) => Object.entries(PROCESS_AGENTS)
      .filter(([id, agent]) => agent.stage === stage && selected.has(id))
      .map(([id]) => id))
    .filter((stage) => stage.length);
}

export async function runIntelligentProcessMesh(input = {}, deps = {}) {
  const config = {
    zeroSpend: deps.config?.zeroSpend ?? true,
    maxDailyAiSpendUsd: Number(deps.config?.maxDailyAiSpendUsd || 0),
  };
  const clock = deps.clock || (() => new Date());
  const executionControl = deps.executionControl;
  if (!executionControl) throw new Error('Intelligent process mesh requires executionControl');

  const selectedAgentIds = Array.isArray(input.processAgents) && input.processAgents.length
    ? input.processAgents.filter((id) => PROCESS_AGENTS[id])
    : Object.keys(PROCESS_AGENTS);
  const stages = buildProcessMeshPlan(selectedAgentIds);
  const outputs = {};
  const events = [];
  const runId = input.runId || randomUUID();

  for (const stage of stages) {
    const completed = await Promise.all(stage.map(async (id) => {
      const agent = PROCESS_AGENTS[id];
      const missingDependency = agent.dependsOn.find((dependency) => selectedAgentIds.includes(dependency) && !outputs[dependency]);
      if (missingDependency) {
        return [id, deterministicEnvelope(id, `Missing dependency ${missingDependency}`), { provider: 'deterministic_dependency_guard' }];
      }
      const dependencyOutputs = Object.fromEntries(agent.dependsOn.filter((dependency) => outputs[dependency]).map((dependency) => [dependency, outputs[dependency]]));
      const prompt = promptForAgent(id, agent, input.context || input, dependencyOutputs);
      const key = `mesh:${runId}:${id}`;
      try {
        const once = await executionControl.runOnce({
          key,
          payload: { id, prompt, version: PROCESS_MESH_VERSION },
          execute: async () => {
            const invoked = await invokeWithControls({ id, agent, prompt, config, deps: { ...deps, clock }, executionControl });
            const envelope = validateAuthority(parseAgentEnvelope(invoked.result.text));
            return { envelope, provider: invoked.invoker, ai: { provider: invoked.result.provider, model: invoked.result.model, costUsd: Number(invoked.result.costUsd || 0) } };
          },
        });
        if (once.status === 'busy') return [id, deterministicEnvelope(id, 'Concurrent execution already owns this process lease'), { provider: 'lease_guard' }];
        return [id, once.result.envelope, { provider: once.result.provider, ai: once.result.ai, replayed: once.replayed }];
      } catch (error) {
        return [id, deterministicEnvelope(id, error instanceof Error ? error.message : String(error), dependencyOutputs), { provider: 'deterministic_fail_safe' }];
      }
    }));

    for (const [id, envelope, meta] of completed) {
      outputs[id] = envelope;
      events.push({ runId, agentId: id, stage: PROCESS_AGENTS[id].stage, timestamp: clock().toISOString(), status: envelope.status, confidence: envelope.confidence, ...meta });
    }
  }

  const critic = outputs.independent_critic;
  const blocked = Object.entries(outputs).filter(([, output]) => output.status === 'blocked').map(([id]) => id);
  const reviewRequired = Object.entries(outputs).filter(([, output]) => output.status === 'review_required').map(([id]) => id);
  const externalActionRequests = Object.entries(outputs).flatMap(([agentId, output]) => output.actions
    .filter((action) => action.externalWrite)
    .map((action) => ({ agentId, ...action, requiresApproval: true })));

  return {
    ok: blocked.length === 0 && Boolean(critic) && critic.status !== 'blocked',
    runId,
    version: PROCESS_MESH_VERSION,
    policy: {
      zeroSpend: config.zeroSpend,
      specialistExternalAuthority: false,
      consequentialWrites: 'execution_control_only',
      productionCodeLearning: 'pull_request_only_after_tests',
    },
    stages,
    outputs,
    events,
    externalActionRequests,
    reviewRequired,
    blocked,
  };
}
