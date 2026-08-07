import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type ImportBody = { dryRun?: boolean };
type SeedRecord = { id: string; [key: string]: unknown };
type SeedFile = {
  schema_version: string;
  dataset: string;
  record_count: number;
  generated_at: string;
  records: SeedRecord[];
};

const seedFiles = [
  'revenue-plays.seed.json',
  'revenue-plays.seed.v1.1.json',
  'revenue-plays.seed.v1.2.json',
  'revenue-plays.seed.v1.3.json',
  'revenue-plays.seed.v1.4.json',
  'revenue-plays.seed.v1.5.json',
  'revenue-plays.seed.v1.6.json',
];

export async function POST(request: Request) {
  const configuredSecret = process.env.REVENUE_OS_IMPORT_SECRET;
  const suppliedSecret = request.headers.get('x-revenue-os-import-secret');

  if (!configuredSecret || suppliedSecret !== configuredSecret) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const uri = process.env.MONGODB_URI;
  const dbName = process.env.MONGODB_DB || 'profitenginev5';
  const collectionName = process.env.REVENUE_OS_COLLECTION || 'revenue_plays';

  if (!uri) {
    return NextResponse.json({ error: 'MONGODB_URI is not configured' }, { status: 503 });
  }

  let body: ImportBody = {};
  try {
    body = (await request.json()) as ImportBody;
  } catch {
    body = {};
  }

  const datasets: SeedFile[] = [];
  for (const fileName of seedFiles) {
    const seedPath = path.join(process.cwd(), 'data/revenue-os', fileName);
    const seed = JSON.parse(await readFile(seedPath, 'utf8')) as SeedFile;
    if (!Array.isArray(seed.records) || seed.records.length !== seed.record_count) {
      return NextResponse.json({ error: `Invalid seed record count: ${fileName}` }, { status: 422 });
    }
    datasets.push(seed);
  }

  const ids = new Set<string>();
  const records: Array<SeedRecord & { seed_schema_version: string; seed_dataset: string; seed_generated_at: Date }> = [];
  for (const dataset of datasets) {
    for (const record of dataset.records) {
      if (!record.id || ids.has(record.id)) {
        return NextResponse.json({ error: `Invalid or duplicate record id: ${record.id}` }, { status: 422 });
      }
      ids.add(record.id);
      records.push({
        ...record,
        seed_schema_version: dataset.schema_version,
        seed_dataset: dataset.dataset,
        seed_generated_at: new Date(dataset.generated_at),
      });
    }
  }

  if (records.length !== 95) {
    return NextResponse.json({ error: `Expected 95 records, found ${records.length}` }, { status: 422 });
  }

  for (let number = 1; number <= 95; number += 1) {
    const expectedId = `RP-${String(number).padStart(3, '0')}`;
    if (!ids.has(expectedId)) {
      return NextResponse.json({ error: `Missing sequential record: ${expectedId}` }, { status: 422 });
    }
  }

  const client = new MongoClient(uri, { maxPoolSize: 5, serverSelectionTimeoutMS: 10_000 });

  try {
    await client.connect();
    const db = client.db(dbName);
    const collection = db.collection(collectionName);

    await collection.createIndex({ id: 1 }, { unique: true, name: 'revenue_play_id_unique' });
    await collection.createIndex({ lane: 1, opportunity_score: -1 }, { name: 'revenue_play_lane_score' });
    await collection.createIndex({ status: 1, next_follow_up_date: 1 }, { name: 'revenue_play_status_followup' });
    await collection.createIndex(
      { revenue_play_name: 'text', pain_solved: 'text', notes: 'text' },
      { name: 'revenue_play_text_search' },
    );

    const existing = await collection.countDocuments({ id: { $in: [...ids] } });
    if (body.dryRun) {
      return NextResponse.json({
        mode: 'dry-run',
        database: dbName,
        collection: collectionName,
        datasets: datasets.length,
        seedRecords: records.length,
        matchingExistingRecords: existing,
        potentialNewRecords: records.length - existing,
        changesApplied: false,
      });
    }

    const now = new Date();
    const result = await collection.bulkWrite(
      records.map((record) => ({
        updateOne: {
          filter: { id: record.id },
          update: {
            $set: { ...record, seed_updated_at: now, updated_at: now },
            $setOnInsert: {
              created_at: now,
              source_type: 'version_controlled_seed',
              manual_overrides: {},
            },
          },
          upsert: true,
        },
      })),
      { ordered: true },
    );

    await db.collection('revenue_os_audit_events').insertOne({
      event_type: 'REVENUE_OS_SEED_IMPORT',
      datasets: datasets.map(({ dataset, schema_version, record_count }) => ({ dataset, schema_version, record_count })),
      record_count: records.length,
      matched_count: result.matchedCount,
      modified_count: result.modifiedCount,
      upserted_count: result.upsertedCount,
      imported_at: now,
      actor: 'api:revenue-os-admin-import',
    });

    return NextResponse.json({
      mode: 'write',
      database: dbName,
      collection: collectionName,
      datasets: datasets.length,
      seedRecords: records.length,
      matchedCount: result.matchedCount,
      modifiedCount: result.modifiedCount,
      upsertedCount: result.upsertedCount,
    });
  } catch (error) {
    console.error('Revenue OS seed import failed', error);
    return NextResponse.json({ error: 'Seed import failed' }, { status: 500 });
  } finally {
    await client.close();
  }
}
