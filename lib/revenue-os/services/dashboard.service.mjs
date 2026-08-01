import { getCollection } from '../../mongodb.mjs';
import { aggregateDashboardStats, countOpportunitiesByStage, findOpportunities } from '../repositories/opportunity.repository.mjs';
import { findRevenuePlays } from '../repositories/revenue-play.repository.mjs';
import { findFollowUps } from '../repositories/follow-up.repository.mjs';

const MONTHLY_REVENUE_TARGET = Number(process.env.REVENUE_OS_MONTHLY_TARGET) || 0;

export async function getDashboardSummary({ limit = 10 } = {}) {
  const stats = await aggregateDashboardStats();
  const pipelineByStage = await countOpportunitiesByStage();
  const revenueWonThisMonth = await getRevenueWonThisMonth();

  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000 - 1);

  const followUpsDueTodayResult = await findFollowUps({
    status: 'OPEN',
    dueBefore: endOfDay,
    dueAfter: startOfDay,
    limit: 100,
  });

  const topOpportunities = await findOpportunities({
    active: true,
    sortBy: 'weightedValue',
    order: 'desc',
    limit,
  });

  const topRecommendedActions = buildRecommendedActions(topOpportunities.records, followUpsDueTodayResult.records, limit);

  const highestScoringRevenuePlaysResult = await findRevenuePlays({ sortBy: 'overallScore', order: 'desc', limit });
  const highestScoringRevenuePlays = highestScoringRevenuePlaysResult.records.map((p) => ({
    recordId: p.recordId,
    revenuePlayName: p.revenuePlayName,
    lane: p.lane,
    overallScore: p.overallScore,
    location: p.location,
  }));

  const followUpsDue = followUpsDueTodayResult.records.slice(0, limit).map((f) => ({
    id: String(f._id),
    entityType: f.entityType,
    summary: f.summary,
    dueDate: f.dueDate ? new Date(f.dueDate).toISOString() : '',
    priority: f.priority,
  }));

  return {
    ...stats,
    followUpsDueToday: followUpsDueTodayResult.total,
    revenueWonThisMonth,
    revenueTargetProgress: MONTHLY_REVENUE_TARGET ? (revenueWonThisMonth / MONTHLY_REVENUE_TARGET) * 100 : 0,
    topRecommendedActions,
    pipelineByStage,
    highestScoringRevenuePlays,
    followUpsDue,
  };
}

async function getRevenueWonThisMonth() {
  const col = await getCollection('opportunities');
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  const result = await col
    .aggregate([
      { $match: { stage: 'Won', updatedAt: { $gte: start, $lt: end } } },
      { $group: { _id: null, total: { $sum: '$estimatedValue' } } },
    ])
    .toArray();
  return result.length ? result[0].total : 0;
}

function buildRecommendedActions(opportunities, followUpsDue, limit = 10) {
  const actions = [];

  for (const o of opportunities.slice(0, limit)) {
    actions.push({
      title: o.title,
      entityType: 'opportunity',
      entityId: String(o._id),
      reason: `High-value ${o.stage.toLowerCase()} opportunity (weighted $${Math.round(o.weightedValue || 0).toLocaleString()})`,
      score: o.probability,
      estimatedValue: o.estimatedValue,
    });
  }

  for (const f of followUpsDue.slice(0, limit)) {
    actions.push({
      title: f.summary,
      entityType: f.entityType,
      entityId: String(f.entityId),
      reason: `Follow-up due ${new Date(f.dueDate).toLocaleDateString()}`,
      score: f.priority === 'HIGH' ? 0.9 : 0.6,
    });
  }

  actions.sort((a, b) => (b.score || 0) - (a.score || 0));
  return actions.slice(0, limit);
}
