import { NextResponse } from 'next/server';
const ORACLE = process.env.ORACLE_API_URL ?? 'http://129.146.167.73:3000';
export async function GET() {
  let oracleStatus = 'unknown';
  try {
    const r = await fetch(`${ORACLE}/api/health`, { signal: AbortSignal.timeout(4000), cache: 'no-store' });
    oracleStatus = r.ok ? 'ok' : `error:${r.status}`;
  } catch { oracleStatus = 'unreachable'; }
  return NextResponse.json({ status: 'ok', ts: new Date().toISOString(), version: 'v5.0', oracle: { status: oracleStatus }, env: { hasAnthropicKey: !!process.env.ANTHROPIC_API_KEY } });
}
