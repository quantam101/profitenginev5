import fs from 'node:fs/promises';
import process from 'node:process';
import { MongoClient } from 'mongodb';

const args = new Set(process.argv.slice(2));
const dryRun = args.has('--dry-run');
const seedPaths = (process.env.REVENUE_OS_SEED_PATHS || process.env.REVENUE_OS_SEED_PATH || 'data/revenue-os/revenue-plays.seed.json,data/revenue-os/revenue-plays.seed.v1.1.json,data/revenue-os/revenue-plays.seed.v1.2.json,data/revenue-os/revenue-plays.seed.v1.3.json')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);
const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB || 'profitenginev5';
const collectionName = process.env.REVENUE_OS_COLLECTION || 'revenue_plays';

if (!uri) {
  console.error('MONGODB_URI is required. No database changes were made.');
  process.exit(1);
}

const datasets = [];
for (const seedPath of seedPaths) {
  const raw = await fs.readFile(seedPath, 'utf8');
  const seed = JSON.parse(raw);
  if (!Array.isArray(seed.records) || seed.records.length !== seed.record_count) {
    throw new Error(`Seed record count mismatch in ${seedPath}: declared ${seed.record_count}, found ${seed.records?.length ?? 0}`);
  }
  datasets.push({ ...seed, seedPath });
}

const ids = new Set();
const records = [];
for (const dataset of datasets) {
  for (const record of dataset.records) {
    if (!record.id) throw new Error(`Every seed record requires id (${dataset.seedPath})`);
    if (ids.has(record.id)) throw new Error(`Duplicate seed id across datasets: ${record.id}`);
    ids.add(record.id);
    records.push({
      ...record,
      seed_schema_version: dataset.schema_version,
      seed_dataset: dataset.dataset,
      seed_generated_at: new Date(dataset.generated_at),
    });
  }
}

if (records.length !== 80) {
  throw new Error(`Expected 80 combined Revenue OS seed records, found ${records.length}`);
}

for (let number = 1; number <= 80; number += 1) {
  const expectedId = `RP-${String(number).padStart(3, '0')}`;
  if (!ids.has(expectedId)) throw new Error(`Missing sequential Revenue OS seed id: ${expectedId}`);
}

const client = new MongoClient(uri, { maxPoolSize: 5, serverSelectionTimeoutMS: 10000 });
await client.connect();

try {
  const db = client.db(dbName);
  const collection = db.collection(collectionName);
  const audit = db.collection('revenue_os_audit_events');

  await collection.createIndex({ id: 1 }, { unique: true, name: 'revenue_play_id_unique' });
  await collection.createIndex({ lane: 1, opportunity_score: -1 }, { name: 'revenue_play_lane_score' });
  await collection.createIndex({ status: 1, next_follow_up_date: 1 }, { name: 'revenue_play_status_followup' });
  await collection.createIndex(
    { revenue_play_name: 'text', pain_solved: 'text', notes: 'text' },
    { name: 'revenue_play_text_search' },
  );

  const now = new Date();
  const operations = records.map((record) => ({
    updateOne: {
      filter: { id: record.id },
      update: {
        $set: {
          ...record,
          seed_updated_at: now,
          updated_at: now,
        },
        $setOnInsert: {
          created_at: now,
          source_type: 'version_controlled_seed',
          manual_overrides: {},
        },
      },
      upsert: true,
    },
  }));

  if (dryRun) {
    const existing = await collection.countDocuments({ id: { $in: [...ids] } });
    console.log(JSON.stringify({
      mode: 'dry-run',
      database: dbName,
      collection: collectionName,
      datasets: datasets.map(({ dataset, schema_version, record_count, seedPath }) => ({ dataset, schema_version, record_count, seedPath })),
      seed_records: records.length,
      matching_existing_records: existing,
      potential_new_records: records.length - existing,
      changes_applied: false,
    }, null, 2));
    process.exitCode = 0;
  } else {
    const result = await collection.bulkWrite(operations, { ordered: true });
    await audit.insertOne({
      event_type: 'REVENUE_OS_SEED_IMPORT',
      datasets: datasets.map(({ dataset, schema_version, record_count, seedPath }) => ({ dataset, schema_version, record_count, seedPath })),
      record_count: records.length,
      matched_count: result.matchedCount,
      modified_count: result.modifiedCount,
      upserted_count: result.upsertedCount,
      imported_at: now,
      actor: process.env.REVENUE_OS_IMPORT_ACTOR || 'system:seed-importer',
    });

    console.log(JSON.stringify({
      mode: 'write',
      database: dbName,
      collection: collectionName,
      datasets: datasets.length,
      seed_records: records.length,
      matched_count: result.matchedCount,
      modified_count: result.modifiedCount,
      upserted_count: result.upsertedCount,
    }, null, 2));
  }
} finally {
  await client.close();
}
