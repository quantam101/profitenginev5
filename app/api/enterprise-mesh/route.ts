import { NextResponse } from 'next/server';

const meshAgents = [
  'offer-scout',
  'margin-guard',
  'listing-optimizer',
  'traffic-agent',
  'proof-ledger',
  'motivation-engine',
  'free-tier-cost-guard',
];

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

export function GET() {
  const verifiedRevenueUsd = Number(process.env.VERIFIED_REVENUE_USD ?? 0);
  const thresholdUsd = 25_000;
  const runtimeUrl = process.env.RUNTIME_API_URL ?? null;

  return NextResponse.json(
    {
      ok: true,
      service: 'enterprise-context-mesh',
      mode: 'local_first_wal_failover',
      runtimeUrl: runtimeUrl ? '[configured]' : '[not configured]',
      runtimeCommand: 'npm run agents:parallel',
      agentCount: meshAgents.length,
      agents: meshAgents.map((id) => ({
        id,
        status: 'ready',
        parallelEligible: true,
        costPolicy: 'zero_paid_calls',
      })),
      consensus: {
        endpoint: 'POST /api/enterprise-mesh',
        algorithm: 'supermajority_vote',
        quorumThreshold: 0.67,
        defaultAgents: [
          'sovereign-orchestrator',
          'local-research',
          'free-tier-cost-guard',
        ],
      },
      failover: [
        'live_parallel_worker',
        'sqlite_wal_snapshot_cache',
        'signed_edge_wal_queue',
        'deterministic_error_when_no_snapshot_exists',
      ],
      edgeFailover: {
        statusEndpoint: '/api/edge-failover',
        localIngestCommand: 'python scripts/edge_failover_ingest.py',
        localReplayCommand: 'python scripts/edge_failover_replay.py',
      },
      proofGate: {
        thresholdUsd,
        verifiedRevenueUsd,
        remainingUsd: Math.max(0, thresholdUsd - verifiedRevenueUsd),
        unlocked: verifiedRevenueUsd >= thresholdUsd,
      },
      productionSafety: {
        publicPostingRequiresApproval: true,
        paymentCaptureRequiresConfiguredProvider: true,
        paidProfitEngineOfferLockedUntilProof: true,
      },
      generatedAt: new Date().toISOString(),
    },
    { headers: NO_STORE },
  );
}

/**
 * POST /api/enterprise-mesh
 *
 * Dispatches an objective to the runtime consensus engine (supermajority vote).
 * Proxies to the Python runtime at RUNTIME_API_URL/consensus.
 *
 * Body (JSON):
 *   objective   string  required  Task for all agents to execute.
 *   context     string  optional  Additional context injected into prompts.
 *   agents      string[]  optional  Override agent IDs (default 3-agent trio).
 *   timeout_sec number  optional  Per-agent timeout 5-300s (default 60).
 *   threshold   number  optional  Quorum fraction 0.5-1.0 (default 0.67).
 */
export async function POST(request: Request) {
  const runtimeUrl = (process.env.RUNTIME_API_URL || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');

  let body: {
    objective?: string;
    context?: string;
    agents?: string[];
    timeout_sec?: number;
    threshold?: number;
  };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { ok: false, error: 'Request body must be valid JSON' },
      { status: 400, headers: NO_STORE },
    );
  }

  const objective = body.objective?.trim();
  if (!objective) {
    return NextResponse.json(
      { ok: false, error: '"objective" is required and must be non-empty' },
      { status: 422, headers: NO_STORE },
    );
  }

  const upstreamPayload = {
    objective,
    context: body.context ?? '',
    agents: Array.isArray(body.agents) ? body.agents : [],
    timeout_sec: typeof body.timeout_sec === 'number' ? body.timeout_sec : 60,
    threshold: typeof body.threshold === 'number' ? body.threshold : 0.67,
  };

  try {
    const upstream = await fetch(`${runtimeUrl}/consensus`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(upstreamPayload),
      signal: AbortSignal.timeout(95_000), // 5s slack over max timeout_sec
    });

    const result: unknown = await upstream.json();
    return NextResponse.json(result, {
      status: upstream.ok ? 200 : 502,
      headers: NO_STORE,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, error: `Runtime unreachable: ${message}` },
      { status: 503, headers: NO_STORE },
    );
  }
}
