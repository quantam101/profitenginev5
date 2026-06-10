import { NextRequest, NextResponse } from 'next/server';
import { getAIGatewayConfig, getAIGatewayPolicy, routeAI } from '../../../lib/ai-gateway.mjs';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function json(data: unknown, status = 200) {
  return NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': 'no-store'
    }
  });
}

function isAuthorized(request: NextRequest) {
  const configuredToken = process.env.AI_GATEWAY_API_TOKEN || process.env.PROFITENGINE_WEBHOOK_TOKEN;
  if (!configuredToken) return true;

  const authHeader = request.headers.get('authorization') || '';
  const bearer = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';
  const headerToken = request.headers.get('x-profitengine-token') || '';

  return bearer === configuredToken || headerToken === configuredToken;
}

export async function GET() {
  const config = getAIGatewayConfig();
  return json({
    ok: true,
    gateway: 'profitenginev5-ai-gateway',
    providerOrder: config.providerOrder,
    providers: [
      {
        id: config.gemma.id,
        family: 'gemma4',
        enabled: config.gemma.enabled,
        stage: config.gemma.promotionStage,
        model: config.gemma.model,
        tokenConfigured: Boolean(config.gemma.token)
      },
      {
        id: config.qwen.id,
        family: 'qwen',
        enabled: config.qwen.enabled,
        stage: config.qwen.promotionStage,
        model: config.qwen.model,
        tokenConfigured: Boolean(config.qwen.token)
      },
      {
        id: config.fallback.id,
        family: 'deterministic_local',
        enabled: config.fallback.enabled,
        stage: 'always_available',
        tokenConfigured: true
      }
    ],
    policy: getAIGatewayPolicy()
  });
}

export async function POST(request: NextRequest) {
  if (!isAuthorized(request)) {
    return json({ ok: false, error: 'unauthorized' }, 401);
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'invalid_json' }, 400);
  }

  const task = typeof body.task === 'string' ? body.task : 'internal_planning';
  const prompt = typeof body.prompt === 'string' ? body.prompt : typeof body.input === 'string' ? body.input : '';

  if (!prompt.trim() && !Array.isArray(body.messages)) {
    return json({ ok: false, error: 'prompt_or_messages_required' }, 400);
  }

  const result = await routeAI({
    task,
    prompt,
    input: body.input,
    system: body.system,
    messages: body.messages,
    maxTokens: body.maxTokens,
    temperature: body.temperature,
    metadata: {
      source: 'api_route',
      route: '/api/ai-gateway',
      requestedAt: new Date().toISOString()
    }
  });

  return json(result, result.ok ? 200 : result.blocked ? 403 : 500);
}
