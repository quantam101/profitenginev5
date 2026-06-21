import { NextRequest, NextResponse } from 'next/server';
import { getClient, getTransaction } from '@/lib/client-db';

export async function GET(
  request: NextRequest,
  { params }: { params: { client_id: string; txn_id: string } }
) {
  try {
    const { client_id, txn_id } = params;

    // Validate client exists
    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    // Get transaction
    const transaction = await getTransaction(client_id, txn_id);
    if (!transaction) {
      return NextResponse.json(
        { error: 'Transaction not found' },
        { status: 404 }
      );
    }

    // Check if all verifications passed
    const verified =
      transaction.status === 'succeeded' &&
      transaction.webhook_delivered &&
      transaction.webhook_response_code === 200;

    return NextResponse.json(
      {
        ok: true,
        transaction_id: transaction.id,
        stripe_charge_id: transaction.stripe_charge_id,
        amount: transaction.amount / 100,
        status: transaction.status,
        webhook_event_id: transaction.webhook_event_id,
        webhook_delivered: transaction.webhook_delivered,
        webhook_response_code: transaction.webhook_response_code,
        verified,
        created_at: transaction.created_at,
        updated_at: transaction.updated_at,
        ready_to_go_live: verified,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Transaction lookup failed:', error);
    return NextResponse.json(
      { error: 'Transaction lookup failed' },
      { status: 500 }
    );
  }
}
