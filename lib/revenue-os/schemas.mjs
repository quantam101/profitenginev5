import { z } from 'zod';

export const ticketUnitSchema = z.enum(['dispatch', 'project', 'month', 'route', 'location']);

export const estimatedTicketValueSchema = z.object({
  minimum: z.number().min(0),
  maximum: z.number().min(0),
  unit: ticketUnitSchema,
});

export const revenuePlayStatusSchema = z.enum([
  'SEED_READY',
  'RESEARCH',
  'ACTIVE',
  'PAUSED',
  'ARCHIVED',
]);

export const scoreInputsSchema = z.object({
  dailyRevenuePotential: z.number().min(0).max(20),
  speedToFirstCash: z.number().min(0).max(20),
  repeatability: z.number().min(0).max(20),
  routeStacking: z.number().min(0).max(20),
  lowStartupCost: z.number().min(0).max(20),
  lowLiability: z.number().min(0).max(20),
  recurringRetainer: z.number().min(0).max(20),
  databaseAiValue: z.number().min(0).max(20),
});

export const revenuePlaySchema = z.object({
  recordId: z.string().min(1),
  source: z.string().min(1),
  lane: z.string().min(1),
  revenuePlayName: z.string().min(1),
  buyerType: z.string().min(1),
  exampleTargetCompanyOrMarket: z.string().min(1),
  contactPath: z.string().min(1),
  location: z.string().min(1),
  painSolved: z.string().min(1),
  estimatedTicketValue: estimatedTicketValueSchema,
  costRequired: z.number().min(0),
  profitPotential: z.number().min(0).max(1),
  timeToRevenueDays: z.number().min(0),
  recurringPotential: z.number().min(0).max(1),
  stackingFit: z.number().min(0).max(1),
  liabilityScore: z.number().min(0).max(1),
  databaseValueScore: z.number().min(0).max(1),
  startupRequirements: z.array(z.string()),
  first10TargetStrategy: z.string().min(1),
  riskFlags: z.array(z.string()),
  recommendedAction: z.string().min(1),
  status: revenuePlayStatusSchema,
  nextFollowUpDate: z.date().optional(),
  notes: z.string().min(1),
  scoreInputs: scoreInputsSchema.optional(),
  opportunityScore: z.number().optional(),
  overallScore: z.number().min(0).max(100),
  createdAt: z.date(),
  updatedAt: z.date(),
});

const numericRangeRegex = /\$(\d[\d,]*)\s*(?:-\s*\$?([\d,]+))?/i;
const singleValueRegex = /\$([\d,]+)/;

export function parseEstimatedTicketValue(raw) {
  const str = String(raw || '');
  const rangeMatch = str.match(numericRangeRegex);
  let minimum = 0;
  let maximum = 0;
  if (rangeMatch) {
    minimum = Number(rangeMatch[1].replace(/,/g, '')) || 0;
    maximum = rangeMatch[2]
      ? Number(rangeMatch[2].replace(/,/g, '')) || minimum
      : minimum;
  } else {
    const singleMatch = str.match(singleValueRegex);
    if (singleMatch) {
      minimum = maximum = Number(singleMatch[1].replace(/,/g, '')) || 0;
    }
  }
  if (maximum < minimum) [minimum, maximum] = [maximum, minimum];

  const lower = str.toLowerCase();
  let unit = 'project';
  if (lower.includes('month') || lower.includes('/mo')) unit = 'month';
  else if (lower.includes('route') || lower.includes('mile')) unit = 'route';
  else if (lower.includes('location') || lower.includes('site')) unit = 'location';
  else if (lower.includes('dispatch') || lower.includes('ticket')) unit = 'dispatch';

  return { minimum, maximum, unit };
}

export function parseCostRequired(raw) {
  const str = String(raw || '');
  if (/\$0\b/.test(str) || /\b0\s+new spend/.test(str) || /\$0\s+to evaluate/.test(str)) {
    return 0;
  }
  const match = str.match(/\$([\d,]+(?:\.\d{1,2})?)/);
  return match ? Number(match[1].replace(/,/g, '')) : 0;
}

export function parseTimeToRevenue(raw) {
  const str = String(raw || '').toLowerCase();
  const range = str.match(/(\d+)\s*(?:-\s*(\d+))?\s*(day|days|week|weeks|month|months)/);
  if (range) {
    const min = Number(range[1]);
    const max = range[2] ? Number(range[2]) : min;
    let avg = (min + max) / 2;
    if (range[3].startsWith('week')) avg *= 7;
    else if (range[3].startsWith('month')) avg *= 30;
    return Math.round(avg);
  }
  if (str.includes('fast') || str.includes('immediate')) return 7;
  if (str.includes('medium')) return 30;
  if (str.includes('slow')) return 90;
  return 30;
}

const potentialMap = {
  'very high': 0.95,
  high: 0.8,
  medium: 0.5,
  low: 0.25,
  'very low': 0.1,
};

export function parsePotential(raw) {
  const str = String(raw || '').toLowerCase().trim();
  for (const [key, value] of Object.entries(potentialMap)) {
    if (str.includes(key)) return value;
  }
  return 0.5;
}

const fitMap = {
  excellent: 0.95,
  good: 0.75,
  fair: 0.5,
  poor: 0.25,
};

export function parseFit(raw) {
  const str = String(raw || '').toLowerCase().trim();
  for (const [key, value] of Object.entries(fitMap)) {
    if (str.includes(key)) return value;
  }
  return 0.5;
}

export function splitSemicolonOrComma(raw) {
  const str = String(raw || '');
  if (str.includes(';')) return str.split(';').map((s) => s.trim()).filter(Boolean);
  return str.split(',').map((s) => s.trim()).filter(Boolean);
}

export function normalizeSeedRecord(record) {
  const scoreInputs = record.score_inputs
    ? {
        dailyRevenuePotential: Number(record.score_inputs.daily_revenue_potential) || 0,
        speedToFirstCash: Number(record.score_inputs.speed_to_first_cash) || 0,
        repeatability: Number(record.score_inputs.repeatability) || 0,
        routeStacking: Number(record.score_inputs.route_stacking) || 0,
        lowStartupCost: Number(record.score_inputs.low_startup_cost) || 0,
        lowLiability: Number(record.score_inputs.low_liability) || 0,
        recurringRetainer: Number(record.score_inputs.recurring_retainer) || 0,
        databaseAiValue: Number(record.score_inputs.database_ai_value) || 0,
      }
    : undefined;

  return {
    recordId: record.id,
    source: record.source,
    lane: record.lane,
    revenuePlayName: record.revenue_play_name,
    buyerType: record.buyer_type,
    exampleTargetCompanyOrMarket: record.example_target_company_or_market,
    contactPath: record.contact_path,
    location: record.location,
    painSolved: record.pain_solved,
    estimatedTicketValue: parseEstimatedTicketValue(record.estimated_ticket_value),
    costRequired: parseCostRequired(record.cost_required),
    profitPotential: parsePotential(record.profit_potential),
    timeToRevenueDays: parseTimeToRevenue(record.time_to_revenue),
    recurringPotential: parsePotential(record.recurring_potential),
    stackingFit: parseFit(record.stacking_fit),
    liabilityScore: scoreInputs ? scoreInputs.lowLiability / 20 : 0.5,
    databaseValueScore: scoreInputs ? scoreInputs.databaseAiValue / 20 : 0.5,
    startupRequirements: splitSemicolonOrComma(record.startup_requirements),
    first10TargetStrategy: record.first_10_target_strategy,
    riskFlags: splitSemicolonOrComma(record.risk_flags),
    recommendedAction: record.recommended_action,
    status: revenuePlayStatusSchema.safeParse(record.status).data || 'SEED_READY',
    nextFollowUpDate: record.next_follow_up_date ? new Date(record.next_follow_up_date) : undefined,
    notes: record.notes,
    scoreInputs,
    opportunityScore: Number(record.opportunity_score) || 0,
  };
}
