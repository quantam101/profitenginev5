import { NextRequest, NextResponse } from 'next/server';
import { routeAI } from '@/lib/ai-gateway.mjs';
import {
  collectRssSources,
  runPassiveIncomeCycle,
} from '@/lib/revenue-os/passive-income-engine.mjs';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 300;

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

function json(data: unknown, status = 200) {
  return NextResponse.json(data, { status, headers: NO_STORE });
}

function authorized(request: NextRequest) {
  const secret = process.env.CRON_SECRET;
  if (!secret) return false;
  return request.headers.get('authorization') === `Bearer ${secret}`;
}

function scheduledAgents(now = new Date()) {
  const agents = ['technical_product', 'stock_asset'];
  if (now.getUTCDay() === 0) agents.push('newsletter');
  return agents;
}

export async function GET(request: NextRequest) {
  if (!authorized(request)) return json({ ok: false, error: 'Unauthorized' }, 401);
  if (process.env.REVENUE_OS_ENABLED !== 'true') return json({ ok: false, error: 'Revenue OS is not enabled' }, 503);

  const agents = scheduledAgents();
  const newsletterRun = agents.includes('newsletter');
  const feedUrls = String(process.env.PASSIVE_INCOME_RSS_FEEDS || '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

  const rss = newsletterRun && feedUrls.length
    ? await collectRssSources(feedUrls)
    : { ok: false, sources: [], errors: [] };

  try {
    const result = await runPassiveIncomeCycle({
      publish: true,
      agents,
      sources: rss.sources,
      newsletterNiche: process.env.PASSIVE_INCOME_NEWSLETTER_NICHE || 'AI operations and infrastructure for small technology businesses',
    }, {
      routeAI,
      env: process.env,
    });

    return json({
      ...result,
      scheduler: {
        trigger: 'vercel_cron',
        agents,
        newsletterRun,
        rssFeedsConfigured: feedUrls.length,
        rssItemsCollected: rss.sources.length,
        rssErrors: rss.errors,
      },
    }, result.ok ? 200 : 422);
  } catch (error) {
    console.error('[passive-income] cron cycle failed:', error);
    return json({ ok: false, error: 'Scheduled passive income cycle failed safely' }, 500);
  }
}
