import { NextRequest, NextResponse } from 'next/server';
import { appendFileSync, mkdirSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';

/**
 * Gumroad webhook payload structure
 *
 * Gumroad sends the following fields in form-encoded POST:
 * - product_id: Unique product identifier
 * - product_name: Display name of the product
 * - price: Amount in USD (as string or number)
 * - purchase_email: Buyer's email address
 * - license_key: (optional) Generated license key if product has licensing
 * - variant_title: (optional) Selected variant if product has variants
 * - timestamp: (optional) Unix timestamp when sale occurred
 *
 * Full webhook URL: https://profitengine.alreadyherellc.com/api/webhooks/gumroad
 */
interface GumroadWebhookPayload {
  product_id: string;
  product_name?: string;
  license_key?: string;
  purchase_email?: string;
  purchaser?: {
    email: string;
    name?: string;
  };
  price: string | number;
  currency?: string;
  timestamp?: string | number;
  variant_title?: string;
  created_at?: string;
  [key: string]: unknown;
}

interface TransactionRecord {
  channel: string;
  amount_usd: number;
  timestamp: string;
  source_id: string;
  description: string;
  content_id: string;
  metadata: Record<string, unknown>;
}

/**
 * Normalize Gumroad price to USD amount
 * Gumroad typically sends prices in the product's currency
 */
function normalizePriceToUSD(price: string | number): number {
  let amount = typeof price === 'string' ? parseFloat(price) : price;

  // Handle case where price is in cents (unlikely for USD but safe to check)
  if (amount > 10000) {
    amount = amount / 100;
  }

  return Math.round(amount * 100) / 100; // Round to 2 decimal places
}

/**
 * Ensure revenue directory exists
 */
function ensureRevenueDir(): string {
  const runtimeDir = join(process.cwd(), '.runtime', 'revenue');
  try {
    mkdirSync(runtimeDir, { recursive: true });
  } catch (error) {
    // Directory might already exist or be inaccessible
    console.warn('Could not create revenue directory:', error);
  }
  return runtimeDir;
}

/**
 * Log transaction to JSONL file
 */
function logTransaction(transaction: TransactionRecord): boolean {
  try {
    const runtimeDir = ensureRevenueDir();
    const transactionPath = join(runtimeDir, 'transactions.jsonl');
    appendFileSync(transactionPath, JSON.stringify(transaction) + '\n', 'utf8');
    return true;
  } catch (error) {
    console.warn('Failed to log transaction to JSONL:', error);
    return false;
  }
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();

  try {
    // Parse the incoming webhook payload
    // Gumroad sends form-encoded data, Next.js automatically parses it as JSON
    const payload = await request.json() as GumroadWebhookPayload;

    // Extract and normalize fields
    const product_id = payload.product_id?.trim() || 'unknown';
    const product_name = (
      payload.product_name ||
      payload.variant_title ||
      'Unknown Product'
    ).trim();

    const amount_usd = normalizePriceToUSD(payload.price || 0);
    const purchaser_email = (
      payload.purchase_email ||
      payload.purchaser?.email ||
      'unknown'
    ).toLowerCase().trim();

    const license_key = payload.license_key?.trim() || null;
    const variant_title = payload.variant_title?.trim() || null;

    // Use provided timestamp or current time
    let timestamp: string;
    if (payload.timestamp) {
      const ts = typeof payload.timestamp === 'string'
        ? parseInt(payload.timestamp, 10)
        : payload.timestamp;
      timestamp = new Date(ts * 1000).toISOString();
    } else if (payload.created_at) {
      timestamp = new Date(payload.created_at).toISOString();
    } else {
      timestamp = new Date().toISOString();
    }

    // Generate unique source ID
    const source_id = `gumroad_${product_id}_${Math.floor(Date.now() / 1000)}`;

    // Create transaction record matching the ledger schema
    const transaction: TransactionRecord = {
      channel: 'gumroad',
      amount_usd,
      timestamp,
      source_id,
      description: `Gumroad sale: ${product_name}`,
      content_id: product_id,
      metadata: {
        purchaser_email,
        product_name,
        license_key,
        variant: variant_title,
        // Include raw payload for audit
        raw_payload: {
          product_id,
          currency: payload.currency || 'usd',
        },
      },
    };

    // Persist to transaction log
    const logged = logTransaction(transaction);

    // Log success
    const processingTime = Date.now() - startTime;
    console.log(
      `✅ Gumroad webhook processed in ${processingTime}ms | ` +
      `$${amount_usd} from ${purchaser_email} | ` +
      `Product: ${product_name} | ` +
      `License: ${license_key ? 'YES' : 'NO'}`
    );

    // Return success response
    return NextResponse.json(
      {
        ok: true,
        transaction_id: source_id,
        amount_usd,
        product_name,
        purchaser_email,
        logged,
        processing_time_ms: processingTime,
      },
      { status: 200 }
    );

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`❌ Gumroad webhook failed: ${errorMessage}`);

    return NextResponse.json(
      {
        ok: false,
        error: 'Webhook processing failed',
        details: errorMessage,
        timestamp: new Date().toISOString(),
      },
      { status: 400 }
    );
  }
}

/**
 * Health check endpoint - GET /api/webhooks/gumroad
 */
export async function GET(request: NextRequest) {
  return NextResponse.json({
    ok: true,
    service: 'Gumroad Webhook Handler',
    version: '2.0',
    endpoint: '/api/webhooks/gumroad',
    method: 'POST',
    expected_fields: [
      'product_id',
      'product_name',
      'price',
      'purchase_email',
      'license_key (optional)',
      'variant_title (optional)',
      'timestamp (optional)',
    ],
  });
}
