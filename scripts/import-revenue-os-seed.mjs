import fs from 'node:fs/promises';
import process from 'node:process';
import { MongoClient } from 'mongodb';

const args = new Set(process.argv.slice(2));
const dryRun = args.has('--dry-run');
const seedPath = process.env.REVENUE_OS_SEED_PATH || 'data/revenue-os/revenue-plays.seed.json';
const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB || 'profitenginev5';
const collectionName = process.env.REVENUE_OS_COLLECTION || 'revenue_plays';

if (!uri) {
  console.error('MONGODB_URI is required. No database changes were made.');
  process.exit(1);
}

const raw = await fs.readFile(seedPath, 'utf8');
const seed = JSON.parse(raw);
if (!Array.isArray(seed.records) || seed.records.length !== seed.record_count) {
  throw new Error(`Seed record count mismatch: declared ${seed.record_count}, found ${seed.records?.length ?? 0}`);
}

const ids = new Set();
for (const record of seed.records) {
  if (!record.id) throw new Error('Every seed record requires id');
  if (ids.has(record.id)) throw new Error(`Duplicate seed id: ${record.id}`);
  ids.add(record.id);
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
  const operations = seed.records.map((record) => ({
    updateOne: {
      filter: { id: record.id },
      update: {
        $set: {
          ...record,
          seed_schema_version: seed.schema_version,
          seed_dataset: seed.dataset,
          seed_generated_at: new Date(seed.generated_at),
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
      seed_records: seed.records.length,
      matching_existing_records: existing,
      potential_new_records: seed.records.length - existing,
      changes_applied: false,
    }, null, 2));
    process.exitCode = 0;
  } else {
    const result = await collection.bulkWrite(operations, { ordered: true });
    await audit.insertOne({
      event_type: 'REVENUE_OS_SEED_IMPORT',
      dataset: seed.dataset,
      schema_version: seed.schema_version,
      record_count: seed.records.length,
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
      seed_records: seed.records.length,
      matched_count: result.matchedCount,
      modified_count: result.modifiedCount,
      upserted_count: result.upsertedCount,
      acknowledged: result.acknowledged,
    }, null, 2));
  }
} finally {
  await client.close();
}
