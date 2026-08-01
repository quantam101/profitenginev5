import { createFollowUp } from '../repositories/follow-up.repository.mjs';
import { createActivity } from '../repositories/activity.repository.mjs';

export const STAGE_FOLLOW_UP_RULES = {
  'Research': { days: 1, summary: 'Review new target and confirm fit', priority: 'MEDIUM' },
  'Qualified': { days: 1, summary: 'Confirm qualification and next action', priority: 'MEDIUM' },
  'Approval Needed': { days: 1, summary: 'Review opportunity for approval', priority: 'HIGH' },
  'Outreach Approved': { days: 0, summary: 'Send outreach through approved workflow', priority: 'HIGH' },
  'Contacted': { days: 3, summary: 'Follow up if no response', priority: 'HIGH' },
  'Conversation': { days: 3, summary: 'Advance the conversation', priority: 'MEDIUM' },
  'Proposal': { days: 3, summary: 'Check proposal status', priority: 'HIGH' },
  'Negotiation': { days: 3, summary: 'Push negotiation forward', priority: 'HIGH' },
  'Won': { days: 30, summary: 'Long-term nurture and onboarding check-in', priority: 'LOW' },
  'Lost': { days: 30, summary: 'Long-term nurture', priority: 'LOW' },
  'On Hold': { days: 7, summary: 'Re-activate stalled opportunity', priority: 'MEDIUM' },
};

export function addBusinessDays(startDate, days) {
  const date = new Date(startDate);
  let added = 0;
  while (added < days) {
    date.setDate(date.getDate() + 1);
    const day = date.getDay();
    if (day !== 0 && day !== 6) added++;
  }
  return date;
}

export function calculateNextFollowUpDate(stage, lastActivityDate = new Date()) {
  const rule = STAGE_FOLLOW_UP_RULES[stage] || STAGE_FOLLOW_UP_RULES['Research'];
  if (rule.days === 0) return new Date(lastActivityDate);
  return addBusinessDays(lastActivityDate, rule.days);
}

export async function onOpportunityCreated(opportunity, actor) {
  const stage = opportunity.stage || 'Research';
  const dueDate = calculateNextFollowUpDate(stage, opportunity.createdAt);
  const rule = STAGE_FOLLOW_UP_RULES[stage] || STAGE_FOLLOW_UP_RULES['Research'];
  const followUp = await createFollowUp({
    entityType: 'opportunity',
    entityId: opportunity._id,
    type: 'new_opportunity',
    summary: `${rule.summary} — ${opportunity.title}`,
    dueDate,
    assignedTo: opportunity.assignedTo,
    priority: rule.priority,
  });
  await createActivity({
    entityType: 'opportunity',
    entityId: opportunity._id,
    actionType: 'created',
    actor,
    summary: `Created opportunity "${opportunity.title}" in ${stage}`,
    metadata: { stage, followUpId: followUp._id },
  });
  return followUp;
}

export async function onOpportunityStageChanged(opportunity, previousStage, actor) {
  const stage = opportunity.stage;
  const dueDate = calculateNextFollowUpDate(stage, opportunity.updatedAt);
  const rule = STAGE_FOLLOW_UP_RULES[stage] || STAGE_FOLLOW_UP_RULES['Research'];
  const followUp = await createFollowUp({
    entityType: 'opportunity',
    entityId: opportunity._id,
    type: 'stage_changed',
    summary: `${rule.summary} — ${opportunity.title}`,
    dueDate,
    assignedTo: opportunity.assignedTo,
    priority: rule.priority,
  });
  await createActivity({
    entityType: 'opportunity',
    entityId: opportunity._id,
    actionType: 'stage_changed',
    actor,
    summary: `Advanced opportunity "${opportunity.title}" from ${previousStage} to ${stage}`,
    metadata: { previousStage, stage, followUpId: followUp._id },
  });
  return followUp;
}

export async function onNoActivity(opportunity, actor) {
  const stage = opportunity.stage;
  const dueDate = calculateNextFollowUpDate(stage, new Date());
  const rule = STAGE_FOLLOW_UP_RULES[stage] || STAGE_FOLLOW_UP_RULES['Research'];
  const followUp = await createFollowUp({
    entityType: 'opportunity',
    entityId: opportunity._id,
    type: 'no_activity',
    summary: `No activity — ${rule.summary} — ${opportunity.title}`,
    dueDate,
    assignedTo: opportunity.assignedTo,
    priority: rule.priority === 'LOW' ? 'MEDIUM' : 'HIGH',
  });
  await createActivity({
    entityType: 'opportunity',
    entityId: opportunity._id,
    actionType: 'no_activity_alert',
    actor,
    summary: `No-activity alert for "${opportunity.title}"`,
    metadata: { stage, followUpId: followUp._id },
  });
  return followUp;
}
