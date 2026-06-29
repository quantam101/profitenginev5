import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

export const maxDuration = 60;

const products = {
  travel: [
    { tier: 'starter', name: 'Budget Itinerary', price: 49900 },
    { tier: 'standard', name: 'Extended Itinerary', price: 149900 },
    { tier: 'premium', name: 'VIP Concierge', price: 249900 },
  ],
  newsletter: [
    { tier: 'starter', name: '1 Month Trial', price: 99900 },
    { tier: 'standard', name: '3-Month Package', price: 249900 },
    { tier: 'premium', name: 'Annual Retainer', price: 299900 },
  ],
  'sales-copy': [
    { tier: 'starter', name: 'Basic Page', price: 499900 },
    { tier: 'standard', name: 'Professional Page', price: 1299900 },
    { tier: 'premium', name: 'Enterprise Package', price: 2499900 },
  ],
  linkedin: [
    { tier: 'starter', name: 'Single Post', price: 49900 },
    { tier: 'standard', name: 'Monthly Package', price: 199900 },
    { tier: 'premium', name: 'Quarterly Retainer', price: 499900 },
  ],
  resume: [
    { tier: 'starter', name: 'Resume Only', price: 24900 },
    { tier: 'standard', name: 'Bundle', price: 69900 },
    { tier: 'premium', name: 'Career Package', price: 149900 },
  ],
  kdp: [
    { tier: 'starter', name: 'Single Book', price: 49900 },
    { tier: 'standard', name: 'Book Bundle', price: 129900 },
    { tier: 'premium', name: 'Publishing Bundle', price: 249900 },
  ],
};

export async function POST(request: NextRequest) {
  // Security: require authorization header
  const auth = request.headers.get('authorization');
  if (auth !== `Bearer ${process.env.STRIPE_SETUP_TOKEN || 'test-token'}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const stripeKey = process.env.STRIPE_SECRET_KEY;
  if (!stripeKey) {
    return NextResponse.json({ error: 'Stripe key not configured' }, { status: 500 });
  }

  const stripe = new Stripe(stripeKey);
  const priceIds: string[] = [];

  try {
    for (const [tool, tiers] of Object.entries(products)) {
      // Create or find product
      const existingProducts = await stripe.products.list({ limit: 100 });
      let product = existingProducts.data.find((p) =>
        p.name.toLowerCase().includes(tool.replace('-', ' ').toLowerCase())
      );

      if (!product) {
        product = await stripe.products.create({
          name: tool.replace('-', ' ').toUpperCase(),
          description: `${tool.replace('-', ' ')} service package`,
        });
      }

      // Create prices
      for (const { tier, name, price } of tiers) {
        const priceObj = await stripe.prices.create({
          product: product.id,
          unit_amount: price,
          currency: 'usd',
          nickname: `${tool}-${tier}`,
          metadata: { tool, tier, displayName: name },
        });

        priceIds.push(priceObj.id);
      }
    }

    return NextResponse.json({
      success: true,
      message: 'All products and prices created',
      priceIds,
      nextSteps: [
        'Go to: https://dashboard.stripe.com/billing/pricing-tables',
        'Click "Create pricing table"',
        'Add all price IDs above',
        'Configure and create',
        'Copy the Pricing Table ID (prctbl_xxxxx)',
      ],
    });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
