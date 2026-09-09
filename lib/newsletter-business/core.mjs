import crypto from 'node:crypto';

export function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase();
}

export function sha256(value) {
  return crypto.createHash('sha256').update(String(value)).digest('hex');
}

export function randomToken(bytes = 24) {
  return crypto.randomBytes(bytes).toString('base64url');
}

export function publicBaseUrl() {
  return (process.env.NEXT_PUBLIC_SITE_URL || process.env.PUBLIC_SITE_URL || 'https://app.alreadyherellc.com').replace(/\/$/, '');
}

export function confirmationUrl(token) {
  return `${publicBaseUrl()}/api/newsletter/confirm?token=${encodeURIComponent(token)}`;
}

export function unsubscribeUrl(token) {
  return `${publicBaseUrl()}/api/newsletter/unsubscribe?token=${encodeURIComponent(token)}`;
}

export function renderConfirmationHtml({ confirmUrl }) {
  return `<!doctype html>
<html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#101010">
  <h1>Confirm your ProfitEngine AI subscription</h1>
  <p>You asked to receive ProfitEngine AI: practical AI automation, revenue systems, field-service workflows, and proof-first business experiments from Already Here LLC.</p>
  <p><a href="${escapeHtml(confirmUrl)}" style="display:inline-block;padding:12px 18px;background:#111;color:#fff;text-decoration:none;border-radius:6px">Confirm subscription</a></p>
  <p>If you did not request this, ignore this email.</p>
</body></html>`;
}

export function renderIssueHtml(issue, unsubscribeHref) {
  const title = escapeHtml(issue.title || issue.subject || 'ProfitEngine AI');
  const body = String(issue.bodyHtml || '<p>No content supplied.</p>');
  const cta = issue.ctaUrl && issue.ctaLabel
    ? `<p style="margin:28px 0"><a href="${escapeHtml(issue.ctaUrl)}" style="display:inline-block;padding:12px 18px;background:#111;color:#fff;text-decoration:none;border-radius:6px">${escapeHtml(issue.ctaLabel)}</a></p>`
    : '';
  return `<!doctype html>
<html><body style="font-family:Arial,sans-serif;line-height:1.65;color:#101010;max-width:720px;margin:auto;padding:24px">
  <div style="font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#666">ProfitEngine AI · Already Here LLC</div>
  <h1>${title}</h1>
  ${body}
  ${cta}
  <hr style="border:0;border-top:1px solid #ddd;margin:32px 0" />
  <p style="font-size:12px;color:#666">You are receiving this because you subscribed to ProfitEngine AI. <a href="${escapeHtml(unsubscribeHref)}">Unsubscribe</a>.</p>
</body></html>`;
}

export function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 90);
}

export function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
