import { getCollection } from '../../mongodb.mjs';
import { findOpportunities, isActiveOpportunity, OPPORTUNITY_STAGES } from '../repositories/opportunity.repository.mjs';
import { findRevenuePlays } from '../repositories/revenue-play.repository.mjs';
import { findFollowUps } from '../repositories/follow-up.repository.mjs';

const MONTHLY_REVENUE_TARGET = Number(process.env.REVENUE_OS_MONTHLY_TARGET) || 0;

export async function getDashboardSummary({ limit = 10 } = {}) {
  const opportunities = await findOpportunities({ active: true, limit: 1000 });
  const activeRecords = opportunities.records.filter(isActiveOpportunity);
  const activeOpportunities = activeRecords.length;
  const weightedPipelineValue = activeRecords.reduce((sum, o) => sum + (o.weightedValue || 0), 0);
  const monthlyRecurringPotential = activeRecords.reduce((sum, o) => sum + (o.recurringMonthlyValue || 0), 0);
  const averageOpportunityScore = activeOpportunities
    ? activeRecords.reduce((sum, o) => sum + (o.probability || 0), 0) / activeOpportunities
    : 0;

  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000 - 1);

  const followUpsDueTodayResult = await findFollowUps({
    status: 'OPEN',
    dueBefore: endOfDay,
    dueAfter: startOfDay,
    limit: 1000,
  });
  const followUpsDueToday = followUpsDueTodayResult.total;

  const fastCashResult = await getFastCashOpportunities({ limit: 20 });
  const fastCashOpportunities = fastCashResult.total;

  const revenueWonThisMonth = await getRevenueWonThisMonth();

  const pipelineByStage = await countPipelineByStage();

  const topRecommendedActions = await getTopRecommendedActions(activeRecords, followUpsDueTodayResult.records, limit);

  const highestScoringRevenuePlaysResult = await findRevenuePlays({ sortBy: 'overallScore', order: 'desc', limit: 5 });
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
    activeOpportunities,
    weightedPipelineValue,
    monthlyRecurringPotential,
    followUpsDueToday,
    fastCashOpportunities,
    averageOpportunityScore,
    revenueWonThisMonth,
    revenueTargetProgress: MONTHLY_REVENUE_TARGET ? (revenueWonThisMonth / MONTHLY_REVENUE_TARGET) * 100 : 0,
    topRecommendedActions,
    pipelineByStage,
    highestScoringRevenuePlays,
    followUpsDue,
  };
}

async function getFastCashOpportunities({ limit = 20 } = {}) {
  const opportunities = await findOpportunities({ active: true, limit: 1000 });
  const fastRecords = opportunities.records.filter((o) => {
    const fastStages = ['Research', 'Qualified', 'Approval Needed', 'Outreach Approved', 'Contacted'];
    return fastStages.includes(o.stage);
  });
  return { records: fastRecords.slice(0, limit), total: fastRecords.length };
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

async function countPipelineByStage() {
  const col = await getCollection('opportunities');
  const rows = await col.aggregate([{ $group: { _id: '$stage', count: { $sum: 1 }, value: { $sum: '$estimatedValue' } } }]).toArray();
  const result = {};
  for (const stage of OPPORTUNITY_STAGES) result[stage] = { count: 0, value: 0 };
  for (const row of rows) {
    result[row._id] = { count: row.count, value: row.value || 0 };
  }
  return result;
}

async function getTopRecommendedActions(activeOpportunities, followUpsDue, limit = 10) {
  const actions = [];

  const staged = activeOpportunities
    .slice()
    .sort((a, b) => (b.weightedValue || 0) - (a.weightedValue || 0))
    .slice(0, limit);

  for (const o of staged) {
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
