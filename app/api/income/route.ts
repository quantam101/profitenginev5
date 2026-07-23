import { NextResponse } from 'next/server';
import { getRuntimeBase } from '@/app/lib/runtime';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const RUNTIME = getRuntimeBase();

export async function GET() {
  try {
    const resp = await fetch(`${RUNTIME}/income/summary`, {
      signal: AbortSignal.timeout(8_000),
      cache: 'no-store',
      headers: { 'User-Agent': 'ProfitEngine/5.0' },
    });
    if (resp.ok) return NextResponse.json(await resp.json(), { status: 200, headers: NO_STORE });
  } catch {
    // fall through to degraded fallback
  }
  return NextResponse.json(
    { ok: true, streams: {}, total_usd: 0, source: 'degraded' },
    { status: 200, headers: NO_STORE },
  );
}
