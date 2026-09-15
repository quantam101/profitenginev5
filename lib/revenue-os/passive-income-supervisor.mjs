import { getDb } from '../mongodb.mjs';
import { getPassiveIncomeConfig, runPassiveIncomeCycle } from './passive-income-engine.mjs';
import {
  InMemoryExecutionStore,
  MongoExecutionStore,
  createExecutionControl,
} from './execution-control.mjs';
import { createControlledAIRoute } from './controlled-ai-route.mjs';
import { runIntelligentProcessMesh } from './intelligent-process-mesh.mjs';
import { buildDeliveryApprovalRequest, executeControlledDelivery } from './safe-delivery.mjs';

function bool(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return ['1', 'true', 'yes', 'on'].includes(String(value).toLowerCase());
}

function sanitizeForMesh(result) {
  return {
    id: result.id,
    agentId: result.agentId,
    lane: result.lane,
    qualityScore: result.qualityScore,
    profitScore: result.profitScore,
    ai: {
      ok: result.ai?.ok,
      provider: result.ai?.provider,
      model: result.ai?.model,
      costUsd: result.ai?.costUsd,
      data: result.ai?.data,
      build: result.ai?.build ? {
        ok: result.ai.build.ok,
        provider: result.ai.build.provider,
        model: result.ai.build.model,
        costUsd: result.ai.build.costUsd,
        data: result.ai.build.data,
      } : undefined,
    },
    artifactManifest: result.artifactManifest,
    sourceGate: result.sourceGate,
    platformGates: result.platformGates,
  };
}

function technicalDelivery(result) {
  return {
    resource: 'storefront:technical_product',
    payload: {
      lane: 'technical_product',
      packet: {
        id: result.id,
        qualityScore: result.qualityScore,
        profitScore: result.profitScore,
        artifactManifest: result.artifactManifest,
      },
    },
  };
}

function newsletterDelivery(result, config) {
  return {
    resource: `beehiiv:publication:${config.beehiiv.publicationId}`,
    payload: {
      title: result.ai?.data?.subject || 'Industry Briefing',
      body_content: JSON.stringify(result.ai?.data || { raw: result.ai?.text || '' }),
      status: 'draft',
    },
  };
}

function buildFetchAdapter({ url, token, fetchImpl = fetch }) {
  if (!url) return null;
  return async ({ payload, signal, idempotencyKey }) => {
    const response = await fetchImpl(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
      signal,
    });
    const raw = await response.text();
    let proof;
    try { proof = raw ? JSON.parse(raw) : null; } catch { proof = raw.slice(0, 1000); }
    return response.ok
      ? { ok: true, proof: { status: response.status, response: proof } }
      : { ok: false, reason: `Delivery adapter returned HTTP ${response.status}` };
  };
}

async function resolveExecutionStore({ store, env, production }) {
  if (store) return store;
  if (!production && bool(env.PASSIVE_INCOME_USE_MEMORY_CONTROL, false)) return new InMemoryExecutionStore();
  const db = await getDb();
  const mongoStore = new MongoExecutionStore(db);
  await mongoStore.ensureIndexes();
  return mongoStore;
}

function deliveryGateForLane(lane, mesh) {
  const global = ['portfolio_supervisor', 'independent_critic', 'delivery_controller'];
  const laneSpecific = lane === 'technical_product'
    ? ['technical_product_strategist', 'technical_product_builder', 'technical_product_verifier', 'seo_optimizer']
    : lane === 'newsletter'
      ? ['newsletter_researcher', 'newsletter_editor', 'seo_optimizer']
      : lane === 'stock_asset'
        ? ['stock_concept_designer', 'stock_compliance_reviewer', 'seo_optimizer']
        : [];
  const required = [...global, ...laneSpecific];
  const failures = required.filter((id) => mesh.outputs?.[id]?.status !== 'ready');
  return { allowed: failures.length === 0, failures };
}

function approvalTokenFor(input, lane) {
  return input?.approvalTokens?.[lane] || null;
}

export async function runHardenedPassiveIncomeCycle(input = {}, overrides = {}) {
  const env = overrides.env || process.env;
  const production = overrides.production ?? env.NODE_ENV === 'production';
  const store = await resolveExecutionStore({ store: overrides.executionStore, env, production });
  const executionControl = overrides.executionControl || createExecutionControl({
    store,
    approvalSecret: env.PASSIVE_INCOME_APPROVAL_SECRET || overrides.approvalSecret || '',
    clock: overrides.clock || (() => new Date()),
    circuitFailureThreshold: Number(env.PASSIVE_INCOME_CIRCUIT_FAILURE_THRESHOLD || 3),
    circuitResetMs: Number(env.PASSIVE_INCOME_CIRCUIT_RESET_MS || 300_000),
  });

  const deliveryConfig = getPassiveIncomeConfig(env);
  const safeEnv = { ...env, PASSIVE_INCOME_EXTERNAL_WRITES: 'false' };
  const generationConfig = getPassiveIncomeConfig(safeEnv);
  const controlledRouteAI = createControlledAIRoute({
    executionControl,
    config: generationConfig,
    env,
    fetchImpl: overrides.fetchImpl || fetch,
    zeroCostRouteAI: overrides.zeroCostRouteAI,
    routeAI: overrides.routeAI,
    routeAICapability: overrides.routeAICapability,
    clock: overrides.clock || (() => new Date()),
  });

  const generation = await runPassiveIncomeCycle(
    { ...input, publish: false },
    {
      routeAI: controlledRouteAI,
      env: safeEnv,
      config: generationConfig,
      fetchImpl: overrides.fetchImpl || fetch,
      clock: overrides.clock,
    },
  );

  const mesh = await runIntelligentProcessMesh(
    {
      runId: `passive-income:${generation.cycleId}`,
      context: {
        objective: input.objective || generation.plan?.objective,
        requestedPublish: input.publish === true,
        generation: {
          spendGate: generation.spendGate,
          metrics: generation.metrics,
          results: generation.results.map(sanitizeForMesh),
        },
      },
    },
    {
      zeroCostRouteAI: controlledRouteAI,
      executionControl,
      config: generationConfig,
      env,
      fetchImpl: overrides.fetchImpl || fetch,
      clock: overrides.clock || (() => new Date()),
    },
  );

  const deliveries = [];
  const approvalRequests = [];
  const publishRequested = input.publish === true;
  const writesEnabled = deliveryConfig.explicitExternalWrites === true;

  for (const result of generation.results) {
    const lane = result.lane;
    const laneGate = deliveryGateForLane(lane, mesh);
    if (!publishRequested || !writesEnabled || !laneGate.allowed || !generation.spendGate.allowed || result.ai?.ok === false) {
      deliveries.push({
        lane,
        attempted: false,
        ok: false,
        mode: 'gated',
        reasons: [
          ...(!publishRequested ? ['publish not requested'] : []),
          ...(!writesEnabled ? ['external writes disabled'] : []),
          ...(!generation.spendGate.allowed ? [generation.spendGate.reason] : []),
          ...(result.ai?.ok === false ? ['generation AI failed'] : []),
          ...laneGate.failures.map((id) => `${id} not ready`),
        ],
      });
      continue;
    }

    if (lane === 'stock_asset') {
      deliveries.push({ lane, attempted: false, ok: true, mode: 'reviewed_handoff', reasons: ['Stock contributor upload remains human-reviewed by platform policy.'] });
      continue;
    }

    let delivery;
    let adapter;
    if (lane === 'technical_product') {
      delivery = technicalDelivery(result);
      adapter = overrides.deliveryAdapters?.technical_product || buildFetchAdapter({
        url: deliveryConfig.storefrontWebhookUrl,
        token: deliveryConfig.workerToken,
        fetchImpl: overrides.fetchImpl || fetch,
      });
    } else if (lane === 'newsletter' && deliveryConfig.beehiiv.apiPublishEligible && deliveryConfig.beehiiv.apiKey && deliveryConfig.beehiiv.publicationId) {
      delivery = newsletterDelivery(result, deliveryConfig);
      adapter = overrides.deliveryAdapters?.newsletter || buildFetchAdapter({
        url: `https://api.beehiiv.com/v2/publications/${encodeURIComponent(deliveryConfig.beehiiv.publicationId)}/posts`,
        token: deliveryConfig.beehiiv.apiKey,
        fetchImpl: overrides.fetchImpl || fetch,
      });
    } else {
      deliveries.push({ lane, attempted: false, ok: false, mode: 'missing_adapter', reasons: ['No verified delivery adapter is configured.'] });
      continue;
    }

    const approvalRequest = buildDeliveryApprovalRequest({ lane, ...delivery });
    approvalRequests.push(approvalRequest);
    const executed = await executeControlledDelivery({
      lane,
      ...delivery,
      adapter,
      executionControl,
      approvalToken: approvalTokenFor(input, lane),
      production,
      store,
    });
    deliveries.push(executed);
  }

  const hardFailures = deliveries.filter((item) => item.mode === 'blocked' || (item.attempted && !item.ok));
  return {
    ok: generation.ok && mesh.ok && hardFailures.length === 0,
    mode: 'hardened_supervised_process_mesh',
    generation,
    mesh,
    deliveries,
    approvalRequests,
    policy: {
      generationExternalWrites: false,
      deliveryRequiresSignedApproval: true,
      deliveryIdempotent: true,
      durableProductionControl: true,
      zeroSpend: generationConfig.zeroSpend,
      learning: 'Lifelong Catch and Correct proposals only; source changes require tested pull requests',
    },
  };
}
