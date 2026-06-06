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

export function GET() {
  const verifiedRevenueUsd = Number(process.env.VERIFIED_REVENUE_USD ?? 0);
  const thresholdUsd = 25_000;

  return NextResponse.json({
    ok: true,
    service: 'enterprise-context-mesh',
    mode: 'local_first_wal_failover',
    runtimeCommand: 'npm run agents:parallel',
    agentCount: meshAgents.length,
    agents: meshAgents.map((id) => ({
      id,
      status: 'ready',
      parallelEligible: true,
      costPolicy: 'zero_paid_calls',
    })),
    failover: [
      'live_parallel_worker',
      'sqlite_wal_snapshot_cache',
      'deterministic_error_when_no_snapshot_exists',
    ],
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
  }, { headers: { 'Cache-Control': 'no-store' } });
}
