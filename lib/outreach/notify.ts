import type { OutreachMessage } from './types';

async function postJson(url: string, payload: unknown) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) throw new Error(`Webhook failed: ${response.status}`);
}

export async function notifyOutreach(event: string, message: OutreachMessage) {
  const jobs: Promise<unknown>[] = [];
  const slackWebhook = process.env.SLACK_OUTREACH_WEBHOOK_URL ?? process.env.PROFITENGINE_SLACK_WEBHOOK_URL;
  const zapierWebhook = process.env.ZAPIER_OUTREACH_WEBHOOK_URL;

  if (slackWebhook) {
    jobs.push(postJson(slackWebhook, {
      text: [
        `Already Here outreach: ${event}`,
        `Company: ${message.company}`,
        `Lane: ${message.lane}`,
        `Status: ${message.status}`,
        `To: ${message.recipients.to.join(', ')}`,
        `Subject: ${message.subject}`,
        message.error ? `Error: ${message.error}` : '',
      ].filter(Boolean).join('\n'),
    }));
  }

  if (zapierWebhook) {
    jobs.push(postJson(zapierWebhook, { event, outreach: message }));
  }

  const results = await Promise.allSettled(jobs);
  return results.map((result) => result.status === 'fulfilled' ? 'ok' : result.reason instanceof Error ? result.reason.message : String(result.reason));
}
