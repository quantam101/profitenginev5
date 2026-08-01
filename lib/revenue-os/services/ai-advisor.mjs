import { findOpportunities, getOpportunityById } from '../repositories/opportunity.repository.mjs';
import { getCompanyById, findCompanies } from '../repositories/company.repository.mjs';
import { getContactById, findContacts } from '../repositories/contact.repository.mjs';
import { getRevenuePlayById } from '../repositories/revenue-play.repository.mjs';
import { createAIAction, getAIActionById, updateAIActionStatus, findAIActions, deleteExpiredActions } from '../repositories/ai-action.repository.mjs';
import { createActivity } from '../repositories/activity.repository.mjs';

/** @typedef {import('../types').AIAction} AIAction */
/** @typedef {import('../types').DataQualityFlag} DataQualityFlag */
/** @typedef {import('../types').OpportunityRanking} OpportunityRanking */

const LOCAL_MODEL_ENABLED = String(process.env.GMAOS_LOCAL_MODEL_ENABLED).toLowerCase() === 'true';
const LOCAL_MODEL_ENDPOINT = (process.env.GMAOS_LOCAL_MODEL_ENDPOINT || 'http://localhost:11434').replace(/\/$/, '');
const LOCAL_MODEL_NAME = process.env.GMAOS_LOCAL_MODEL_NAME || 'llama3.1:8b';
const LOCAL_MODEL_TIMEOUT = Number(process.env.GMAOS_LOCAL_MODEL_TIMEOUT || 120) * 1000;

export const VALID_STATUSES = ['Draft', 'Needs Review', 'Approved', 'Rejected', 'Executed', 'Expired'];

const NEXT_ACTION_BY_STAGE = {
  Research: 'Confirm target fit and collect location/contacts',
  Qualified: 'Prepare outreach draft for approval',
  'Approval Needed': 'Route to human reviewer for outreach approval',
  'Outreach Approved': 'Send the approved outreach message',
  Contacted: 'Follow up if no response within 3 business days',
  Conversation: 'Schedule capability review or proposal call',
  Proposal: 'Finalize scope and pricing, send proposal for approval',
  Negotiation: 'Confirm terms and close the deal',
  Won: 'Schedule onboarding and route-stacking',
  Lost: 'Archive and capture lessons learned',
  'On Hold': 'Re-engage at the next planned checkpoint',
};

const DRAFT_TEMPLATES = {
  intro_email: (ctx) => `Subject: ${ctx.company?.displayName || 'there'} — ${ctx.play?.painSolved || 'field service support'}

Hi ${ctx.contact?.fullName || 'team'},

I noticed ${ctx.company?.displayName || 'your organization'} ${ctx.play?.buyerType ? `is a ${ctx.play.buyerType}` : ''} and may be dealing with ${ctx.play?.painSolved || 'operational challenges'}.

Already Here LLC helps ${ctx.play?.exampleTargetCompanyOrMarket || 'companies like yours'} with ${ctx.play?.revenuePlayName || 'specialized support'} — typically ${ctx.play?.estimatedTicketValue ? `$${ctx.play.estimatedTicketValue.minimum}-$${ctx.play.estimatedTicketValue.maximum} per ${ctx.play.estimatedTicketValue.unit}` : 'competitive rates'}.

Could we schedule a 15-minute call this week to see if there is a fit?

Best,
Already Here LLC`,
  follow_up_email: (ctx) => `Hi ${ctx.contact?.fullName || 'team'},

Quick follow-up on my note about ${ctx.play?.revenuePlayName || 'our service'}.

${ctx.opportunity?.nextAction ? `Next step: ${ctx.opportunity.nextAction}` : 'Would you like a short capability overview?'}

Best,
Already Here LLC`,
  capability_statement: (ctx) => `Already Here LLC delivers ${ctx.play?.revenuePlayName || 'field operations support'} to ${ctx.play?.buyerType || 'qualified buyers'}.

• Pain solved: ${ctx.play?.painSolved || 'operational bottlenecks'}
• Typical value: ${ctx.play?.estimatedTicketValue ? `$${ctx.play.estimatedTicketValue.minimum}-$${ctx.play.estimatedTicketValue.maximum} per ${ctx.play.estimatedTicketValue.unit}` : 'contact for quote'}
• Time to revenue: ${ctx.play?.timeToRevenueDays ? `${ctx.play.timeToRevenueDays} days` : 'rapid deployment'}
• Recurring potential: ${ctx.play?.recurringPotential ? `${ctx.play.recurringPotential}` : 'yes'}

Contact: ${ctx.contact?.fullName || 'our team'} ${ctx.contact?.email ? `(${ctx.contact.email})` : ''}`,
  call_script: (ctx) => `1. Opening: "Hi ${ctx.contact?.fullName || 'there'}, this is Already Here LLC. We work with ${ctx.play?.buyerType || 'companies like yours'} to ${ctx.play?.painSolved || 'solve operational challenges'}."
2. Hook: "We typically see ${ctx.play?.painSolved || 'this issue'} in ${ctx.play?.exampleTargetCompanyOrMarket || 'your market'}."
3. Question: "What does that look like for ${ctx.company?.displayName || 'your team'} right now?"
4. Value: "Our ${ctx.play?.revenuePlayName || 'solution'} runs about ${ctx.play?.estimatedTicketValue ? `$${ctx.play.estimatedTicketValue.minimum}-$${ctx.play.estimatedTicketValue.maximum} per ${ctx.play.estimatedTicketValue.unit}` : 'a competitive rate'} and can be live in ${ctx.play?.timeToRevenueDays || 'a few'} days."
5. Close: "Can we book a 20-minute walkthrough this week?"`,
  proposal_summary: (ctx) => `Proposal Summary: ${ctx.opportunity?.title || ctx.play?.revenuePlayName || 'Engagement'}
Client: ${ctx.company?.displayName || 'Prospect'}
Scope: ${ctx.play?.revenuePlayName || 'Service engagement'} — ${ctx.play?.painSolved || 'address operational need'}
Estimated value: $${ctx.opportunity?.estimatedValue?.toLocaleString?.() || ctx.opportunity?.estimatedValue || 0}
Recurring monthly value: $${ctx.opportunity?.recurringMonthlyValue?.toLocaleString?.() || ctx.opportunity?.recurringMonthlyValue || 0}
Time to launch: ${ctx.play?.timeToRevenueDays ? `${ctx.play.timeToRevenueDays} days` : 'TBD'}
Start-up requirements: ${(ctx.play?.startupRequirements || []).join(', ') || 'standard onboarding'}`,
  sow_draft: (ctx) => `Statement of Work — Draft

1. Background
${ctx.company?.displayName || 'Client'} needs ${ctx.play?.painSolved || 'operational support'}.

2. Scope
Deliver ${ctx.play?.revenuePlayName || 'the service'} to ${ctx.play?.exampleTargetCompanyOrMarket || 'specified locations'}.

3. Pricing
Estimated ticket value: ${ctx.play?.estimatedTicketValue ? `$${ctx.play.estimatedTicketValue.minimum}-$${ctx.play.estimatedTicketValue.maximum} per ${ctx.play.estimatedTicketValue.unit}` : 'per agreement'}.
Recurring monthly value: $${ctx.opportunity?.recurringMonthlyValue || 0}.

4. Timeline
First value within ${ctx.play?.timeToRevenueDays || 'TBD'} days of approval.

5. Acceptance
Client signature and initial deposit before work begins.`,
};

async function callLocalModel(system, user, maxTokens = 512) {
  if (!LOCAL_MODEL_ENABLED) return null;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(new Error('Ollama timeout')), LOCAL_MODEL_TIMEOUT);
    const response = await fetch(`${LOCAL_MODEL_ENDPOINT}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: LOCAL_MODEL_NAME,
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: user },
        ],
        stream: false,
        options: { num_predict: maxTokens },
      }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!response.ok) return null;
    const body = await response.json();
    return typeof body?.message?.content === 'string' ? body.message.content : null;
  } catch {
    return null;
  }
}

async function loadOpportunityContext(opportunityId) {
  const opportunity = await getOpportunityById(opportunityId);
  if (!opportunity) return null;
  const [company, revenuePlay] = await Promise.all([
    opportunity.companyId ? getCompanyById(opportunity.companyId) : null,
    opportunity.revenuePlayId ? getRevenuePlayById(opportunity.revenuePlayId) : null,
  ]);
  const primaryContactId = opportunity.contactIds?.[0];
  const contact = primaryContactId ? await getContactById(primaryContactId) : null;
  return { opportunity, company, revenuePlay, contact };
}

/**
 * @param {{ limit?: number }} [options]
 * @returns {Promise<OpportunityRanking[]>}
 */
export async function rankOpportunities(options = {}) {
  const limit = options?.limit || 10;
  const result = await findOpportunities({ active: true, sortBy: 'weightedValue', order: 'desc', limit });
  const rankings = [];
  for (const o of result.records) {
    const ctx = await loadOpportunityContext(o._id);
    const play = ctx?.revenuePlay;
    const startupRequirements = Array.isArray(play?.startupRequirements) ? play.startupRequirements : [];
    const expectedRevenue = Number(o.estimatedValue) || 0;
    const score = Number(o.weightedValue) || 0;
    rankings.push({
      opportunityId: String(o._id),
      title: o.title,
      stage: o.stage,
      expectedRevenue,
      startupRequirements,
      recommendedNextAction: NEXT_ACTION_BY_STAGE[o.stage] || 'Review and advance',
      reason: `Weighted value $${Math.round(score).toLocaleString()} from ${play?.revenuePlayName || 'opportunity'}; probability ${Math.round((o.probability || 0) * 100)}%`,
      score,
    });
  }
  return rankings;
}

/**
 * @param {{ type?: string, opportunityId: string, overrides?: Record<string, unknown> }} options
 * @returns {Promise<{ ok: true, type: string, content: string, context: Record<string, string | undefined> } | { ok: false, error: string }>}
 */
export async function generateDraft(options) {
  const opts = options || {};
  const type = DRAFT_TEMPLATES[opts.type] ? opts.type : 'intro_email';
  const ctx = await loadOpportunityContext(opts.opportunityId);
  if (!ctx?.opportunity) {
    return { ok: false, error: 'Opportunity not found' };
  }

  const system = 'You are a concise, professional revenue-operations copywriter for Already Here LLC. Write only the requested draft. Do not include disclaimers or placeholders.';
  const user = `Draft a ${type.replace(/_/g, ' ')} for this opportunity:
Title: ${ctx.opportunity.title || ''}
Company: ${ctx.company?.displayName || ''}
Contact: ${ctx.contact?.fullName || ''}
Revenue play: ${ctx.revenuePlay?.revenuePlayName || ''}
Pain solved: ${ctx.revenuePlay?.painSolved || ''}
Ticket value: ${ctx.revenuePlay?.estimatedTicketValue ? `$${ctx.revenuePlay.estimatedTicketValue.minimum}-$${ctx.revenuePlay.estimatedTicketValue.maximum} per ${ctx.revenuePlay.estimatedTicketValue.unit}` : ''}
Next action: ${ctx.opportunity.nextAction || ''}`;

  let content = await callLocalModel(system, user, 700);
  if (!content) {
    content = DRAFT_TEMPLATES[type](ctx);
  }

  if (opts.overrides?.tone === 'formal') {
    content = content.replace(/Hi\b/g, 'Dear').replace(/Quick follow-up/g, 'Following up');
  }

  return {
    ok: true,
    type,
    content,
    context: {
      opportunityId: String(ctx.opportunity._id),
      companyId: ctx.company ? String(ctx.company._id) : undefined,
      revenuePlayId: ctx.revenuePlay ? String(ctx.revenuePlay._id) : undefined,
      contactId: ctx.contact ? String(ctx.contact._id) : undefined,
    },
  };
}

/**
 * @param {{ type?: string, opportunityId: string, actor: string, overrides?: Record<string, unknown> }} options
 * @returns {Promise<{ ok: true, action: AIAction } | { ok: false, error: string }>}
 */
export async function createDraftAction(options) {
  const opts = options || {};
  const draft = await generateDraft({ type: opts.type, opportunityId: opts.opportunityId, overrides: opts.overrides });
  if (!draft.ok) return draft;
  const action = await createAIAction({
    entityType: 'opportunity',
    entityId: draft.context.opportunityId,
    actionType: opts.type,
    content: draft.content,
    status: 'Draft',
    metadata: { context: draft.context, overrides: opts.overrides },
    createdBy: opts.actor,
    expiresAt: getDefaultExpiry(),
  });
  await createActivity({
    entityType: 'ai_action',
    entityId: action._id,
    actionType: 'draft_created',
    actor: opts.actor,
    summary: `Created ${opts.type} draft for opportunity ${draft.context.opportunityId}`,
    metadata: { opportunityId: draft.context.opportunityId, actionType: opts.type },
  });
  return { ok: true, action: { ...action, _id: String(action._id) } };
}

/**
 * @returns {Promise<DataQualityFlag[]>}
 */
export async function auditDataQuality() {
  const [opportunitiesResult, companiesResult, contactsResult] = await Promise.all([
    findOpportunities({ active: true, limit: 1000 }),
    findCompanies({ limit: 1000 }),
    findContacts({ limit: 1000 }),
  ]);
  const flags = [];
  const now = new Date();
  const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  for (const o of opportunitiesResult.records) {
    const ctx = await loadOpportunityContext(o._id);
    if (!o.contactIds || o.contactIds.length === 0) {
      flags.push({ entityType: 'opportunity', entityId: String(o._id), issue: 'No contacts linked', severity: 'high', suggestedFix: 'Add a contact for this opportunity' });
    }
    if (!o.location && !ctx?.company?.locations?.length) {
      flags.push({ entityType: 'opportunity', entityId: String(o._id), issue: 'Missing location', severity: 'medium', suggestedFix: 'Add company location or opportunity coordinates' });
    }
    if (!o.nextAction || String(o.nextAction).trim().length < 3) {
      flags.push({ entityType: 'opportunity', entityId: String(o._id), issue: 'No clear next action', severity: 'medium', suggestedFix: 'Set the next action in the opportunity record' });
    }
    if (!o.estimatedValue || o.estimatedValue <= 0) {
      flags.push({ entityType: 'opportunity', entityId: String(o._id), issue: 'Unsupported ticket estimate', severity: 'high', suggestedFix: 'Set a positive estimated value' });
    }
    if (o.nextFollowUpDate && new Date(o.nextFollowUpDate) < oneWeekAgo) {
      flags.push({ entityType: 'opportunity', entityId: String(o._id), issue: 'Old follow-up date', severity: 'medium', suggestedFix: 'Reschedule or complete the overdue follow-up' });
    }
    if (o.source && !['manual', 'import', 'verified'].includes(String(o.source).toLowerCase())) {
      flags.push({ entityType: 'opportunity', entityId: String(o._id), issue: 'Unverified source', severity: 'low', suggestedFix: 'Verify the opportunity source' });
    }
  }

  for (const c of companiesResult.records) {
    if (!c.locations?.length) {
      flags.push({ entityType: 'company', entityId: String(c._id), issue: 'No locations on company', severity: 'medium', suggestedFix: 'Add at least one location' });
    }
    if (!c.website && !c.domain && !c.legalName) {
      flags.push({ entityType: 'company', entityId: String(c._id), issue: 'Missing identifying information', severity: 'high', suggestedFix: 'Add legal name, website, or domain' });
    }
  }

  for (const c of contactsResult.records) {
    if (!c.email && !c.phone) {
      flags.push({ entityType: 'contact', entityId: String(c._id), issue: 'No reachable contact method', severity: 'medium', suggestedFix: 'Add email or phone' });
    }
  }

  return flags;
}

/**
 * @param {string} actionId
 * @param {string} actor
 * @returns {Promise<{ ok: true, action: AIAction } | { ok: false, error: string }>}
 */
export async function submitForReview(actionId, actor) {
  return transitionStatus(actionId, 'Needs Review', actor, ['Draft']);
}

/**
 * @param {string} actionId
 * @param {string} actor
 * @returns {Promise<{ ok: true, action: AIAction } | { ok: false, error: string }>}
 */
export async function approveAction(actionId, actor) {
  return transitionStatus(actionId, 'Approved', actor, ['Needs Review']);
}

/**
 * @param {string} actionId
 * @param {string} actor
 * @returns {Promise<{ ok: true, action: AIAction } | { ok: false, error: string }>}
 */
export async function rejectAction(actionId, actor) {
  return transitionStatus(actionId, 'Rejected', actor, ['Needs Review', 'Approved']);
}

/**
 * @param {string} actionId
 * @param {string} actor
 * @returns {Promise<{ ok: true, action: AIAction } | { ok: false, error: string }>}
 */
export async function executeApprovedAction(actionId, actor) {
  const action = await getAIActionById(actionId);
  if (!action) return { ok: false, error: 'Action not found' };
  if (action.status !== 'Approved') return { ok: false, error: 'Action must be Approved before execution' };

  // External actions (send email, post, spend, commit) are intentionally not wired here.
  // Execution only marks the action as Executed and writes an audit entry.
  const updated = await updateAIActionStatus(actionId, 'Executed', actor);
  await createActivity({
    entityType: 'ai_action',
    entityId: action._id,
    actionType: 'executed',
    actor,
    summary: `Executed ${action.actionType} action`,
    metadata: { previousStatus: 'Approved' },
  });
  return { ok: true, action: { ...updated, _id: String(updated._id) } };
}

/**
 * @param {Date} [before]
 * @returns {Promise<number>}
 */
export async function expireOldActions(before = new Date()) {
  const result = await deleteExpiredActions(before);
  return result.deletedCount;
}

/**
 * @param {string} actionId
 * @param {string} status
 * @param {string} actor
 * @param {string[]} allowedFrom
 * @returns {Promise<{ ok: true, action: AIAction } | { ok: false, error: string }>}
 */
async function transitionStatus(actionId, status, actor, allowedFrom) {
  const action = await getAIActionById(actionId);
  if (!action) return { ok: false, error: 'Action not found' };
  if (!allowedFrom.includes(action.status)) {
    return { ok: false, error: `Cannot move from ${action.status} to ${status}` };
  }
  const updated = await updateAIActionStatus(actionId, status, actor);
  await createActivity({
    entityType: 'ai_action',
    entityId: action._id,
    actionType: `status_${status.toLowerCase().replace(/\s+/g, '_')}`,
    actor,
    summary: `AI action ${action._id} moved to ${status}`,
    metadata: { previousStatus: action.status },
  });
  return { ok: true, action: { ...updated, _id: String(updated._id) } };
}

function getDefaultExpiry() {
  return new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
}

export { findAIActions };
