import { NextRequest, NextResponse } from 'next/server';
import { loadSkillRegistry, routeSkill } from '../../../lib/skill-gateway.mjs';

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
  const configuredToken = process.env.SKILL_GATEWAY_API_TOKEN || process.env.AI_GATEWAY_API_TOKEN || process.env.PROFITENGINE_WEBHOOK_TOKEN;
  if (!configuredToken) return true;

  const authHeader = request.headers.get('authorization') || '';
  const bearer = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';
  const headerToken = request.headers.get('x-profitengine-token') || '';

  return bearer === configuredToken || headerToken === configuredToken;
}

export async function GET() {
  const registry = await loadSkillRegistry();
  return json({
    ok: true,
    gateway: 'profitenginev5-skill-gateway',
    mode: registry.system?.mode || 'controlled_full_automation',
    autoSelect: registry.automation_policy?.auto_select_skill === true,
    autoFallback: registry.automation_policy?.auto_fallback === true,
    directSkillExecutionAllowed: registry.system?.direct_skill_execution_allowed === true,
    skills: registry.skills.map((skill: Record<string, unknown>) => ({
      id: skill.id,
      vendor: skill.vendor,
      status: skill.status,
      risk: skill.risk,
      autoEligible: skill.auto_eligible
    }))
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

  const task = typeof body.task === 'string' ? body.task : 'reference_lookup';
  const result = await routeSkill({
    task,
    requestId: typeof body.requestId === 'string' ? body.requestId : undefined,
    metadata: {
      source: 'api_route',
      route: '/api/skill-gateway',
      requestedAt: new Date().toISOString()
    }
  });

  return json(result, result.ok ? 200 : result.blocked ? 403 : 500);
}
