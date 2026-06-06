import { NextResponse } from 'next/server';

const PROOF_THRESHOLD_USD = 25_000;

const storeLinks = {
  etsy: 'https://www.etsy.com/shop/AlreadyHereLLC',
  printify: 'https://fly-culture-shop.printify.me',
  shopify: 'https://flydesignvault.com',
  profitengine: 'https://profitengine-tau.vercel.app',
};

const offers = [
  { id: 'etsy-pod-shirt', name: 'Proof-first builder apparel', stream: 'pod', price: 29.99, cost: 16.5, hours: 0.05, proofRequired: false, cta: storeLinks.etsy },
  { id: 'etsy-printify-build', name: 'Etsy/Printify store build', stream: 'service', price: 499, cost: 25, hours: 5, proofRequired: false, cta: 'mailto:dispatch@alreadyherellc.com?subject=Etsy%20Printify%20Store%20Build' },
  { id: 'stripe-payment-setup', name: 'Stripe payment setup', stream: 'service', price: 349, cost: 10, hours: 3, proofRequired: false, cta: 'mailto:dispatch@alreadyherellc.com?subject=Stripe%20Payment%20Setup' },
  { id: 'ai-content-system', name: 'AI content system setup', stream: 'service', price: 799, cost: 35, hours: 8, proofRequired: false, cta: 'mailto:dispatch@alreadyherellc.com?subject=AI%20Content%20System%20Setup' },
  { id: 'local-automation', name: 'Local business automation', stream: 'service', price: 999, cost: 50, hours: 10, proofRequired: false, cta: 'mailto:dispatch@alreadyherellc.com?subject=Local%20Business%20Automation' },
  { id: 'printify-affiliate-content', name: 'Printify education affiliate funnel', stream: 'affiliate', price: 0, cost: 0, hours: 1, proofRequired: false, cta: storeLinks.printify },
  { id: 'profitengine-hosted-beta', name: 'ProfitEngine hosted beta', stream: 'saas', price: 149, cost: 20, hours: 2, proofRequired: true, cta: `${storeLinks.profitengine}#waitlist` },
];

function margin(offer: typeof offers[number]) {
  const platformFee = offer.stream === 'pod' ? 0.2 + offer.price * 0.065 : 0;
  const paymentFee = offer.price > 0 ? offer.price * 0.03 + 0.25 : 0;
  const net = offer.price - offer.cost - platformFee - paymentFee;
  return {
    ...offer,
    estimatedPlatformFeeUsd: Number(platformFee.toFixed(2)),
    estimatedPaymentFeeUsd: Number(paymentFee.toFixed(2)),
    estimatedNetUsd: Number(net.toFixed(2)),
    estimatedMarginPct: offer.price > 0 ? Number(((net / offer.price) * 100).toFixed(1)) : 0,
    netPerHourUsd: offer.hours ? Number((net / offer.hours).toFixed(2)) : 0,
  };
}

export async function GET() {
  const verifiedRevenueUsd = Number(process.env.VERIFIED_REVENUE_USD ?? 0);
  const rankedOffers = offers.map(margin).sort((a, b) => {
    if (a.proofRequired !== b.proofRequired) return a.proofRequired ? 1 : -1;
    return b.netPerHourUsd - a.netPerHourUsd;
  });
  return NextResponse.json({
    proof: {
      thresholdUsd: PROOF_THRESHOLD_USD,
      verifiedRevenueUsd,
      remainingUsd: Math.max(0, PROOF_THRESHOLD_USD - verifiedRevenueUsd),
      unlocked: verifiedRevenueUsd >= PROOF_THRESHOLD_USD,
      rule: 'Paid ProfitEngine/Command OS offers stay waitlist-only until verified revenue reaches $25,000.',
    },
    storeLinks,
    rankedOffers,
    agents: ['offer-scout', 'margin-guard', 'listing-optimizer', 'traffic-agent', 'proof-ledger'],
    immediateStreams: ['POD + Etsy/Printify', 'productized services', 'affiliate education content'],
  }, { headers: { 'Cache-Control': 'no-store' } });
}
