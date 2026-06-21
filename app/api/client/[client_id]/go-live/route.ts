import { NextRequest, NextResponse } from 'next/server';
import { getClient, updateClient, getClientTransactions } from '@/lib/client-db';

export async function POST(
  request: NextRequest,
  { params }: { params: { client_id: string } }
) {
  try {
    const { confirmation } = await request.json();
    const { client_id } = params;

    // Validate client
    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    // Validate confirmation
    if (!confirmation || typeof confirmation !== 'string') {
      return NextResponse.json(
        { error: 'Confirmation statement required' },
        { status: 400 }
      );
    }

    // Check pre-requisites
    const errors: string[] = [];

    if (!client.stripe_account_id) {
      errors.push('Stripe account not connected');
    }

    if (!client.webhook_url) {
      errors.push('Webhook URL not configured');
    }

    // Check if they have at least one successful test transaction
    const transactions = await getClientTransactions(client_id);
    const successfulTxn = transactions.find((t) => t.status === 'succeeded');
    if (!successfulTxn) {
      errors.push('Must complete at least one test transaction');
    }

    if (errors.length > 0) {
      return NextResponse.json(
        {
          error: 'Pre-requisites not met',
          missing_requirements: errors,
        },
        { status: 400 }
      );
    }

    // Update client to live mode
    const updated = await updateClient(client_id, {
      status: 'live',
      stripe_test_mode: false,
    });

    if (!updated) {
      return NextResponse.json(
        { error: 'Failed to update client status' },
        { status: 500 }
      );
    }

    console.log(`✅ Client ${client_id} is now LIVE - ready for real customer payments`);

    return NextResponse.json(
      {
        ok: true,
        status: 'live',
        mode: 'production',
        client_id: updated.id,
        business_name: updated.business_name,
        message: 'Your Stripe account is now accepting real customer payments',
        commission_rate: updated.commission_rate,
        commission_payout_schedule: 'daily at 00:00 UTC',
        stripe_account_id: updated.stripe_account_id,
        webhook_url: updated.webhook_url,
        api_key: updated.api_key,
        next_steps: [
          'Monitor your dashboard at /client/' + client_id + '/dashboard',
          'Payments will be routed to your webhook URL',
          'Commission (2.5%) will be calculated daily',
          'Payouts will be sent daily',
        ],
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Go-live failed:', error);
    return NextResponse.json(
      { error: 'Go-live failed' },
      { status: 500 }
    );
  }
}
