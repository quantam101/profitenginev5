import { routeAI as systemRouteAI } from '../ai-gateway.mjs';

function localOllamaRoute({ env = process.env, fetchImpl = fetch } = {}) {
  const baseUrl = String(env.PASSIVE_INCOME_OLLAMA_URL || env.OLLAMA_BASE_URL || 'http://127.0.0.1:11434').replace(/\/$/, '');
  const model = String(env.PASSIVE_INCOME_OLLAMA_MODEL || 'qwen2.5:14b');
  return {
    id: `ollama:${model}`,
    certifiedZeroCost: true,
    maxCallCostUsd: 0,
    async invoke(request) {
      const response = await fetchImpl(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          stream: false,
          format: 'json',
          messages: [
            { role: 'system', content: request.system || 'Return strict JSON only.' },
            { role: 'user', content: request.prompt },
          ],
          options: { temperature: Number(request.temperature ?? 0.15) },
        }),
        signal: AbortSignal.timeout(Number(env.PASSIVE_INCOME_OLLAMA_TIMEOUT_MS || 45_000)),
      });
      if (!response.ok) throw new Error(`Ollama request failed with HTTP ${response.status}`);
      const payload = await response.json();
      const text = payload?.message?.content;
      if (!text) throw new Error('Ollama response missing message content');
      return { ok: true, provider: 'ollama_local', model, text, costUsd: 0, fallbackUsed: false };
    },
  };
}

function injectedRoute(routeAI, capability = {}) {
  return {
    id: capability.id || 'injected_ai_route',
    certifiedZeroCost: capability.certifiedZeroCost === true,
    maxCallCostUsd: Number(capability.maxCallCostUsd || 0),
    invoke: (request) => routeAI(request, capability.overrides || {}),
  };
}

function gatewayRoute({ env = process.env } = {}) {
  return {
    id: 'system_ai_gateway',
    certifiedZeroCost: false,
    maxCallCostUsd: 0,
    invoke: (request) => systemRouteAI(request, { env }),
  };
}

function dayBucket(clock) {
  return `ai:${clock().toISOString().slice(0, 10)}`;
}

export function createControlledAIRoute({
  executionControl,
  config = {},
  env = process.env,
  fetchImpl = fetch,
  zeroCostRouteAI,
  routeAI,
  routeAICapability = {},
  clock = () => new Date(),
} = {}) {
  if (!executionControl) throw new Error('createControlledAIRoute requires executionControl');
  const zeroSpend = config.zeroSpend ?? true;
  const maxDailyAiSpendUsd = Number(config.maxDailyAiSpendUsd || 0);

  const provider = zeroCostRouteAI
    ? injectedRoute(zeroCostRouteAI, { id: 'injected_zero_cost_ai', certifiedZeroCost: true, maxCallCostUsd: 0 })
    : routeAI
      ? injectedRoute(routeAI, routeAICapability)
      : zeroSpend
        ? localOllamaRoute({ env, fetchImpl })
        : gatewayRoute({ env });

  return async function controlledRouteAI(request) {
    if (zeroSpend && !provider.certifiedZeroCost) {
      return {
        ok: false,
        blocked: true,
        provider: provider.id,
        costUsd: 0,
        reason: `Zero-spend preflight blocked ${provider.id}: route is not certified zero-cost`,
        text: '',
      };
    }

    let reservedUsd = 0;
    if (!zeroSpend && !provider.certifiedZeroCost) {
      if (!(provider.maxCallCostUsd > 0)) {
        return {
          ok: false,
          blocked: true,
          provider: provider.id,
          costUsd: 0,
          reason: `AI route ${provider.id} has no bounded maximum call cost`,
          text: '',
        };
      }
      const reservation = await executionControl.reserveBudget({
        bucket: dayBucket(clock),
        amountUsd: provider.maxCallCostUsd,
        maxUsd: maxDailyAiSpendUsd,
        zeroSpend: false,
      });
      if (!reservation.allowed) {
        return {
          ok: false,
          blocked: true,
          provider: provider.id,
          costUsd: 0,
          reason: `Daily AI budget blocked ${provider.id}`,
          text: '',
        };
      }
      reservedUsd = provider.maxCallCostUsd;
    }

    const circuit = await executionControl.beforeCircuitCall(`ai:${provider.id}`);
    if (!circuit.allowed) {
      return {
        ok: false,
        blocked: true,
        provider: provider.id,
        costUsd: 0,
        reason: `AI circuit ${circuit.mode} for ${provider.id}`,
        text: '',
      };
    }

    try {
      const result = await provider.invoke(request);
      const actualCostUsd = Number(result?.costUsd || 0);
      if (zeroSpend && actualCostUsd > 0) throw new Error(`Provider violated zero-spend contract with $${actualCostUsd}`);
      if (!zeroSpend && !provider.certifiedZeroCost && actualCostUsd > reservedUsd + Number.EPSILON) {
        throw new Error(`Provider exceeded reserved maximum call cost: ${actualCostUsd} > ${reservedUsd}`);
      }
      if (!result?.ok) throw new Error(result?.reason || result?.failureReason || 'AI provider returned not-ok');
      await executionControl.recordCircuitSuccess(`ai:${provider.id}`, circuit.probeOwner);
      return { ...result, costUsd: actualCostUsd };
    } catch (error) {
      await executionControl.recordCircuitFailure(`ai:${provider.id}`, circuit.probeOwner);
      return {
        ok: false,
        blocked: true,
        provider: provider.id,
        costUsd: 0,
        reason: error instanceof Error ? error.message : String(error),
        text: '',
      };
    }
  };
}
