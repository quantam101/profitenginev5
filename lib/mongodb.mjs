import { MongoClient } from 'mongodb';

function getUri() {
  return process.env.MONGODB_URI || process.env.MONGO_URL;
}

function deriveDbName() {
  if (process.env.MONGODB_DB) return process.env.MONGODB_DB;
  if (process.env.DB_NAME) return process.env.DB_NAME;
  const uri = getUri();
  if (uri) {
    try {
      const pathname = new URL(uri).pathname;
      if (pathname && pathname.length > 1) return pathname.slice(1);
    } catch {
      // fall through to default
    }
  }
  return 'profitengine';
}

function getClientOptions() {
  return {
    maxPoolSize: Number(process.env.MONGODB_MAX_POOL_SIZE || 10),
    minPoolSize: Number(process.env.MONGODB_MIN_POOL_SIZE || 1),
  };
}

let clientPromise = null;

export async function getClient() {
  if (!clientPromise) {
    const uri = getUri();
    if (!uri) {
      throw new Error('MONGODB_URI or MONGO_URL is not set');
    }
    const client = new MongoClient(uri, getClientOptions());
    clientPromise = client.connect();
  }
  return clientPromise;
}

export async function getDb() {
  const client = await getClient();
  return client.db(deriveDbName());
}

export async function getCollection(name) {
  const db = await getDb();
  return db.collection(name);
}

export async function closeClient() {
  if (clientPromise) {
    const client = await clientPromise;
    await client.close();
    clientPromise = null;
  }
}
