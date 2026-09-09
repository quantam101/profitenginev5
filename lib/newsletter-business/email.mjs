const RESEND_ENDPOINT = 'https://api.resend.com/emails';

export function newsletterDeliveryConfigured() {
  return Boolean(process.env.RESEND_API_KEY && process.env.NEWSLETTER_FROM_EMAIL);
}

export async function sendNewsletterEmail({ to, subject, html, idempotencyKey, replyTo }) {
  if (!newsletterDeliveryConfigured()) {
    return { ok: false, configured: false, error: 'RESEND_API_KEY and NEWSLETTER_FROM_EMAIL are required' };
  }

  const response = await fetch(RESEND_ENDPOINT, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    },
    body: JSON.stringify({
      from: process.env.NEWSLETTER_FROM_EMAIL,
      to: [String(to)],
      subject: String(subject),
      html: String(html),
      ...(replyTo ? { reply_to: replyTo } : {}),
    }),
  });

  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    return {
      ok: false,
      configured: true,
      status: response.status,
      error: data?.message || data?.error || `Resend returned HTTP ${response.status}`,
      data,
    };
  }

  return { ok: true, configured: true, status: response.status, id: data?.id, data };
}
