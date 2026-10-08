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

function authorize(req: Request) {
  // The dedicated CONTENT_SYNC_TOKEN wins when configured; the legacy
  // PROFITENGINE_WEBHOOK_TOKEN is accepted only as a fallback so a webhook
  // token holder cannot reach content-sync once a dedicated token exists.
  const tokens = process.env.CONTENT_SYNC_TOKEN
    ? [process.env.CONTENT_SYNC_TOKEN]
    : [process.env.PROFITENGINE_WEBHOOK_TOKEN].filter(Boolean) as string[];
  if (!tokens.length) {
    return NextResponse.json(
      { ok: false, error: 'content-sync auth not configured' },
      { status: 503 },
    );
  }
  const presented = req.headers.get('authorization') || '';
  if (!tokens.some((t) => presented === `Bearer ${t}`)) {
    return NextResponse.json({ ok: false, error: 'unauthorized' }, { status: 401 });
  }
  return null;
}

function storeError(err: unknown) {
  const msg = String(err || '');
  // Driver internals stay server-side; callers get only the error class.
  const unconfigured = /MONGODB_URI|MONGO_URL is not set/.test(msg);
  if (!unconfigured) console.error('[content-sync] store error:', msg);
  return NextResponse.json(
    { ok: false, error: `content-sync store ${unconfigured ? 'not configured' : 'error'}` },
    { status: unconfigured ? 503 : 502 },
  );
}

export async function POST(req: Request) {
  const denied = authorize(req);
  if (denied) return denied;
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
  const denied = authorize(req);
  if (denied) return denied;
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
