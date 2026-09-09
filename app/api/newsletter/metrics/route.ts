import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { getNewsletterMetrics } from '@/lib/newsletter-business/repository.mjs';
import { newsletterDeliveryConfigured } from '@/lib/newsletter-business/email.mjs';
import { getRuntimeNewsletterStats, newsletterRuntimeConfigured } from '@/lib/newsletter-business/runtime.mjs';

export const runtime = 'nodejs';

function runtimeMetrics(data: any) {
  const active = Number(data?.resend?.total_subscribers ?? data?.total_subscribers ?? 0) || 0;
  const unsubscribed = Number(data?.resend?.unsubscribed ?? 0) || 0;
  return {
    subscribers: { total: active + unsubscribed, active, pending: 0, unsubscribed },
    issues: { drafts: 0, ready: 0, published: 0 },
    delivery: { sent: 0, failed: 0 },
  };
}

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const metrics = await getNewsletterMetrics();
    return NextResponse.json({
      ok: true,
      source: 'mongodb',
      metrics,
      delivery: {
        provider: newsletterRuntimeConfigured() ? 'resend-runtime' : 'resend-direct',
        configured: newsletterRuntimeConfigured() || newsletterDeliveryConfigured(),
        from: process.env.NEWSLETTER_FROM_EMAIL || process.env.NEWSLETTER_FROM || null,
      },
    });
  } catch (error) {
    console.warn('[newsletter] Mongo metrics unavailable; checking live runtime:', error);
    const stats = await getRuntimeNewsletterStats();
    if (stats.ok) {
      return NextResponse.json({
        ok: true,
        source: 'runtime',
        metrics: runtimeMetrics(stats.data),
        delivery: {
          provider: stats.data?.resend?.provider || 'resend-runtime',
          configured: true,
          audienceId: stats.data?.resend?.audience_id || null,
        },
        runtime: stats.data,
      });
    }

    return NextResponse.json({
      ok: false,
      error: 'Newsletter metrics unavailable',
      runtimeError: stats.error || null,
    }, { status: 503 });
  }
}
