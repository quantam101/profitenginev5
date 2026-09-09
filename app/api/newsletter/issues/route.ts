import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { listPublishedIssues, upsertIssue } from '@/lib/newsletter-business/repository.mjs';

export const runtime = 'nodejs';

const issueSchema = z.object({
  slug: z.string().max(100).optional(),
  title: z.string().min(3).max(180),
  subject: z.string().min(3).max(180).optional(),
  excerpt: z.string().max(500).optional(),
  bodyHtml: z.string().min(1),
  ctaLabel: z.string().max(100).optional(),
  ctaUrl: z.string().url().optional(),
  status: z.enum(['draft', 'ready', 'published']).default('draft'),
  monetization: z.record(z.unknown()).optional(),
});

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = Math.min(Math.max(Number(searchParams.get('limit')) || 12, 1), 50);
  try {
    const issues = await listPublishedIssues(limit);
    return NextResponse.json({
      ok: true,
      source: 'mongodb',
      issues: issues.map((issue: any) => ({
        slug: issue.slug,
        title: issue.title,
        excerpt: issue.excerpt,
        publishedAt: issue.publishedAt,
        ctaLabel: issue.ctaLabel,
        ctaUrl: issue.ctaUrl,
      })),
    });
  } catch (error) {
    // Production currently uses the existing ProfitEngine runtime + Resend
    // audience and does not require Mongo for public acquisition/delivery.
    // Keep the archive endpoint healthy while Mongo remains optional.
    console.warn('[newsletter] issue archive storage unavailable:', error);
    return NextResponse.json({
      ok: true,
      source: 'runtime',
      issues: [],
      warning: 'Issue archive storage is not configured; newsletter delivery remains available through the live runtime.',
    });
  }
}

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = issueSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: parsed.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  try {
    const issue = await upsertIssue(parsed.data);
    return NextResponse.json({ ok: true, issue: { ...issue, _id: String(issue?._id || '') } }, { status: 201 });
  } catch (error) {
    console.error('[newsletter] issue create error:', error);
    return NextResponse.json({
      ok: false,
      error: 'Persistent issue storage is not configured. Set MONGODB_URI before creating issues through this API.',
    }, { status: 503 });
  }
}
