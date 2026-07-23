import { NextResponse } from 'next/server';
import { getRuntimeBase } from '@/app/lib/runtime';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const RUNTIME = getRuntimeBase();

/** GET /api/newsletter — Beehiiv publication stats */
export async function GET() {
  try {
    const r = await fetch(`${RUNTIME}/newsletter/stats`, {
      signal: AbortSignal.timeout(8_000),
      cache: 'no-store',
      headers: { 'User-Agent': 'ProfitEngine/5.0' },
    });
    if (r.ok) return NextResponse.json(await r.json(), { status: 200, headers: NO_STORE });
  } catch {
    // fall through
  }
  return NextResponse.json(
    { ok: true, total_subscribers: 0, subscribers: {}, source: 'degraded' },
    { status: 200, headers: NO_STORE },
  );
}

/**
 * POST /api/newsletter
 * Publish a digest to Beehiiv.
 * Body: { headline, sections: [{heading, body}], tags?, cta_url? }
 */
export async function POST(request: Request) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400, headers: NO_STORE }); }
  const r = await fetch(`${RUNTIME}/newsletter/publish`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), signal: AbortSignal.timeout(30_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}
