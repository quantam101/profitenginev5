import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { getIssueBySlug, listActiveSubscribers, markIssuePublished, recordEvent } from '@/lib/newsletter-business/repository.mjs';
import { renderIssueHtml, unsubscribeUrl } from '@/lib/newsletter-business/core.mjs';
import { newsletterDeliveryConfigured, sendNewsletterBatch } from '@/lib/newsletter-business/email.mjs';

export const runtime = 'nodejs';

const schema = z.object({
  slug: z.string().min(1).max(100),
  confirm: z.literal('PUBLISH'),
});

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
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: 'Explicit confirm=PUBLISH is required' }, { status: 400 });
  }
  if (!newsletterDeliveryConfigured()) {
    return NextResponse.json({ ok: false, error: 'Newsletter delivery is not configured' }, { status: 503 });
  }

  try {
    const issue = await getIssueBySlug(parsed.data.slug);
    if (!issue) return NextResponse.json({ ok: false, error: 'Issue not found' }, { status: 404 });
    if (!['ready', 'published'].includes(String(issue.status))) {
      return NextResponse.json({ ok: false, error: 'Issue must be in ready state before publishing' }, { status: 409 });
    }
    if (issue.status === 'published') {
      return NextResponse.json({ ok: true, alreadyPublished: true, issue: { slug: issue.slug, publishedAt: issue.publishedAt } });
    }

    const subscribers = await listActiveSubscribers(10000);
    if (!subscribers.length) {
      return NextResponse.json({ ok: false, error: 'No active subscribers' }, { status: 409 });
    }

    const batches = [];
    for (let i = 0; i < subscribers.length; i += 100) batches.push(subscribers.slice(i, i + 100));

    let sent = 0;
    let failed = 0;
    const failures: Array<{ batch: number; error: string }> = [];

    for (let batchIndex = 0; batchIndex < batches.length; batchIndex += 1) {
      const batch = batches[batchIndex];
      const messages = batch.map((subscriber: any) => ({
        to: subscriber.email,
        subject: issue.subject || issue.title,
        html: renderIssueHtml(issue, unsubscribeUrl(subscriber.unsubscribeToken)),
        replyTo: process.env.NEWSLETTER_REPLY_TO || 'dispatch@alreadyherellc.com',
        tags: [
          { name: 'category', value: 'profitengine_newsletter' },
          { name: 'issue', value: String(issue.slug).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64) },
        ],
      }));
      const result = await sendNewsletterBatch({
        messages,
        idempotencyKey: `newsletter/${String(issue._id)}/batch-${batchIndex + 1}`,
      });
      if (result.ok) {
        sent += batch.length;
        await Promise.all(batch.map((subscriber: any) => recordEvent({
          type: 'delivery_sent',
          subscriberId: subscriber._id,
          issueId: issue._id,
          metadata: { provider: 'resend', batch: batchIndex + 1 },
        })));
      } else {
        failed += batch.length;
        failures.push({ batch: batchIndex + 1, error: result.error || 'Unknown delivery error' });
        await Promise.all(batch.map((subscriber: any) => recordEvent({
          type: 'delivery_failed',
          subscriberId: subscriber._id,
          issueId: issue._id,
          metadata: { provider: 'resend', batch: batchIndex + 1, error: result.error },
        })));
      }
    }

    const summary = { audience: subscribers.length, sent, failed, batches: batches.length };
    if (failed === 0) {
      const published = await markIssuePublished(issue._id, summary);
      return NextResponse.json({ ok: true, published: true, summary, issue: { slug: published?.slug, publishedAt: published?.publishedAt } });
    }

    await recordEvent({ type: 'issue_delivery_partial', issueId: issue._id, metadata: { ...summary, failures } });
    return NextResponse.json({ ok: false, published: false, summary, failures }, { status: 502 });
  } catch (error) {
    console.error('[newsletter] publish error:', error);
    return NextResponse.json({ ok: false, error: 'Publish failed' }, { status: 500 });
  }
}
