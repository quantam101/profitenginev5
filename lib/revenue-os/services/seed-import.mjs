import fs from 'node:fs';
import path from 'node:path';
import { getCollection } from '../../mongodb.mjs';
import { normalizeSeedRecord } from '../schemas.mjs';
import { calculateOverallScore } from '../scoring.mjs';
import { ensureIndexes } from '../repositories/revenue-play.repository.mjs';

const SEED_PATH = path.resolve('data/revenue-os/revenue-plays.seed.json');

function stableStringify(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (value instanceof Date) return JSON.stringify(value.toISOString());
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  const keys = Object.keys(value).filter((k) => value[k] !== undefined).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(value[k])}`).join(',')}}`;
}

const REQUIRED_FIELDS = [
  'id',
  'source',
  'lane',
  'revenue_play_name',
  'buyer_type',
  'example_target_company_or_market',
  'contact_path',
  'location',
  'pain_solved',
  'estimated_ticket_value',
  'cost_required',
  'profit_potential',
  'time_to_revenue',
  'recurring_potential',
  'stacking_fit',
  'startup_requirements',
  'first_10_target_strategy',
  'risk_flags',
  'recommended_action',
  'status',
  'next_follow_up_date',
  'notes',
  'score_inputs',
  'opportunity_score',
];

export async function importRevenueOsSeed(options = {}) {
  const {
    seedPath = SEED_PATH,
    dryRun = false,
    actor = 'system',
    source = 'revenue-os-seed-importer',
  } = options;

  const summary = {
    total: 0,
    inserted: 0,
    updated: 0,
    unchanged: 0,
    errors: [],
    dryRun,
    seedPath,
  };

  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(seedPath, 'utf8'));
  } catch (err) {
    summary.errors.push(`Failed to read/parse seed: ${err.message}`);
    return summary;
  }

  if (parsed.record_count !== 65) {
    summary.errors.push(`record_count must be 65, got ${parsed.record_count}`);
  }
  if (!Array.isArray(parsed.records)) {
    summary.errors.push('records must be an array');
    return summary;
  }

  summary.total = parsed.records.length;

  const seen = new Set();
  const normalized = [];

  for (const [index, raw] of parsed.records.entries()) {
    const missing = REQUIRED_FIELDS.filter(
      (field) => raw[field] === undefined || raw[field] === null || raw[field] === ''
    );
    if (missing.length) {
      summary.errors.push(`records[${index}] missing fields: ${missing.join(', ')}`);
      continue;
    }

    const scoreSum = Object.values(raw.score_inputs ?? {}).reduce(
      (sum, value) => sum + Number(value),
      0
    );
    if (scoreSum !== Number(raw.opportunity_score)) {
      summary.errors.push(
        `${raw.id} opportunity_score ${raw.opportunity_score} != computed ${scoreSum}`
      );
    }

    if (seen.has(raw.id)) {
      summary.errors.push(`duplicate id ${raw.id}`);
      continue;
    }
    seen.add(raw.id);

    try {
      const base = normalizeSeedRecord(raw);
      const overallScore = calculateOverallScore(base);
      normalized.push({ ...base, overallScore });
    } catch (err) {
      summary.errors.push(`records[${index}] normalization error: ${err.message}`);
    }
  }

  if (summary.errors.length) {
    return summary;
  }

  const revenueCollection = dryRun ? null : await getCollection('revenue_plays');
  const existingMap = dryRun ? new Map() : new Map();

  if (!dryRun) {
    const existing = await revenueCollection
      .find({ recordId: { $in: normalized.map((r) => r.recordId) } })
      .project({ _id: 0 })
      .toArray();
    for (const doc of existing) {
      existingMap.set(doc.recordId, doc);
    }
  }

  const now = new Date();
  for (const doc of normalized) {
    const fullDoc = { ...doc, updatedAt: now };
    const existing = existingMap.get(doc.recordId);
    if (existing) {
      const comparable = { ...existing };
      delete comparable.createdAt;
      delete comparable.updatedAt;
      const newComparable = { ...fullDoc };
      delete newComparable.updatedAt;
      if (stableStringify(comparable) === stableStringify(newComparable)) {
        summary.unchanged += 1;
        continue;
      }
      summary.updated += 1;
    } else {
      summary.inserted += 1;
    }

    if (!dryRun) {
      try {
        await revenueCollection.updateOne(
          { recordId: fullDoc.recordId },
          { $set: fullDoc, $setOnInsert: { createdAt: now } },
          { upsert: true }
        );
      } catch (err) {
        summary.errors.push(`upsert ${fullDoc.recordId} failed: ${err.message}`);
      }
    }
  }

  if (!dryRun) {
    try {
      await ensureIndexes();
    } catch (err) {
      summary.errors.push(`index creation failed: ${err.message}`);
    }
  }

  if (!dryRun) {
    try {
      const activityCollection = await getCollection('activities');
      await activityCollection.insertOne({
        entityType: 'revenue_plays',
        entityId: 'seed-import',
        actionType: 'SEED_IMPORT',
        actor,
        summary: `Imported ${summary.total} revenue play seed records: ${summary.inserted} inserted, ${summary.updated} updated, ${summary.unchanged} unchanged.`,
        metadata: { ...summary, source },
        createdAt: now,
      });
    } catch (err) {
      summary.errors.push(`activity log failed: ${err.message}`);
    }
  }

  return summary;
}
