import { getCollection } from '../../mongodb.mjs';
import { createActivity } from '../repositories/activity.repository.mjs';

const SLACK_ENABLED = String(process.env.REVENUE_OS_SLACK_ENABLED).toLowerCase() === 'true';
const SLACK_WEBHOOK_URL = process.env.SLACK_REVENUE_WEBHOOK || '';
const SLACK_TIMEOUT_MS = Number(process.env.SLACK_TIMEOUT_MS || 10000);

const COLLECTION = 'slack_notifications';

let indexesEnsured = false;

async function ensureIndexes() {
  if (indexesEnsured) return;
  const col = await getCollection(COLLECTION);
  await col.createIndex({ channel: 1, createdAt: -1 });
  await col.createIndex({ notificationType: 1 });
  indexesEnsured = true;
}

async function persistNotification(doc) {
  await ensureIndexes();
  const col = await getCollection(COLLECTION);
  const result = await col.insertOne(doc);
  return { _id: result.insertedId, ...doc };
}

export function isSlackEnabled() {
  return SLACK_ENABLED && SLACK_WEBHOOK_URL.startsWith('https://hooks.slack.com/');
}

/**
 * Send a notification to the configured Slack incoming webhook.
 * The channel is logged locally; the actual target channel is controlled by the webhook URL.
 * @param {{ notificationType: string, channel?: string, text: string, blocks?: any[], actor?: string }} options
 * @returns {Promise<{ ok: boolean, sent: boolean, reason?: string, error?: string }>}
 */
export async function sendSlackNotification({ notificationType, channel, text, blocks, actor = 'system' }) {
  const payload = {
    notificationType: String(notificationType),
    channel: String(channel || 'revenue-ops'),
    text: String(text || ''),
    blocks: blocks || undefined,
    status: 'SKIPPED',
    responseStatus: undefined,
    error: undefined,
    createdAt: new Date(),
  };

  if (!isSlackEnabled()) {
    await persistNotification(payload);
    return { ok: true, sent: false, reason: 'Slack notifications are disabled or not configured' };
  }

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(new Error('Slack request timeout')), SLACK_TIMEOUT_MS);
    const response = await fetch(SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: `[${payload.channel}] ${payload.text}`,
        blocks,
      }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    payload.status = response.ok ? 'SENT' : 'FAILED';
    payload.responseStatus = response.status;
  } catch (error) {
    payload.status = 'FAILED';
    payload.error = String(error?.message || error);
  }

  const record = await persistNotification(payload);
  await createActivity({
    entityType: 'slack_notification',
    entityId: record._id,
    actionType: payload.status.toLowerCase(),
    actor,
    summary: `Slack ${notificationType} ${payload.status}`,
    metadata: { channel: payload.channel, status: payload.status, responseStatus: payload.responseStatus },
  });

  return { ok: payload.status === 'SENT', sent: payload.status === 'SENT', status: payload.status, error: payload.error };
}

/** @param {{ summary: Record<string, unknown>, actor?: string }} options */
export async function notifyDailySummary({ summary, actor = 'system' }) {
  const text = `Daily Revenue Summary\nActive opportunities: ${summary.activeOpportunities}\nWeighted pipeline: $${Math.round(summary.weightedPipelineValue || 0).toLocaleString()}\nFollow-ups due: ${summary.followUpsDueToday || 0}`;
  return sendSlackNotification({ notificationType: 'daily_summary', channel: '#revenue-ops', text, actor });
}

/** @param {{ opportunity: Record<string, unknown>, revenuePlay?: Record<string, unknown>, actor?: string }} options */
export async function notifyHighScoreOpportunity({ opportunity, revenuePlay, actor = 'system' }) {
  const text = `High-score opportunity added: ${opportunity.title} (${revenuePlay?.revenuePlayName || 'unknown play'}) — weighted value $${Math.round(opportunity.weightedValue || 0).toLocaleString()}`;
  return sendSlackNotification({ notificationType: 'high_score_opportunity', channel: '#revenue-ops', text, actor });
}

/** @param {{ followUp: Record<string, unknown>, actor?: string }} options */
export async function notifyFollowUpOverdue({ followUp, actor = 'system' }) {
  const text = `Follow-up overdue: ${followUp.summary} (due ${new Date(followUp.dueDate).toLocaleDateString()})`;
  return sendSlackNotification({ notificationType: 'follow_up_overdue', channel: '#revenue-ops', text, actor });
}

/** @param {{ opportunity: Record<string, unknown>, actor?: string }} options */
export async function notifyProposalAwaitingApproval({ opportunity, actor = 'system' }) {
  const text = `Proposal awaiting approval: ${opportunity.title} — $${Math.round(opportunity.estimatedValue || 0).toLocaleString()}`;
  return sendSlackNotification({ notificationType: 'proposal_awaiting_approval', channel: '#office-command', text, actor });
}

/** @param {{ opportunity: Record<string, unknown>, company?: Record<string, unknown>, actor?: string }} options */
export async function notifyDealWon({ opportunity, company, actor = 'system' }) {
  const text = `Deal won: ${opportunity.title} (${company?.displayName || 'Unknown'}) — $${Math.round(opportunity.estimatedValue || 0).toLocaleString()}`;
  return sendSlackNotification({ notificationType: 'deal_won', channel: '#deals-won', text, actor });
}

/** @param {{ opportunity: Record<string, unknown>, actor?: string }} options */
export async function notifyDispatchReadyWork({ opportunity, actor = 'system' }) {
  const text = `New dispatch-ready work: ${opportunity.title} — stage ${opportunity.stage}`;
  return sendSlackNotification({ notificationType: 'dispatch_ready', channel: '#avery-dispatch', text, actor });
}
