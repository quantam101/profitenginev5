const MINIMUM_WORDS_FOR_PRODUCT = 350;

function normalizeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function sentenceCase(value) {
  const text = normalizeText(value);
  if (!text) return 'Untitled';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function estimateReadingMinutes(wordCount) {
  return Math.max(1, Math.ceil(Number(wordCount || 0) / 220));
}

function estimatePageCount(wordCount) {
  return Math.max(1, Math.ceil(Number(wordCount || 0) / 300));
}

function buildChapters(article) {
  const topic = sentenceCase(article.topic || 'General');
  return [
    `${topic}: Executive Summary`,
    'Problem, Audience, and Offer Fit',
    'Reusable Proof-of-Work Asset',
    'Distribution and Buyer Path',
    'Risk Controls and Next Actions'
  ];
}

function calculateReadiness(article) {
  const titleScore = normalizeText(article.title).length >= 8 ? 20 : 8;
  const contentScore = article.wordCount >= MINIMUM_WORDS_FOR_PRODUCT ? 35 : Math.round((article.wordCount / MINIMUM_WORDS_FOR_PRODUCT) * 35);
  const topicScore = normalizeText(article.topic).length >= 3 ? 15 : 5;
  const structureScore = normalizeText(article.content).split(/[.!?]+/).filter(Boolean).length >= 5 ? 15 : 7;
  const riskScore = /guarantee|guaranteed|risk-free|instant profit/i.test(article.content) ? 0 : 15;
  return Math.max(0, Math.min(100, titleScore + contentScore + topicScore + structureScore + riskScore));
}

function buildOfferStack(article, readinessScore) {
  const baseTitle = sentenceCase(article.title);
  const reportPrice = readinessScore >= 80 ? 29 : 17;
  const ebookPrice = readinessScore >= 80 ? 19 : 9;

  return [
    {
      productType: 'downloadable_report',
      title: `${baseTitle}: Field-Ready Revenue Report`,
      suggestedPriceUsd: reportPrice,
      targetBuyer: 'small business owner, operator, or field-service lead',
      deliveryFormat: 'PDF report',
      minimumViableChannel: 'owned website intake page'
    },
    {
      productType: 'ebook',
      title: `${baseTitle}: Practical Playbook`,
      suggestedPriceUsd: ebookPrice,
      targetBuyer: 'solo operator or early-stage service business',
      deliveryFormat: 'PDF ebook',
      minimumViableChannel: 'Gumroad, Payhip, or direct Stripe link'
    },
    {
      productType: 'consulting_upsell',
      title: `${baseTitle}: Implementation Review`,
      suggestedPriceUsd: 150,
      targetBuyer: 'buyer who needs setup help after download',
      deliveryFormat: 'paid review call or written implementation audit',
      minimumViableChannel: 'Already Here LLC intake form'
    }
  ];
}

function buildRiskControls(article) {
  const flags = [];
  const text = normalizeText(article.content);

  if (article.wordCount < MINIMUM_WORDS_FOR_PRODUCT) {
    flags.push('Content is too short for a standalone paid product without expansion.');
  }
  if (/guarantee|guaranteed|risk-free|instant profit/i.test(text)) {
    flags.push('Remove income or outcome guarantees before publishing.');
  }
  if (!/cost|risk|step|process|checklist|buyer|customer/i.test(text)) {
    flags.push('Add practical buyer-focused sections before selling.');
  }

  return flags.length ? flags : ['No immediate publishing blockers detected from the supplied article text.'];
}

export async function runMonetizationTest(articleInput) {
  const article = {
    title: sentenceCase(articleInput?.title),
    topic: sentenceCase(articleInput?.topic || 'General'),
    content: normalizeText(articleInput?.content),
    wordCount: Number(articleInput?.wordCount || 0)
  };

  if (!article.wordCount && article.content) {
    article.wordCount = article.content.split(/\s+/).filter(Boolean).length;
  }

  const readinessScore = calculateReadiness(article);
  const offerStack = buildOfferStack(article, readinessScore);
  const estimatedMonthlyUnits = readinessScore >= 80 ? 25 : readinessScore >= 60 ? 10 : 3;
  const projectedGrossUsd = offerStack
    .filter((offer) => offer.productType !== 'consulting_upsell')
    .reduce((sum, offer) => sum + offer.suggestedPriceUsd * estimatedMonthlyUnits, 0);

  return {
    success: true,
    mode: 'local-proof',
    article: {
      title: article.title,
      topic: article.topic,
      wordCount: article.wordCount,
      readingMinutes: estimateReadingMinutes(article.wordCount)
    },
    readiness: {
      score: readinessScore,
      grade: readinessScore >= 80 ? 'A' : readinessScore >= 65 ? 'B' : readinessScore >= 50 ? 'C' : 'Needs Work',
      publishableNow: readinessScore >= 65
    },
    ebookBlueprint: {
      title: `${article.title}: Practical Playbook`,
      estimatedPages: estimatePageCount(article.wordCount) + 8,
      chapters: buildChapters(article)
    },
    podReportBlueprint: {
      title: `${article.title}: Print-on-Demand Report`,
      estimatedPages: estimatePageCount(article.wordCount) + 12,
      sections: ['Cover', 'Executive Summary', 'Action Checklist', 'Implementation Notes', 'Closeout Page']
    },
    offerStack,
    revenueModel: {
      estimatedMonthlyUnits,
      projectedGrossUsd,
      assumptions: [
        'Direct traffic or warm audience required.',
        'No paid ads required for proof mode.',
        'Final revenue depends on offer quality, distribution, and buyer fit.'
      ]
    },
    riskControls: buildRiskControls(article),
    nextActions: [
      'Expand weak sections until the report is independently useful.',
      'Create PDF export and one-page checkout description.',
      'Publish only after Stephen approval and compliance review.',
      'Track every click, lead, sale, refund, and support request in the revenue spine.'
    ]
  };
}
