import { NextRequest } from 'next/server';

const token = process.env.PROFITENGINE_WEBHOOK_TOKEN ?? '';

export function hasWebhookAccess(req: NextRequest) {
  if (!token) return false;
  return req.headers.get('x-profitengine-token') === token;
}
