import { NextRequest, NextResponse } from 'next/server';
import { appendFileSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';

interface GumroadPayload {
  product_id: string;
  product_name?: string;
  license_key?: string;
  purchaser?: {
    email: string;
    name?: string;
  };
  price: number;
  currency?: string;
  timestamp?: string;
  variant_title?: string;
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json() as GumroadPayload;

    // Parse Gumroad data
    const amount_usd = payload.price || 0;
    const purchaser_email = payload.purchaser?.email || 'unknown';
    const product_name = payload.product_name || payload.variant_title || 'Unknown Product';
    const timestamp = new Date().toISOString();

    // Create transaction record
    const transaction = {
      channel: 'gumroad',
      amount_usd,
      timestamp,
      source_id: `gumroad_${payload.product_id}_${Date.now()}`,
      description: `Gumroad sale: ${product_name}`,
      content_id: payload.product_id,
      metadata: {
        purchaser_email,
        product_name,
        license_key: payload.license_key || null,
        variant: payload.variant_title || null,
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

    console.log(`✅ Gumroad sale logged: $${amount_usd} from ${purchaser_email}`);

    return NextResponse.json({
      ok: true,
      transaction_id: transaction.source_id,
      amount: amount_usd,
    });
  } catch (error) {
    console.error('Gumroad webhook error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 400 }
    );
  }
}
