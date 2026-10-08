import { NextResponse } from 'next/server';
import { z } from 'zod';
import { randomToken, sha256, confirmationUrl, renderConfirmationHtml } from '@/lib/newsletter-business/core.mjs';
import { upsertSubscriber, recordEvent } from '@/lib/newsletter-business/repository.mjs';
import { newsletterDeliveryConfigured, sendNewsletterEmail } from '@/lib/newsletter-business/email.mjs';
import { newsletterRuntimeConfigured, subscribeViaRuntime } from '@/lib/newsletter-business/runtime.mjs';

export const runtime = 'nodejs';

// The public signup form is embedded on the Jekyll blog
// (www.alreadyherellc.com / quantam101.github.io), so cross-origin POSTs
// from those origins only need CORS clearance. Everything else gets none.
const SIGNUP_ORIGINS = new Set([
  'https://www.alreadyherellc.com',
  'https://alreadyherellc.com',
  'https://quantam101.github.io',
]);

function corsHeaders(request: Request): Record<string, string> {
  const origin = request.headers.get('origin') || '';
  if (!SIGNUP_ORIGINS.has(origin)) return {};
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

function respond(request: Request, body: unknown, init?: ResponseInit) {
  return NextResponse.json(body, { ...init, headers: { ...corsHeaders(request), ...(init?.headers || {}) } });
}

export async function OPTIONS(request: Request) {
  return new NextResponse(null, { status: 204, headers: corsHeaders(request) });
}

const schema = z.object({
  email: z.string().email(),
  consent: z.literal(true),
  firstName: z.string().max(100).optional(),
  source: z.string().max(120).optional(),
  utmSource: z.string().max(120).optional(),
  utmMedium: z.string().max(120).optional(),
  utmCampaign: z.string().max(160).optional(),
});

export async function POST(request: Request) {
  if (process.env.NEWSLETTER_BUSINESS_ENABLED === 'false') {
    return respond(request, { ok: false, error: 'Newsletter business is disabled' }, { status: 404 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return respond(request, { ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return respond(request, { ok: false, error: parsed.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  // Production already has a working ProfitEngine runtime backed by the
  // verified Already Here Resend audience. Prefer that durable subscriber
  // store rather than requiring a second database before acquisition can work.
  if (newsletterRuntimeConfigured()) {
    const runtimeResult = await subscribeViaRuntime({
      email: parsed.data.email,
      firstName: parsed.data.firstName || '',
    });
    if (runtimeResult.ok) {
      // Mongo is an optional analytics mirror. Failure here must never discard
      // a subscriber already persisted by the live newsletter provider.
      try {
        const mirrorToken = randomToken();
        await upsertSubscriber({
          ...parsed.data,
          consentAt: new Date(),
          confirmationTokenHash: sha256(mirrorToken),
          confirmationExpiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24),
          unsubscribeToken: randomToken(),
        });
      } catch (error) {
        console.warn('[newsletter] optional Mongo subscriber mirror unavailable:', error);
      }

      return respond(request, {
        ok: true,
        captured: true,
        status: 'active',
        provider: 'resend-runtime',
        providerId: runtimeResult.data?.id || null,
      }, { status: 201 });
    }
  }

  // Standalone fallback for environments that have Mongo + direct Resend but
  // no runtime bridge (local development or a future independent deployment).
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
      return respond(request, { ok: true, captured: true, status: 'active', confirmationSent: false });
    }

    if (!newsletterDeliveryConfigured()) {
      return respond(request, {
        ok: false,
        captured: true,
        status: 'pending',
        error: 'Subscriber was stored, but newsletter delivery is not configured',
      }, { status: 503 });
    }

    const result = await sendNewsletterEmail({
      to: parsed.data.email,
      subject: 'Confirm your ProfitEngine AI subscription',
      html: renderConfirmationHtml({ confirmUrl: confirmationUrl(confirmToken) }),
      idempotencyKey: `newsletter-confirm/${sha256(parsed.data.email).slice(0, 24)}/${sha256(confirmToken).slice(0, 16)}`,
      replyTo: process.env.NEWSLETTER_REPLY_TO || 'dispatch@alreadyherellc.com',
    });
    await recordEvent({
      type: result.ok ? 'confirmation_sent' : 'confirmation_failed',
      subscriberId: subscriber?._id,
      metadata: { provider: 'resend', providerId: result.id, error: result.error },
    });

    return respond(request, {
      ok: result.ok,
      captured: true,
      status: 'pending',
      confirmationSent: result.ok,
      deliveryConfigured: true,
      ...(result.ok ? {} : { error: result.error || 'Confirmation delivery failed' }),
    }, { status: result.ok ? 201 : 502 });
  } catch (error) {
    console.error('[newsletter] subscribe error:', error);
    return respond(request, { ok: false, error: 'Subscriber capture failed' }, { status: 500 });
  }
}
