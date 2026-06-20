import { NextRequest, NextResponse } from 'next/server';
import { appendFileSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';

interface BeehiivSponsorPayload {
  event: string;
  data: {
    sponsor_id?: string;
    sponsor_name: string;
    sponsorship_amount: number;
    sponsorship_duration?: string;
    start_date?: string;
    currency?: string;
  };
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json() as BeehiivSponsorPayload;

    // Handle sponsorship events
    if (!payload.event?.includes('sponsor') && !payload.data?.sponsorship_amount) {
      return NextResponse.json({ ok: true, skipped: 'Not a sponsorship event' });
    }

    const { sponsor_name, sponsorship_amount, sponsorship_duration, start_date } = payload.data;
    const amount_usd = sponsorship_amount || 0;
    const timestamp = start_date || new Date().toISOString();

    // Create transaction record
    const transaction = {
      channel: 'newsletter',
      amount_usd,
      timestamp,
      source_id: `beehiiv_sponsor_${sponsor_name}_${Date.now()}`,
      description: `Newsletter sponsorship: ${sponsor_name} (${sponsorship_duration || '1 month'})`,
      content_id: null,
      metadata: {
        sponsor_name,
        duration: sponsorship_duration || '1 month',
        currency: payload.data.currency || 'USD',
        sponsor_id: payload.data.sponsor_id || null,
      },
    };

    // Log to JSONL file
    const runtimeDir = join(process.cwd(), '.runtime', 'revenue');
    const transactionPath = join(runtimeDir, 'transactions.jsonl');

    try {
      appendFileSync(transactionPath, JSON.stringify(transaction) + '\n', 'utf8');
    } catch (writeError) {
      console.warn('Failed to write transaction to file (non-fatal):', writeError);
    }

    console.log(`✅ Newsletter sponsorship logged: ${sponsor_name} - $${amount_usd}`);

    return NextResponse.json({
      ok: true,
      sponsor: sponsor_name,
      amount: amount_usd,
      recorded_at: timestamp,
    });
  } catch (error) {
    console.error('Newsletter webhook error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 400 }
    );
  }
}

// Sponsor payment via Stripe checkout (POST to this endpoint to initiate)
export async function PUT(request: NextRequest) {
  try {
    const { sponsor_name, amount_usd } = await request.json() as { sponsor_name: string; amount_usd: number };

    // This would integrate with Stripe to create checkout session
    // For now, return placeholder response
    return NextResponse.json({
      ok: true,
      message: 'Stripe checkout would be created here',
      sponsor: sponsor_name,
      amount: amount_usd,
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to process payment request' },
      { status: 400 }
    );
  }
}
