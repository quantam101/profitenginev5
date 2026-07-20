import type { OutreachMessage } from './types';

let tokenCache: { accessToken: string; expiresAt: number } | undefined;

function encodeBase64Url(value: string) {
  return Buffer.from(value, 'utf8').toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function headerValue(value: string, field: string) {
  if (/\r|\n/.test(value)) throw new Error(`${field} contains invalid newline characters`);
  return value.trim();
}

function addresses(values?: string[]) {
  return values?.filter(Boolean).map((value) => headerValue(value, 'recipient')).join(', ') ?? '';
}

async function accessToken() {
  if (tokenCache && tokenCache.expiresAt > Date.now() + 60_000) return tokenCache.accessToken;
  const clientId = process.env.GMAIL_CLIENT_ID;
  const clientSecret = process.env.GMAIL_CLIENT_SECRET;
  const refreshToken = process.env.GMAIL_REFRESH_TOKEN;
  if (!clientId || !clientSecret || !refreshToken) throw new Error('Gmail OAuth credentials are not configured');

  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: clientId, client_secret: clientSecret, refresh_token: refreshToken, grant_type: 'refresh_token' }),
    cache: 'no-store',
  });
  if (!response.ok) throw new Error(`Gmail token refresh failed: ${response.status}`);
  const data = (await response.json()) as { access_token: string; expires_in?: number };
  tokenCache = { accessToken: data.access_token, expiresAt: Date.now() + (data.expires_in ?? 3600) * 1000 };
  return data.access_token;
}

export async function sendGmailMessage(message: OutreachMessage) {
  const from = process.env.GMAIL_FROM_ADDRESS;
  if (!from) throw new Error('GMAIL_FROM_ADDRESS is not configured');

  const lines = [
    `From: ${headerValue(from, 'from')}`,
    `To: ${addresses(message.recipients.to)}`,
    ...(message.recipients.cc?.length ? [`Cc: ${addresses(message.recipients.cc)}`] : []),
    ...(message.recipients.bcc?.length ? [`Bcc: ${addresses(message.recipients.bcc)}`] : []),
    `Subject: ${headerValue(message.subject, 'subject')}`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
  ];
  const raw = encodeBase64Url(`${lines.join('\r\n')}\r\n\r\n${message.body}`);
  const token = await accessToken();
  const response = await fetch('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw }),
    cache: 'no-store',
  });
  if (!response.ok) throw new Error(`Gmail send failed: ${response.status} ${(await response.text()).slice(0, 500)}`);
  return (await response.json()) as { id: string; threadId?: string };
}
