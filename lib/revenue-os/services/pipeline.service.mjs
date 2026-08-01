import { getOpportunityById, updateOpportunity, updateOpportunityStage, getNextStage } from '../repositories/opportunity.repository.mjs';
import { onOpportunityStageChanged } from './follow-up.service.mjs';
import { createActivity } from '../repositories/activity.repository.mjs';

export async function advanceOpportunityStage(id, actor, targetStage) {
  const opportunity = await getOpportunityById(id);
  if (!opportunity) return { ok: false, error: 'Opportunity not found' };

  const previousStage = opportunity.stage;
  let nextStage = targetStage;

  if (!nextStage) {
    nextStage = getNextStage(previousStage);
  }
  if (!nextStage) {
    return { ok: false, error: `Cannot advance from ${previousStage}` };
  }

  const updated = await updateOpportunityStage(id, nextStage);
  const followUp = await onOpportunityStageChanged(updated, previousStage, actor);

  return { ok: true, opportunity: updated, previousStage, nextStage, followUp };
}

export async function setOpportunityStage(id, stage, actor) {
  const opportunity = await getOpportunityById(id);
  if (!opportunity) return { ok: false, error: 'Opportunity not found' };

  if (opportunity.stage === stage) {
    return { ok: true, opportunity, previousStage: stage, nextStage: stage };
  }

  const previousStage = opportunity.stage;
  const updated = await updateOpportunityStage(id, stage);
  const followUp = await onOpportunityStageChanged(updated, previousStage, actor);
  return { ok: true, opportunity: updated, previousStage, nextStage: stage, followUp };
}

export async function updateOpportunityNextAction(id, nextAction, actor) {
  const opportunity = await getOpportunityById(id);
  if (!opportunity) return { ok: false, error: 'Opportunity not found' };

  const updated = await updateOpportunity(id, { nextAction });
  await createActivity({
    entityType: 'opportunity',
    entityId: updated._id,
    actionType: 'next_action_updated',
    actor,
    summary: `Next action updated: ${nextAction}`,
    metadata: { previousNextAction: opportunity.nextAction },
  });
  return { ok: true, opportunity: updated };
}
