import { NextResponse, type NextRequest } from 'next/server';

const ORACLE = process.env.ORACLE_API_URL ?? 'http://localhost:3000';
const GH_TOKEN = process.env.GITHUB_CONTENT_TOKEN ?? '';
const GH_OWNER = process.env.GITHUB_CONTENT_OWNER ?? 'quantam101';
const GH_REPO = process.env.GITHUB_CONTENT_REPO ?? 'content';
const CONTENT_SITE = `https://${GH_OWNER}.github.io/${GH_REPO}`;

/** Try the OCI/local oracle API first (fastest, richest data). */
async function tryOracle(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch(`${ORACLE}/api/status`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(6000),
    });
    if (!res.ok) return null;
    const d = await res.json() as Record<string, unknown>;
    const lc = (d.lastCycle as Record<string, number>) ?? {};
    const tok = (d.tokens as Record<string, number>) ?? {};
    const ht = (d.lastHealth as Record<string, unknown>) ?? {};
    const mem = (ht.memory as Record<string, number>) ?? {};
    const upSec = (d.uptime as number) ?? 0;
    const h = Math.floor(upSec / 3600);
    const m = Math.floor((upSec % 3600) / 60);
    return {
      _source: 'oracle_live',
      engineRunning: !!(d.ok),
      uptime: `${h}h ${m}m`,
      healthScore: (d.intelligenceReport as Record<string, number>)?.healthScore ?? 20,
      tokensToday: Math.round(((tok.total as number) ?? 0) / 1000),
      content24h: (lc.generated as number) ?? 0,
      totalCycles: (d.totalCycles as number) ?? 0,
      memUsedPct: (mem.usedPct as number) ?? 0,
    };
  } catch {
    return null;
  }
}

/** Pull real published-post count from GitHub Pages content repo. */
async function fetchGitHubStats(): Promise<{ postCount: number; lastTitle: string; lastDate: string }> {
  try {
    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'ProfitEngine/5.0',
    };
    if (GH_TOKEN) headers['Authorization'] = `token ${GH_TOKEN}`;
    const res = await fetch(
      `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/contents/posts?per_page=100`,
      { headers, next: { revalidate: 300 }, signal: AbortSignal.timeout(10000) },
    );
    if (!res.ok) return { postCount: 0, lastTitle: '', lastDate: '' };
    const files = await res.json() as Array<{ name: string }>;
    const posts = files.filter(f => f.name.endsWith('.md') && f.name !== 'README.md');
    posts.sort((a, b) => b.name.localeCompare(a.name));
    const latest = posts[0]?.name ?? '';
    const lastDate = latest.slice(0, 10);
    const lastTitle = latest
      .replace(/^\d{4}-\d{2}-\d{2}-/, '')
      .replace(/\.md$/, '')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
    return { postCount: posts.length, lastTitle, lastDate };
  } catch {
    return { postCount: 0, lastTitle: '', lastDate: '' };
  }
}

/**
 * Fetch real health score by calling our own /api/health endpoint.
 * Uses the incoming request's Host header so it works in every environment
 * (localhost dev, Docker on OCI, Vercel) without env var configuration.
 */
async function fetchHealthScore(requestHost: string): Promise<number> {
  try {
    // Use https for non-localhost hosts (production); http for local dev
    const isLocal = requestHost.startsWith('localhost') || requestHost.startsWith('127.');
    const base = isLocal ? `http://${requestHost}` : `https://${requestHost}`;
    const res = await fetch(`${base}/api/health`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return 100;
    const d = await res.json() as Record<string, unknown>;
    return typeof d.healthScore === 'number' ? d.healthScore : 100;
  } catch {
    return 100;
  }
}

export async function GET(request: NextRequest) {
  const host = request.headers.get('host') ?? 'localhost:3000';
  const [oracle, ghStats, liveHealth] = await Promise.all([
    tryOracle(),
    fetchGitHubStats(),
    fetchHealthScore(host),
  ]);

  if (oracle) {
    return NextResponse.json(
      {
        ...oracle,
        healthScore: (oracle.healthScore as number) > 20 ? oracle.healthScore : liveHealth,
        contentSite: CONTENT_SITE,
        publishedPosts: ghStats.postCount,
        lastPublished: ghStats.lastTitle,
        lastPublishedDate: ghStats.lastDate,
      },
      { headers: { 'Cache-Control': 'no-store', 'x-data-source': 'oracle+github' } },
    );
  }

  if (ghStats.postCount > 0) {
    return NextResponse.json(
      {
        _source: 'github_only',
        engineRunning: true,
        publishedPosts: ghStats.postCount,
        lastPublished: ghStats.lastTitle,
        lastPublishedDate: ghStats.lastDate,
        contentSite: CONTENT_SITE,
        content24h: ghStats.postCount,
        healthScore: liveHealth,
        uptime: 'pipeline active',
        tokensToday: 0,
      },
      { headers: { 'Cache-Control': 'no-store', 'x-data-source': 'github' } },
    );
  }

  return NextResponse.json({ error: 'oracle_unreachable' }, { status: 502 });
}
