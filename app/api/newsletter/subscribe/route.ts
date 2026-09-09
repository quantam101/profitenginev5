import { NextResponse } from 'next/server';
import { z } from 'zod';
import { randomToken, sha256, confirmationUrl, renderConfirmationHtml } from '@/lib/newsletter-business/core.mjs';
import { upsertSubscriber, recordEvent } from '@/lib/newsletter-business/repository.mjs';
import { newsletterDeliveryConfigured, sendNewsletterEmail } from '@/lib/newsletter-business/email.mjs';

export const runtime = 'nodejs';

const schema = z.object({
  email: z.string().email(),
  consent: z.literal(true),
  source: z.string().max(120).optional(),
  utmSource: z.string().max(120).optional(),
  utmMedium: z.string().max(120).optional(),
  utmCampaign: z.string().max(160).optional(),
});

export async function POST(request: Request) {
  if (process.env.NEWSLETTER_BUSINESS_ENABLED === 'false') {
    return NextResponse.json({ ok: false, error: 'Newsletter business is disabled' }, { status: 404 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: parsed.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const confirmToken = randomToken();
  const unsubscribeToken = randomToken();
  const expires = new Date(Date.now() + 1000 * 60 * 60 * 24);

  try {
    const subscriber = await upsertSubscriber({
      ...parsed.data,
      consentAt: new Date(),
      confirmationTokenHash: sha256(confirmToken),
      confirmationExpiresAt: expires,
      unsubscribeToken,
    });

    if (subscriber?.status === 'active') {
      return NextResponse.json({ ok: true, captured: true, status: 'active', confirmationSent: false });
    }

    let confirmationSent = false;
    let deliveryError: string | undefined;
    if (newsletterDeliveryConfigured()) {
      const result = await sendNewsletterEmail({
        to: parsed.data.email,
        subject: 'Confirm your ProfitEngine AI subscription',
        html: renderConfirmationHtml({ confirmUrl: confirmationUrl(confirmToken) }),
        idempotencyKey: `newsletter-confirm/${sha256(parsed.data.email).slice(0, 24)}/${sha256(confirmToken).slice(0, 16)}`,
        replyTo: process.env.NEWSLETTER_REPLY_TO || 'dispatch@alreadyherellc.com',
      });
      confirmationSent = result.ok;
      if (!result.ok) deliveryError = result.error;
      await recordEvent({
        type: result.ok ? 'confirmation_sent' : 'confirmation_failed',
        subscriberId: subscriber?._id,
        metadata: { provider: 'resend', providerId: result.id, error: result.error },
      });
    }

    return NextResponse.json({
      ok: true,
      captured: true,
      status: 'pending',
      confirmationSent,
      deliveryConfigured: newsletterDeliveryConfigured(),
      ...(deliveryError ? { deliveryError } : {}),
    }, { status: 201 });
  } catch (error) {
    console.error('[newsletter] subscribe error:', error);
    return NextResponse.json({ ok: false, error: 'Subscriber capture failed' }, { status: 500 });
  }
}
