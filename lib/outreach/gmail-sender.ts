import tls from 'node:tls';
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

function buildMime(message: OutreachMessage, from: string, includeBcc: boolean = false) {
  const lines = [
    `From: ${headerValue(from, 'from')}`,
    `To: ${addresses(message.recipients.to)}`,
    ...(message.recipients.cc?.length ? [`Cc: ${addresses(message.recipients.cc)}`] : []),
    ...(includeBcc && message.recipients.bcc?.length ? [`Bcc: ${addresses(message.recipients.bcc)}`] : []),
    `Subject: ${headerValue(message.subject, 'subject')}`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
  ];
  return `${lines.join('\r\n')}\r\n\r\n${message.body.replace(/\r?\n/g, '\r\n')}`;
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

async function sendViaGmailApi(message: OutreachMessage, from: string) {
  const raw = encodeBase64Url(buildMime(message, from, true));
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

function smtpSend(message: OutreachMessage, user: string, password: string, from: string) {
  return new Promise<{ id: string }>((resolve, reject) => {
    const socket = tls.connect({ host: 'smtp.gmail.com', port: 465, servername: 'smtp.gmail.com', rejectUnauthorized: true });
    socket.setTimeout(30_000);
    let buffer = '';
    let waiter: ((line: string) => void) | undefined;

    const fail = (error: Error) => {
      socket.destroy();
      reject(error);
    };

    socket.on('error', fail);
    socket.on('timeout', () => fail(new Error('Gmail SMTP connection timed out')));
    socket.on('data', (chunk) => {
      buffer += chunk.toString('utf8');
      const lines = buffer.split('\r\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (/^\d{3} /.test(line) && waiter) {
          const current = waiter;
          waiter = undefined;
          current(line);
        }
      }
    });

    const command = (value: string, expected: number[]) => new Promise<string>((resolveCommand, rejectCommand) => {
      waiter = (line) => {
        const code = Number(line.slice(0, 3));
        if (expected.includes(code)) resolveCommand(line);
        else rejectCommand(new Error(`Gmail SMTP rejected command (${line})`));
      };
      if (value) socket.write(`${value}\r\n`);
    });

    const ehloDomain = process.env.NEXT_PUBLIC_SITE_URL ? new URL(process.env.NEXT_PUBLIC_SITE_URL).hostname : 'alreadyherellc.com';
    void (async () => {
      try {
        await command('', [220]);
        await command(`EHLO ${ehloDomain}`, [250]);
        await command('AUTH LOGIN', [334]);
        await command(Buffer.from(user).toString('base64'), [334]);
        await command(Buffer.from(password).toString('base64'), [235]);
        await command(`MAIL FROM:<${headerValue(from, 'from')}>`, [250]);
        const recipients = [...message.recipients.to, ...(message.recipients.cc ?? []), ...(message.recipients.bcc ?? [])];
        for (const recipient of recipients) await command(`RCPT TO:<${headerValue(recipient, 'recipient')}>`, [250, 251]);
        await command('DATA', [354]);
        const mime = buildMime(message, from, false).replace(/^\./gm, '..');
        await command(`${mime}\r\n.`, [250]);
        await command('QUIT', [221]);
        socket.end();
        resolve({ id: `smtp-${Date.now()}` });
      } catch (error) {
        fail(error instanceof Error ? error : new Error(String(error)));
      }
    })();
  });
}

export async function sendGmailMessage(message: OutreachMessage) {
  const oauthReady = Boolean(process.env.GMAIL_CLIENT_ID && process.env.GMAIL_CLIENT_SECRET && process.env.GMAIL_REFRESH_TOKEN);
  const smtpUser = process.env.GMAIL_USER;
  const smtpPassword = process.env.GMAIL_APP_PASSWORD;
  const from = process.env.GMAIL_FROM_ADDRESS ?? smtpUser;
  if (!from) throw new Error('GMAIL_FROM_ADDRESS or GMAIL_USER is not configured');

  if (oauthReady) return sendViaGmailApi(message, from);
  if (smtpUser && smtpPassword) return smtpSend(message, smtpUser, smtpPassword, from);
  throw new Error('Gmail credentials are not configured (OAuth or GMAIL_USER/GMAIL_APP_PASSWORD required)');
}
