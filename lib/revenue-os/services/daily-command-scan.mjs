import fs from 'node:fs';
import path from 'node:path';
import { normalizeSeedRecord } from '../schemas.mjs';
import { calculateOverallScore } from '../scoring.mjs';

export const EVENT_TYPE = 'revenue_opportunity.detected';
export const EVENT_SOURCE = 'profitenginev5.revenue-os';
export const DEFAULT_LIMIT = 10;
export const MAX_LIMIT = 50;
export const DEFAULT_MIN_SCORE = 50;

const INACTIVE_STAGES = ['Won', 'Lost', 'On Hold'];
const SCANNABLE_PLAY_STATUSES = ['SEED_READY', 'RESEARCH', 'ACTIVE'];
const MAX_TEXT = 500;

function text(value) {
  if (value === null || value === undefined) return undefined;
  const str = String(value).replace(/\s+/g, ' ').trim();
  if (!str) return undefined;
  return str.length > MAX_TEXT ? str.slice(0, MAX_TEXT - 1) + '…' : str;
}

function compact(obj) {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== ''));
}

function money(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return undefined;
  return '$' + Math.round(n).toLocaleString('en-US');
}

function positiveDays(value) {
  const n = Math.round(Number(value));
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

function clamp(value, min, max, fallback) {
  const n = Math.floor(Number(value));
  if (!Number.isFinite(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

export function gradeFromScore(score) {
  const s = Number(score) || 0;
  if (s >= 80) return 'A';
  if (s >= 65) return 'B';
  if (s >= 45) return 'C';
  return 'D';
}

export function gradeFromProbability(probability) {
  const p = Number(probability) || 0;
  if (p >= 0.6) return 'A';
  if (p >= 0.4) return 'B';
  if (p >= 0.2) return 'C';
  return 'D';
}

export function playPricingModel(play) {
  const ticket = play.estimatedTicketValue || {};
  const min = money(ticket.minimum);
  const max = money(ticket.maximum);
  if (!min && !max) return undefined;
  const range = min && max && min !== max ? min + '-' + max : min || max;
  if (ticket.unit === 'month') return range + '/month recurring';
  const base = range + ' per ' + (ticket.unit || 'project');
  return Number(play.recurringPotential) >= 0.7 ? base + '; recurring retainer potential' : base;
}

export function playScore(play) {
  const stored = Number(play.overallScore);
  if (Number.isFinite(stored) && stored > 0) return stored;
  return calculateOverallScore(play);
}

export function revenuePlayToEvent(play) {
  const externalId = 'revenue-os:play:' + play.recordId;
  return {
    event_type: EVENT_TYPE,
    source: EVENT_SOURCE,
    idempotency_key: externalId,
    data: compact({
      company: text(play.exampleTargetCompanyOrMarket) || text(play.buyerType) || text(play.revenuePlayName),
      niche: text(play.lane),
      location: text(play.location),
      pain_signal: text(play.painSolved),
      recommended_offer: text(play.revenuePlayName),
      pricing_model: playPricingModel(play),
      grade: gradeFromScore(playScore(play)),
      expected_speed_to_revenue_days: positiveDays(play.timeToRevenueDays),
      attribution_requirements: text(play.source),
      outreach_draft: text(play.recommendedAction),
      external_id: externalId,
    }),
  };
}

function companyLocation(company) {
  const loc = Array.isArray(company?.locations) ? company.locations[0] : undefined;
  if (!loc) return undefined;
  return text([loc.city, loc.state].filter(Boolean).join(', '));
}

function opportunityPricingModel(opp) {
  const monthly = money(opp.recurringMonthlyValue);
  const total = money(opp.estimatedValue);
  if (monthly && total) return monthly + '/month recurring; ' + total + ' estimated value';
  if (monthly) return monthly + '/month recurring';
  if (total) return total + ' estimated value';
  return undefined;
}

export function pipelineOpportunityToEvent(opp, company, play) {
  const externalId = 'revenue-os:opportunity:' + String(opp._id);
  return {
    event_type: EVENT_TYPE,
    source: EVENT_SOURCE,
    idempotency_key: externalId,
    data: compact({
      company: text(company?.displayName) || text(company?.legalName) || text(opp.title),
      niche: text(play?.lane) || text(company?.industry),
      location: companyLocation(company) || text(play?.location),
      source_url: company?.website && /^https?:\/\//i.test(company.website) ? company.website : undefined,
      pain_signal: text(play?.painSolved),
      recommended_offer: text(play?.revenuePlayName) || text(opp.title),
      pricing_model: opportunityPricingModel(opp),
      grade: gradeFromProbability(opp.probability),
      expected_speed_to_revenue_days: positiveDays(play?.timeToRevenueDays),
      attribution_requirements: 'Revenue OS pipeline opportunity (stage: ' + opp.stage + ')',
      outreach_draft: text(opp.nextAction),
      external_id: externalId,
    }),
  };
}

export function loadSeedRevenuePlays(seedPath = path.join(process.cwd(), 'data', 'revenue-os', 'revenue-plays.seed.json')) {
  const raw = JSON.parse(fs.readFileSync(seedPath, 'utf8'));
  const records = Array.isArray(raw) ? raw : raw.records;
  if (!Array.isArray(records)) throw new Error('Revenue OS seed catalog has no records array');
  return records.map((record) => {
    const play = normalizeSeedRecord(record);
    return { ...play, overallScore: calculateOverallScore(play) };
  });
}

export function rankRevenuePlays(plays, { minScore = DEFAULT_MIN_SCORE, limit = DEFAULT_LIMIT } = {}) {
  return plays
    .filter((play) => play && play.recordId && SCANNABLE_PLAY_STATUSES.includes(play.status || 'SEED_READY'))
    .map((play) => ({ play, score: playScore(play) }))
    .filter(({ score }) => score >= minScore)
    .sort(
      (a, b) =>
        b.score - a.score ||
        (Number(b.play.opportunityScore) || 0) - (Number(a.play.opportunityScore) || 0) ||
        String(a.play.recordId).localeCompare(String(b.play.recordId)),
    )
    .slice(0, limit)
    .map(({ play }) => play);
}

export function createMongoScanStore(getCollection) {
  return {
    async activePipelineOpportunities(limit) {
      const col = await getCollection('opportunities');
      return col
        .find({ stage: { $nin: INACTIVE_STAGES } })
        .sort({ weightedValue: -1, updatedAt: -1 })
        .limit(limit)
        .toArray();
    },
    async companiesByIds(ids) {
      if (!ids.length) return [];
      return (await getCollection('companies')).find({ _id: { $in: ids } }).toArray();
    },
    async revenuePlaysByIds(ids) {
      if (!ids.length) return [];
      return (await getCollection('revenue_plays')).find({ _id: { $in: ids } }).toArray();
    },
    async scannableRevenuePlays() {
      return (await getCollection('revenue_plays'))
        .find({ status: { $in: SCANNABLE_PLAY_STATUSES } })
        .toArray();
    },
  };
}

function byId(docs) {
  return new Map(docs.map((doc) => [String(doc._id), doc]));
}

export async function runDailyCommandScan(options = {}) {
  const limit = clamp(options.limit, 1, MAX_LIMIT, DEFAULT_LIMIT);
  const minScore = clamp(options.minScore, 0, 100, DEFAULT_MIN_SCORE);
  const store = options.store || null;
  const loadSeed = options.loadSeed || loadSeedRevenuePlays;
  const warnings = [];
  const events = [];
  let pipelineCount = 0;
  let playSource = 'seed_catalog';
  let plays = [];

  if (store) {
    try {
      const opportunities = await store.activePipelineOpportunities(limit);
      const companies = byId(await store.companiesByIds([...new Set(opportunities.map((o) => o.companyId).filter(Boolean))]));
      const pipelinePlays = byId(await store.revenuePlaysByIds([...new Set(opportunities.map((o) => o.revenuePlayId).filter(Boolean))]));
      for (const opp of opportunities) {
        events.push(pipelineOpportunityToEvent(opp, companies.get(String(opp.companyId)), pipelinePlays.get(String(opp.revenuePlayId))));
      }
      pipelineCount = opportunities.length;
      plays = await store.scannableRevenuePlays();
      if (plays.length) playSource = 'mongodb';
    } catch (error) {
      warnings.push('Revenue OS store unavailable: ' + (error instanceof Error ? error.message : String(error)));
      plays = [];
    }
  } else {
    warnings.push('Revenue OS store not configured; using committed revenue play catalog only');
  }

  if (!plays.length) {
    plays = loadSeed();
    playSource = 'seed_catalog';
  }

  const remaining = Math.max(0, limit - events.length);
  const ranked = rankRevenuePlays(plays, { minScore, limit: remaining });
  for (const play of ranked) events.push(revenuePlayToEvent(play));

  return {
    ok: true,
    status: 'completed',
    scanned_at: new Date().toISOString(),
    limit,
    min_score: minScore,
    sources: {
      pipeline_opportunities: pipelineCount,
      revenue_plays_considered: plays.length,
      revenue_plays_emitted: ranked.length,
      revenue_play_source: playSource,
    },
    warnings,
    event_count: events.length,
    events,
  };
}
