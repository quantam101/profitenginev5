import crypto from 'node:crypto';
import { NextRequest, NextResponse } from 'next/server';

const EDGE_SECRET = process.env.PROFITENGINE_EDGE_WEBHOOK_SECRET ?? '';
const RUNTIME = process.env.RUNTIME_API_URL ?? '';

function verifySignature(rawBody: string, signature: string | null) {
  if (!EDGE_SECRET || !signature) return false;
  const supplied = signature.replace(/^sha256=/, '').trim();
  const expected = crypto.createHmac('sha256', EDGE_SECRET).update(rawBody).digest('hex');
  const expectedBuffer = Buffer.from(expected);
  const suppliedBuffer = Buffer.from(supplied);
  return expectedBuffer.length === suppliedBuffer.length && crypto.timingSafeEqual(expectedBuffer, suppliedBuffer);
}

export function GET() {
  return NextResponse.json({
    ok: true,
    service: 'edge-failover-ingress',
    mode: 'signed_ingress_with_python_wal_edge_runner',
    productionRuntime: {
      signedWebhook: '/api/edge-failover',
      localWalIngest: 'python scripts/edge_failover_ingest.py',
      localWalReplay: 'python scripts/edge_failover_replay.py',
      durableQueueOwner: 'runtime.edge_failover.EdgeFailoverEngine',
    },
    failoverOrder: [
      'authenticated Next.js ingress',
      'runtime API dispatch when available',
      'local Python edge WAL queue for disconnected operation',
      'replay through enterprise mesh when runtime returns',
    ],
    safety: {
      hmacRequired: true,
      paymentCapture: false,
      publicPosting: false,
      fakeSuccessOnFailure: false,
    },
    generatedAt: new Date().toISOString(),
  }, { headers: { 'Cache-Control': 'no-store' } });
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get('x-profitengine-signature');

  if (!verifySignature(rawBody, signature)) {
    return NextResponse.json({ ok: false, error: 'unauthorized' }, { status: 401 });
  }

  if (!RUNTIME) {
    return NextResponse.json({
      ok: true,
      accepted: true,
      mode: 'signed_payload_verified_runtime_not_configured',
      nextStep: 'Run python scripts/edge_failover_ingest.py on the edge worker for durable WAL staging.',
    }, { status: 202, headers: { 'Cache-Control': 'no-store' } });
  }

  try {
    const runtimeResponse = await fetch(`${RUNTIME}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: rawBody,
      signal: AbortSignal.timeout(5000),
    });

    return NextResponse.json({
      ok: runtimeResponse.ok,
      accepted: true,
      mode: runtimeResponse.ok ? 'runtime_dispatch' : 'runtime_dispatch_failed',
      runtimeStatus: runtimeResponse.status,
      durableFallback: 'If this is deployed on an edge worker, stage the same signed payload with scripts/edge_failover_ingest.py.',
    }, {
      status: runtimeResponse.ok ? 202 : 503,
      headers: { 'Cache-Control': 'no-store' },
    });
  } catch (error) {
    return NextResponse.json({
      ok: false,
      accepted: true,
      mode: 'runtime_unreachable',
      error: error instanceof Error ? error.message : String(error),
      durableFallback: 'Stage the same signed payload with python scripts/edge_failover_ingest.py on the local edge runner.',
    }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  }
}
