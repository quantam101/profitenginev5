import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { getNewsletterMetrics } from '@/lib/newsletter-business/repository.mjs';
import { newsletterDeliveryConfigured } from '@/lib/newsletter-business/email.mjs';

export const runtime = 'nodejs';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const metrics = await getNewsletterMetrics();
    return NextResponse.json({
      ok: true,
      metrics,
      delivery: {
        provider: 'resend',
        configured: newsletterDeliveryConfigured(),
        from: process.env.NEWSLETTER_FROM_EMAIL || null,
      },
    });
  } catch (error) {
    console.error('[newsletter] metrics error:', error);
    return NextResponse.json({ ok: false, error: 'Metrics unavailable' }, { status: 500 });
  }
}
