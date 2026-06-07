export type KdpUnitEconomics = 'ebook70' | 'ebook35' | 'paperbackStandard' | 'paperbackExpanded';

export type KdpRevenueOffer = {
  id: string;
  name: string;
  stream: 'publishing';
  price: number;
  cost: number;
  hours: number;
  proofRequired: boolean;
  cta: string;
  format: 'ebook' | 'paperback' | 'hardcover';
  unitEconomics: KdpUnitEconomics;
  royaltyRate: number;
  aiDisclosureRequired: boolean;
  humanApprovalRequired: boolean;
  qualityGate: string[];
  rightsGate: string[];
  launchStatus: 'research-ready' | 'draft-ready' | 'publish-ready';
};

export const kdpPolicySnapshot = {
  verifiedAt: '2026-06-07',
  posture: 'approval-gated, no auto-submission, no fake authors, no scraped copyrighted content',
  aiRule:
    'AI-generated text, images, or translations must be disclosed in KDP. AI-assisted editing, brainstorming, refinement, or error-checking does not require disclosure.',
  pricingRule:
    'US Kindle eBooks qualify for the 70% royalty option only inside the $2.99-$9.99 price band, subject to territory and delivery-cost rules.',
  printRule:
    'US paperbacks use 50% or 60% standard distribution royalty depending on list price, minus printing cost; expanded distribution uses 40% minus printing cost.',
  adsRule:
    'Amazon Ads for KDP books are CPC-based and must remain disabled until a book has a compliant detail page, real proof, and approved budget.',
  sourceUrls: [
    'https://kdp.amazon.com/en_US/help/topic/G200672390',
    'https://kdp.amazon.com/en_US/help/topic/G200634500',
    'https://kdp.amazon.com/en_US/help/topic/G200634560',
    'https://kdp.amazon.com/en_US/help/topic/G8BKPU9AGVZSF9QF',
    'https://kdp.amazon.com/en_US/help/topic/G201499010',
  ],
} as const;

export const kdpLaunchGates = [
  'Original Already Here LLC subject-matter expertise only',
  'No medical, legal, financial, or safety claims without documented review',
  'No copyrighted source copying, derivative summaries, fake author identities, or review manipulation',
  'Human approval required for title, subtitle, author name, description, keywords, categories, manuscript, cover, and AI disclosure state',
  'Manual KDP submission only; ProfitEngine may prepare assets and economics but must not publish or certify automatically',
  'Proof copy required before paid ads or broad promotion for print editions',
] as const;

export const kdpRevenueOffers: KdpRevenueOffer[] = [
  {
    id: 'kdp-field-tech-playbook-ebook',
    name: 'Field Tech Playbook eBook',
    stream: 'publishing',
    price: 9.99,
    cost: 0.18,
    hours: 6,
    proofRequired: false,
    cta: 'mailto:dispatch@alreadyherellc.com?subject=KDP%20Field%20Tech%20Playbook%20Build',
    format: 'ebook',
    unitEconomics: 'ebook70',
    royaltyRate: 0.7,
    aiDisclosureRequired: false,
    humanApprovalRequired: true,
    launchStatus: 'draft-ready',
    qualityGate: [
      'Practical field checklists and dispatch scripts from Already Here LLC experience',
      'No copied manuals, vendor-confidential procedures, or trademark misuse',
      'KDP description must accurately represent the book contents',
    ],
    rightsGate: [
      'Use original writing or licensed assets only',
      'Use Already Here LLC-owned diagrams/screenshots only',
      'Avoid client names unless already public and approved',
    ],
  },
  {
    id: 'kdp-municipal-procurement-ebook',
    name: 'Small IT Company Municipal Procurement Guide',
    stream: 'publishing',
    price: 7.99,
    cost: 0.12,
    hours: 5,
    proofRequired: false,
    cta: 'mailto:dispatch@alreadyherellc.com?subject=KDP%20Municipal%20Procurement%20Guide%20Build',
    format: 'ebook',
    unitEconomics: 'ebook70',
    royaltyRate: 0.7,
    aiDisclosureRequired: false,
    humanApprovalRequired: true,
    launchStatus: 'draft-ready',
    qualityGate: [
      'Actionable vendor registration, capability statement, and bid/no-bid workflow',
      'No legal advice; use clear operational disclaimer',
      'Include document checklist and city outreach templates',
    ],
    rightsGate: [
      'Use public procurement information only with attribution where needed',
      'Do not imply government endorsement',
      'Do not claim certifications unless verified',
    ],
  },
  {
    id: 'kdp-ai-profit-suite-operator-workbook',
    name: 'AI Profit Suite Operator Workbook',
    stream: 'publishing',
    price: 14.99,
    cost: 4.6,
    hours: 7,
    proofRequired: false,
    cta: 'mailto:dispatch@alreadyherellc.com?subject=KDP%20Operator%20Workbook%20Build',
    format: 'paperback',
    unitEconomics: 'paperbackStandard',
    royaltyRate: 0.6,
    aiDisclosureRequired: false,
    humanApprovalRequired: true,
    launchStatus: 'research-ready',
    qualityGate: [
      'Workbook must contain meaningful prompts, workflows, diagrams, and exercises',
      'Not positioned as a low-content blank journal',
      'Order proof copy before ads or broad promotion',
    ],
    rightsGate: [
      'Original workbook layouts only',
      'No stock-art license ambiguity',
      'No misleading software-income claims',
    ],
  },
];

export function estimateKdpNetUsd(offer: KdpRevenueOffer): number {
  if (offer.unitEconomics === 'ebook70' || offer.unitEconomics === 'ebook35') {
    return Number((offer.royaltyRate * Math.max(0, offer.price - offer.cost)).toFixed(2));
  }

  return Number((offer.royaltyRate * offer.price - offer.cost).toFixed(2));
}

export function rankKdpOffers(offers: KdpRevenueOffer[] = kdpRevenueOffers) {
  return offers
    .map((offer) => {
      const estimatedNetUsd = estimateKdpNetUsd(offer);
      return {
        ...offer,
        estimatedNetUsd,
        estimatedMarginPct: Number(((estimatedNetUsd / offer.price) * 100).toFixed(1)),
        netPerBuildHourUsd: Number((estimatedNetUsd / offer.hours).toFixed(2)),
      };
    })
    .sort((a, b) => b.netPerBuildHourUsd - a.netPerBuildHourUsd);
}

export function getKdpRevenueDashboard() {
  return {
    ok: true,
    service: 'profitengine-kdp-revenue-stream',
    mode: 'research_to_assets_manual_publish',
    policySnapshot: kdpPolicySnapshot,
    launchGates: kdpLaunchGates,
    rankedOffers: rankKdpOffers(),
    nextOperatorActions: [
      'Choose first title from rankedOffers',
      'Draft original table of contents and claims register',
      'Generate manuscript asset pack for human review',
      'Confirm AI disclosure state before KDP upload',
      'Manually upload to KDP only after approval',
    ],
  };
}
