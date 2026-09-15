import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { routePassiveIncomeAI } from '@/lib/revenue-os/passive-income-ai.mjs';
import {
  buildSupervisorPlan,
  getPassiveIncomeConfig,
  runPassiveIncomeCycle,
} from '@/lib/revenue-os/passive-income-engine.mjs';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 300;

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

function json(data: unknown, status = 200) {
  return NextResponse.json(data, { status, headers: NO_STORE });
}

async function requireSession() {
  const session = await getServerSession(authOptions);
  return session?.user ? session : null;
}

export async function GET() {
  const session = await requireSession();
  if (!session) return json({ ok: false, error: 'Unauthorized' }, 401);

  const config = getPassiveIncomeConfig(process.env);
  return json({
    ok: true,
    plan: buildSupervisorPlan({}, process.env),
    readiness: {
      revenueOsEnabled: process.env.REVENUE_OS_ENABLED === 'true',
      zeroSpend: config.zeroSpend,
      externalWrites: config.explicitExternalWrites,
      offlineProductionKernel: true,
      workerConfigured: Boolean(config.workerWebhookUrl),
      storefrontAdapterConfigured: Boolean(config.storefrontWebhookUrl),
      beehiiv: {
        plan: config.beehiiv.plan || 'unconfigured',
        publicationConfigured: Boolean(config.beehiiv.publicationId),
        apiKeyConfigured: Boolean(config.beehiiv.apiKey),
        apiPublishEligible: config.beehiiv.apiPublishEligible,
      },
    },
  });
}

export async function POST(request: NextRequest) {
  const session = await requireSession();
  if (!session) return json({ ok: false, error: 'Unauthorized' }, 401);
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return json({ ok: false, error: 'Revenue OS is not enabled' }, 503);
  }

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid JSON' }, 400);
  }

  const mode = body.mode === 'plan' ? 'plan' : 'run';
  if (mode === 'plan') return json({ ok: true, plan: buildSupervisorPlan(body, process.env) });

  try {
    const result = await runPassiveIncomeCycle(body, {
      routeAI: routePassiveIncomeAI,
      env: process.env,
    });
    return json(result, result.ok ? 200 : 422);
  } catch (error) {
    console.error('[passive-income] cycle failed:', error);
    return json({ ok: false, error: 'Passive income cycle failed safely' }, 500);
  }
}
