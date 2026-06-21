import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { getClient, logTransaction, Transaction } from '@/lib/client-db';
import { randomUUID } from 'crypto';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY not configured');
  }
  return new Stripe(stripeKey);
}

export async function POST(
  request: NextRequest,
  { params }: { params: { client_id: string } }
) {
  try {
    const { amount = 99 } = await request.json(); // Default to $0.99
    const { client_id } = params;

    // Validate client
    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    if (!client.stripe_account_id) {
      return NextResponse.json(
        { error: 'Stripe account not connected' },
        { status: 400 }
      );
    }

    if (client.status !== 'stripe_connected' && client.status !== 'testing' && client.status !== 'live') {
      return NextResponse.json(
        { error: 'Client not ready for transactions' },
        { status: 400 }
      );
    }

    // Validate amount
    if (amount < 1 || amount > 99999) {
      return NextResponse.json(
        { error: 'Amount must be between $0.01 and $999.99' },
        { status: 400 }
      );
    }

    const stripe = getStripe();
    const transactionId = randomUUID();

    // Create test charge on client's Stripe account
    // Using OAuth to charge the connected account
    const charge = await stripe.charges.create(
      {
        amount: Math.round(amount), // in cents
        currency: 'usd',
        description: `Test charge for client ${client_id}`,
        metadata: {
          client_id,
          transaction_id: transactionId,
          test_mode: 'true',
        },
      },
      {
        stripeAccount: client.stripe_account_id,
      }
    );

    // Log transaction
    const transaction: Transaction = {
      id: transactionId,
      client_id,
      stripe_charge_id: charge.id,
      amount: charge.amount,
      status: charge.status === 'succeeded' ? 'succeeded' : 'pending',
      webhook_event_id: null,
      webhook_delivered: false,
      webhook_response_code: null,
      created_at: Date.now(),
      updated_at: Date.now(),
    };

    await logTransaction(transaction);

    // Update client status to testing if this succeeds
    if (charge.status === 'succeeded') {
      const updatedClient = await import('@/lib/client-db').then(m =>
        m.updateClient(client_id, { status: 'testing' })
      );
    }

    console.log(`✅ Test transaction created for client ${client_id}: ${charge.id}`);

    return NextResponse.json(
      {
        ok: true,
        transaction_id: transactionId,
        stripe_charge_id: charge.id,
        amount: charge.amount / 100,
        status: charge.status,
        webhook_event_id: null,
        expected_webhook: 'within 5 seconds',
        check_status_url: `/api/client/${client_id}/transaction/${transactionId}`,
        webhook_url_required: 'Configure at /api/client/[client_id]/configure-webhook',
      },
      { status: 201 }
    );
  } catch (error: any) {
    console.error('Test transaction failed:', error);
    return NextResponse.json(
      {
        error: 'Test transaction failed',
        message: error.message,
      },
      { status: 500 }
    );
  }
}
