import { NextRequest, NextResponse } from 'next/server';
import { getClient, updateClient } from '@/lib/client-db';

export async function POST(
  request: NextRequest,
  { params }: { params: { client_id: string } }
) {
  try {
    const { stripe_account_id, code } = await request.json();
    const { client_id } = params;

    // Validate input
    if (!stripe_account_id && !code) {
      return NextResponse.json(
        { error: 'stripe_account_id or code required' },
        { status: 400 }
      );
    }

    // Get client
    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    // In production, exchange code for stripe_account_id
    // For now, accept direct stripe_account_id
    let accountId = stripe_account_id;

    if (code && !stripe_account_id) {
      // Exchange OAuth code for account ID
      // This would call Stripe's OAuth token endpoint
      // For MVP, we require direct account ID
      return NextResponse.json(
        { error: 'Direct stripe_account_id required for MVP' },
        { status: 400 }
      );
    }

    // Validate Stripe account ID format
    if (!accountId || !accountId.startsWith('acct_')) {
      return NextResponse.json(
        { error: 'Invalid Stripe account ID format' },
        { status: 400 }
      );
    }

    // Update client with Stripe account
    const updated = await updateClient(client_id, {
      stripe_account_id: accountId,
      stripe_test_mode: true,
      status: 'stripe_connected',
    });

    if (!updated) {
      return NextResponse.json(
        { error: 'Failed to update client' },
        { status: 500 }
      );
    }

    console.log(`✅ Stripe connected for client ${client_id}: ${accountId}`);

    return NextResponse.json(
      {
        ok: true,
        client_id: updated.id,
        status: updated.status,
        stripe_account_id: updated.stripe_account_id,
        stripe_test_mode: updated.stripe_test_mode,
        next_step: `Test payment at /api/client/${client_id}/test-transaction`,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('OAuth callback failed:', error);
    return NextResponse.json(
      { error: 'OAuth callback failed' },
      { status: 500 }
    );
  }
}
