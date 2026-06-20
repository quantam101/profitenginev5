import { NextRequest, NextResponse } from 'next/server';
import { appendFileSync, mkdirSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';

interface PrintifyLineItem {
  title: string;
  quantity: number;
  sku?: string;
}

interface PrintifyOrder {
  id: string;
  status: string;
  total_price: number;
  currency: string;
  line_items?: PrintifyLineItem[];
  shipping_address?: {
    first_name?: string;
    last_name?: string;
  };
  cost?: number; // Total cost in USD
}

interface PrintifyWebhookPayload {
  action: string;
  data: PrintifyOrder;
}

/**
 * Calculate COGS (Cost of Goods Sold) for a Printify product
 * Estimates based on typical POD margins:
 * - T-shirt: ~35% margin = 65% COGS
 * - Hoodie: ~40% margin = 60% COGS
 * - Mug/Accessories: ~50% margin = 50% COGS
 * - Default: 60% COGS, 40% profit margin
 */
function calculateCOGS(price: number, productTitle?: string): number {
  const title = (productTitle || '').toLowerCase();

  // Adjust COGS ratio based on product type
  let cogsRatio = 0.6; // Default 60% COGS

  if (title.includes('hoodie') || title.includes('sweatshirt') || title.includes('jacket')) {
    cogsRatio = 0.55; // Better margin on apparel
  } else if (title.includes('t-shirt') || title.includes('shirt') || title.includes('tee')) {
    cogsRatio = 0.60;
  } else if (title.includes('mug') || title.includes('cup') || title.includes('tumbler')) {
    cogsRatio = 0.50; // Better margin on hard goods
  } else if (title.includes('poster') || title.includes('canvas') || title.includes('print')) {
    cogsRatio = 0.45; // Excellent margin on prints
  } else if (title.includes('sticker') || title.includes('decal')) {
    cogsRatio = 0.40; // Premium margin on stickers
  }

  return Math.round(price * cogsRatio * 100) / 100;
}

/**
 * Ensure runtime directory exists and is writable
 */
function ensureRuntimeDir(): string {
  const runtimeDir = join(process.cwd(), '.runtime', 'revenue');
  try {
    mkdirSync(runtimeDir, { recursive: true, mode: 0o755 });
  } catch (err) {
    console.warn('Could not create runtime directory (may already exist):', err);
  }
  return runtimeDir;
}

/**
 * Log webhook event for debugging/auditing
 */
function logWebhookEvent(orderId: string, status: string, amount: number): void {
  const logDir = join(process.cwd(), '.runtime', 'webhooks');
  try {
    mkdirSync(logDir, { recursive: true, mode: 0o755 });
    const logFile = join(logDir, 'printify.log');
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] Order ${orderId}: ${status} - $${amount.toFixed(2)}\n`;
    appendFileSync(logFile, logEntry, 'utf8');
  } catch (err) {
    // Non-fatal: webhook processing continues even if logging fails
    console.warn('Could not log webhook event:', err);
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json() as PrintifyWebhookPayload;

    // Only process order.created and order.completed events
    if (payload.action !== 'order.created' && payload.action !== 'order.completed') {
      return NextResponse.json({
        ok: true,
        skipped: `Action '${payload.action}' not tracked`,
      });
    }

    const order = payload.data;
    const amount_usd = order.total_price || 0;
    const timestamp = new Date().toISOString();

    // Extract product info
    const productTitle = order.line_items?.length
      ? order.line_items[0].title
      : 'Print on Demand Product';

    const quantity = order.line_items?.length
      ? order.line_items.reduce((sum, item) => sum + (item.quantity || 1), 0)
      : 1;

    // Calculate profit margins
    const cogs = order.cost || calculateCOGS(amount_usd, productTitle);
    const profit = Math.max(0, amount_usd - cogs);
    const profitMargin = amount_usd > 0 ? Math.round((profit / amount_usd) * 100) : 0;

    // Build customer name
    const customerName = order.shipping_address?.first_name
      ? `${order.shipping_address.first_name} ${order.shipping_address.last_name || ''}`.trim()
      : 'Unknown';

    // Create comprehensive transaction record
    const transaction = {
      channel: 'printify',
      amount_usd,
      cogs: cogs,
      profit: profit,
      profit_margin: profitMargin,
      timestamp,
      source_id: `printify_order_${order.id}`,
      description: `POD: ${productTitle} (qty: ${quantity}) - ${order.status}`,
      content_id: order.id,
      metadata: {
        order_id: order.id,
        product: productTitle,
        quantity: quantity,
        status: order.status,
        currency: order.currency,
        customer_name: customerName,
        calculation: {
          revenue: amount_usd,
          cogs: cogs,
          profit: profit,
          margin_percent: profitMargin,
        },
      },
    };

    // Write to revenue tracking file
    const runtimeDir = ensureRuntimeDir();
    const transactionPath = join(runtimeDir, 'transactions.jsonl');

    try {
      appendFileSync(transactionPath, JSON.stringify(transaction) + '\n', 'utf8');
    } catch (writeError) {
      console.warn('Failed to write transaction to file (non-fatal):', writeError);
      // Continue anyway - don't fail webhook response
    }

    // Log event for audit trail
    logWebhookEvent(order.id, order.status, amount_usd);

    // Log success
    const profitStr = profit > 0 ? ` (profit: $${profit.toFixed(2)}, ${profitMargin}%)` : '';
    console.log(
      `✅ Printify order logged: Order ${order.id} - $${amount_usd.toFixed(2)}${profitStr} - ${order.status}`
    );

    return NextResponse.json({
      ok: true,
      order_id: order.id,
      amount: amount_usd,
      cogs: cogs,
      profit: profit,
      profit_margin: profitMargin,
      status: order.status,
      timestamp: timestamp,
    });
  } catch (error) {
    console.error('Printify webhook error:', error);
    return NextResponse.json(
      {
        error: 'Webhook processing failed',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 400 }
    );
  }
}
