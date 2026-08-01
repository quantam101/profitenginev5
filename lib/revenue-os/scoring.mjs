/**
 * Revenue OS weighted scoring engine.
 *
 * Weights:
 * - dailyRevenueScore      20%
 * - firstCashScore         18%
 * - repeatabilityScore     14%
 * - stackingScore          12%
 * - startupCostScore       10%
 * - liabilityScore          8%
 * - recurringScore         10%
 * - databaseValueScore      8%
 */

const WEIGHTS = {
  dailyRevenue: 0.20,
  firstCash: 0.18,
  repeatability: 0.14,
  stacking: 0.12,
  startupCost: 0.10,
  liability: 0.08,
  recurring: 0.10,
  databaseValue: 0.08,
};

function scoreFromInputs(inputs, key, fallback) {
  if (inputs && typeof inputs[key] === 'number') {
    return (inputs[key] / 20) * 100;
  }
  return typeof fallback === 'function' ? fallback() : fallback;
}

function dailyRevenueScore(play) {
  return scoreFromInputs(play.scoreInputs, 'dailyRevenuePotential', () => {
    const max = play.estimatedTicketValue?.maximum || 0;
    if (max >= 5000) return 100;
    if (max >= 1000) return 80;
    if (max >= 500) return 60;
    if (max >= 250) return 40;
    return 20;
  });
}

function firstCashScore(play) {
  return scoreFromInputs(play.scoreInputs, 'speedToFirstCash', () => {
    const days = play.timeToRevenueDays ?? 30;
    if (days <= 7) return 100;
    if (days <= 14) return 80;
    if (days <= 30) return 60;
    if (days <= 60) return 40;
    return 20;
  });
}

function repeatabilityScore(play) {
  return scoreFromInputs(play.scoreInputs, 'repeatability', () => (play.profitPotential ?? 0.5) * 100);
}

function stackingScore(play) {
  return scoreFromInputs(play.scoreInputs, 'routeStacking', () => (play.stackingFit ?? 0.5) * 100);
}

function startupCostScore(play) {
  return scoreFromInputs(play.scoreInputs, 'lowStartupCost', () => {
    const cost = play.costRequired ?? 0;
    if (cost === 0) return 100;
    if (cost <= 100) return 80;
    if (cost <= 500) return 60;
    if (cost <= 1000) return 40;
    return 20;
  });
}

function liabilityScoreFn(play) {
  return scoreFromInputs(play.scoreInputs, 'lowLiability', () => (play.liabilityScore ?? 0.5) * 100);
}

function recurringScore(play) {
  return scoreFromInputs(play.scoreInputs, 'recurringRetainer', () => (play.recurringPotential ?? 0.5) * 100);
}

function databaseValueScoreFn(play) {
  return scoreFromInputs(play.scoreInputs, 'databaseAiValue', () => (play.databaseValueScore ?? 0.5) * 100);
}

export function calculateOverallScore(play) {
  const scores = {
    dailyRevenue: dailyRevenueScore(play),
    firstCash: firstCashScore(play),
    repeatability: repeatabilityScore(play),
    stacking: stackingScore(play),
    startupCost: startupCostScore(play),
    liability: liabilityScoreFn(play),
    recurring: recurringScore(play),
    databaseValue: databaseValueScoreFn(play),
  };

  const overall =
    scores.dailyRevenue * WEIGHTS.dailyRevenue +
    scores.firstCash * WEIGHTS.firstCash +
    scores.repeatability * WEIGHTS.repeatability +
    scores.stacking * WEIGHTS.stacking +
    scores.startupCost * WEIGHTS.startupCost +
    scores.liability * WEIGHTS.liability +
    scores.recurring * WEIGHTS.recurring +
    scores.databaseValue * WEIGHTS.databaseValue;

  return Number(overall.toFixed(2));
}

export function calculateMetrics(play) {
  const ticket = play.estimatedTicketValue || { minimum: 0, maximum: 0, unit: 'project' };
  const avgTicket = (ticket.minimum + ticket.maximum) / 2;
  return {
    expectedFirst30DayRevenue: Number((avgTicket * 4).toFixed(2)),
    weightedPipelineValue: Number((avgTicket * (play.profitPotential || 0.5)).toFixed(2)),
    monthlyRecurringPotential: ticket.unit === 'month' ? avgTicket : Number((avgTicket * (play.recurringPotential || 0.5)).toFixed(2)),
  };
}
