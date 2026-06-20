import { NextRequest, NextResponse } from 'next/server';
import { appendFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import crypto from 'crypto';

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

// Verify Beehiiv webhook signature
function verifyBeehiivSignature(
  payload: string,
  signature: string,
  apiKey: string
): boolean {
  try {
    const hash = crypto
      .createHmac('sha256', apiKey)
      .update(payload)
      .digest('hex');
    return hash === signature;
  } catch (error) {
    console.error('Signature verification error:', error);
    return false;
  }
}

export async function POST(request: NextRequest) {
  try {
    // Get raw body for signature verification
    const bodyBuffer = await request.arrayBuffer();
    const bodyString = Buffer.from(bodyBuffer).toString('utf8');

    // Extract signature from headers
    const signature = request.headers.get('x-beehiiv-signature');
    const beehiivKey = process.env.BEEHIIV_API_KEY;

    if (!signature || !beehiivKey) {
      console.warn('Missing signature or API key for Beehiiv webhook');
      return NextResponse.json(
        { error: 'Webhook authentication failed' },
        { status: 401 }
      );
    }

    // Verify signature
    const isValid = verifyBeehiivSignature(bodyString, signature, beehiivKey);
    if (!isValid) {
      console.warn('Invalid Beehiiv webhook signature');
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 401 }
      );
    }

    const payload = JSON.parse(bodyString) as BeehiivSponsorPayload;

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

    // Ensure runtime directory exists
    const runtimeDir = join(process.cwd(), '.runtime', 'revenue');
    try {
      mkdirSync(runtimeDir, { recursive: true });
    } catch (error) {
      console.warn('Failed to create runtime directory:', error);
    }

    // Log to JSONL file
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
