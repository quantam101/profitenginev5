import { NextRequest, NextResponse } from 'next/server';
import {
  getClient,
  getClientTransactions,
  calculateClientCommission,
} from '@/lib/client-db';

export async function GET(
  request: NextRequest,
  { params }: { params: { client_id: string } }
) {
  try {
    const { client_id } = params;

    // Validate client
    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    // Get all transactions
    const transactions = await getClientTransactions(client_id);

    // Calculate stats
    const testTransactions = transactions.filter(
      (t) => t.status === 'succeeded' && t.created_at
    ).length;
    const liveTransactions = transactions.filter(
      (t) => t.status === 'succeeded' && client.status === 'live'
    ).length;
    const totalVolume = transactions
      .filter((t) => t.status === 'succeeded')
      .reduce((sum, t) => sum + t.amount, 0);

    const commissionEarned = await calculateClientCommission(client_id);

    // Build setup progress
    const progress = {
      step: 1,
      completed: ['register'],
      next: 'Connect Stripe',
    };

    if (client.status === 'stripe_connected') {
      progress.step = 2;
      progress.completed = ['register', 'connect_stripe'];
      progress.next = 'Make test payment';
    } else if (client.status === 'testing') {
      progress.step = 3;
      progress.completed = ['register', 'connect_stripe', 'test_payment'];
      progress.next = 'Configure webhook and go live';
    } else if (client.status === 'live') {
      progress.step = 4;
      progress.completed = ['register', 'connect_stripe', 'test_payment', 'go_live'];
      progress.next = 'Monitor transactions';
    }

    // Build go-live checklist
    const checklist = [
      { item: 'Stripe connected', done: !!client.stripe_account_id },
      { item: 'Test payment succeeded', done: testTransactions > 0 },
      { item: 'Webhook configured', done: !!client.webhook_url },
      { item: 'Ready to go live', done: testTransactions > 0 && !!client.webhook_url },
    ];

    return NextResponse.json(
      {
        ok: true,
        client: {
          id: client.id,
          email: client.email,
          business_name: client.business_name,
          status: client.status,
          api_key: client.api_key,
          created_at: client.created_at,
        },
        stripe_connection: {
          connected: !!client.stripe_account_id,
          account_id: client.stripe_account_id,
          test_mode: client.stripe_test_mode,
        },
        setup_progress: progress,
        revenue: {
          test_transactions: testTransactions,
          live_transactions: liveTransactions,
          total_volume: (totalVolume / 100).toFixed(2),
          total_volume_cents: totalVolume,
          commission_earned: (commissionEarned / 100).toFixed(2),
          commission_earned_cents: commissionEarned,
          commission_rate: client.commission_rate,
          payout_schedule: 'daily at 00:00 UTC',
        },
        webhook: {
          configured: !!client.webhook_url,
          url: client.webhook_url,
        },
        webhook_logs: transactions.map((t) => ({
          event_id: t.webhook_event_id,
          transaction_id: t.id,
          stripe_charge_id: t.stripe_charge_id,
          timestamp: t.created_at,
          status: t.status,
          webhook_delivered: t.webhook_delivered,
          webhook_response_code: t.webhook_response_code,
        })),
        go_live_checklist: checklist,
        ready_to_go_live: checklist.every((c) => c.done),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Dashboard fetch failed:', error);
    return NextResponse.json(
      { error: 'Dashboard fetch failed' },
      { status: 500 }
    );
  }
}
