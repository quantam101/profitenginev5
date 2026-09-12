import { NextRequest, NextResponse } from 'next/server';
import {
  recordRevenueOnce,
  verifySquareSignature,
} from '@/lib/revenue-attribution.mjs';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  const signatureKey = process.env.SQUARE_WEBHOOK_SIGNATURE_KEY;
  const notificationUrl = process.env.SQUARE_WEBHOOK_NOTIFICATION_URL;
  if (!signatureKey || !notificationUrl) {
    return NextResponse.json({ ok: false, error: 'Square webhook not configured' }, { status: 503 });
  }

  const signature = request.headers.get('x-square-hmacsha256-signature') || '';
  const rawBody = await request.text();
  if (!verifySquareSignature({ signatureKey, notificationUrl, body: rawBody, signature })) {
    return NextResponse.json({ ok: false, error: 'Invalid signature' }, { status: 403 });
  }

  let event: any;
  try { event = JSON.parse(rawBody); }
  catch { return NextResponse.json({ ok: false, error: 'Invalid JSON body' }, { status: 400 }); }

  const payment = event?.data?.object?.payment;
  if (!payment || payment.status !== 'COMPLETED') {
    return NextResponse.json({ ok: true, ignored: true, type: event?.type || 'unknown' });
  }

  const metadata = payment.note && typeof payment.note === 'string'
    ? Object.fromEntries(
        payment.note
          .split(';')
          .map((part: string) => part.trim().split('='))
          .filter((pair: string[]) => pair.length === 2),
      )
    : {};
  const leadId = payment.reference_id || metadata.lead_id || '';
  const bookingId = payment.order_id || metadata.booking_id || '';
  const amount = Number(payment.amount_money?.amount || 0);
  const currency = String(payment.amount_money?.currency || 'USD').toLowerCase();

  try {
    const result = await recordRevenueOnce({
      provider: 'square',
      paymentId: payment.id,
      providerEventId: event.event_id || event.id || '',
      leadId,
      bookingId,
      checkoutId: payment.order_id || '',
      amount,
      currency,
      rawType: event.type || '',
    });

    return NextResponse.json({
      ok: true,
      inserted: result.inserted,
      duplicate: result.duplicate,
      revenueEventId: result.event?.revenueEventId,
      leadId,
      bookingId,
      paymentId: payment.id,
    });
  } catch (error) {
    console.error('Square revenue reconciliation failed:', error);
    return NextResponse.json({ ok: false, error: 'Revenue reconciliation failed' }, { status: 500 });
  }
}
