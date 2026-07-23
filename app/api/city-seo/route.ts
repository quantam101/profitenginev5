import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const RUNTIME = (process.env.RUNTIME_API_URL || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');

/**
 * POST /api/city-seo
 * Generate and commit programmatic SEO city pages.
 * Body: { niches?, tiers?, limit?, dry_run? }
 */
export async function POST(request: Request) {
  let body: unknown = {};
  try { body = await request.json(); } catch { /* use defaults */ }
  const r = await fetch(`${RUNTIME}/city-seo/generate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), signal: AbortSignal.timeout(300_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}
