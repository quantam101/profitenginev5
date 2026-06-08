import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/**
 * GET /api/income
 * Aggregate revenue dashboard across all 10 income streams.
 */
export async function GET() {
  const runtimeUrl = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!runtimeUrl) {
    return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  }
  try {
    const resp = await fetch(`${runtimeUrl}/income/summary`, { signal: AbortSignal.timeout(15_000) });
    return NextResponse.json(await resp.json(), { status: resp.ok ? 200 : 502, headers: NO_STORE });
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err) }, { status: 503, headers: NO_STORE });
  }
}
