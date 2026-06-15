import Stripe from 'stripe';
import { query } from './db';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || process.env.STRIPE_API_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY or STRIPE_API_KEY not configured');
  }
  return new Stripe(stripeKey);
}

export type ContractorPayoutRequest = {
  jobId: string;
  contractorId: string;
  contractorEmail: string;
  contractorName?: string;
  amount: number; // Payout amount in USD
};

export type PayoutRecord = {
  id: string;
  job_id: string;
  contractor_id: string;
  contractor_stripe_account: string | null;
  amount: number;
  currency: string;
  stripe_transfer_id: string | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

// Create or get contractor's Stripe Connect account
export async function getOrCreateContractorAccount(
  contractorId: string,
  email: string,
  name?: string
): Promise<string> {
  const stripe = getStripe();

  // Check if contractor already has a connected account
  const existing = await query(
    `SELECT contractor_stripe_account FROM contractor_accounts
     WHERE contractor_id = $1`,
    [contractorId]
  );

  if (existing.rows.length > 0 && existing.rows[0].contractor_stripe_account) {
    return existing.rows[0].contractor_stripe_account;
  }

  // Create a new connected account for this contractor
  const account = await stripe.accounts.create({
    type: 'express',
    country: 'US',
    email,
    metadata: {
      contractor_id: contractorId,
      name: name || 'Contractor',
    },
  });

  // Store the account mapping
  await query(
    `INSERT INTO contractor_accounts (contractor_id, contractor_stripe_account)
     VALUES ($1, $2)
     ON CONFLICT (contractor_id) DO UPDATE SET contractor_stripe_account = $2`,
    [contractorId, account.id]
  );

  return account.id;
}

// Create a payout to a contractor
export async function createPayout(req: ContractorPayoutRequest): Promise<PayoutRecord> {
  const stripe = getStripe();

  try {
    // Get or create contractor's Stripe Connect account
    const stripeAccountId = await getOrCreateContractorAccount(
      req.contractorId,
      req.contractorEmail,
      req.contractorName
    );

    // Create transfer to contractor's account
    const transfer = await stripe.transfers.create({
      amount: Math.round(req.amount * 100), // Convert to cents
      currency: 'usd',
      destination: stripeAccountId,
      metadata: {
        job_id: req.jobId,
        contractor_id: req.contractorId,
      },
    });

    // Record payout in database
    const payout = await query(
      `INSERT INTO payouts
       (job_id, contractor_id, contractor_stripe_account, amount, currency, stripe_transfer_id, status)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING id, job_id, contractor_id, contractor_stripe_account, amount, currency,
                 stripe_transfer_id, status, error_message, created_at, completed_at`,
      [
        req.jobId,
        req.contractorId,
        stripeAccountId,
        req.amount,
        'usd',
        transfer.id,
        'completed',
      ]
    );

    return payoutRowToRecord(payout.rows[0]);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const payout = await query(
      `INSERT INTO payouts
       (job_id, contractor_id, amount, currency, status, error_message)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, job_id, contractor_id, contractor_stripe_account, amount, currency,
                 stripe_transfer_id, status, error_message, created_at, completed_at`,
      [req.jobId, req.contractorId, req.amount, 'usd', 'failed', errorMessage]
    );

    return payoutRowToRecord(payout.rows[0]);
  }
}

// Get payout by ID
export async function getPayoutById(payoutId: string): Promise<PayoutRecord | null> {
  const result = await query(
    `SELECT id, job_id, contractor_id, contractor_stripe_account, amount, currency,
            stripe_transfer_id, status, error_message, created_at, completed_at
     FROM payouts WHERE id = $1`,
    [payoutId]
  );

  return result.rows.length > 0 ? payoutRowToRecord(result.rows[0]) : null;
}

// Get payouts by contractor
export async function getContractorPayouts(contractorId: string): Promise<PayoutRecord[]> {
  const result = await query(
    `SELECT id, job_id, contractor_id, contractor_stripe_account, amount, currency,
            stripe_transfer_id, status, error_message, created_at, completed_at
     FROM payouts WHERE contractor_id = $1 ORDER BY created_at DESC`,
    [contractorId]
  );

  return result.rows.map(payoutRowToRecord);
}

// Get payout by job
export async function getPayoutByJob(jobId: string): Promise<PayoutRecord | null> {
  const result = await query(
    `SELECT id, job_id, contractor_id, contractor_stripe_account, amount, currency,
            stripe_transfer_id, status, error_message, created_at, completed_at
     FROM payouts WHERE job_id = $1 LIMIT 1`,
    [jobId]
  );

  return result.rows.length > 0 ? payoutRowToRecord(result.rows[0]) : null;
}

// Get contractor's Stripe onboarding link (refresh or initial)
export async function getContractorOnboardingLink(
  contractorId: string,
  refreshUrl: string
): Promise<string> {
  const stripe = getStripe();

  // Get contractor's account ID
  const result = await query(
    `SELECT contractor_stripe_account FROM contractor_accounts
     WHERE contractor_id = $1`,
    [contractorId]
  );

  if (result.rows.length === 0) {
    throw new Error('Contractor account not found');
  }

  const accountId = result.rows[0].contractor_stripe_account;

  // Create account link for onboarding
  const link = await stripe.accountLinks.create({
    account: accountId,
    type: 'account_onboarding',
    refresh_url: refreshUrl,
    return_url: refreshUrl,
  });

  return link.url;
}

function payoutRowToRecord(row: any): PayoutRecord {
  return {
    id: row.id.toString(),
    job_id: row.job_id.toString(),
    contractor_id: row.contractor_id,
    contractor_stripe_account: row.contractor_stripe_account || null,
    amount: parseFloat(row.amount),
    currency: row.currency,
    stripe_transfer_id: row.stripe_transfer_id || null,
    status: row.status,
    error_message: row.error_message || null,
    created_at: new Date(row.created_at).toISOString(),
    completed_at: row.completed_at ? new Date(row.completed_at).toISOString() : null,
  };
}
