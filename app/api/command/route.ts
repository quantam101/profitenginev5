import { NextRequest, NextResponse } from 'next/server';
const ORACLE = process.env.ORACLE_API_URL ?? 'http://129.146.167.73:3000';
const MAP: Record<string, string> = { 'Run Cycle': '/api/run-cycle', 'Self-Improve': '/api/self-improve', 'Pause All': '/api/pause', 'Resume All': '/api/resume' };
export async function POST(req: NextRequest) {
  const { command } = await req.json();
  const path = MAP[command];
  if (!path) return NextResponse.json({ error: 'unknown command' }, { status: 400 });
  try {
    const res = await fetch(`${ORACLE}${path}`, { method: 'POST', signal: AbortSignal.timeout(10000) });
    return NextResponse.json({ ok: res.ok, status: res.status });
  } catch {
    return NextResponse.json({ ok: false, error: 'oracle_unreachable' }, { status: 502 });
  }
}
