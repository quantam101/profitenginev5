import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../../lib/outreach/auth';

export async function GET(request: Request) {
  try {
    requireOutreachAdmin(request);
    const checks = {
      mongodb: Boolean(process.env.MONGODB_URI),
      gmailClientId: Boolean(process.env.GMAIL_CLIENT_ID),
      gmailClientSecret: Boolean(process.env.GMAIL_CLIENT_SECRET),
      gmailRefreshToken: Boolean(process.env.GMAIL_REFRESH_TOKEN),
      gmailFromAddress: Boolean(process.env.GMAIL_FROM_ADDRESS),
      slackWebhook: Boolean(process.env.SLACK_OUTREACH_WEBHOOK_URL),
      zapierWebhook: Boolean(process.env.ZAPIER_OUTREACH_WEBHOOK_URL),
      adminToken: Boolean(process.env.OUTREACH_ADMIN_TOKEN),
    };
    const criticalReady = checks.mongodb && checks.gmailClientId && checks.gmailClientSecret && checks.gmailRefreshToken && checks.gmailFromAddress && checks.adminToken;
    return NextResponse.json({ ok: criticalReady, checks }, { status: criticalReady ? 200 : 503, headers: { 'Cache-Control': 'no-store' } });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status: 401 });
  }
}
