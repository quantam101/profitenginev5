import { query } from './db';
import { createPayout, ContractorPayoutRequest } from './payouts.server';

type PayoutResult = {
  contractorId: string;
  amount: number;
  status: 'completed' | 'failed';
  error?: string;
};

type DailyPayoutResult = {
  success: boolean;
  payouts: PayoutResult[];
  totalCommission: number;
  errors: string[];
};

export async function dailyCommissionPayout(): Promise<DailyPayoutResult> {
  const payouts: PayoutResult[] = [];
  const errors: string[] = [];
  let totalCommission = 0;

  try {
    const pendingResult = await query(
      `SELECT j.id AS job_id, j.contractor_id, j.contractor_email,
              j.contractor_name, j.commission_amount
       FROM jobs j
       WHERE j.status = 'completed'
         AND j.commission_paid = false
         AND j.commission_amount > 0
       ORDER BY j.completed_at ASC`
    );

    for (const row of pendingResult.rows) {
      try {
        const req: ContractorPayoutRequest = {
          jobId: row.job_id.toString(),
          contractorId: row.contractor_id,
          contractorEmail: row.contractor_email,
          contractorName: row.contractor_name,
          amount: parseFloat(row.commission_amount),
        };

        const record = await createPayout(req);

        if (record.status === 'completed') {
          totalCommission += Math.round(req.amount * 100);
          payouts.push({
            contractorId: req.contractorId,
            amount: req.amount,
            status: 'completed',
          });

          await query(
            `UPDATE jobs SET commission_paid = true WHERE id = $1`,
            [row.job_id]
          );
        } else {
          payouts.push({
            contractorId: req.contractorId,
            amount: req.amount,
            status: 'failed',
            error: record.error_message || 'Unknown error',
          });
          errors.push(
            `Payout failed for contractor ${req.contractorId}: ${record.error_message}`
          );
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        errors.push(`Payout error for job ${row.job_id}: ${msg}`);
        payouts.push({
          contractorId: row.contractor_id,
          amount: parseFloat(row.commission_amount),
          status: 'failed',
          error: msg,
        });
      }
    }

    return {
      success: errors.length === 0,
      payouts,
      totalCommission,
      errors,
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      payouts,
      totalCommission,
      errors: [msg],
    };
  }
}
