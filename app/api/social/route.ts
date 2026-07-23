import { NextResponse } from 'next/server';
import { getRuntimeBase } from '@/app/lib/runtime';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/**
 * GET /api/social
 * Returns which social platforms are configured (have credentials set).
 */
export async function GET() {
  const platforms = {
    twitter:   !!(process.env.TWITTER_API_KEY),
    linkedin:  !!(process.env.LINKEDIN_ACCESS_TOKEN),
    facebook:  !!(process.env.FB_PAGE_ACCESS_TOKEN),
    instagram: !!(process.env.IG_USER_ID && process.env.FB_PAGE_ACCESS_TOKEN),
    tiktok:    !!(process.env.TIKTOK_ACCESS_TOKEN),
    youtube:   !!(process.env.YOUTUBE_REFRESH_TOKEN),
    telegram:  !!(process.env.TELEGRAM_BOT_TOKEN),
    reddit:    !!(process.env.REDDIT_CLIENT_ID),
    mastodon:  !!(process.env.MASTODON_ACCESS_TOKEN),
    pinterest: !!(process.env.PINTEREST_ACCESS_TOKEN),
    devto:     !!(process.env.DEVTO_API_KEY),
    hashnode:  !!(process.env.HASHNODE_API_KEY),
    medium:    !!(process.env.MEDIUM_API_KEY),
    beehiiv:   !!(process.env.BEEHIIV_API_KEY),
  };

  const active   = Object.entries(platforms).filter(([, v]) => v).map(([k]) => k);
  const inactive = Object.entries(platforms).filter(([, v]) => !v).map(([k]) => k);

  return NextResponse.json(
    { ok: true, active_count: active.length, active, inactive },
    { headers: NO_STORE }
  );
}

/**
 * POST /api/social
 * Manually trigger a social distribution for a post.
 * Body: { text, title?, url?, platforms? }
 */
export async function POST(request: Request) {
  const rt = getRuntimeBase();
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400, headers: NO_STORE }); }
  const r = await fetch(`${rt}/social/distribute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}
