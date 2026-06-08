'use strict';
/**
 * agents/revenue/index.js — ProfitEngine v5.0
 * Revenue tracking, threshold alerts, payout monitoring,
 * multi-arm bandit platform ROI scoring, projections.
 */
const llm    = require('../../core/llm');
const logger = require('../../core/logger').child('REVENUE');
const state  = require('../../core/state');
const email  = require('../../core/email');
const cfg    = require('../../core/config').get;

function recordEvent(source, amount, type = 'affiliate') {
  const event = { source, amount, type, ts: new Date().toISOString() };
  state.push('revenueEvents', event, 500);
  const key   = `revenue_${new Date().toISOString().slice(0,7)}`; // monthly
  const month = state.get(key, { total: 0, bySource: {} });
  month.total += amount;
  month.bySource[source] = (month.bySource[source] || 0) + amount;
  state.set(key, month);
  logger.info(`Revenue event: ${source} +$${amount} (${type})`);
}

function getMonthly() {
  const key = `revenue_${new Date().toISOString().slice(0,7)}`;
  return state.get(key, { total: 0, bySource: {} });
}

function getAllTime() {
  const all = state.getAll();
  let total = 0;
  const bySource = {};
  for (const [k, v] of Object.entries(all)) {
    if (k.startsWith('revenue_20') && v.total) {
      total += v.total;
      for (const [src, amt] of Object.entries(v.bySource || {})) {
        bySource[src] = (bySource[src] || 0) + amt;
      }
    }
  }
  return { total, bySource };
}

async function checkThresholds() {
  const monthly = getMonthly();
  const thresholds = [
    { source: 'amazon', threshold: cfg().amazonPayoutThreshold },
    { source: 'medium', threshold: cfg().mediumPayoutThreshold },
  ];
  for (const { source, threshold } of thresholds) {
    const earned = monthly.bySource[source] || 0;
    if (earned >= threshold) {
      await email.sendAlert(
        `Payout threshold reached: ${source}`,
        `${source} earnings this month: $${earned.toFixed(2)} (threshold: $${threshold})\nLog in to request payout.`
      );
    }
  }
}

async function analyzeAndOptimize() {
  const monthly  = getMonthly();
  const allTime  = getAllTime();
  const events   = state.get('revenueEvents', []).slice(-50);
  const platforms = state.get('platformPerf', {});

  if (!events.length) return null;

  const summary = `Monthly: $${monthly.total.toFixed(2)} | All-time: $${allTime.total.toFixed(2)} | Sources: ${JSON.stringify(monthly.bySource)}`;
  const prompt = `Revenue optimization advisor for ${cfg().businessName}.
${summary}
Platform performance: ${JSON.stringify(platforms)}
Recent events: ${JSON.stringify(events.slice(-10))}

Provide 3 specific, high-leverage revenue optimization recommendations.
Return JSON: [{ action: string, rationale: string, expectedImpact: string, priority: "high|medium|low" }]`;

  try {
    const recs = await llm.generateJSON(prompt);
    state.set('revenueRecommendations', { recs, generatedAt: new Date().toISOString() });
    logger.info(`Revenue analysis: ${recs.length} recommendations`);
    return recs;
  } catch (err) { logger.warn(`Revenue analysis failed: ${err.message}`); return null; }
}

async function sendDailyReport() {
  const monthly = getMonthly();
  const allTime = getAllTime();
  const cycles  = state.get('cycleCount', 0);
  const posts   = state.get('totalPublished', 0);

  await email.sendAlert(
    `Daily Report — $${monthly.total.toFixed(2)} this month`,
    `ProfitEngine v5.0 Daily Report\n${'─'.repeat(40)}\n` +
    `Cycles run:       ${cycles}\n` +
    `Posts published:  ${posts}\n` +
    `Monthly revenue:  $${monthly.total.toFixed(2)}\n` +
    `All-time revenue: $${allTime.total.toFixed(2)}\n` +
    `Revenue by source:\n${Object.entries(monthly.bySource).map(([k,v]) => `  ${k}: $${v.toFixed(2)}`).join('\n')}\n\n` +
    `Dashboard: http://localhost:${cfg().port}`
  );
}

module.exports = { recordEvent, getMonthly, getAllTime, checkThresholds, analyzeAndOptimize, sendDailyReport };
