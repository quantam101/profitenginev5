import { NextResponse } from 'next/server';
import { getCollection } from '../../../../lib/mongodb.mjs';

export const dynamic = 'force-dynamic';

const TOPICS_COLLECTION = 'contentsync_topics';
const LOG_COLLECTION = 'contentsync_published';
const MAX_LIMIT = 100;

interface TopicDoc {
  topic: string;
  consumed_at: string | null;
}

function storeError(err: unknown) {
  const msg = String(err || '');
  const unconfigured = /MONGODB_URI|MONGO_URL is not set/.test(msg);
  return NextResponse.json(
    { ok: false, error: `content-sync store ${unconfigured ? 'not configured' : 'error'}: ${msg.slice(0, 160)}` },
    { status: unconfigured ? 503 : 502 },
  );
}

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = (await req.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ ok: false, error: 'invalid JSON body' }, { status: 400 });
  }
  const title = String(body?.title || '').trim();
  const canonicalUrl = String(body?.canonical_url || '').trim();
  if (!title || !canonicalUrl) {
    return NextResponse.json(
      { ok: false, error: 'title and canonical_url are required' },
      { status: 400 },
    );
  }
  const record = {
    title,
    topic: String(body?.topic || ''),
    canonical_url: canonicalUrl,
    devto_url: String(body?.devto_url || ''),
    medium_url: String(body?.medium_url || ''),
    hashnode_url: String(body?.hashnode_url || ''),
    platforms: Array.isArray(body?.platforms) ? body.platforms : [],
    logged_at: new Date().toISOString(),
  };
  try {
    const log = await getCollection(LOG_COLLECTION);
    await log.insertOne(record);
    // Consume the matching queued topic so it is not re-served.
    const topic = record.topic.trim();
    if (topic) {
      const topics = await getCollection(TOPICS_COLLECTION);
      await topics.updateOne(
        { topic, consumed_at: null },
        { $set: { consumed_at: new Date().toISOString() } },
      );
    }
    return NextResponse.json({ ok: true, logged: true });
  } catch (err) {
    return storeError(err);
  }
}

export async function GET(req: Request) {
  const limit = Math.min(MAX_LIMIT, Math.max(1, Number(new URL(req.url).searchParams.get('limit') || 20) || 20));
  try {
    const col = await getCollection(LOG_COLLECTION);
    const records = await col
      .find({}, { projection: { _id: 0 } })
      .sort({ logged_at: -1 })
      .limit(limit)
      .toArray();
    return NextResponse.json({ ok: true, records });
  } catch (err) {
    return storeError(err);
  }
}
