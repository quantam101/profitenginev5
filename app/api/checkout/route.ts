import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import {
  linkBooking,
  newBookingId,
  persistLead,
} from '@/lib/revenue-attribution.mjs';

interface CheckoutRequest {
  tool: string;
  tier: string;
  email?: string;
  leadId?: string;
  bookingId?: string;
}

const toolPricing: Record<string, Record<string, { name: string; price: number }>> = {
  travel: {
    starter: { name: 'Budget Itinerary', price: 49900 },
    standard: { name: 'Extended Itinerary', price: 149900 },
    premium: { name: 'VIP Concierge', price: 249900 },
  },
  newsletter: {
    starter: { name: '1 Month Trial', price: 99900 },
    standard: { name: '3-Month Package', price: 249900 },
    premium: { name: 'Annual Retainer', price: 299900 },
  },
  'sales-copy': {
    starter: { name: 'Basic Page', price: 499900 },
    standard: { name: 'Professional Page', price: 1299900 },
    premium: { name: 'Enterprise Package', price: 2499900 },
  },
  linkedin: {
    starter: { name: 'Single Post', price: 49900 },
    standard: { name: 'Monthly Package', price: 199900 },
    premium: { name: 'Quarterly Retainer', price: 499900 },
  },
  resume: {
    starter: { name: 'Resume Only', price: 24900 },
    standard: { name: 'Bundle', price: 69900 },
    premium: { name: 'Career Package', price: 149900 },
  },
  kdp: {
    starter: { name: 'Single Book', price: 49900 },
    standard: { name: 'Book Bundle', price: 129900 },
    premium: { name: 'Publishing Bundle', price: 249900 },
  },
};

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body: CheckoutRequest = await request.json();
    const { tool, tier, email } = body;

    if (!tool || !tier) {
      return NextResponse.json({ error: 'Tool and tier are required' }, { status: 400 });
    }

    const pricing = toolPricing[tool]?.[tier];
    if (!pricing) {
      return NextResponse.json({ error: 'Invalid tool or tier' }, { status: 400 });
    }

    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || process.env.NEXT_PUBLIC_SITE_URL || 'https://app.alreadyherellc.com';
    const stripeKey = process.env.STRIPE_SECRET_KEY;

    if (!stripeKey) {
      return NextResponse.json({ error: 'Stripe key not configured' }, { status: 500 });
    }

    const lead = body.leadId
      ? { leadId: body.leadId }
      : await persistLead({
          email,
          service: `${tool}:${tier}`,
          source: 'direct-checkout',
          landingPage: '/checkout',
        });
    const bookingId = body.bookingId || newBookingId();

    const stripe = new Stripe(stripeKey);
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: `${pricing.name} - ${tool.replace('-', ' ')}`,
              description: `${tool} ${tier} package`,
            },
            unit_amount: pricing.price,
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${baseUrl}/success?session_id={CHECKOUT_SESSION_ID}&lead_id=${encodeURIComponent(lead.leadId)}&booking_id=${encodeURIComponent(bookingId)}`,
      cancel_url: `${baseUrl}/checkout`,
      ...(email && { customer_email: email }),
      metadata: {
        tool,
        tier,
        lead_id: lead.leadId,
        booking_id: bookingId,
      },
      payment_intent_data: {
        metadata: {
          tool,
          tier,
          lead_id: lead.leadId,
          booking_id: bookingId,
        },
      },
    });

    await linkBooking({
      leadId: lead.leadId,
      bookingId,
      provider: 'stripe',
      checkoutId: session.id,
      amount: pricing.price,
      currency: 'usd',
    });

    return NextResponse.json({
      sessionId: session.id,
      url: session.url,
      leadId: lead.leadId,
      bookingId,
    });
  } catch (error) {
    console.error('Checkout error:', error);
    return NextResponse.json(
      {
        error: 'Failed to create checkout session',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
