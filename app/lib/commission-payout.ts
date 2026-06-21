/**
 * Commission Calculation & Automatic Payout System
 *
 * Runs daily (scheduled via cron job) to:
 * 1. Calculate commission from each client's transactions
 * 2. Create payouts to your Stripe account (2.5% of all client charges)
 * 3. Log transactions for audit trail
 * 4. Send receipts to clients (optional)
 */

import Stripe from 'stripe';
import fs from 'fs';
import path from 'path';
import {
  listClients,
  getClientTransactions,
  calculateClientCommission,
} from './client-db';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY not configured');
  }
  return new Stripe(stripeKey);
}

/**
 * Payout log entry
 */
interface CommissionPayout {
  date: string; // ISO date
  client_id: string;
  client_email: string;
  business_name: string;
  transaction_count: number;
  total_volume: number; // in cents
  commission_rate: number; // 2.5%
  commission_amount: number; // in cents
  stripe_payout_id?: string;
  payout_status: 'pending' | 'succeeded' | 'failed';
  error?: string;
  created_at: number;
}

/**
 * Get payouts log directory
 */
function getPayoutsDir(): string {
  const dir = path.join(process.cwd(), '.runtime', 'payouts');
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

/**
 * Log a commission payout
 */
async function logPayout(payout: CommissionPayout): Promise<void> {
  const date = payout.date.split('T')[0]; // YYYY-MM-DD
  const logPath = path.join(getPayoutsDir(), `${date}.jsonl`);

  // Append to daily log file
  fs.appendFileSync(logPath, JSON.stringify(payout) + '\n');
}

/**
 * Create a payout to your Stripe account
 */
async function createPayout(
  amount: number, // in cents
  description: string
): Promise<{ id: string; status: string }> {
  try {
    const stripe = getStripe();

    // Create payout to your Stripe account
    // Note: In production, you'd use Stripe Transfer API or manual payouts
    // For MVP, we log the payout intent

    console.log(`💸 Payout created: $${(amount / 100).toFixed(2)}`);
    console.log(`   Description: ${description}`);

    // In production, you would:
    // const payout = await stripe.payouts.create({
    //   amount: amount,
    //   currency: 'usd',
    //   description: description,
    // });
    // return { id: payout.id, status: payout.status };

    // For now, return a mock payout
    return {
      id: `payout_${Date.now()}`,
      status: 'pending',
    };
  } catch (error) {
    console.error('Failed to create payout:', error);
    throw error;
  }
}

/**
 * Run daily commission payout job
 * Should be called once per day (e.g., at 00:00 UTC)
 */
export async function dailyCommissionPayout(): Promise<{
  success: boolean;
  payouts: CommissionPayout[];
  totalCommission: number;
  errors: string[];
}> {
  const results: CommissionPayout[] = [];
  const errors: string[] = [];
  let totalCommission = 0;

  const today = new Date().toISOString();

  try {
    console.log('\n🔄 Starting daily commission payout job...');
    console.log(`📅 Date: ${today}`);

    // Get all clients
    const clients = await listClients();
    console.log(`👥 Processing ${clients.length} clients...`);

    for (const client of clients) {
      // Only process clients in live mode
      if (client.status !== 'live') {
        continue;
      }

      try {
        // Get yesterday's transactions
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        yesterday.setHours(0, 0, 0, 0);
        const yesterdayTimestamp = yesterday.getTime();

        const transactions = await getClientTransactions(
          client.id,
          yesterdayTimestamp
        );

        // Filter for successful transactions
        const successfulTxns = transactions.filter(
          (t) => t.status === 'succeeded'
        );

        if (successfulTxns.length === 0) {
          continue; // No transactions yesterday
        }

        // Calculate commission
        const totalVolume = successfulTxns.reduce((sum, t) => sum + t.amount, 0);
        const commissionAmount = Math.round(totalVolume * (client.commission_rate / 100));

        if (commissionAmount === 0) {
          continue; // No commission to pay
        }

        // Create payout
        const payout = await createPayout(
          commissionAmount,
          `Commission from ${client.business_name} - ${successfulTxns.length} transactions`
        );

        // Log payout
        const log: CommissionPayout = {
          date: today,
          client_id: client.id,
          client_email: client.email,
          business_name: client.business_name,
          transaction_count: successfulTxns.length,
          total_volume: totalVolume,
          commission_rate: client.commission_rate,
          commission_amount: commissionAmount,
          stripe_payout_id: payout.id,
          payout_status: payout.status as 'pending' | 'succeeded' | 'failed',
          created_at: Date.now(),
        };

        await logPayout(log);
        results.push(log);
        totalCommission += commissionAmount;

        console.log(
          `✅ ${client.business_name}: ${successfulTxns.length} txns = $${(commissionAmount / 100).toFixed(2)} commission`
        );
      } catch (clientError) {
        const errorMsg = clientError instanceof Error ? clientError.message : String(clientError);
        errors.push(`Client ${client.id}: ${errorMsg}`);
        console.error(`❌ Error processing client ${client.id}:`, clientError);
      }
    }

    console.log(`\n✅ Commission payout job completed`);
    console.log(`💰 Total commission: $${(totalCommission / 100).toFixed(2)}`);
    console.log(`📋 Payouts processed: ${results.length}`);

    if (errors.length > 0) {
      console.log(`⚠️  Errors: ${errors.length}`);
      errors.forEach((e) => console.log(`   - ${e}`));
    }

    return {
      success: true,
      payouts: results,
      totalCommission,
      errors,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error('Daily commission payout job failed:', error);
    return {
      success: false,
      payouts: results,
      totalCommission,
      errors: [...errors, `Job failed: ${errorMsg}`],
    };
  }
}

/**
 * Get payout history for a specific date
 */
export async function getPayoutHistory(date: string): Promise<CommissionPayout[]> {
  try {
    const logPath = path.join(getPayoutsDir(), `${date}.jsonl`);

    if (!fs.existsSync(logPath)) {
      return [];
    }

    const content = fs.readFileSync(logPath, 'utf-8');
    return content
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line));
  } catch (error) {
    console.error(`Failed to get payout history for ${date}:`, error);
    return [];
  }
}

/**
 * Get total commission earned (optionally filtered by date range)
 */
export async function getTotalCommission(
  startDate?: string,
  endDate?: string
): Promise<number> {
  try {
    const dir = getPayoutsDir();

    if (!fs.existsSync(dir)) {
      return 0;
    }

    const files = fs.readdirSync(dir).filter((f) => f.endsWith('.jsonl'));
    let total = 0;

    for (const file of files) {
      const date = file.replace('.jsonl', '');

      // Filter by date range if provided
      if (startDate && date < startDate) continue;
      if (endDate && date > endDate) continue;

      const payouts = await getPayoutHistory(date);
      for (const payout of payouts) {
        if (payout.payout_status === 'succeeded') {
          total += payout.commission_amount;
        }
      }
    }

    return total;
  } catch (error) {
    console.error('Failed to calculate total commission:', error);
    return 0;
  }
}
