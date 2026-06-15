import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || process.env.STRIPE_API_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY or STRIPE_API_KEY not configured');
  }
  return new Stripe(stripeKey);
}

export async function POST(request: NextRequest) {
  const stripe = getStripe();
  try {
    const { jobId, jobTitle, pay, contractorId, customerEmail } = await request.json();

    // Validate required fields
    if (!jobId || !pay || !contractorId || !customerEmail) {
      return NextResponse.json(
        { error: 'Missing required fields: jobId, pay, contractorId, customerEmail' },
        { status: 400 }
      );
    }

    if (pay < 300) {
      return NextResponse.json(
        { error: 'Minimum job pay is $300' },
        { status: 400 }
      );
    }

    // Create PaymentIntent
    const paymentIntent = await stripe.paymentIntents.create({
      amount: Math.round(pay * 100), // Convert to cents
      currency: 'usd',
      payment_method_types: ['card'],
      metadata: {
        jobId,
        jobTitle,
        contractorId,
        customerEmail,
      },
      receipt_email: customerEmail,
      description: `Job Payment - ${jobTitle}`,
    });

    return NextResponse.json(
      {
        ok: true,
        clientSecret: paymentIntent.client_secret,
        intentId: paymentIntent.id,
        amount: pay,
        jobId,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Failed to create payment intent:', error);
    return NextResponse.json(
      { error: 'Failed to create payment intent' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const stripe = getStripe();
  const searchParams = request.nextUrl.searchParams;
  const intentId = searchParams.get('intent_id');

  if (!intentId) {
    return NextResponse.json(
      { error: 'intent_id required' },
      { status: 400 }
    );
  }

  try {
    const paymentIntent = await stripe.paymentIntents.retrieve(intentId);

    return NextResponse.json({
      ok: true,
      status: paymentIntent.status,
      amount: paymentIntent.amount / 100,
      currency: paymentIntent.currency,
      jobId: paymentIntent.metadata?.jobId,
    });
  } catch (error) {
    console.error('Failed to retrieve payment intent:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve payment intent' },
      { status: 500 }
    );
  }
}
