import { NextResponse } from 'next/server';
import { getCollection } from '../../../../lib/mongodb.mjs';

export const dynamic = 'force-dynamic';

const COLLECTION = 'contentsync_topics';
const MAX_LIMIT = 50;

function storeError(err: unknown) {
  const msg = String(err || '');
  // Unconfigured store → honest 503 so probes report FAILED, never READY.
  const unconfigured = /MONGODB_URI|MONGO_URL is not set/.test(msg);
  return NextResponse.json(
    { ok: false, error: `content-sync store ${unconfigured ? 'not configured' : 'error'}: ${msg.slice(0, 160)}` },
    { status: unconfigured ? 503 : 502 },
  );
}

export async function GET(req: Request) {
  const limit = Math.min(
    MAX_LIMIT,
    Math.max(1, Number(new URL(req.url).searchParams.get('limit') || 1) || 1),
  );
  try {
    const col = await getCollection(COLLECTION);
    const docs = await col
      .find({ consumed_at: null }, { projection: { _id: 0, topic: 1 } })
      .sort({ queued_at: 1 })
      .limit(limit)
      .toArray();
    return NextResponse.json({ ok: true, topics: docs.map((d: { topic: string }) => ({ topic: d.topic })) });
  } catch (err) {
    return storeError(err);
  }
}

export async function POST(req: Request) {
  let body: { topic?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'invalid JSON body' }, { status: 400 });
  }
  const topic = String(body?.topic || '').trim();
  if (!topic || topic.length > 300) {
    return NextResponse.json(
      { ok: false, error: 'topic must be a non-empty string up to 300 chars' },
      { status: 400 },
    );
  }
  try {
    const col = await getCollection(COLLECTION);
    await col.insertOne({ topic, queued_at: new Date().toISOString(), consumed_at: null });
    return NextResponse.json({ ok: true, queued: topic });
  } catch (err) {
    return storeError(err);
  }
}
