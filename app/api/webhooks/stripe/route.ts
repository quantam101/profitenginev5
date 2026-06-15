import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || process.env.STRIPE_API_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY or STRIPE_API_KEY not configured');
  }
  return new Stripe(stripeKey);
}

function getWebhookSecret() {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET || '';
  if (!webhookSecret) {
    throw new Error('STRIPE_WEBHOOK_SECRET not configured');
  }
  return webhookSecret;
}

export async function POST(request: NextRequest) {
  const stripe = getStripe();
  const webhookSecret = getWebhookSecret();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    return NextResponse.json(
      { error: 'Missing stripe-signature header' },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    const rawBody = await request.text();
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    console.error('Webhook signature verification failed:', error);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 401 }
    );
  }

  // Handle different event types
  switch (event.type) {
    case 'payment_intent.succeeded': {
      const paymentIntent = event.data.object as Stripe.PaymentIntent;
      console.log(`✅ Payment succeeded: ${paymentIntent.id}`);

      // TODO: Update job status to "paid" in database
      // TODO: Create contractor payout via Stripe Connect
      // TODO: Send notification to contractor
      // TODO: Log conversion in /prospects if B2B deal

      return NextResponse.json(
        {
          ok: true,
          message: 'Payment succeeded',
          jobId: paymentIntent.metadata?.jobId,
          amount: paymentIntent.amount / 100,
        },
        { status: 200 }
      );
    }

    case 'payment_intent.payment_failed': {
      const paymentIntent = event.data.object as Stripe.PaymentIntent;
      console.log(`❌ Payment failed: ${paymentIntent.id}`);

      // TODO: Update job status to "payment_failed"
      // TODO: Send retry email to customer

      return NextResponse.json(
        {
          ok: true,
          message: 'Payment failed notification logged',
          jobId: paymentIntent.metadata?.jobId,
        },
        { status: 200 }
      );
    }

    case 'charge.refunded': {
      const charge = event.data.object as Stripe.Charge;
      console.log(`↩️ Charge refunded: ${charge.id}`);

      // TODO: Reverse contractor payout
      // TODO: Update job status to "refunded"
      // TODO: Notify contractor

      return NextResponse.json(
        {
          ok: true,
          message: 'Refund processed',
        },
        { status: 200 }
      );
    }

    case 'invoice.payment_succeeded': {
      const invoice = event.data.object as Stripe.Invoice;
      console.log(`✅ Invoice paid: ${invoice.id}`);

      // TODO: Update prospect status to "won + closed"
      // TODO: Mark B2B retainer as active
      // TODO: Send confirmation to client

      return NextResponse.json(
        {
          ok: true,
          message: 'Invoice payment succeeded',
        },
        { status: 200 }
      );
    }

    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      console.log(`❌ Invoice payment failed: ${invoice.id}`);

      // TODO: Mark invoice as failed
      // TODO: Send retry reminder

      return NextResponse.json(
        {
          ok: true,
          message: 'Invoice payment failed logged',
        },
        { status: 200 }
      );
    }

    default:
      return NextResponse.json(
        { ok: true, message: `Unhandled event type: ${event.type}` },
        { status: 200 }
      );
  }
}
