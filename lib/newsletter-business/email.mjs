const RESEND_ENDPOINT = 'https://api.resend.com/emails';
const RESEND_BATCH_ENDPOINT = 'https://api.resend.com/emails/batch';

export function newsletterDeliveryConfigured() {
  return Boolean(process.env.RESEND_API_KEY && process.env.NEWSLETTER_FROM_EMAIL);
}

async function parseResponse(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return { raw: text };
  }
}

function headers(idempotencyKey) {
  return {
    Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
    'Content-Type': 'application/json',
    ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
  };
}

export async function sendNewsletterEmail({ to, subject, html, idempotencyKey, replyTo }) {
  if (!newsletterDeliveryConfigured()) {
    return { ok: false, configured: false, error: 'RESEND_API_KEY and NEWSLETTER_FROM_EMAIL are required' };
  }

  const response = await fetch(RESEND_ENDPOINT, {
    method: 'POST',
    headers: headers(idempotencyKey),
    body: JSON.stringify({
      from: process.env.NEWSLETTER_FROM_EMAIL,
      to: [String(to)],
      subject: String(subject),
      html: String(html),
      ...(replyTo ? { reply_to: replyTo } : {}),
    }),
  });

  const data = await parseResponse(response);
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

export async function sendNewsletterBatch({ messages, idempotencyKey }) {
  if (!newsletterDeliveryConfigured()) {
    return { ok: false, configured: false, error: 'RESEND_API_KEY and NEWSLETTER_FROM_EMAIL are required' };
  }
  if (!Array.isArray(messages) || messages.length < 1 || messages.length > 100) {
    return { ok: false, configured: true, error: 'Batch must contain between 1 and 100 messages' };
  }

  const body = messages.map((message) => ({
    from: process.env.NEWSLETTER_FROM_EMAIL,
    to: [String(message.to)],
    subject: String(message.subject),
    html: String(message.html),
    ...(message.replyTo ? { reply_to: message.replyTo } : {}),
    ...(message.tags ? { tags: message.tags } : {}),
  }));

  const response = await fetch(RESEND_BATCH_ENDPOINT, {
    method: 'POST',
    headers: headers(idempotencyKey),
    body: JSON.stringify(body),
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    return {
      ok: false,
      configured: true,
      status: response.status,
      error: data?.message || data?.error || `Resend batch returned HTTP ${response.status}`,
      data,
    };
  }

  return { ok: true, configured: true, status: response.status, data };
}
