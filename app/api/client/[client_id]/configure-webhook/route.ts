import { NextRequest, NextResponse } from 'next/server';
import { getClient, updateClient } from '@/lib/client-db';

export async function POST(
  request: NextRequest,
  { params }: { params: { client_id: string } }
) {
  try {
    const { webhook_url, events } = await request.json();
    const { client_id } = params;

    // Validate client
    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    // Validate webhook URL
    if (!webhook_url || typeof webhook_url !== 'string') {
      return NextResponse.json(
        { error: 'Valid webhook_url required' },
        { status: 400 }
      );
    }

    // Validate URL format
    try {
      new URL(webhook_url);
    } catch {
      return NextResponse.json(
        { error: 'Invalid URL format for webhook' },
        { status: 400 }
      );
    }

    // Validate events (optional but recommended)
    const validEvents = ['charge.succeeded', 'charge.failed', 'charge.refunded', 'payment_intent.succeeded'];
    if (events && Array.isArray(events)) {
      const invalid = events.filter((e: string) => !validEvents.includes(e));
      if (invalid.length > 0) {
        return NextResponse.json(
          {
            error: 'Invalid event types',
            valid_events: validEvents,
          },
          { status: 400 }
        );
      }
    }

    // Update client with webhook URL
    const updated = await updateClient(client_id, {
      webhook_url,
    });

    if (!updated) {
      return NextResponse.json(
        { error: 'Failed to update client' },
        { status: 500 }
      );
    }

    console.log(`✅ Webhook configured for client ${client_id}: ${webhook_url}`);

    return NextResponse.json(
      {
        ok: true,
        webhook_id: `wh_${client_id}_${Date.now()}`,
        webhook_url: updated.webhook_url,
        status: 'configured',
        events: events || validEvents,
        test_send_url: `/api/client/${client_id}/test-webhook`,
        ready_to_go_live: true,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Webhook configuration failed:', error);
    return NextResponse.json(
      { error: 'Webhook configuration failed' },
      { status: 500 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { client_id: string } }
) {
  try {
    const { client_id } = params;

    const client = await getClient(client_id);
    if (!client) {
      return NextResponse.json(
        { error: 'Client not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(
      {
        ok: true,
        webhook_url: client.webhook_url,
        configured: !!client.webhook_url,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Webhook lookup failed:', error);
    return NextResponse.json(
      { error: 'Webhook lookup failed' },
      { status: 500 }
    );
  }
}
