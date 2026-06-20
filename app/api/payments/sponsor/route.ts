import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

export const runtime = 'nodejs';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || process.env.STRIPE_API_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY or STRIPE_API_KEY not configured');
  }
  return new Stripe(stripeKey);
}

interface SponsorCheckoutRequest {
  sponsor_name: string;
  sponsorship_amount: number;
  return_url: string;
  duration?: string;
  email?: string;
}

interface SponsorCheckoutResponse {
  ok: boolean;
  session_url?: string;
  session_id?: string;
  error?: string;
  details?: string;
}

/**
 * POST /api/payments/sponsor
 * Create a Stripe Checkout session for sponsor payment
 * Request body:
 *   - sponsor_name (string): Name of the sponsor
 *   - sponsorship_amount (number): Amount in USD
 *   - return_url (string): URL to return to after checkout
 *   - duration (optional): Sponsorship duration (e.g., "1 month", "3 months")
 *   - email (optional): Sponsor email for receipt
 * Response: { ok: true, session_url, session_id }
 */
export async function POST(request: NextRequest) {
  const stripe = getStripe();
  try {
    const body = await request.json() as SponsorCheckoutRequest;
    const {
      sponsor_name,
      sponsorship_amount,
      return_url,
      duration = '1 month',
      email,
    } = body;

    // Validate required fields
    if (!sponsor_name || !sponsorship_amount || !return_url) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Missing required fields',
          details: 'Required: sponsor_name, sponsorship_amount, return_url',
        } as SponsorCheckoutResponse,
        { status: 400 }
      );
    }

    // Validate amount (minimum $5)
    if (sponsorship_amount < 5) {
      return NextResponse.json(
        {
          ok: false,
          error: 'Minimum sponsorship amount is $5',
          details: `Received: $${sponsorship_amount}`,
        } as SponsorCheckoutResponse,
        { status: 400 }
      );
    }

    // Create Stripe Checkout session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      mode: 'payment',
      success_url: `${return_url}?session_id={CHECKOUT_SESSION_ID}&success=true`,
      cancel_url: `${return_url}?cancelled=true`,
      customer_email: email,
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: `Newsletter Sponsorship: ${sponsor_name}`,
              description: `${duration} sponsorship`,
              images: [], // Can be enhanced with logo URLs
              metadata: {
                sponsor_name,
                duration,
              },
            },
            unit_amount: Math.round(sponsorship_amount * 100), // Convert to cents
          },
          quantity: 1,
        },
      ],
      metadata: {
        sponsor_name,
        duration,
        channel: 'newsletter',
        sponsor_email: email || 'unknown',
      },
      receipt_email: email,
      submit_type: 'pay',
    });

    if (!session.url) {
      throw new Error('Failed to generate checkout URL');
    }

    console.log(`✅ Stripe checkout session created for ${sponsor_name}: ${session.id}`);

    return NextResponse.json(
      {
        ok: true,
        session_url: session.url,
        session_id: session.id,
      } as SponsorCheckoutResponse,
      { status: 201 }
    );
  } catch (error) {
    console.error('Sponsor checkout error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      {
        ok: false,
        error: 'Failed to create checkout session',
        details: errorMessage,
      } as SponsorCheckoutResponse,
      { status: 500 }
    );
  }
}

/**
 * GET /api/payments/sponsor?session_id=<id>
 * Retrieve checkout session status
 */
export async function GET(request: NextRequest) {
  const stripe = getStripe();
  try {
    const sessionId = request.nextUrl.searchParams.get('session_id');

    if (!sessionId) {
      return NextResponse.json(
        {
          ok: false,
          error: 'session_id required as query parameter',
        },
        { status: 400 }
      );
    }

    const session = await stripe.checkout.sessions.retrieve(sessionId);

    // Get payment intent details if completed
    let paymentStatus = session.payment_status;
    let paymentIntentId = null;

    if (session.payment_intent) {
      const pi = await stripe.paymentIntents.retrieve(
        session.payment_intent as string
      );
      paymentStatus = pi.status;
      paymentIntentId = pi.id;
    }

    return NextResponse.json({
      ok: true,
      session_id: session.id,
      status: session.status,
      payment_status: paymentStatus,
      amount_total: session.amount_total ? session.amount_total / 100 : 0,
      currency: session.currency,
      customer_email: session.customer_email,
      metadata: session.metadata,
      payment_intent_id: paymentIntentId,
    });
  } catch (error) {
    console.error('Failed to retrieve session:', error);
    return NextResponse.json(
      {
        ok: false,
        error: 'Failed to retrieve session',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
