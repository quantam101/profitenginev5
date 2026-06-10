import { NextResponse } from 'next/server';

const RUNTIME = process.env.RUNTIME_API_URL;
const WEBHOOK_TOKEN = process.env.PROFITENGINE_WEBHOOK_TOKEN;

export async function POST() {
  if (!RUNTIME) {
    return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503 });
  }
  if (!WEBHOOK_TOKEN) {
    return NextResponse.json({ ok: false, error: 'PROFITENGINE_WEBHOOK_TOKEN not configured' }, { status: 503 });
  }
  try {
    const res = await fetch(`${RUNTIME}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-profitengine-token': WEBHOOK_TOKEN,
      },
      body: JSON.stringify({
        objective:
          'Run automated profit cycle: scan trends, generate content, seo-optimize, publish, and record results.',
        agent_id: 'sovereign-orchestrator',
        namespace: 'cycle',
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
