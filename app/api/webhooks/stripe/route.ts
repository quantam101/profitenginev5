import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { recordRevenueOnce } from '@/lib/revenue-attribution.mjs';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  const stripeKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!stripeKey || !webhookSecret) {
    return NextResponse.json({ ok: false, error: 'Stripe webhook not configured' }, { status: 503 });
  }

  const signature = request.headers.get('stripe-signature');
  if (!signature) {
    return NextResponse.json({ ok: false, error: 'Missing Stripe signature' }, { status: 400 });
  }

  const stripe = new Stripe(stripeKey);
  const rawBody = await request.text();
  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    console.error('Stripe webhook signature verification failed:', error);
    return NextResponse.json({ ok: false, error: 'Invalid signature' }, { status: 400 });
  }

  if (event.type !== 'checkout.session.completed' && event.type !== 'checkout.session.async_payment_succeeded') {
    return NextResponse.json({ ok: true, ignored: true, type: event.type });
  }

  const session = event.data.object as Stripe.Checkout.Session;
  if (session.payment_status !== 'paid') {
    return NextResponse.json({ ok: true, ignored: true, reason: 'payment_not_paid' });
  }

  const paymentId = typeof session.payment_intent === 'string'
    ? session.payment_intent
    : session.payment_intent?.id || session.id;
  const leadId = session.metadata?.lead_id || '';
  const bookingId = session.metadata?.booking_id || '';

  try {
    const result = await recordRevenueOnce({
      provider: 'stripe',
      paymentId,
      providerEventId: event.id,
      leadId,
      bookingId,
      checkoutId: session.id,
      amount: session.amount_total || 0,
      currency: session.currency || 'usd',
      rawType: event.type,
    });

    return NextResponse.json({
      ok: true,
      inserted: result.inserted,
      duplicate: result.duplicate,
      revenueEventId: result.event?.revenueEventId,
      leadId,
      bookingId,
      paymentId,
    });
  } catch (error) {
    console.error('Stripe revenue reconciliation failed:', error);
    return NextResponse.json({ ok: false, error: 'Revenue reconciliation failed' }, { status: 500 });
  }
}
