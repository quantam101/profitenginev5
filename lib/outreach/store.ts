import { MongoClient, type Collection } from 'mongodb';
import type { OutreachMessage } from './types';

const databaseName = process.env.OUTREACH_MONGODB_DATABASE ?? 'profitengine';
const collectionName = process.env.OUTREACH_MONGODB_COLLECTION ?? 'outreach_messages';

let clientPromise: Promise<MongoClient> | undefined;

function getClient() {
  const uri = process.env.MONGODB_URI;
  if (!uri) throw new Error('MONGODB_URI is not configured');
  clientPromise ??= new MongoClient(uri, { maxPoolSize: 10 }).connect();
  return clientPromise;
}

async function collection(): Promise<Collection<OutreachMessage>> {
  const client = await getClient();
  const target = client.db(databaseName).collection<OutreachMessage>(collectionName);
  await target.createIndex({ id: 1 }, { unique: true });
  await target.createIndex({ status: 1, createdAt: -1 });
  return target;
}

export async function insertOutreach(message: OutreachMessage) {
  await (await collection()).insertOne(message);
  return message;
}

export async function getOutreach(id: string) {
  return (await collection()).findOne({ id }, { projection: { _id: 0 } });
}

export async function listOutreach(limit = 50) {
  return (await collection())
    .find({}, { projection: { _id: 0 } })
    .sort({ createdAt: -1 })
    .limit(Math.min(Math.max(limit, 1), 200))
    .toArray();
}

export async function updateOutreach(id: string, patch: Partial<OutreachMessage>) {
  const updatedAt = new Date().toISOString();
  const result = await (await collection()).findOneAndUpdate(
    { id },
    { $set: { ...patch, updatedAt } },
    { returnDocument: 'after', projection: { _id: 0 } },
  );
  return result;
}
