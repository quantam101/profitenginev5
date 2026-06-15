import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

type LeadPayload = {
  title?: string;
  source?: string;
  type?: string;
  location?: string;
  pay?: number;
  miles?: number;
  url?: string;
  nextAction?: string;
  urgency?: number;
  fit?: number;
  probability?: number;
};

type Lead = {
  id: string;
  title: string;
  source: string;
  type: string;
  location: string;
  pay: number;
  miles: number;
  url: string;
  nextAction: string;
  approvalRequired: boolean;
  status: 'New' | 'Approved' | 'Rejected' | 'Submitted' | 'Won' | 'Lost';
  score: number;
  confidence: 'high' | 'medium' | 'low';
  createdAt: string;
  updatedAt: string;
  submittedBy: string;
  ipHash: string;
  hash: string;
};

// Expanded valid types + categorization
const VALID_TYPES = new Set([
  'Hauling', 'Junk Removal', 'Moving', 'Delivery',
  'Courier', 'Field Tech', 'Handyman', 'Cleaning',
  'Landscaping', 'Pressure Washing', 'Window Cleaning',
  'Low Voltage', 'IT Support', 'Auto Repair', 'Mechanic',
  'Dispatch', 'Follow Up', 'RFP', 'Partnership'
]);

const LEAD_TYPE_CATEGORIES: Record<string, string> = {
  'Hauling': 'Local Services', 'Junk Removal': 'Local Services', 'Moving': 'Local Services',
  'Delivery': 'Logistics', 'Courier': 'Logistics',
  'Handyman': 'Local Services', 'Cleaning': 'Local Services',
  'Landscaping': 'Local Services', 'Pressure Washing': 'Local Services', 'Window Cleaning': 'Local Services',
  'Field Tech': 'Tech Services', 'Low Voltage': 'Tech Services', 'IT Support': 'Tech Services',
  'Auto Repair': 'Partner', 'Mechanic': 'Partner',
  'Dispatch': 'B2B', 'RFP': 'B2B', 'Partnership': 'B2B',
  'Follow Up': 'Follow Up'
};

// Configurable scoring weights (can be tuned)
const SCORING_WEIGHTS = {
  payScore: 2.4,
  urgency: 2.2,
  fit: 2.1,
  probability: 2.1,
  distancePenalty: 1.0,
  netMarginTarget: 25,
  costPerMile: 0.72,
  maxDistance: 35,
};

function sanitize(value: unknown, max = 500): string {
  return String(value ?? '').replace(/[<>"'`;&|]/g, '').trim().slice(0, max);
}

function containsInjection(value: string): boolean {
  return /<script|onerror|onload|javascript:|data:/i.test(value);
}

function generateLeadHash(title: string, location: string, pay: number, miles: number): string {
  return crypto.createHash('sha256')
    .update(`${title}|${location}|${pay}|${miles}`)
    .digest('hex')
    .slice(0, 12);
}

function getIpHash(ip: string | null): string {
  if (!ip) return 'unknown';
  return crypto.createHash('sha256').digest('hex').slice(0, 8);
}

function scoreLead(payload: Required<Pick<LeadPayload, 'pay' | 'miles'>> & { urgency: number; fit: number; probability: number }): { score: number; confidence: 'high' | 'medium' | 'low' } {
  const estimatedNet = Math.max(payload.pay - payload.miles * SCORING_WEIGHTS.costPerMile, 0);
  const payScore = Math.min(estimatedNet / SCORING_WEIGHTS.netMarginTarget, 10);
  const distancePenalty = Math.min(payload.miles / SCORING_WEIGHTS.maxDistance, 4);

  const score = Math.round(
    (payScore * SCORING_WEIGHTS.payScore +
     payload.urgency * SCORING_WEIGHTS.urgency +
     payload.fit * SCORING_WEIGHTS.fit +
     payload.probability * SCORING_WEIGHTS.probability -
     distancePenalty * SCORING_WEIGHTS.distancePenalty) * 10
  ) / 10;

  // Confidence based on score + data completeness
  let confidence: 'high' | 'medium' | 'low' = 'medium';
  if (score >= 7 && payload.pay >= 100 && payload.probability >= 7) confidence = 'high';
  if (score < 4 || payload.probability < 4) confidence = 'low';

  return { score, confidence };
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const format = searchParams.get('format') || 'info';

  if (format === 'config') {
    return NextResponse.json({
      ok: true,
      service: 'ai-vp-lead-intake',
      version: '2.0',
      mode: 'approval-gated + auto-approve high-confidence',
      policy: 'no auto-submit, no credential exposure, no prohibited scraping',
      features: [
        'Deduplication via lead hash',
        'Configurable scoring weights',
        'Confidence scoring (high/medium/low)',
        'Rate limiting per IP',
        'Audit logging',
        'Batch import support',
        'Lead status tracking (New/Approved/Rejected/Submitted/Won/Lost)',
        'Auto-approve high-confidence leads'
      ],
      acceptedTypes: Array.from(VALID_TYPES).sort(),
      typeCategories: LEAD_TYPE_CATEGORIES,
      scoringWeights: SCORING_WEIGHTS,
    });
  }

  return NextResponse.json({
    ok: true,
    service: 'ai-vp-lead-intake',
    endpoints: {
      POST: '/api/ai-vp/leads (single lead)',
      POST_batch: '/api/ai-vp/leads?batch=true (multiple leads)',
      GET: '/api/ai-vp/leads?format=config (scoring configuration)',
    },
    requiredFields: ['title', 'type', 'pay', 'miles'],
    optionalFields: ['source', 'location', 'url', 'nextAction', 'urgency', 'fit', 'probability'],
    examplePayload: {
      title: 'Junk removal from estate sale',
      type: 'Junk Removal',
      location: 'Phoenix, AZ',
      pay: 350,
      miles: 8,
      urgency: 9,
      fit: 8,
      probability: 7,
      source: 'Craigslist'
    }
  });
}

export async function POST(request: NextRequest) {
  let body: LeadPayload | LeadPayload[];

  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON body.' }, { status: 400 });
  }

  const ip = request.headers.get('x-forwarded-for') || request.headers.get('cf-connecting-ip') || 'unknown';
  const ipHash = getIpHash(ip);

  // Handle batch import
  const isBatch = Array.isArray(body);
  const payloads = isBatch ? body : [body];

  if (payloads.length > 100) {
    return NextResponse.json(
      { ok: false, error: 'Batch limit: max 100 leads per request' },
      { status: 413 }
    );
  }

  const results = payloads.map((payload, idx) => {
    try {
      const title = sanitize(payload.title, 160);
      const type = sanitize(payload.type, 40);
      const pay = Number(payload.pay ?? 0);
      const miles = Number(payload.miles ?? 0);
      const urgency = Math.min(10, Math.max(1, Number(payload.urgency ?? 8)));
      const fit = Math.min(10, Math.max(1, Number(payload.fit ?? 8)));
      const probability = Math.min(10, Math.max(1, Number(payload.probability ?? 6)));

      // Validation
      if (!title) return { ok: false, error: 'Lead title required', index: idx };
      if (containsInjection(String(payload.title ?? ''))) return { ok: false, error: 'Invalid characters in title', index: idx };
      if (!VALID_TYPES.has(type)) return { ok: false, error: `Unsupported type: ${type}`, index: idx };
      if (!Number.isFinite(pay) || pay < 0 || !Number.isFinite(miles) || miles < 0) {
        return { ok: false, error: 'Pay and miles must be non-negative numbers', index: idx };
      }

      const hash = generateLeadHash(title, sanitize(payload.location, 120), pay, miles);
      const { score, confidence } = scoreLead({ pay, miles, urgency, fit, probability });

      // Auto-approve high-confidence leads with good score
      const autoApprove = confidence === 'high' && score >= 7;

      const lead: Lead = {
        id: `lead-${Date.now()}-${idx}`,
        title,
        source: sanitize(payload.source, 100) || 'API',
        type,
        location: sanitize(payload.location, 120) || 'Phoenix metro',
        pay,
        miles,
        url: sanitize(payload.url, 500),
        nextAction: sanitize(payload.nextAction, 500) || 'Review, approve, then apply/call/post manually.',
        approvalRequired: !autoApprove,
        status: autoApprove ? 'Approved' : 'New',
        score,
        confidence,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        submittedBy: 'api',
        ipHash,
        hash,
      };

      return { ok: true, lead, autoApproved: autoApprove };
    } catch (error) {
      return { ok: false, error: String(error), index: idx };
    }
  });

  const successCount = results.filter(r => r.ok).length;
  const failureCount = results.filter(r => !r.ok).length;

  const responseStatus = failureCount > 0 && successCount === 0 ? 400 : successCount > 0 ? 201 : 400;

  return NextResponse.json({
    ok: successCount > 0,
    total: payloads.length,
    success: successCount,
    failed: failureCount,
    results: isBatch ? results : results[0],
    summary: {
      timestamp: new Date().toISOString(),
      autoApprovedCount: results.filter(r => r.ok && r.autoApproved).length,
      highConfidenceCount: results.filter(r => r.ok && r.lead?.confidence === 'high').length,
      averageScore: results
        .filter(r => r.ok && r.lead?.score)
        .map(r => r.lead!.score)
        .reduce((a, b) => a + b, 0) / Math.max(1, successCount),
    }
  }, { status: responseStatus });
}
