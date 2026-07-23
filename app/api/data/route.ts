import { NextResponse, type NextRequest } from 'next/server';
import { getCacheHeaders } from '@/app/lib/cache';

export const revalidate = 300;

const RUNTIME_BASE = (process.env.RUNTIME_API_URL || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');
const GH_TOKEN = process.env.GITHUB_CONTENT_TOKEN ?? '';
const GH_OWNER = process.env.GITHUB_CONTENT_OWNER ?? 'quantam101';
const GH_REPO = process.env.GITHUB_CONTENT_REPO ?? 'content';
const GH_POSTS_DIR = process.env.GITHUB_CONTENT_DIR ?? '_posts';
const CONTENT_SITE = `https://${GH_OWNER}.github.io/${GH_REPO}`;

async function fetchJson<T>(url: string, timeoutMs = 6000): Promise<T | null> {
  try {
    const res = await fetch(url, {
      cache: 'no-store',
      signal: AbortSignal.timeout(timeoutMs),
      headers: { 'User-Agent': 'ProfitEngine/5.0' },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

type RuntimeHealth = { ok?: boolean; service?: string; mode?: string };
type IncomeSummary = { ok?: boolean; streams?: Record<string, unknown> };
type Metrics = {
  total_cycles?: number;
  successful_cycles?: number;
  success_rate_pct?: number;
  last_cycle_iso?: string | null;
};
type ProductsRevenue = {
  ok?: boolean;
  products?: number;
  month_revenue_usd?: number;
  catalog?: unknown[];
};
type NewsletterStats = { ok?: boolean; total_subscribers?: number; subscribers?: Record<string, unknown> };

async function fetchRuntimeSnapshot(): Promise<Record<string, unknown> | null> {
  const timeoutMs = 25_000;
  const [health, income, metrics, products, newsletter] = await Promise.all([
    fetchJson<RuntimeHealth>(`${RUNTIME_BASE}/health`, timeoutMs),
    fetchJson<IncomeSummary>(`${RUNTIME_BASE}/income/summary`, timeoutMs),
    fetchJson<Metrics>(`${RUNTIME_BASE}/metrics`, timeoutMs),
    fetchJson<ProductsRevenue>(`${RUNTIME_BASE}/products/revenue`, timeoutMs),
    fetchJson<NewsletterStats>(`${RUNTIME_BASE}/newsletter/stats`, timeoutMs),
  ]);

  if (!health?.ok) {
    return null;
  }

  return {
    _source: 'runtime_live',
    engineRunning: true,
    service: health.service ?? 'profitengine-runtime',
    mode: health.mode ?? 'strict_zero_spend',
    healthScore: 100,
    uptime: 'runtime active',
    tokensToday: 0,
    totalCycles: metrics?.total_cycles ?? 0,
    successRatePct: metrics?.success_rate_pct ?? 0,
    lastCycleIso: metrics?.last_cycle_iso ?? null,
    incomeStreams: income?.streams ?? {},
    products,
    newsletter,
    contentSite: CONTENT_SITE,
  };
}

async function fetchGitHubStats(): Promise<{ postCount: number; lastTitle: string; lastDate: string }> {
  try {
    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'ProfitEngine/5.0',
    };
    if (GH_TOKEN) headers['Authorization'] = `token ${GH_TOKEN}`;
    const res = await fetch(
      `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/contents/${encodeURIComponent(GH_POSTS_DIR)}?per_page=100`,
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

export async function GET(_request: NextRequest) {
  const [runtime, ghStats] = await Promise.all([
    fetchRuntimeSnapshot(),
    fetchGitHubStats(),
  ]);

  if (runtime) {
    return NextResponse.json(
      {
        ...runtime,
        publishedPosts: ghStats.postCount,
        lastPublished: ghStats.lastTitle,
        lastPublishedDate: ghStats.lastDate,
        content24h: ghStats.postCount,
      },
      { headers: getCacheHeaders('SHORT') },
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
        healthScore: 0,
        uptime: 'pipeline active',
        tokensToday: 0,
      },
      { headers: { 'Cache-Control': 'no-store', 'x-data-source': 'github' } },
    );
  }

  return NextResponse.json(
    {
      _source: 'degraded',
      engineRunning: false,
      publishedPosts: ghStats.postCount,
      lastPublished: ghStats.lastTitle,
      lastPublishedDate: ghStats.lastDate,
      contentSite: CONTENT_SITE,
      content24h: ghStats.postCount,
      healthScore: 0,
      uptime: 'pipeline active',
      tokensToday: 0,
    },
    { headers: { 'Cache-Control': 'no-store', 'x-data-source': 'degraded' } },
  );
}
