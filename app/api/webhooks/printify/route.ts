import { NextRequest, NextResponse } from 'next/server';
import { appendFileSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';

interface PrintifyOrder {
  id: string;
  status: string;
  total_price: number;
  currency: string;
  line_items?: Array<{
    title: string;
    quantity: number;
  }>;
  shipping_address?: {
    first_name?: string;
    last_name?: string;
  };
}

interface PrintifyWebhookPayload {
  action: string;
  data: PrintifyOrder;
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json() as PrintifyWebhookPayload;

    // Only process order.created events
    if (payload.action !== 'order.created' && payload.action !== 'order.completed') {
      return NextResponse.json({ ok: true, skipped: 'Not an order event' });
    }

    const order = payload.data;
    const amount_usd = order.total_price || 0;
    const timestamp = new Date().toISOString();

    // Get product title from line items
    const productTitle = order.line_items?.length
      ? order.line_items[0].title
      : 'Print on Demand Product';

    // Create transaction record
    const transaction = {
      channel: 'printify',
      amount_usd,
      timestamp,
      source_id: `printify_order_${order.id}`,
      description: `POD Order: ${productTitle} - Status: ${order.status}`,
      content_id: order.id,
      metadata: {
        order_id: order.id,
        product: productTitle,
        status: order.status,
        currency: order.currency,
        customer_name: order.shipping_address?.first_name
          ? `${order.shipping_address.first_name} ${order.shipping_address.last_name || ''}`
          : 'Unknown',
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

    console.log(`✅ Printify order logged: Order ${order.id} - $${amount_usd} - Status: ${order.status}`);

    return NextResponse.json({
      ok: true,
      order_id: order.id,
      amount: amount_usd,
      status: order.status,
    });
  } catch (error) {
    console.error('Printify webhook error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 400 }
    );
  }
}
