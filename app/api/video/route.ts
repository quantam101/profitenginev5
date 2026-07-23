import { NextResponse } from 'next/server';
import { getRuntimeBase } from '@/app/lib/runtime';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const RUNTIME = getRuntimeBase();

/**
 * GET /api/video
 * Returns the video engine status from the runtime.
 */
export async function GET() {
  try {
    const resp = await fetch(`${RUNTIME}/eaos/health`, {
      signal: AbortSignal.timeout(8_000),
      cache: 'no-store',
      headers: { 'User-Agent': 'ProfitEngine/5.0' },
    });
    const data: unknown = await resp.json();
    if (resp.ok) return NextResponse.json(data, { status: 200, headers: NO_STORE });
  } catch {
    // fall through
  }
  return NextResponse.json(
    { ok: true, video: 'degraded', source: 'degraded' },
    { status: 200, headers: NO_STORE },
  );
}

/**
 * POST /api/video
 *
 * Render a faceless vertical video from an article.
 * Proxies to the Python runtime at RUNTIME_API_URL/video.
 *
 * Tier routing (automatic, no config needed):
 *   1. Wan 2.7 MoE 27B FP8 (GPU node, if EAOS_GPU_ENABLED=true)
 *   2. HuggingFace TTS + FFmpeg slideshow (HF_TOKEN set)
 *   3. Pure FFmpeg text-overlay slideshow (always available)
 *
 * Body (JSON):
 *   title          string  required  Article title (≤ 200 chars)
 *   body           string  required  Article body text (≥ 20 chars)
 *   canonical_url  string  optional  Source URL for attribution
 */
export async function POST(request: Request) {
  let body: { title?: string; body?: string; canonical_url?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { ok: false, error: 'Request body must be valid JSON' },
      { status: 400, headers: NO_STORE },
    );
  }

  if (!body.title?.trim()) {
    return NextResponse.json(
      { ok: false, error: '"title" is required' },
      { status: 422, headers: NO_STORE },
    );
  }
  if (!body.body || body.body.trim().length < 20) {
    return NextResponse.json(
      { ok: false, error: '"body" must be at least 20 characters' },
      { status: 422, headers: NO_STORE },
    );
  }

  try {
    const upstream = await fetch(`${RUNTIME}/video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: body.title.trim(),
        body: body.body.trim(),
        canonical_url: body.canonical_url ?? '',
      }),
      // Video render can take several minutes
      signal: AbortSignal.timeout(360_000),
      cache: 'no-store',
    });

    const result: unknown = await upstream.json();
    return NextResponse.json(result, {
      status: upstream.ok ? 200 : 502,
      headers: NO_STORE,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, error: `Runtime unreachable: ${message}` },
      { status: 503, headers: NO_STORE },
    );
  }
}
