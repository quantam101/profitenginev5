import { NextRequest, NextResponse } from 'next/server';
import { hasWebhookAccess } from '../../../../lib/webhookAuth';
import { createDispatchProof } from '../../../../lib/proofPublish';

interface DispatchPayload {
  dispatchId: string;
  fullName: string;
  company: string;
  email: string;
  phone: string;
  siteCity: string;
  serviceType: string;
  message: string;
  source: string;
  submittedAt: string;
}

const RUNTIME = process.env.RUNTIME_API_URL ?? 'http://runtime:8080';

export async function POST(req: NextRequest) {
  if (!hasWebhookAccess(req)) {
    return NextResponse.json({ ok: false, error: 'unauthorized' }, { status: 401 });
  }

  try {
    const body = (await req.json()) as Partial<DispatchPayload>;

    if (!body.dispatchId || !body.fullName || !body.email) {
      return NextResponse.json(
        { ok: false, error: 'dispatchId, fullName, and email are required' },
        { status: 400 },
      );
    }

    const record = {
      type: 'dispatch_alert',
      receivedAt: new Date().toISOString(),
      dispatchId: body.dispatchId,
      fullName: body.fullName,
      company: body.company ?? '',
      email: body.email,
      phone: body.phone ?? '',
      siteCity: body.siteCity ?? '',
      serviceType: body.serviceType ?? '',
      message: (body.message ?? '').slice(0, 1000),
      source: body.source ?? 'alreadyherellc.com',
      submittedAt: body.submittedAt ?? new Date().toISOString(),
    };

    // ── ProofPublish: append-only dispatch proof record (fire-and-forget) ────
    const [proofResult] = await Promise.allSettled([
      createDispatchProof(
        {
          dispatchId: record.dispatchId,
          fullName: record.fullName,
          company: record.company,
          siteCity: record.siteCity,
          serviceType: record.serviceType,
          submittedAt: record.submittedAt,
          source: record.source,
        },
        'alreadyherellc',
      ),
      // Sovereign orchestrator notification (non-blocking)
      fetch(`${RUNTIME}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objective: `Dispatch alert: ${body.serviceType ?? 'dispatch'} — ${body.siteCity ?? 'unknown'} — ${body.company ?? body.fullName}`,
          dynamic_context: JSON.stringify(record),
          agent_id: 'sovereign-orchestrator',
          namespace: 'webhook',
          actor: 'webhook-dispatch',
        }),
        signal: AbortSignal.timeout(15000),
      }).then((r) => r.body?.cancel()),
    ]);

    const proof =
      proofResult.status === 'fulfilled' ? proofResult.value : null;

    return NextResponse.json(
      { ok: true, record, proof: proof ?? undefined },
      { status: 201 },
    );
  } catch {
    return NextResponse.json(
      { ok: false, error: 'invalid_payload' },
      { status: 400 },
    );
  }
}
