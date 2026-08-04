import { NextRequest, NextResponse } from 'next/server';

function selfOrigin(): string | undefined {
  // Vercel provides the current deployment domain; use it for self-calls so
  // the command route works in Preview and Production without relying on the
  // request Host header (which is attacker-controllable).
  const vercelUrl = process.env.VERCEL_URL;
  if (vercelUrl) return `https://${vercelUrl}`;
  return undefined;
}

const ORACLE = (process.env.ORACLE_API_URL ?? process.env.PROFITENGINE_URL ?? selfOrigin())?.replace(/\/$/, '');
const MAP: Record<string, string> = { 'Run Cycle': '/api/run-cycle', 'Self-Improve': '/api/self-improve', 'Pause All': '/api/pause', 'Resume All': '/api/resume' };

export async function POST(req: NextRequest) {
  const { command } = await req.json();
  const path = MAP[command];
  if (!path) return NextResponse.json({ error: 'unknown command' }, { status: 400 });
  if (!ORACLE) {
    return NextResponse.json({ ok: false, error: 'oracle not configured' }, { status: 503 });
  }
  try {
    const res = await fetch(`${ORACLE}${path}`, { method: 'POST', signal: AbortSignal.timeout(10000) });
    return NextResponse.json({ ok: res.ok, status: res.status });
  } catch {
    return NextResponse.json({ ok: false, error: 'oracle_unreachable' }, { status: 502 });
  }
}
