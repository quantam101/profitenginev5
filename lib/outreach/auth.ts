import { timingSafeEqual } from 'node:crypto';

function safeEqual(left: string, right: string) {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

export function requireOutreachAdmin(request: Request) {
  const configured = process.env.OUTREACH_ADMIN_TOKEN ?? process.env.PROFITENGINE_WEBHOOK_TOKEN;
  if (!configured) throw new Error('OUTREACH_ADMIN_TOKEN or PROFITENGINE_WEBHOOK_TOKEN is not configured');

  const authorization = request.headers.get('authorization') ?? '';
  const supplied = authorization.startsWith('Bearer ') ? authorization.slice(7) : '';
  if (!supplied || !safeEqual(supplied, configured)) {
    const error = new Error('Unauthorized');
    Object.assign(error, { status: 401 });
    throw error;
  }
}
