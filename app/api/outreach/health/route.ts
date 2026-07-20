import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../../lib/outreach/auth';

export async function GET(request: Request) {
  try {
    requireOutreachAdmin(request);
    const oauthReady = Boolean(process.env.GMAIL_CLIENT_ID && process.env.GMAIL_CLIENT_SECRET && process.env.GMAIL_REFRESH_TOKEN);
    const smtpReady = Boolean(process.env.GMAIL_USER && process.env.GMAIL_APP_PASSWORD);
    const checks = {
      mongodb: Boolean(process.env.MONGODB_URI),
      gmailOAuth: oauthReady,
      gmailSmtp: smtpReady,
      gmailFromAddress: Boolean(process.env.GMAIL_FROM_ADDRESS ?? process.env.GMAIL_USER),
      slackWebhook: Boolean(process.env.SLACK_OUTREACH_WEBHOOK_URL ?? process.env.PROFITENGINE_SLACK_WEBHOOK_URL),
      zapierWebhook: Boolean(process.env.ZAPIER_OUTREACH_WEBHOOK_URL),
      adminToken: Boolean(process.env.OUTREACH_ADMIN_TOKEN ?? process.env.PROFITENGINE_WEBHOOK_TOKEN),
    };
    const criticalReady = checks.mongodb && (checks.gmailOAuth || checks.gmailSmtp) && checks.gmailFromAddress && checks.adminToken;
    return NextResponse.json({ ok: criticalReady, checks }, { status: criticalReady ? 200 : 503, headers: { 'Cache-Control': 'no-store' } });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status: 401 });
  }
}
