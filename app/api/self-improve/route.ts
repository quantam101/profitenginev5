import { NextResponse } from 'next/server';

const RUNTIME = process.env.RUNTIME_API_URL ?? 'http://runtime:8080';

export async function POST() {
  try {
    const res = await fetch(`${RUNTIME}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        objective:
          'Run LC&C self-improvement loop: analyze recent outputs, rewrite underperforming prompts, measure CTR uplift.',
        agent_id: 'lifelong-catch-correct',
        namespace: 'self-improve',
      }),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) throw new Error(`runtime ${res.status}`);
    return NextResponse.json({ ok: true, result: await res.json() });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'unknown';
    return NextResponse.json({ ok: false, error: msg }, { status: 502 });
  }
}
